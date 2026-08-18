"""tdb builder: rebuild tdb binary from parsed tables, optionally replacing values.

IMPORTANT format facts (reverse-engineered):
- header: u32 version=1 @0, u32 X @4 (per-table constant, preserve as-is), tablename,
  6x u32 meta (meta[0]=langs, meta[1]=subs, meta[2]=keys), subs, keys.
- each entry: u32 subhash @0 (hash of subtable name; 0x434A7EAB when no subs),
  u32 hash @4 (per-value hash, preserve), u32 cc @8, utf-16le value @12.
"""
import struct
import sys

MAGIC = 0x434A7EAB


def build_tdb(tablename, header4, meta, subs, keys, langs):
    """langs: list of (name, [(subhash, hash, value)...]) — value is a python str."""
    out = bytearray()
    out += struct.pack("<II", 1, header4)
    out += tablename.encode("latin1")
    for m in meta:
        out += struct.pack("<I", m)
    for s in subs:
        sb = s.encode("latin1")
        out += struct.pack("<I", len(sb)) + sb
    for k in keys:
        kb = k.encode("latin1")
        out += struct.pack("<I", len(kb)) + kb
    for lname, values in langs:
        nb = lname.encode("latin1")
        body = bytearray()
        for subh, h, v in values:
            vb = v.encode("utf-16-le")
            body += struct.pack("<III", subh, h, len(vb) // 2) + vb
        out += struct.pack("<I", len(nb)) + nb
        out += struct.pack("<I", len(body)) + body
    return bytes(out)


def parse_tdb_raw(data):
    """Returns (tname, header4, meta, subs, keys, langs) with
    langs = [(name, [(subhash, hash, value)...])]."""
    version, header4 = struct.unpack_from("<II", data, 0)
    off = 8
    start = off
    while 0x20 <= data[off] < 0x7F:
        off += 1
    tname = data[start:off].decode()
    meta = [struct.unpack_from("<I", data, off + 4 * i)[0] for i in range(6)]
    off += 24
    nsub = meta[1]
    nkeys = meta[2]
    nlangs = meta[0]
    subs = []
    for _ in range(nsub):
        ln = struct.unpack_from("<I", data, off)[0]
        subs.append(data[off + 4:off + 4 + ln].decode())
        off += 4 + ln
    keys = []
    for _ in range(nkeys):
        ln = struct.unpack_from("<I", data, off)[0]
        keys.append(data[off + 4:off + 4 + ln].decode())
        off += 4 + ln
    langs = []
    for _ in range(nlangs):
        ln = struct.unpack_from("<I", data, off)[0]
        lname = data[off + 4:off + 4 + ln].decode()
        off += 4 + ln
        bsize = struct.unpack_from("<I", data, off)[0]
        off += 4
        end = off + bsize
        values = []
        while off + 12 <= end:
            subh = struct.unpack_from("<I", data, off)[0]
            h = struct.unpack_from("<I", data, off + 4)[0]
            cc = struct.unpack_from("<I", data, off + 8)[0]
            if off + 12 + cc * 2 > end or cc > 1000000:
                break
            values.append((subh, h, data[off + 12:off + 12 + cc * 2].decode("utf-16-le", "replace")))
            off += 12 + cc * 2
        off = end
        langs.append((lname, values))
    return tname, header4, meta, subs, keys, langs


if __name__ == "__main__":
    p = r"F:\Game\AMS2-ZH\work\extract\BOOTSPLASH\file_0004.tdb"
    data = open(p, "rb").read()
    tname, header4, meta, subnames, keys, langs = parse_tdb_raw(data)
    print(f"table={tname} header4={header4} meta={meta} sub={len(subnames)} keys={len(keys)} langs={[l[0] for l in langs]}")

    # smoke test: marker in English (ASCII, visible in any language) + Chinese-Simple
    MARKERS = {"English": "LOADING TEST OK", "Chinese-Simple": "加载中..."}
    new_langs = []
    for lname, values in langs:
        new_vals = []
        for i, (subh, h, v) in enumerate(values):
            if i == 0 and lname in MARKERS:
                new_vals.append((subh, h, MARKERS[lname]))
            else:
                new_vals.append((subh, h, v))
        new_langs.append((lname, new_vals))

    rebuilt = build_tdb(tname, header4, meta, subnames, keys, new_langs)
    out_p = r"F:\Game\AMS2-ZH\work\extract\BOOTSPLASH\file_0004_new.tdb"
    open(out_p, "wb").write(rebuilt)
    print(f"rebuilt size={len(rebuilt)} (orig={len(data)})")

    # verify: reparse the rebuilt file
    t2, h2, m2, s2, k2, l2 = parse_tdb_raw(rebuilt)
    ok = (t2 == tname and h2 == header4 and m2 == meta and s2 == subnames and k2 == keys
          and [l[0] for l in l2] == [l[0] for l in langs]
          and [len(l[1]) for l in l2] == [len(l[1]) for l in langs])
    print(f"reparse OK: {ok}")
    print(f"rebuilt value[0]: {[(l[0], l[1][0][2][:30]) for l in l2]}")