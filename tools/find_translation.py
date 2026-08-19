# -*- coding: utf-8 -*-
"""find_translation.py — 在 translations.json 中按关键词查找翻译条目。

用法:
  python tools/find_translation.py 关键词 [表名]

示例:
  python tools/find_translation.py 光头胎          # 按中文找
  python tools/find_translation.py TestDay        # 按键名找
  python tools/find_translation.py 赛道 Game      # 限定表名

提示: 若 cmd 下中文乱码，先执行 chcp 65001

输出格式: 表名<TAB>键名<TAB>当前中文
找到后编辑: work/translations/translations.json
"""
import json
import sys

TRANS_PATH = r"F:\Game\AMS2-ZH\work\translations\translations.json"

# 强制 UTF-8 输出，避免 cmd(GBK) 下中文乱码；配合 chcp 65001 使用
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    kw = sys.argv[1].lower()
    table_filter = sys.argv[2] if len(sys.argv) > 2 else None

    trans = json.load(open(TRANS_PATH, encoding="utf-8"))
    hits = 0
    for table, entries in trans.items():
        if table_filter and table != table_filter:
            continue
        for key, val in entries.items():
            if kw in key.lower() or kw in val.lower():
                print("%s\t%s\t%s" % (table, key, val))
                hits += 1

    print("\n%d 条匹配（表/键/当前中文）" % hits)
    print("修改方式: 用编辑器打开 %s，按键名搜索后改中文值" % TRANS_PATH)


if __name__ == "__main__":
    main()
