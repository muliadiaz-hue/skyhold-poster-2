#!/usr/bin/env python3
"""SKYHOLD - make.fun entry program.

The poster for this entry is a finished image asset (asset.jpg, kept next
to this program). This program does not redraw it. It checks that the
asset is a real JPEG inside the competition limits, then delivers it as
entry.png in the output directory.

Behaviour:
  * the asset is read from the same directory as this program;
  * the asset must start with the JPEG magic bytes FF D8 FF, be at most
    1,048,576 bytes, and be at most 1024x1024 pixels (dimensions are read
    from the JPEG start-of-frame segment, parsed by hand);
  * the output directory is $MAKEFUN_OUTPUT_DIR when set, otherwise
    /output when it exists, otherwise ./output next to this program;
  * stale files inside the output directory are removed, but the output
    directory itself is never removed;
  * entry.png is written through a temporary file plus rename, so a
    reader never sees a half-written file.
"""

from __future__ import annotations

import os
import struct
import sys
import tempfile
from pathlib import Path

MAX_BYTES = 1_048_576
MAX_WIDTH = 1024
MAX_HEIGHT = 1024
ASSET_NAME = "asset.jpg"
ENTRY_NAME = "entry.png"


class AssetError(ValueError):
    """The poster asset failed validation."""


def read_jpeg_dimensions(data: bytes) -> tuple[int, int]:
    """Return (width, height) from the first SOF marker of a JPEG stream."""
    if len(data) < 3 or data[:3] != b"\xff\xd8\xff":
        raise AssetError("not a JPEG file: missing SOI marker (FF D8 FF)")
    pos = 2
    total = len(data)
    while pos + 1 < total:
        if data[pos] != 0xFF:
            raise AssetError(f"bad JPEG segment marker at offset {pos}")
        marker = data[pos + 1]
        if marker == 0xFF:
            pos += 1  # padding byte before a marker
            continue
        if marker == 0x00:
            raise AssetError("unexpected escaped 0xFF byte in JPEG header")
        if marker == 0xD9:
            break  # end of image reached without any SOF segment
        if marker == 0x01 or 0xD0 <= marker <= 0xD8:
            pos += 2  # standalone marker, no length field
            continue
        if marker == 0xDA:
            # Start of scan: entropy-coded data follows, so no SOF
            # segment can appear after this point in a valid file.
            raise AssetError("no SOF marker found before scan data (SOS)")
        if pos + 4 > total:
            raise AssetError("truncated JPEG segment header")
        (length,) = struct.unpack(">H", data[pos + 2:pos + 4])
        if length < 2 or pos + 2 + length > total:
            raise AssetError("truncated JPEG segment")
        if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
            # Start-of-frame segment: precision (1 byte), then height
            # and width as two big-endian 16-bit values.
            if length < 7:
                raise AssetError("short SOF segment in JPEG header")
            height, width = struct.unpack(">HH", data[pos + 5:pos + 9])
            return width, height
        pos += 2 + length
    raise AssetError("no SOF marker found in JPEG data")


def load_and_validate(asset_path: Path) -> tuple[bytes, int, int]:
    """Read the asset, validate it, return (data, width, height)."""
    try:
        data = asset_path.read_bytes()
    except OSError as exc:
        raise AssetError(f"cannot read {asset_path}: {exc}") from exc
    if len(data) > MAX_BYTES:
        raise AssetError(
            f"asset too large: {len(data)} bytes (limit {MAX_BYTES})"
        )
    width, height = read_jpeg_dimensions(data)
    if width > MAX_WIDTH or height > MAX_HEIGHT:
        raise AssetError(
            f"asset too big: {width}x{height} "
            f"(limit {MAX_WIDTH}x{MAX_HEIGHT})"
        )
    return data, width, height


def resolve_output_dir() -> Path:
    """Pick the output directory: env var, /output, or ./output."""
    env_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "").strip()
    if env_dir:
        return Path(env_dir)
    if Path("/output").is_dir():
        return Path("/output")
    return Path(__file__).resolve().parent / "output"


def clear_stale_files(out_dir: Path) -> int:
    """Remove stale files inside out_dir; never touch out_dir itself."""
    removed = 0
    for item in out_dir.iterdir():
        if item.is_file() or item.is_symlink():
            item.unlink()
            removed += 1
    return removed


def write_entry(out_dir: Path, data: bytes) -> Path:
    """Write entry.png via a temporary file plus atomic rename."""
    target = out_dir / ENTRY_NAME
    fd, tmp_name = tempfile.mkstemp(
        prefix=".entry-", suffix=".tmp", dir=out_dir
    )
    try:
        with os.fdopen(fd, "wb") as tmp:
            tmp.write(data)
            tmp.flush()
            os.fsync(tmp.fileno())
        os.replace(tmp_name, target)
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise
    return target


def main() -> int:
    here = Path(__file__).resolve().parent
    asset_path = here / ASSET_NAME
    try:
        data, width, height = load_and_validate(asset_path)
    except AssetError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    out_dir = resolve_output_dir()
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
        removed = clear_stale_files(out_dir)
        target = write_entry(out_dir, data)
    except OSError as exc:
        print(f"error: cannot write output in {out_dir}: {exc}", file=sys.stderr)
        return 1
    print(
        f"SKYHOLD entry written: {target} "
        f"({width}x{height} JPEG, {len(data)} bytes; "
        f"{removed} stale file(s) removed)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
