# -*- coding: utf-8 -*-
"""Extract all UNTRANSLATED entries into a translatable JSON file.

Output: work/translations/untranslated.json
Format: [{"table": "Game", "key": "Game_MainMenu_FinalDrive", "english": "FINAL DRIVE", "chinese": ""}, ...]
"""
import csv, json, os, glob

tsv_dir = r"F:\Game\AMS2-ZH\work\tdb_tables"
out_dir = r"F:\Game\AMS2-ZH\work\translations"
os.makedirs(out_dir, exist_ok=True)

entries = []
stats = {}

for tsv in sorted(glob.glob(os.path.join(tsv_dir, "*.tsv"))):
    table = os.path.basename(tsv).replace(".tsv", "")
    if table.startswith("_"):
        continue
    with open(tsv, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t", quoting=csv.QUOTE_NONE)
        header = next(reader)
        zh_idx = header.index("Chinese-Simple") if "Chinese-Simple" in header else -1
        en_idx = header.index("English") if "English" in header else 2
        if zh_idx < 0:
            continue
        for row in reader:
            if len(row) <= zh_idx:
                continue
            zh = row[zh_idx]
            en = row[en_idx] if len(row) > en_idx else ""
            key = row[1] if len(row) > 1 else ""
            if "UNTRANSLATED" in zh:
                entries.append({
                    "table": table,
                    "key": key,
                    "english": en,
                    "chinese": "",
                })
                stats[table] = stats.get(table, 0) + 1

out_path = os.path.join(out_dir, "untranslated.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(entries, f, ensure_ascii=False, indent=2)

print("Extracted %d untranslated entries to %s" % (len(entries), out_path))
print("\nBreakdown by table:")
for table, count in sorted(stats.items(), key=lambda x: -x[1]):
    print("  %-20s %4d" % (table, count))

# Also extract ALL entries for full translation review
all_entries = []
for tsv in sorted(glob.glob(os.path.join(tsv_dir, "*.tsv"))):
    table = os.path.basename(tsv).replace(".tsv", "")
    if table.startswith("_"):
        continue
    with open(tsv, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t", quoting=csv.QUOTE_NONE)
        header = next(reader)
        zh_idx = header.index("Chinese-Simple") if "Chinese-Simple" in header else -1
        en_idx = header.index("English") if "English" in header else 2
        if zh_idx < 0:
            continue
        for row in reader:
            if len(row) <= zh_idx:
                continue
            zh = row[zh_idx]
            en = row[en_idx] if len(row) > en_idx else ""
            key = row[1] if len(row) > 1 else ""
            all_entries.append({
                "table": table,
                "key": key,
                "english": en,
                "chinese": zh if "UNTRANSLATED" not in zh else "",
            })

all_path = os.path.join(out_dir, "all_entries.json")
with open(all_path, "w", encoding="utf-8") as f:
    json.dump(all_entries, f, ensure_ascii=False, indent=2)

print("\nTotal entries: %d -> %s" % (len(all_entries), all_path))
