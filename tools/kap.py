"""AMS2 (Madness engine) .bff pak extractor — RC4 directory + per-file RC4 + zlib/oodle."""
import ctypes
import os
import struct
import sys
import zlib

KEY = b"4AmRyL4lJJcBVs7r6vjOvW"
OO2 = r"F:\SteamLibrary\steamapps\common\Automobilista 2\oo2core_4_win64.dll"
_oolz = None


def _get_oolz():
    global _oolz
    if _oolz is None:
        _oolz = ctypes.WinDLL(OO2)
        _oolz.OodleLZ_Decompress.restype = ctypes.c_int
        _oolz.OodleLZ_Decompress.argtypes = [
            ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_int,
            ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_void_p, ctypes.c_int]
    return _oolz


def rc4(data: bytes, key: bytes = KEY) -> bytes:
    S = list(range(256)); j = 0
    for i in range(256):
        j = (j + S[i] + key[i % len(key)]) & 0xFF
        S[i], S[j] = S[j], S[i]
    out = bytearray(len(data)); i = j = 0
    for k in range(len(data)):
        i = (i + 1) & 0xFF; j = (j + S[i]) & 0xFF
        S[i], S[j] = S[j], S[i]
        out[k] = data[k] ^ S[(S[i] + S[j]) & 0xFF]
    return bytes(out)


def decompress(ctype: int, comp: bytes, raw_size: int) -> bytes:
    if ctype == 0:
        return comp
    if ctype == 1:
        return zlib.decompress(comp)
    if ctype == 2:
        raise RuntimeError("type 2 (XMemDecompress) not supported yet")
    if ctype == 3:
        oolz = _get_oolz()
        out = ctypes.create_string_buffer(raw_size)
        n = oolz.OodleLZ_Decompress(comp, len(comp), out, raw_size, 1, 1, 0, None, 0)
        if n != raw_size:
            raise RuntimeError(f"oodle fail: {n} != {raw_size}")
        return out.raw
    raise RuntimeError(f"unsupported type {ctype}")


def read_pak(pak_path: str):
    data = open(pak_path, "rb").read()
    files = struct.unpack_from("<I", data, 8)[0]
    x118 = struct.unpack_from("<I", data, 0x118)[0]
    x120 = struct.unpack_from("<I", data, 0x120)[0] - 0x308
    x12d = data[0x12D]
    if x12d != 2:
        raise RuntimeError(f"unsupported x12d={x12d}")
    dir_dec = rc4(data[0x130:0x130 + x118], KEY)
    entries = []
    for i in range(files):
        e = dir_dec[i * 42:(i + 1) * 42]
        ext = struct.unpack_from("<I", e, 38)[0].to_bytes(4, "little").rstrip(b"\x00").decode("latin1")
        entries.append(dict(
            offset=struct.unpack_from("<Q", e, 8)[0],
            zsize=struct.unpack_from("<I", e, 16)[0],
            size=struct.unpack_from("<I", e, 20)[0],
            ctype=e[32],
            crc=struct.unpack_from("<I", e, 34)[0],
            ext=ext))
    return data, entries


def extract(pak_path: str, out_dir: str):
    data, entries = read_pak(pak_path)
    os.makedirs(out_dir, exist_ok=True)
    stats = {}
    for i, en in enumerate(entries):
        blob = data[en["offset"]:en["offset"] + en["zsize"]]
        blob = rc4(blob, KEY)
        raw = decompress(en["ctype"], blob, en["size"])
        name = f"file_{i:04d}.{en['ext']}"
        with open(os.path.join(out_dir, name), "wb") as f:
            f.write(raw)
        stats[en["ctype"]] = stats.get(en["ctype"], 0) + 1
    print(f"extracted {len(entries)} files to {out_dir}: types {stats}")


if __name__ == "__main__":
    pak = sys.argv[1] if len(sys.argv) > 1 else r"F:\SteamLibrary\steamapps\common\Automobilista 2\Pakfiles\MenuSetup.bff"
    out = sys.argv[2] if len(sys.argv) > 2 else r"F:\Game\AMS2-ZH\work\extract\MenuSetup"
    extract(pak, out)