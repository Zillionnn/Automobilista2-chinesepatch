# -*- coding: utf-8 -*-
"""View translation samples and find the failing .tdb file."""
import struct, glob, os

# Find the failing tdb file
print("=== All .tdb files ===")
tdb_files = sorted(glob.glob(r"F:\Game\AMS2-ZH\work\extract\**\*.tdb", recursive=True))
for p in tdb_files:
    data = open(p, "rb").read()
    # Try to find the table name
    off = 8
    start = off
    while off < len(data) and 0x20 <= data[off] < 0x7F:
        off += 1
    tname = data[start:off].decode("latin1", "replace")
    sz = len(data) / 1024
    print("  %-40s  table=%-20s  size=%.0fKB" % (os.path.basename(p), tname, sz))

# Show samples from Game.tsv (largest, has untranslated)
print("\n=== Game.tsv samples (first 20 rows with EN/ZH) ===")
tsv = r"F:\Game\AMS2-ZH\work\tdb_tables\Game.tsv"
if os.path.exists(tsv):
    with open(tsv, "r", encoding="utf-8") as f:
        header = f.readline().strip()
        cols = header.split("\t")
        print("Columns:", cols[:5])
        for i, line in enumerate(f):
            if i >= 20:
                break
            parts = line.strip().split("\t")
            if len(parts) >= 4:
                key = parts[1] if len(parts) > 1 else ""
                en = parts[2] if len(parts) > 2 else ""
                zh = parts[3] if len(parts) > 3 else ""  # Chinese-Simple
                print("  [%d] key=%-30s EN=%-40s ZH=%s" % (i, key[:30], en[:40], zh[:60]))

# Count UNTRANSLATED in each file
print("\n=== UNTRANSLATED count per table ===")
for tsv in sorted(glob.glob(r"F:\Game\AMS2-ZH\work\tdb_tables\*.tsv")):
    with open(tsv, "r", encoding="utf-8") as f:
        header = f.readline()
        total = 0
        untr = 0
        for line in f:
            total += 1
            if "UNTRANSLATED" in line:
                untr += 1
    print("  %-30s  total=%5d  untranslated=%4d" % (os.path.basename(tsv), total, untr))
