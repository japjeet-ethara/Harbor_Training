"""Linux process/build integration tests run inside the verifier test container.

These are not tests of Docker-engine isolation. They exercise the actual Unix
process cleanup and unprivileged build helpers used by the behavior criterion.
"""

import os
import re
import shutil
import shlex
import subprocess
import tempfile
import time
import types
import unittest
from unittest import mock
from pathlib import Path

sys_path = Path(__file__).resolve().parent / "checks"
import sys
sys.path.insert(0, str(sys_path))
sys.path.insert(0, str(sys_path / "behaviour"))

if "rewardkit.session" not in sys.modules:
    rewardkit = types.ModuleType("rewardkit")
    rewardkit.__path__ = []
    session = types.ModuleType("rewardkit.session")
    session.criterion = lambda **kwargs: (lambda fn: fn)
    rewardkit.session = session
    sys.modules["rewardkit"] = rewardkit
    sys.modules["rewardkit.session"] = session

from build_support import (  # noqa: E402
    BUILD_CPU_LIMIT_SEC,
    BUILD_FILE_LIMIT_BYTES,
    MAX_SOURCE_DEPTH,
    MAX_SOURCE_ENTRIES,
    MAX_SOURCE_FILE_BYTES,
    MAX_STAGED_BYTES,
    NOBODY_GID,
    NOBODY_UID,
    _go_build_commands,
    _limit_build_process,
    run_unprivileged_go_build,
    terminate_process_group,
)
import build_support  # noqa: E402
import process_supervisor  # noqa: E402
from behaviour import (  # noqa: E402
    CANDIDATE_GOMEMLIMIT,
    _candidate_environment,
    _limit_candidate,
    _run_candidate,
)


LINUX_ROOT = os.name == "posix" and hasattr(os, "geteuid") and os.geteuid() == 0
HAS_GO = shutil.which("go") is not None
SAFE_STAGING_AVAILABLE = (
    os.name == "posix"
    and hasattr(os, "O_NOFOLLOW")
    and hasattr(os, "O_DIRECTORY")
    and os.open in os.supports_dir_fd
)


class ResourceLimitConfigurationTests(unittest.TestCase):
    def test_behavior_build_checks_all_packages_then_builds_root_binary(self):
        self.assertEqual(
            _go_build_commands(Path("out"), Path("out/candidate"), ["titlecase", "titlecase/internal"]),
            [
                ["go", "build", "-o", str(Path("out/package-0")), "titlecase"],
                ["go", "build", "-o", str(Path("out/package-1")), "titlecase/internal"],
                ["go", "build", "-o", str(Path("out/candidate")), "."],
            ],
        )
        self.assertEqual(
            _go_build_commands(Path("out"), None, ["titlecase"]),
            [["go", "build", "-o", str(Path("out/package-0")), "titlecase"]],
        )

    def capture_limits(self, configure):
        resource = types.ModuleType("resource")
        names = (
            "RLIMIT_CPU", "RLIMIT_AS", "RLIMIT_FSIZE", "RLIMIT_NPROC",
            "RLIMIT_NOFILE", "RLIMIT_CORE",
        )
        for index, name in enumerate(names):
            setattr(resource, name, index)
        calls = {}
        resource.setrlimit = lambda kind, limits: calls.__setitem__(kind, limits)
        with mock.patch.dict(sys.modules, {"resource": resource}):
            configure()
        return calls

    def test_candidate_has_go_memory_guard_and_process_limits(self):
        limits = self.capture_limits(_limit_candidate)
        self.assertEqual(limits[0], (60, 60))
        self.assertEqual(limits[3], (32, 32))
        self.assertEqual(limits[4], (64, 64))
        self.assertEqual(limits[5], (0, 0))
        self.assertNotIn(1, limits)  # RLIMIT_AS can conflict with Go's address reservations.
        self.assertEqual(_candidate_environment()["GOMEMLIMIT"], CANDIDATE_GOMEMLIMIT)

    def test_build_has_cpu_file_and_process_limits(self):
        limits = self.capture_limits(_limit_build_process)
        self.assertEqual(limits[0], (BUILD_CPU_LIMIT_SEC, BUILD_CPU_LIMIT_SEC))
        self.assertEqual(limits[2], (BUILD_FILE_LIMIT_BYTES, BUILD_FILE_LIMIT_BYTES))
        self.assertEqual(limits[3], (64, 64))
        self.assertEqual(limits[4], (256, 256))
        self.assertEqual(limits[5], (0, 0))


class ReferenceStagingBudgetTests(unittest.TestCase):
    def test_reference_solution_and_existing_workspace_fit_staging_budgets(self):
        task_root = Path(__file__).resolve().parents[1]
        repo = task_root / "environment" / "repo"
        solution = (task_root / "solution" / "solve.sh").read_text(encoding="utf-8")
        generated = re.findall(
            r'cat > "\$repo/([^\"]+)" <<\'EOF\'\n(.*?)\nEOF',
            solution,
            flags=re.DOTALL,
        )
        generated_by_name = {name: (body + "\n").encode("utf-8") for name, body in generated}
        self.assertEqual(set(generated_by_name), {"go.mod", "main.go", "titlecase.go"})

        staged = {
            name: data for name, data in generated_by_name.items()
            if name in {"go.mod", "go.sum"} or Path(name).suffix in {".go", ".s", ".syso"}
        }
        self.assertLessEqual(max(map(len, staged.values())), MAX_SOURCE_FILE_BYTES)
        self.assertLessEqual(sum(map(len, staged.values())), MAX_STAGED_BYTES)

        existing_entries = []
        for path in repo.rglob("*"):
            relative = path.relative_to(repo)
            if relative.parts[0] == "titlecase" or (path.is_file() and path.suffix == ".py"):
                continue
            existing_entries.append(relative)
        final_entries = existing_entries + [Path(name) for name in generated_by_name]
        self.assertLessEqual(len(final_entries), MAX_SOURCE_ENTRIES)
        self.assertLessEqual(max(len(path.parts) for path in final_entries), MAX_SOURCE_DEPTH)


class SupervisorConfigurationTests(unittest.TestCase):
    def test_supervisor_passes_empty_supplementary_groups(self):
        process = types.SimpleNamespace(pid=12345, returncode=0)
        process.wait = lambda timeout=None: 0
        process.poll = lambda: 0
        with (
            mock.patch.object(process_supervisor, "_child_subreaper_enabled", side_effect=[False, True]),
            mock.patch.object(process_supervisor, "_set_child_subreaper"),
            mock.patch.object(process_supervisor, "_direct_children", return_value={}),
            mock.patch.object(process_supervisor, "_terminate_and_reap_descendants"),
            mock.patch.object(process_supervisor, "terminate_process_group"),
            mock.patch.object(process_supervisor.subprocess, "Popen", return_value=process) as popen,
            mock.patch.object(process_supervisor.sys, "platform", "linux"),
        ):
            self.assertEqual(
                process_supervisor.run_supervised_process(
                    ["fake"], timeout=1, user=65534, group=65534, extra_groups=(),
                ),
                0,
            )
        self.assertEqual(popen.call_args.kwargs["extra_groups"], ())

    def test_supervisor_initialization_failure_does_not_launch_child(self):
        with (
            mock.patch.object(process_supervisor.sys, "platform", "linux"),
            mock.patch.object(process_supervisor, "_child_subreaper_enabled", side_effect=OSError("no prctl")),
            mock.patch.object(process_supervisor.subprocess, "Popen") as popen,
        ):
            with self.assertRaises(process_supervisor.SupervisorError):
                process_supervisor.run_supervised_process(["candidate"], timeout=1)
        popen.assert_not_called()

    def test_cleanup_failure_raises_instead_of_falling_back(self):
        process = types.SimpleNamespace(pid=12345, returncode=0)
        process.wait = lambda timeout=None: 0
        process.poll = lambda: 0
        with (
            mock.patch.object(process_supervisor, "_child_subreaper_enabled", side_effect=[False, True]),
            mock.patch.object(process_supervisor, "_set_child_subreaper"),
            mock.patch.object(process_supervisor, "_direct_children", return_value={}),
            mock.patch.object(
                process_supervisor, "_terminate_and_reap_descendants",
                side_effect=process_supervisor.SupervisorCleanupError("test cleanup failure"),
            ),
            mock.patch.object(process_supervisor, "terminate_process_group"),
            mock.patch.object(process_supervisor.subprocess, "Popen", return_value=process),
            mock.patch.object(process_supervisor.sys, "platform", "linux"),
        ):
            with self.assertRaises(process_supervisor.SupervisorCleanupError):
                process_supervisor.run_supervised_process(["fake"], timeout=1)


@unittest.skipUnless(LINUX_ROOT and HAS_GO, "requires Linux root and Go")
class EscapedDescendantTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="subreaper-fixture-")
        cls.root = Path(cls.temp.name)
        cls.root.chmod(0o755)
        (cls.root / "go.mod").write_text("module supervisorfixture\n\ngo 1.23\n", encoding="utf-8")
        source = cls.root / "main.go"
        source.write_text(
            '''package main
import (
    "os"
    "os/exec"
    "strconv"
    "strings"
    "syscall"
    "time"
)
func shellQuote(value string) string {
    return "'" + strings.ReplaceAll(value, "'", `'\''`) + "'"
}
func main() {
    mode, parentPath, nestedPath, sleepPath := os.Args[1], os.Args[2], os.Args[3], os.Args[4]
    nested := "sleep 30 & echo $! > " + shellQuote(sleepPath) + "; wait"
    script := "sh -c " + shellQuote(nested) + " & echo $! > " + shellQuote(nestedPath) + "; wait"
    command := exec.Command("/bin/sh", "-c", script)
    attributes := &syscall.SysProcAttr{}
    if mode == "group" { attributes.Setpgid = true }
    if mode == "session" || mode == "nested" { attributes.Setsid = true }
    command.SysProcAttr = attributes
    if err := command.Start(); err != nil { os.Exit(20) }
    _ = os.WriteFile(parentPath, []byte(strconv.Itoa(command.Process.Pid)), 0666)
    deadline := time.Now().Add(2 * time.Second)
    for time.Now().Before(deadline) {
        if _, a := os.Stat(nestedPath); a == nil {
            if _, b := os.Stat(sleepPath); b == nil { os.Exit(0) }
        }
        time.Sleep(10 * time.Millisecond)
    }
    os.Exit(21)
}
''',
            encoding="utf-8",
        )
        env = os.environ.copy()
        env.update({"GOTELEMETRY": "off", "GOTOOLCHAIN": "local", "GOPROXY": "off", "CGO_ENABLED": "0"})
        result = subprocess.run(
            ["go", "build", "-o", str(cls.root / "fixture"), str(source)],
            cwd=cls.root, env=env, capture_output=True, text=True, timeout=120,
        )
        if result.returncode != 0:
            raise RuntimeError(f"failed to build process-supervisor fixture: {result.stderr}")
        (cls.root / "fixture").chmod(0o755)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="subreaper-run-")
        self.root = Path(self.temp.name)
        self.root.chmod(0o755)
        self.cwd = self.root / "cwd"
        self.cwd.mkdir()
        self.wrapper = self.root / "candidate.sh"
        self.pids = {}
        for name in ("parent", "nested", "sleep"):
            path = self.cwd / f"{name}.pid"
            path.touch()
            path.chmod(0o666)
            self.pids[name] = path

    def tearDown(self):
        self.temp.cleanup()

    def run_fixture(self, mode):
        args = " ".join(shlex.quote(str(self.pids[name])) for name in ("parent", "nested", "sleep"))
        self.wrapper.write_text(
            "#!/bin/sh\nexec " + shlex.quote(str(type(self).root / "fixture")) + f" {mode} {args}\n",
            encoding="utf-8",
        )
        self.wrapper.chmod(0o755)
        self.assertEqual(_run_candidate(self.wrapper, b"", self.cwd), b"")
        return [int(path.read_text(encoding="ascii")) for path in self.pids.values()]

    def assert_processes_gone(self, pids):
        for pid in pids:
            with self.subTest(pid=pid):
                with self.assertRaises(ProcessLookupError):
                    os.kill(pid, 0)

    def test_process_group_escape_is_terminated(self):
        self.assert_processes_gone(self.run_fixture("group"))

    def test_session_escape_is_terminated(self):
        self.assert_processes_gone(self.run_fixture("session"))

    def test_nested_descendants_are_reaped_after_parent_escape(self):
        self.assert_processes_gone(self.run_fixture("nested"))


@unittest.skipUnless(LINUX_ROOT, "requires Linux root and the nobody account")
class CandidateProcessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="candidate-process-test-")
        self.root = Path(self.temp.name)
        self.root.chmod(0o755)
        self.cwd = self.root / "cwd"
        self.cwd.mkdir()
        self.executable = self.root / "candidate.sh"

    def tearDown(self):
        self.temp.cleanup()

    def write_script(self, body):
        self.executable.write_text("#!/bin/sh\n" + body, encoding="utf-8")
        self.executable.chmod(0o755)
        return self.executable

    def test_ordinary_candidate(self):
        self.write_script("cat\n")
        self.assertEqual(_run_candidate(self.executable, b"hello\n", self.cwd), b"hello\n")

    def test_timeout_candidate_is_stopped(self):
        self.write_script("while :; do sleep 1; done\n")
        started = time.monotonic()
        self.assertIsNone(_run_candidate(self.executable, b"", self.cwd, timeout=0.1))
        self.assertLess(time.monotonic() - started, 3)

    def test_child_process_is_stopped_with_its_group(self):
        pid_file = self.cwd / "child.pid"
        pid_file.touch()
        pid_file.chmod(0o666)
        self.write_script(f"sleep 30 & echo $! > '{pid_file}'; wait\n")
        self.assertIsNone(_run_candidate(self.executable, b"", self.cwd, timeout=0.2))
        child_pid = int(pid_file.read_text(encoding="ascii"))
        deadline = time.monotonic() + 1
        while time.monotonic() < deadline:
            try:
                os.kill(child_pid, 0)
                stat_file = Path(f"/proc/{child_pid}/stat")
                if stat_file.exists() and stat_file.read_text().split()[2] == "Z":
                    return
            except ProcessLookupError:
                return
            time.sleep(0.025)
        self.fail("candidate child remained running after process-group cleanup")

    def test_sigterm_ignoring_candidate_is_killed(self):
        self.write_script("trap '' TERM; while :; do sleep 1; done\n")
        started = time.monotonic()
        self.assertIsNone(_run_candidate(self.executable, b"", self.cwd, timeout=0.1))
        self.assertLess(time.monotonic() - started, 3)

    def test_unrelated_nobody_sentinel_survives_cleanup(self):
        import grp
        import pwd

        self.assertEqual(pwd.getpwnam("nobody").pw_uid, NOBODY_UID)
        self.assertEqual(grp.getgrnam("nogroup").gr_gid, NOBODY_GID)
        sentinel = subprocess.Popen(
            ["/bin/sleep", "20"], stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            user="nobody", group="nogroup", start_new_session=True,
        )
        try:
            self.write_script("exit 0\n")
            self.assertEqual(_run_candidate(self.executable, b"", self.cwd), b"")
            self.assertIsNone(sentinel.poll(), "unrelated nobody process was killed")
        finally:
            terminate_process_group(sentinel.pid, sentinel)

    def test_excessive_stdout_is_rejected(self):
        self.write_script("head -c 1100000 /dev/zero\n")
        self.assertIsNone(_run_candidate(self.executable, b"", self.cwd))

    def test_excessive_stderr_is_rejected(self):
        self.write_script("head -c 1100000 /dev/zero >&2\n")
        self.assertIsNone(_run_candidate(self.executable, b"", self.cwd))

    def test_candidate_runs_with_runtime_memory_guard_environment(self):
        self.write_script("cat\n")
        self.assertEqual(
            _run_candidate(self.executable, b"memory guard\n", self.cwd),
            b"memory guard\n",
        )


@unittest.skipUnless(SAFE_STAGING_AVAILABLE, "requires POSIX dir_fd and O_NOFOLLOW support")
class SecureStagingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="secure-stage-test-")
        self.root = Path(self.temp.name)
        self.source = self.root / "submission"
        self.source.mkdir()
        self.destination = self.root / "staged"

    def tearDown(self):
        self.temp.cleanup()

    def write_main(self, directive=""):
        body = "package main\n"
        if directive:
            body += 'import _ "embed"\n' + directive + "\nvar embedded string\n"
        body += "func main() {}\n"
        (self.source / "main.go").write_text(body, encoding="utf-8")

    def staged_bytes(self):
        return b"".join(
            path.read_bytes()
            for path in self.destination.rglob("*")
            if path.is_file() and not path.is_symlink()
        )

    def test_normal_go_source_is_staged(self):
        self.write_main()
        build_support.copy_go_sources(self.source, self.destination)
        self.assertEqual((self.destination / "main.go").read_text(encoding="utf-8"),
                         (self.source / "main.go").read_text(encoding="utf-8"))

    def test_normal_embed_file_inside_workspace_is_staged(self):
        self.write_main("//go:embed data.txt")
        (self.source / "data.txt").write_text("workspace asset", encoding="utf-8")
        build_support.copy_go_sources(self.source, self.destination)
        self.assertEqual((self.destination / "data.txt").read_text(encoding="utf-8"), "workspace asset")

    def test_directory_depth_limit_is_enforced_iteratively(self):
        self.write_main()
        nested = self.source / "a" / "b" / "c"
        nested.mkdir(parents=True)
        (nested / "asset.txt").write_text("x", encoding="utf-8")
        with mock.patch.object(build_support, "MAX_SOURCE_DEPTH", 2):
            with self.assertRaisesRegex(ValueError, "directory-depth limit"):
                build_support.copy_go_sources(self.source, self.destination)

    def test_entry_count_limit_is_enforced(self):
        self.write_main()
        (self.source / "other.txt").write_text("x", encoding="utf-8")
        with mock.patch.object(build_support, "MAX_SOURCE_ENTRIES", 1):
            with self.assertRaisesRegex(ValueError, "entry-count limit"):
                build_support.copy_go_sources(self.source, self.destination)

    def test_individual_file_size_limit_counts_sparse_logical_size(self):
        self.write_main()
        sparse = self.source / "large.bin"
        with sparse.open("wb") as file:
            file.truncate(8 << 20)
        with mock.patch.object(build_support, "MAX_SOURCE_FILE_BYTES", 1 << 20):
            with self.assertRaisesRegex(ValueError, "individual-size limit"):
                build_support.copy_go_sources(self.source, self.destination)

    def test_aggregate_staging_limit_is_checked_before_copying_next_file(self):
        self.write_main("//go:embed data.txt")
        (self.source / "data.txt").write_bytes(b"0123456789")
        main_size = (self.source / "main.go").stat().st_size
        with mock.patch.object(build_support, "MAX_STAGED_BYTES", main_size + 4):
            with self.assertRaisesRegex(ValueError, "aggregate staging limit"):
                build_support.copy_go_sources(self.source, self.destination)
        self.assertLessEqual(
            sum(path.stat().st_size for path in self.destination.rglob("*") if path.is_file()),
            main_size + 4,
        )

    def test_final_component_symlink_is_rejected(self):
        self.write_main("//go:embed secret.txt")
        outside = self.root / "outside.txt"
        outside.write_text("FINAL_LINK_SENTINEL", encoding="utf-8")
        (self.source / "secret.txt").symlink_to(outside)
        with self.assertRaisesRegex(ValueError, "symlink"):
            build_support.copy_go_sources(self.source, self.destination)
        self.assertNotIn(b"FINAL_LINK_SENTINEL", self.staged_bytes())

    def test_external_hard_link_is_rejected(self):
        self.write_main("//go:embed linked.txt")
        outside = self.root / "outside.txt"
        outside.write_text("HARD_LINK_SENTINEL", encoding="utf-8")
        os.link(outside, self.source / "linked.txt")
        with self.assertRaisesRegex(ValueError, "hard-linked"):
            build_support.copy_go_sources(self.source, self.destination)
        self.assertNotIn(b"HARD_LINK_SENTINEL", self.staged_bytes())

    def test_symlinked_parent_directory_is_rejected(self):
        self.write_main("//go:embed link/secret.txt")
        outside = self.root / "outside"
        outside.mkdir()
        (outside / "secret.txt").write_text("PARENT_LINK_SENTINEL", encoding="utf-8")
        (self.source / "link").symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "symlink"):
            build_support.copy_go_sources(self.source, self.destination)
        self.assertNotIn(b"PARENT_LINK_SENTINEL", self.staged_bytes())

    def test_hidden_expected_target_is_rejected_without_staging_sentinel(self):
        self.write_main("//go:embed link/hidden_expected.txt")
        verifier_data = self.root / "tests" / "data"
        verifier_data.mkdir(parents=True)
        sentinel = "TEST_ONLY_HIDDEN_SENTINEL_39f54a"
        (verifier_data / "hidden_expected.txt").write_text(sentinel, encoding="utf-8")
        (self.source / "link").symlink_to(verifier_data, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "symlink"):
            build_support.copy_go_sources(self.source, self.destination)
        self.assertNotIn(sentinel.encode(), self.staged_bytes())

    def test_parent_traversal_is_rejected(self):
        self.write_main("//go:embed ../secret.txt")
        with self.assertRaisesRegex(ValueError, "unsafe go:embed path"):
            build_support.copy_go_sources(self.source, self.destination)

    def test_absolute_embed_path_is_rejected(self):
        self.write_main("//go:embed /tests/data/hidden_expected.txt")
        with self.assertRaisesRegex(ValueError, "unsafe go:embed path"):
            build_support.copy_go_sources(self.source, self.destination)

    def test_symlink_replacement_before_open_is_rejected(self):
        self.write_main("//go:embed data.txt")
        asset = self.source / "data.txt"
        asset.write_text("ORIGINAL_IN_TREE_ASSET", encoding="utf-8")
        outside = self.root / "outside.txt"
        outside.write_text("RACE_SENTINEL_MUST_NOT_COPY", encoding="utf-8")
        secure_open = build_support._open_regular_file
        replaced = False

        def replace_then_open(root_fd, relative, entry_info):
            nonlocal replaced
            if relative == Path("data.txt") and not replaced:
                replaced = True
                backup = self.source / "data.backup"
                asset.replace(backup)
                asset.symlink_to(outside)
            return secure_open(root_fd, relative, entry_info)

        with mock.patch.object(build_support, "_open_regular_file", side_effect=replace_then_open):
            with self.assertRaisesRegex(ValueError, "symlink|unsafe|changed"):
                build_support.copy_go_sources(self.source, self.destination)
        self.assertTrue(replaced)
        self.assertNotIn(b"RACE_SENTINEL_MUST_NOT_COPY", self.staged_bytes())

@unittest.skipUnless(LINUX_ROOT and HAS_GO, "requires Linux root and Go")
class SafeBuildTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="safe-build-test-")
        self.root = Path(self.temp.name)
        self.source = self.root / "submission"
        self.source.mkdir()

    def tearDown(self):
        self.temp.cleanup()

    def test_build_failure_is_reported(self):
        (self.source / "main.go").write_text("package main\nfunc main( {\n", encoding="utf-8")
        self.assertFalse(run_unprivileged_go_build(self.source))

    def test_missing_go_mod_fails_instead_of_switching_to_gopath_mode(self):
        (self.source / "main.go").write_text("package main\nfunc main() {}\n", encoding="utf-8")
        self.assertFalse(run_unprivileged_go_build(self.source))

    def test_invalid_go_mod_fails(self):
        (self.source / "go.mod").write_text("not a go module\n", encoding="utf-8")
        (self.source / "main.go").write_text("package main\nfunc main() {}\n", encoding="utf-8")
        self.assertFalse(run_unprivileged_go_build(self.source))

    def test_valid_go_module_and_reference_style_build_succeeds(self):
        (self.source / "go.mod").write_text("module titlecase\n\ngo 1.23\n", encoding="utf-8")
        (self.source / "main.go").write_text(
            'package main\nimport "fmt"\nfunc main() { fmt.Println("Title") }\n',
            encoding="utf-8",
        )
        artifact = self.root / "candidate"
        self.assertTrue(run_unprivileged_go_build(self.source, output_binary=artifact))
        self.assertTrue(artifact.is_file())

    def test_behavior_build_rejects_invalid_non_root_package(self):
        (self.source / "go.mod").write_text("module titlecase\n\ngo 1.23\n", encoding="utf-8")
        (self.source / "main.go").write_text(
            "package main\nfunc main() {}\n", encoding="utf-8",
        )
        package = self.source / "broken"
        package.mkdir()
        (package / "broken.go").write_text("package broken\nfunc {\n", encoding="utf-8")
        artifact = self.root / "candidate"
        self.assertFalse(run_unprivileged_go_build(self.source, output_binary=artifact))
        self.assertFalse(artifact.exists())

    def test_vendored_module_build_succeeds(self):
        (self.source / "go.mod").write_text(
            "module titlecase\n\ngo 1.23\n\nrequire example.com/greet v0.0.0\n",
            encoding="utf-8",
        )
        (self.source / "main.go").write_text(
            'package main\nimport "example.com/greet"\nfunc main() { greet.Hello() }\n',
            encoding="utf-8",
        )
        vendor = self.source / "vendor"
        package = vendor / "example.com" / "greet"
        package.mkdir(parents=True)
        (vendor / "modules.txt").write_text(
            "# example.com/greet v0.0.0\n## explicit; go 1.23\nexample.com/greet\n",
            encoding="utf-8",
        )
        (package / "greet.go").write_text(
            "package greet\nfunc Hello() string { return \"hello\" }\n",
            encoding="utf-8",
        )
        self.assertTrue(run_unprivileged_go_build(self.source))


if __name__ == "__main__":
    unittest.main()
