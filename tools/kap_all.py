"""Batch-extract all AMS2 paks: per-pak key scan + RC4 + zlib/oodle + names(if parseable)."""
import ctypes
import os
import re
import struct
import sys
import zlib

BMS = r"F:\Game\AMS2-ZH\work\nfsshift.bms"
GAME = r"F:\SteamLibrary\steamapps\common\Automobilista 2"
OO2 = os.path.join(GAME, "oo2core_4_win64.dll")

src = open(BMS, encoding="latin1").read()
BLOBS = {}
for m in re.finditer(r'PCARS_KEY_SET == (\d+)', src):
    ks = int(m.group(1))
    bm = re.search(r'set MEMORY_FILE3 binary "([^"]+)"', src[m.end():])
    BLOBS[ks] = bytes.fromhex(re.sub(r'\\x', '', bm.group(1)))


def rc4(data: bytes, key: bytes) -> bytes:
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


def derive_key(blob: bytes, num: int):
    off = num * 0x1b
    raw = blob[off:off + 0x1b]
    if len(raw) < 0x1b:
        return None
    keysz = raw.index(b"\x00") if b"\x00" in raw else len(raw)
    dec = bytearray(bytes(b ^ (0xac, 0xc7, 0x91)[i % 3] for i, b in enumerate(blob)))
    j = off
    for _ in range(keysz // 2):
        dec[j], dec[j + 1] = dec[j + 1], dec[j]
        j += 2
    return bytes(dec[off:off + keysz])


def scan_key(enc_dir: bytes, files: int, data_len: int):
    for ks in sorted(BLOBS):
        for num in range(0x16):
            key = derive_key(BLOBS[ks], num)
            if not key:
                continue
            dec16 = rc4(enc_dir[:16], key)
            if struct.unpack_from(">I", dec16, 0xC)[0] != 0:
                continue
            dec = rc4(enc_dir, key)
            e = dec[0:42]
            if len(e) < 42:
                continue
            o = struct.unpack_from("<Q", e, 8)[0]
            zs = struct.unpack_from("<I", e, 16)[0]
            sz = struct.unpack_from("<I", e, 20)[0]
            if not (0 <= o < data_len and 0 <= zs <= 10_000_000_000 and 0 <= sz <= 10_000_000_000):
                continue
            return key, dec
    return None, None


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


def decompress(ctype: int, comp: bytes, raw_size: int) -> bytes:
    if ctype == 0:
        return comp
    if ctype == 1:
        return zlib.decompress(comp)
    if ctype == 3:
        oolz = _get_oolz()
        out = ctypes.create_string_buffer(raw_size)
        n = oolz.OodleLZ_Decompress(comp, len(comp), out, raw_size, 1, 1, 0, None, 0)
        if n != raw_size:
            raise RuntimeError(f"oodle {n}!={raw_size}")
        return out.raw
    raise RuntimeError(f"type {ctype}")


def extract_pak(pak_path: str, out_dir: str):
    data = open(pak_path, "rb").read()
    files = struct.unpack_from("<I", data, 8)[0]
    x118 = struct.unpack_from("<I", data, 0x118)[0]
    x120 = struct.unpack_from("<I", data, 0x120)[0] - 0x308
    x12d = data[0x12D]
    key, dir_dec = scan_key(data[0x130:0x130 + x118], files, len(data))
    if key is None:
        print(f"{os.path.basename(pak_path)}: NO KEY FOUND x12d={x12d}")
        return
    entries = []
    for i in range(files):
        e = dir_dec[i * 42:(i + 1) * 42]
        ext = struct.unpack_from("<I", e, 38)[0].to_bytes(4, "little").rstrip(b"\x00").decode("latin1", "replace")
        entries.append(dict(
            offset=struct.unpack_from("<Q", e, 8)[0],
            zsize=struct.unpack_from("<I", e, 16)[0],
            size=struct.unpack_from("<I", e, 20)[0],
            ctype=e[32], ext=ext))

    names = None
    try:
        names_dec = rc4(data[0x438 + x118:0x438 + x118 + x120], key)
        ns = []
        for i in range(files):
            no = struct.unpack_from("<Q", names_dec, i * 16)[0]
            nsz = names_dec[no]
            ns.append(names_dec[no + 1:no + 1 + nsz].decode("latin1", "replace"))
        names = ns
    except Exception:
        pass

    os.makedirs(out_dir, exist_ok=True)
    stats = {}
    ok = fail = 0
    for i, en in enumerate(entries):
        try:
            blob = rc4(data[en["offset"]:en["offset"] + en["zsize"]], key)
            raw = decompress(en["ctype"], blob, en["size"])
            name = names[i] if names else f"file_{i:04d}.{en['ext']}"
            name = name.replace("\\", os.sep).lstrip("/\\")
            p = os.path.join(out_dir, name)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "wb") as f:
                f.write(raw)
            ok += 1
        except Exception as ex:
            fail += 1
            print(f"  !! file {i}: {ex}")
        stats[en["ctype"]] = stats.get(en["ctype"], 0) + 1
    print(f"{os.path.basename(pak_path)}: key={key!r} names={'YES' if names else 'no'} "
          f"ok={ok} fail={fail} types={stats}")


if __name__ == "__main__":
    pakdir = os.path.join(GAME, "Pakfiles")
    outroot = r"F:\Game\AMS2-ZH\work\extract"
    only = sys.argv[1] if len(sys.argv) > 1 else None
    for fn in sorted(os.listdir(pakdir)):
        if not fn.lower().endswith(".bff"):
            continue
        if only and only.lower() not in fn.lower():
            continue
        extract_pak(os.path.join(pakdir, fn), os.path.join(outroot, fn[:-4]))