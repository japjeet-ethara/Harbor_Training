"""Linux subreaper supervision for verifier-launched untrusted processes."""

from __future__ import annotations

import ctypes
import errno
import os
import signal
import subprocess
import sys
import time
from pathlib import Path


SUBREAPER_UNAVAILABLE = "Linux child-subreaper supervision is unavailable"
CLEANUP_TIMEOUT_SEC = 3.0
TERM_GRACE_SEC = 0.25
_PR_SET_CHILD_SUBREAPER = 36
_PR_GET_CHILD_SUBREAPER = 37


class SupervisorError(RuntimeError):
    """The supervisor could not safely launch or contain a process tree."""


class SupervisorCleanupError(SupervisorError):
    """The supervisor could not confirm that all descendants were reaped."""


def _libc_prctl(option: int, value: int | ctypes.c_void_p) -> int:
    libc = ctypes.CDLL(None, use_errno=True)
    result = libc.prctl(option, value, 0, 0, 0)
    if result != 0:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error))
    return result


def _child_subreaper_enabled() -> bool:
    enabled = ctypes.c_int()
    _libc_prctl(_PR_GET_CHILD_SUBREAPER, ctypes.cast(ctypes.pointer(enabled), ctypes.c_void_p))
    return bool(enabled.value)


def _set_child_subreaper(enabled: bool) -> None:
    _libc_prctl(_PR_SET_CHILD_SUBREAPER, int(enabled))


def _process_start_time(pid: int) -> int | None:
    """Return field 22 from procfs stat, accounting for spaces in comm."""
    try:
        stat = Path(f"/proc/{pid}/stat").read_text(encoding="ascii")
    except FileNotFoundError:
        return None
    fields = stat.rsplit(")", 1)[1].split()
    return int(fields[19])


def _direct_children() -> dict[int, int]:
    """List direct children of every verifier thread with process identities."""
    if sys.platform != "linux":
        raise SupervisorError(SUBREAPER_UNAVAILABLE)
    children: dict[int, int] = {}
    try:
        for task in Path("/proc/self/task").iterdir():
            child_file = task / "children"
            for raw_pid in child_file.read_text(encoding="ascii").split():
                pid = int(raw_pid)
                started = _process_start_time(pid)
                if started is not None:
                    children[pid] = started
    except (OSError, ValueError, IndexError) as exc:
        raise SupervisorError("cannot enumerate verifier child processes") from exc
    return children


def terminate_process_group(pgid: int, process: subprocess.Popen | None = None) -> None:
    """Signal one group as a first pass; subreaper cleanup handles escaped groups."""
    group_exists = True
    try:
        os.killpg(pgid, signal.SIGTERM)
    except ProcessLookupError:
        group_exists = False
    except OSError:
        if process is not None:
            try:
                process.terminate()
            except OSError:
                pass

    if group_exists:
        deadline = time.monotonic() + TERM_GRACE_SEC
        while time.monotonic() < deadline:
            try:
                os.killpg(pgid, 0)
            except ProcessLookupError:
                group_exists = False
                break
            except OSError:
                break
            time.sleep(0.025)

    if group_exists:
        try:
            os.killpg(pgid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        except OSError:
            if process is not None:
                try:
                    process.kill()
                except OSError:
                    pass
    if process is not None:
        try:
            process.wait(timeout=1)
        except (subprocess.TimeoutExpired, OSError):
            try:
                process.kill()
            except OSError:
                pass
            try:
                process.wait(timeout=1)
            except (subprocess.TimeoutExpired, OSError):
                pass


def _signal_child(pid: int, sig: int) -> None:
    try:
        os.kill(pid, sig)
    except ProcessLookupError:
        pass
    except OSError as exc:
        if exc.errno != errno.ESRCH:
            raise SupervisorCleanupError(f"cannot signal adopted child {pid}") from exc


def _reap_nonblocking(pid: int) -> bool:
    try:
        waited, _status = os.waitpid(pid, os.WNOHANG)
    except ChildProcessError:
        return True
    except OSError as exc:
        if exc.errno == errno.ECHILD:
            return True
        raise SupervisorCleanupError(f"cannot reap adopted child {pid}") from exc
    return waited == pid


def _new_children(baseline: dict[int, int]) -> dict[int, int]:
    return {
        pid: started
        for pid, started in _direct_children().items()
        if baseline.get(pid) != started
    }


def _terminate_and_reap_descendants(baseline: dict[int, int]) -> None:
    """Kill adopted descendants iteratively, including nested/detached trees."""
    deadline = time.monotonic() + CLEANUP_TIMEOUT_SEC
    empty_observations = 0
    while time.monotonic() < deadline:
        active = _new_children(baseline)
        if not active:
            empty_observations += 1
            if empty_observations >= 2:
                return
            time.sleep(0.02)
            continue
        empty_observations = 0

        for pid in active:
            _signal_child(pid, signal.SIGTERM)
        term_deadline = min(deadline, time.monotonic() + TERM_GRACE_SEC)
        while time.monotonic() < term_deadline:
            current = _new_children(baseline)
            if not current:
                break
            for pid in current:
                _reap_nonblocking(pid)
            time.sleep(0.01)

        # Killing a direct child can reparent its own descendants to this
        # subreaper. The outer loop discovers and kills those children too.
        for pid in _new_children(baseline):
            _signal_child(pid, signal.SIGKILL)
            _reap_nonblocking(pid)
        time.sleep(0.01)

    remaining = _new_children(baseline)
    if remaining:
        raise SupervisorCleanupError(
            "descendant cleanup timed out; refusing to score or continue"
        )


def run_supervised_process(args: list[str], *, timeout: float,
                           extra_groups: tuple[int, ...] = (), **popen_kwargs) -> int | None:
    """Run a child and reap its entire descendant tree, regardless of process groups.

    Returns the exit status on normal completion, or None on timeout.
    Any failure to initialize supervision or prove cleanup raises SupervisorError.
    """
    if sys.platform != "linux":
        raise SupervisorError(SUBREAPER_UNAVAILABLE)

    try:
        previous_subreaper = _child_subreaper_enabled()
        baseline = _direct_children()
        _set_child_subreaper(True)
        if not _child_subreaper_enabled():
            raise SupervisorError("kernel did not enable child-subreaper mode")
    except (OSError, SupervisorError) as exc:
        if isinstance(exc, SupervisorError):
            raise
        raise SupervisorError("cannot initialize Linux child-subreaper supervision") from exc

    process = None
    timed_out = False
    returncode = None
    cleanup_complete = False
    try:
        process = subprocess.Popen(
            args, start_new_session=True, extra_groups=extra_groups, **popen_kwargs,
        )
        try:
            returncode = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
    finally:
        try:
            if process is not None:
                terminate_process_group(process.pid, process)
                if process.poll() is None:
                    process.kill()
                    process.wait(timeout=1)
            _terminate_and_reap_descendants(baseline)
            cleanup_complete = True
        except (OSError, subprocess.SubprocessError, SupervisorError) as exc:
            raise SupervisorCleanupError(
                "process supervision cleanup failed; refusing to continue"
            ) from exc
        finally:
            if cleanup_complete:
                try:
                    _set_child_subreaper(previous_subreaper)
                except OSError as exc:
                    raise SupervisorCleanupError(
                        "cannot restore verifier child-subreaper state"
                    ) from exc

    if timed_out:
        return None
    return returncode
