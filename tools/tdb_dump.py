"""tdb_dump.py — parse all tdb files in the extraction tree, export (key, EN, ZH, other langs) tables.

Output: work/tdb_tables/<tablename>.tsv  (tab-separated; key, sub, then one column per language)
Also: work/tdb_tables/_summary.txt
"""
import glob
import os
import struct
import sys

OUT = r"F:\Game\AMS2-ZH\work\tdb_tables"


def parse_tdb(path):
    data = open(path, "rb").read()
    version, _nlang = struct.unpack_from("<II", data, 0)
    off = 8
    start = off
    while off < len(data) and 0x20 <= data[off] < 0x7F:
        off += 1
    tname = data[start:off].decode()
    meta = [struct.unpack_from("<I", data, off + 4 * i)[0] for i in range(6)]
    off += 24
    nsub, nkeys = meta[1], meta[2]
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
    langs = {}
    for _ in range(meta[0]):
        ln = struct.unpack_from("<I", data, off)[0]
        lname = data[off + 4:off + 4 + ln].decode("latin1")
        off += 4 + ln
        bsize = struct.unpack_from("<I", data, off)[0]
        off += 4
        end = off + bsize
        vals = []
        while off + 12 <= end:
            cc = struct.unpack_from("<I", data, off + 8)[0]
            if off + 12 + cc * 2 > end or cc > 1000000:
                break
            vals.append(data[off + 12:off + 12 + cc * 2].decode("utf-16-le", "replace"))
            off += 12 + cc * 2
        off = end
        langs[lname] = vals
    return version, tname, meta, subs, keys, langs


def main():
    os.makedirs(OUT, exist_ok=True)
    summary = []
    for path in sorted(glob.glob(r"F:\Game\AMS2-ZH\work\extract\**\*.tdb", recursive=True)):
        version, tname, meta, subs, keys, langs = parse_tdb(path)
        counts = {k: len(v) for k, v in langs.items()}
        zh = langs.get("Chinese-Simple")
        if zh:
            untr = sum(1 for v in zh if v.startswith("UNTRANSLATED ("))
        else:
            untr = -1
        summary.append(f"{os.path.basename(os.path.dirname(path))}/{os.path.basename(path)}\t{tname}\tkeys={len(keys)}\tsubs={len(subs)}\tlangs={counts}\tZH-untranslated={untr}")
        safe = tname.replace("/", "_")
        with open(os.path.join(OUT, safe + ".tsv"), "w", encoding="utf-8", newline="") as f:
            langs_order = [k for k, v in counts.items()]
            f.write("sub\tkey\t" + "\t".join(langs_order) + "\n")
            for i, k in enumerate(keys):
                row = [subs[i // (len(keys) // len(subs))] if len(subs) and len(keys) % len(subs) == 0 else "", k]
                for ln in langs_order:
                    row.append(langs[ln][i].replace("\t", " ").replace("\n", " "))
                f.write("\t".join(row) + "\n")
        print(f"{tname}: keys={len(keys)} langs={counts} untranslated_ZH={untr}")
    with open(os.path.join(OUT, "_summary.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(summary))
    print("done")


if __name__ == "__main__":
    main()