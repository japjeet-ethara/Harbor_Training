import ctypes
import os
import resource
import sys


def main():
    uid = 65534
    os.setgroups([])
    os.setgid(uid)
    os.setuid(uid)
    if ctypes.CDLL(None, use_errno=True).prctl(38, 1, 0, 0, 0) != 0:
        raise OSError(ctypes.get_errno(), "prctl(PR_SET_NO_NEW_PRIVS)")
    resource.setrlimit(resource.RLIMIT_FSIZE, (32 << 20, 32 << 20))
    resource.setrlimit(resource.RLIMIT_NOFILE, (128, 128))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_NPROC, (128, 128))
    if len(sys.argv) == 1:
        if os.access("/tests", os.R_OK | os.X_OK) or os.access("/logs/verifier", os.W_OK):
            raise PermissionError("candidate UID can access verifier files")
        return
    os.execv(sys.argv[1], sys.argv[1:])


if __name__ == "__main__":
    main()
