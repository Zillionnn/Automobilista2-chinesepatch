"""kap_repack.py — rebuild a .bff pak from extracted files, replacing selected entries.

Usage: kap_repack.py <pak.bff> <key> <replacement-map.json> <out.bff>
replacement-map.json: {"<entry_index>": "<path-to-new-raw-file>"}

The names region is copied byte-identical; directory is re-encrypted with the pak key;
unmodified entries keep their original encrypted bytes (cheap copy); modified entries
are recompressed with zlib (type 1).

Directory row CRC field (offset 34) = JAMCRC (crc32 init 0xFFFFFFFF, no final xor)
over the RC4-encrypted stored bytes. All other row fields are copied from the
original row untouched.
"""
import json
import struct
import sys
import zlib

sys.path.insert(0, r"F:\Game\AMS2-ZH\tools")
from kap import rc4

KEY = None


def parse_pak(data):
    assert data[0:4] == b" KAP"
    nfiles = struct.unpack_from("<I", data, 8)[0]
    x118 = struct.unpack_from("<I", data, 0x118)[0]
    x120 = struct.unpack_from("<I", data, 0x120)[0]
    dir_dec = rc4(data[0x130:0x130 + x118], KEY)
    rows = [dir_dec[i * 42:(i + 1) * 42] for i in range(nfiles)]
    entries = []
    for i, e in enumerate(rows):
        entries.append({
            "off": struct.unpack_from("<Q", e, 8)[0],
            "zsize": struct.unpack_from("<I", e, 16)[0],
            "size": struct.unpack_from("<I", e, 20)[0],
            "type": e[32],
            "crc": struct.unpack_from("<I", e, 34)[0],
            "ext": e[38:42].decode("latin1"),
            "row": rows[i],
        })
    names_off = 0x438 + x118
    names_size = x120 - 0x308
    names = data[names_off:names_off + names_size]
    data_off = names_off + names_size
    return entries, names, data_off, x118


def build_pak(data, repl):
    """Rebuild pak. Data is placed contiguously starting at data_off (proven
    engine-agnostic layout — the engine only follows directory offsets, so
    byte-identical placement of original padding is not required)."""
    entries, names, data_off, x118 = parse_pak(data)
    newdata = bytearray()
    out_rows = []
    for i, e in enumerate(entries):
        raw = data[e["off"]:e["off"] + e["zsize"]]
        row = bytearray(e["row"])
        if str(i) in repl:
            newraw = open(repl[str(i)], "rb").read()
            comp = zlib.compress(newraw, 9)
            enc = rc4(comp, KEY)
            off = data_off + len(newdata)
            newdata += enc
            struct.pack_into("<Q", row, 8, off)
            struct.pack_into("<I", row, 16, len(enc))
            struct.pack_into("<I", row, 20, len(newraw))
            crc = zlib.crc32(enc) & 0xFFFFFFFF ^ 0xFFFFFFFF
            struct.pack_into("<I", row, 34, crc)
            print(f"entry {i}: replaced ({e['ext']}) raw {e['size']}->{len(newraw)} crc={crc:08x}")
        else:
            off = data_off + len(newdata)
            newdata += raw
            struct.pack_into("<Q", row, 8, off)
        out_rows.append(bytes(row))
    dir_raw = b"".join(out_rows)
    assert len(dir_raw) == len(entries) * 42
    dir_enc = rc4(dir_raw, KEY)
    out = bytearray(data)
    out[0x130:0x130 + len(dir_enc)] = dir_enc
    names_off = 0x438 + x118
    out[names_off:names_off + len(names)] = names
    out[names_off + len(names):] = newdata
    return bytes(out)


if __name__ == "__main__":
    KEY = sys.argv[2].encode("latin1") if isinstance(sys.argv[2], str) else sys.argv[2]
    repl = json.load(open(sys.argv[3], encoding="utf-8"))
    data = open(sys.argv[1], "rb").read()
    out = build_pak(data, repl)
    open(sys.argv[4], "wb").write(out)
    print(f"wrote {sys.argv[4]} ({len(out)} bytes, orig {len(data)})")