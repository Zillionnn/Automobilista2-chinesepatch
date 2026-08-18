# -*- coding: utf-8 -*-
"""tdb_repack.py — Write translated Chinese-Simple text back into .tdb files.

Parses the .tdb binary format (same logic as tdb_dump.py), replaces
Chinese-Simple entries with translated text, writes a new .tdb file.

.tdb format:
  u32 version
  u32 _nlang (not actual lang count; meta[0] is)
  ASCII table name (read until non-printable byte)
  6 x u32 meta (meta[0]=nlang, meta[1]=nsub, meta[2]=nkeys)
  nsub x length-prefixed sub names
  nkeys x length-prefixed key names
  per language (meta[0] total):
    length-prefixed lang name
    u32 block_size
    entries: 12-byte header (u32 u32 u32_charcount) + UTF-16LE text

Usage:
  python tdb_repack.py <input.tdb> <translations.json> <output.tdb>

translations.json format:
  {"table_name": {"key": "chinese_translation", ...}, ...}
"""
import json
import struct
import sys


def parse_tdb(data):
    """Parse .tdb binary, return dict with structure and raw byte offsets."""
    version = struct.unpack_from("<I", data, 0)[0]
    field4 = struct.unpack_from("<I", data, 4)[0]  # engine-internal field, preserve as-is
    off = 8
    start = off
    while off < len(data) and 0x20 <= data[off] < 0x7F:
        off += 1
    tname = data[start:off].decode("latin1")
    meta = [struct.unpack_from("<I", data, off + 4 * i)[0] for i in range(6)]
    off += 24
    nsub, nkeys = meta[1], meta[2]

    subs = []
    for _ in range(nsub):
        ln = struct.unpack_from("<I", data, off)[0]
        subs.append(data[off + 4:off + 4 + ln].decode("latin1"))
        off += 4 + ln

    keys = []
    for _ in range(nkeys):
        ln = struct.unpack_from("<I", data, off)[0]
        keys.append(data[off + 4:off + 4 + ln].decode("latin1"))
        off += 4 + ln

    lang_blocks = []
    for _ in range(meta[0]):
        ln = struct.unpack_from("<I", data, off)[0]
        lname = data[off + 4:off + 4 + ln].decode("latin1")
        off += 4 + ln
        bsize = struct.unpack_from("<I", data, off)[0]
        off += 4
        block_end = off + bsize

        entries = []
        ent_off = off
        while ent_off + 12 <= block_end:
            h1 = struct.unpack_from("<I", data, ent_off)[0]
            h2 = struct.unpack_from("<I", data, ent_off + 4)[0]
            cc = struct.unpack_from("<I", data, ent_off + 8)[0]
            if ent_off + 12 + cc * 2 > block_end or cc > 1000000:
                break
            val = data[ent_off + 12:ent_off + 12 + cc * 2].decode("utf-16-le", "replace")
            entries.append((h1, h2, cc, val))
            ent_off += 12 + cc * 2

        lang_blocks.append((lname, entries))
        off = block_end

    return {
        "version": version,
        "field4": field4,
        "tname": tname,
        "meta": meta,
        "subs": subs,
        "keys": keys,
        "lang_blocks": lang_blocks,
    }


def build_tdb(tdb, translations):
    """Rebuild .tdb with translated Chinese-Simple entries."""
    out = bytearray()
    out += struct.pack("<II", tdb["version"], tdb["field4"])  # preserve original field4
    # Write table name as raw ASCII (no length prefix)
    out += tdb["tname"].encode("latin1")
    for m in tdb["meta"]:
        out += struct.pack("<I", m)
    for s in tdb["subs"]:
        b = s.encode("latin1")
        out += struct.pack("<I", len(b)) + b
    for k in tdb["keys"]:
        b = k.encode("latin1")
        out += struct.pack("<I", len(b)) + b

    table_trans = translations.get(tdb["tname"], {})

    for lname, entries in tdb["lang_blocks"]:
        b = lname.encode("latin1")
        out += struct.pack("<I", len(b)) + b

        entry_bytes = bytearray()
        for i, (h1, h2, cc, val) in enumerate(entries):
            new_val = val
            if lname == "Chinese-Simple":
                key = tdb["keys"][i] if i < len(tdb["keys"]) else ""
                if key in table_trans and table_trans[key]:
                    new_val = table_trans[key]

            new_val_bytes = new_val.encode("utf-16-le")
            new_cc = len(new_val_bytes) // 2  # UTF-16 code unit count
            entry_bytes += struct.pack("<III", h1, h2, new_cc)
            entry_bytes += new_val_bytes

        out += struct.pack("<I", len(entry_bytes))
        out += entry_bytes

    return bytes(out)


def main():
    if len(sys.argv) < 4:
        print("Usage: tdb_repack.py <input.tdb> <translations.json> <output.tdb>")
        sys.exit(1)

    inp = sys.argv[1]
    trans_path = sys.argv[2]
    outp = sys.argv[3]

    data = open(inp, "rb").read()
    translations = json.load(open(trans_path, encoding="utf-8"))

    tdb = parse_tdb(data)
    print("Table: %s, keys=%d, langs=%d" % (
        tdb["tname"], len(tdb["keys"]), len(tdb["lang_blocks"])))

    table_trans = translations.get(tdb["tname"], {})
    if table_trans:
        replaced = sum(1 for k in tdb["keys"] if k in table_trans and table_trans[k])
        print("  Translations to apply: %d / %d keys" % (replaced, len(tdb["keys"])))

    new_data = build_tdb(tdb, translations)
    with open(outp, "wb") as f:
        f.write(new_data)
    print("  Written: %s (%d -> %d bytes)" % (outp, len(data), len(new_data)))


if __name__ == "__main__":
    main()
