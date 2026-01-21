'''
Code Purpose: Read and parse the header of a PRESTO/SIGPROC filterbank file compressed with zstd
Note: Ripped from https://github.com/evanocathain/mockHeader/tree/master and modified to read from zstd-compressed files with python.
'''
#!/usr/bin/env python3
import argparse
import json
import struct
import subprocess
from typing import BinaryIO, Dict, Any, Optional

STRING_VALUE_KEYS = {"rawdatafile", "source_name"}  # add more if present
INT_VALUE_KEYS = {
    "machine_id", "telescope_id", "data_type",
    "nchans", "nbits", "nifs", "nbeams", "ibeam",
}
DOUBLE_VALUE_KEYS = {
    "src_raj", "src_dej", "az_start", "za_start",
    "tstart", "tsamp", "fch1", "foff", "refdm", "period",
}

def read_exact(stream: BinaryIO, n: int) -> bytes:
    b = stream.read(n)
    if b is None or len(b) != n:
        raise EOFError(f"Unexpected EOF while reading {n} bytes")
    return b

def read_i32(stream: BinaryIO) -> int:
    return struct.unpack("<i", read_exact(stream, 4))[0]


def read_f64(stream: BinaryIO) -> float:
    return struct.unpack("<d", read_exact(stream, 8))[0]

def read_sigproc_string(stream: BinaryIO) -> str:
    n = read_i32(stream)
    if n < 0 or n > 10_000_000:
        raise ValueError(f"Unreasonable string length {n}")
    return read_exact(stream, n).decode("ascii", errors="replace")


def hexdump_c(data: bytes, width: int = 16) -> str:
    out = []
    for off in range(0, len(data), width):
        chunk = data[off:off + width]
        hexpart = " ".join(f"{x:02x}" for x in chunk).ljust(width * 3 - 1)
        asciipart = "".join(chr(x) if 32 <= x <= 126 else "." for x in chunk)
        out.append(f"{off:08x}  {hexpart}  |{asciipart}|")
    return "\n".join(out)

def parseheader(stream: BinaryIO) -> Dict[str, Any]:
    header: Dict[str, Any] = {}

    start = read_sigproc_string(stream)
    if start != "HEADER_START":
        raise ValueError(f"Expected HEADER_START, got {start!r}")

    while True:
        key = read_sigproc_string(stream)

        if key == "HEADER_END":
            return header

        if key in STRING_VALUE_KEYS:
            header[key] = read_sigproc_string(stream)
        elif key in INT_VALUE_KEYS:
            header[key] = read_i32(stream)
        elif key in DOUBLE_VALUE_KEYS:
            header[key] = read_f64(stream)
        else:
            raise KeyError(
                f"Unknown key {key!r}. Add it to STRING_VALUE_KEYS / INT_VALUE_KEYS / DOUBLE_VALUE_KEYS."
            )
            
def zstheader(path: str) -> Dict[str, Any]:
    """
    Read and return the SIGPROC header from a zstd-compressed filterbank file.
    Raises on corruption.
    """
    proc = subprocess.Popen(["zstd", "-dc", path], stdout=subprocess.PIPE)
    assert proc.stdout is not None

    try:
        return parseheader(proc.stdout)
    finally:
        proc.kill()

def main():
    ap = argparse.ArgumentParser(description="Parse PRESTO/SIGPROC filterbank header from .fil.zst")
    ap.add_argument("path", help="Input file")
    ap.add_argument("--dump512", action="store_true", help="Dump first 512 bytes of file in hex")
    args = ap.parse_args()

    proc = subprocess.Popen(["zstd", "-dc", args.path], stdout=subprocess.PIPE)
    assert proc.stdout is not None

    try:
        header = parseheader(proc.stdout)
    except (EOFError, ValueError, KeyError, struct.error) as e:
        print(f"{args.path}: corrupt header, skipping file")
        proc.kill()
        return

    proc.kill()
    print(json.dumps(header, indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
