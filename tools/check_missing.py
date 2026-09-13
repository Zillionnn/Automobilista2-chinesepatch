# -*- coding: utf-8 -*-
"""check_missing.py — 对比「新版未翻译条目」与「现有 translations.json」。

游戏更新后使用：先 tdb_dump.py，再 tdb_extract.py，然后本工具。

输出:
  - 新版未翻译条目总数 / 其中已有翻译（部署即生效）
  - 需要新翻译的条目 → work/translations/need_translation.json
  - 现有翻译中在新版表里已不存在的键（过时条目，可留可删）
"""
import json
import sys
from collections import Counter

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TRANS = r"F:\Game\AMS2-ZH\work\translations\translations.json"
UNTR = r"F:\Game\AMS2-ZH\work\translations\untranslated.json"
ALL = r"F:\Game\AMS2-ZH\work\translations\all_entries.json"
NEED = r"F:\Game\AMS2-ZH\work\translations\need_translation.json"


def main():
    trans = json.load(open(TRANS, encoding="utf-8"))
    untr = json.load(open(UNTR, encoding="utf-8"))
    allent = json.load(open(ALL, encoding="utf-8"))

    have = 0
    need = []
    for e in untr:
        t, k = e["table"], e["key"]
        if trans.get(t, {}).get(k):
            have += 1
        else:
            need.append(e)

    keyset = {(e["table"], e["key"]) for e in allent}
    obsolete = [(t, k) for t, d in trans.items() for k in d if (t, k) not in keyset]

    json.dump(need, open(NEED, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    print("新版未翻译条目: %d" % len(untr))
    print("  其中已有翻译（部署即生效）: %d" % have)
    print("  需要新翻译: %d  -> %s" % (len(need), NEED))
    print("现有翻译中已过时的键: %d" % len(obsolete))
    if need:
        print("\n按表分布:")
        for t, n in Counter(e["table"] for e in need).most_common():
            print("  %-12s %d" % (t, n))


if __name__ == "__main__":
    main()
