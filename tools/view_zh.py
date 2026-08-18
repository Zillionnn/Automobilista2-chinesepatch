# -*- coding: utf-8 -*-
"""View Chinese-Simple translations correctly (column 14 in TSV)."""
import csv, os

tsv_dir = r"F:\Game\AMS2-ZH\work\tdb_tables"

# Read Game.tsv with proper column mapping
tsv = os.path.join(tsv_dir, "Game.tsv")
with open(tsv, "r", encoding="utf-8") as f:
    reader = csv.reader(f, delimiter="\t")
    header = next(reader)
    print("Columns:", header)
    zh_idx = header.index("Chinese-Simple") if "Chinese-Simple" in header else -1
    en_idx = header.index("English") if "English" in header else 2
    print("EN column: %d, ZH column: %d" % (en_idx, zh_idx))

    print("\n=== Game.tsv: EN -> ZH samples ===")
    shown = 0
    untr_count = 0
    for row in reader:
        if len(row) <= zh_idx:
            continue
        key = row[1] if len(row) > 1 else ""
        en = row[en_idx] if len(row) > en_idx else ""
        zh = row[zh_idx] if len(row) > zh_idx else ""

        if "UNTRANSLATED" in zh:
            untr_count += 1
            if untr_count <= 10:
                print("  [UNTR] key=%-30s EN=%-40s" % (key[:30], en[:40]))
        elif shown < 20:
            print("  [ OK ] key=%-30s EN=%-30s ZH=%s" % (key[:30], en[:30], zh[:50]))
            shown += 1

    print("\n  Total UNTRANSLATED in Game: %d" % untr_count)

# Also check General.tsv
print("\n=== General.tsv: UNTRANSLATED samples ===")
tsv2 = os.path.join(tsv_dir, "General.tsv")
with open(tsv2, "r", encoding="utf-8") as f:
    reader = csv.reader(f, delimiter="\t")
    header = next(reader)
    zh_idx = header.index("Chinese-Simple") if "Chinese-Simple" in header else -1
    en_idx = header.index("English") if "English" in header else 2
    untr_count = 0
    for row in reader:
        if len(row) <= zh_idx:
            continue
        zh = row[zh_idx]
        en = row[en_idx]
        key = row[1]
        if "UNTRANSLATED" in zh:
            untr_count += 1
            if untr_count <= 15:
                print("  key=%-35s EN=%s" % (key[:35], en[:60]))
    print("  Total UNTRANSLATED in General: %d" % untr_count)

# Check RAC.tsv
print("\n=== RAC.tsv: UNTRANSLATED samples ===")
tsv3 = os.path.join(tsv_dir, "RAC.tsv")
with open(tsv3, "r", encoding="utf-8") as f:
    reader = csv.reader(f, delimiter="\t")
    header = next(reader)
    zh_idx = header.index("Chinese-Simple") if "Chinese-Simple" in header else -1
    en_idx = header.index("English") if "English" in header else 2
    untr_count = 0
    for row in reader:
        if len(row) <= zh_idx:
            continue
        zh = row[zh_idx]
        en = row[en_idx]
        key = row[1]
        if "UNTRANSLATED" in zh:
            untr_count += 1
            if untr_count <= 15:
                print("  key=%-35s EN=%s" % (key[:35], en[:60]))
    print("  Total UNTRANSLATED in RAC: %d" % untr_count)
