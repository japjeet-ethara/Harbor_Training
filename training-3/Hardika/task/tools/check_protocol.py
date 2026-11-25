import subprocess
import sys

from reference import record_bytes, titlecase


def verify(executable):
    long_title = "  the coast and d'ßelle; of the folio\u00a0" * 14_000
    cases = {
        "empty stream": (b"", b""),
        "blank records": (b"\n\n\n", b"\n\n\n"),
        "CRLF including a blank record": (
            b"of the charts\r\n\r\nand the tide\r\n",
            record_bytes(map(titlecase, ("of the charts", "", "and the tide"))),
        ),
        "missing final LF": (
            b"of paper\nand ink", record_bytes(map(titlecase, ("of paper", "and ink"))),
        ),
        "whitespace and embedded CR": (
            b"  of\tand\rthe   \n", record_bytes([titlecase("  of\tand\rthe   ")]),
        ),
        "long record": (
            long_title.encode() + b"\n", record_bytes([titlecase(long_title)]),
        ),
    }
    for name, (payload, expected) in cases.items():
        result = subprocess.run([executable], input=payload, capture_output=True,
                                timeout=60, check=True)
        assert result.stdout == expected, name
        assert result.stderr == b"", name
        print(f"{name}: passed ({len(payload)} input bytes, {len(expected)} output bytes)")


if __name__ == "__main__":
    verify(sys.argv[1])
