# -*- coding: utf-8 -*-
"""find_translation.py — 查找翻译条目（补丁翻译 + 游戏内置翻译）。

默认搜 translations.json（我们维护的补丁翻译）；加 --all 同时搜
all_entries.json（游戏内置翻译全量参考，只读，用来查键名）。

用法:
  python tools/find_translation.py 关键词 [表名] [--all]

示例:
  python tools/find_translation.py 光头胎              # 补丁翻译
  python tools/find_translation.py 煞车死区 --all     # 内置翻译（含补丁）
  python tools/find_translation.py TestDay Game       # 限定表名

输出格式: 表名<TAB>键名<TAB>中文<TAB>[来源]
修改方式: 把 "表名/键名/新中文" 写进 translations.json，然后 deploy.py --deploy
"""
import json
import sys

TRANS_PATH = r"F:\Game\AMS2-ZH\work\translations\translations.json"
ALL_PATH = r"F:\Game\AMS2-ZH\work\translations\all_entries.json"

# 强制 UTF-8 输出，避免 cmd(GBK) 下中文乱码；配合 chcp 65001 使用
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def search_translations(kw, table_filter):
    """搜补丁翻译 translations.json。"""
    hits = 0
    trans = json.load(open(TRANS_PATH, encoding="utf-8"))
    for table, entries in trans.items():
        if table_filter and table != table_filter:
            continue
        for key, val in entries.items():
            if kw in key.lower() or kw in val.lower():
                print("%s\t%s\t%s\t[补丁翻译]" % (table, key, val))
                hits += 1
    return hits


def search_all_entries(kw, table_filter):
    """搜游戏内置翻译 all_entries.json（全量参考）。"""
    hits = 0
    data = json.load(open(ALL_PATH, encoding="utf-8"))
    for e in data:
        if table_filter and e["table"] != table_filter:
            continue
        if kw in e["key"].lower() or kw in e["english"].lower() or kw in e["chinese"].lower():
            print("%s\t%s\t%s\t[游戏内置]" % (e["table"], e["key"], e["chinese"]))
            hits += 1
    return hits


def main():
    args = [a for a in sys.argv[1:] if a != "--all"]
    all_flag = "--all" in sys.argv
    if not args:
        print(__doc__)
        sys.exit(1)
    kw = args[0].lower()
    table_filter = args[1] if len(args) > 1 else None

    hits = search_translations(kw, table_filter)
    if all_flag:
        hits += search_all_entries(kw, table_filter)

    print("\n%d 条匹配（表/键/中文/来源）" % hits)
    print("修改方式: 用编辑器打开 translations.json，按键名搜索后改中文值，再运行 deploy.py --deploy")


if __name__ == "__main__":
    main()
