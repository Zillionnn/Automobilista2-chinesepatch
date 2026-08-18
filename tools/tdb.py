"""Full tdb parser v2: [version][langCount][table: name,6meta,keys][lang blocks]."""
import struct
import sys


def parse_tdb(path):
    data = open(path, "rb").read()
    version = struct.unpack_from("<I", data, 0)[0]
    nlang = struct.unpack_from("<I", data, 4)[0]
    off = 8

    start = off
    while off < len(data) and 0x20 <= data[off] < 0x7F:
        off += 1
    tname = data[start:off].decode("latin1")
    meta = [struct.unpack_from("<I", data, off + 4 * i)[0] for i in range(6)]
    off += 24

    keys = []
    while True:
        ln = struct.unpack_from("<I", data, off)[0]
        if ln > 0x8000 or off + 4 + ln > len(data):
            break
        s = data[off + 4:off + 4 + ln]
        if not all(0x20 <= b < 0x7F for b in s):
            break
        keys.append(s.decode("latin1"))
        off += 4 + ln

    langs = []
    for _ in range(nlang):
        ln = struct.unpack_from("<I", data, off)[0]
        lname = data[off + 4:off + 4 + ln].decode("latin1")
        off += 4 + ln
        bsize = struct.unpack_from("<I", data, off)[0]
        off += 4
        end = off + bsize
        entries = []
        while off + 12 <= end:
            h = data[off:off + 4].hex()
            cc = struct.unpack_from("<I", data, off + 8)[0]
            if off + 12 + cc * 2 > end or cc > 1_000_000:
                break
            val = data[off + 12:off + 12 + cc * 2].decode("utf-16-le", "replace")
            entries.append((h, cc, val))
            off += 12 + cc * 2
        langs.append((lname, bsize, entries))
    return tname, meta, keys, langs


if __name__ == "__main__":
    p = sys.argv[1] if len(sys.argv) > 1 else r"F:\Game\AMS2-ZH\work\extract\BOOTSPLASH\file_0004.tdb"
    tname, meta, keys, langs = parse_tdb(p)
    print(f"table={tname!r} meta={meta} keys={len(keys)} langs={[l[0] for l in langs]}")
    for i, (h, cc, v) in enumerate(langs[0][2][:8]):
        k = keys[i] if i < len(keys) else "?"
        print(f"  [{i}] {k!r} -> {v[:60]!r}")