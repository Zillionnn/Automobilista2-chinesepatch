# -*- coding: utf-8 -*-
"""relocate_v4.py — 游戏更新后自动重定位 V4 字体补丁地址。

用法:
    python tools\\relocate_v4.py               # 用内置的旧版原版备份作参照，对照当前游戏 exe
    python tools\\relocate_v4.py --old <old.exe> --new <new.exe>

原理（见 deliverables/docs/addresses.md「重新定位」）:
  1. 在旧版原版 exe 与新 exe 中分别用特征字节定位三个锚点：
       glyph-fb  `74 0A 0F B7 D7`                     （唯一命中）
       E85C4E    `48 8B 8B 58 03 00 00 48 85 C9 74 12`
       fb-store  `49 89 85 58 03 00 00`                （唯一命中）
  2. 三个锚点的 (新 - 旧) 差值必须一致 → 引擎代码整体平移，其余站点直接加同一差值。
  3. 校验派生函数入口（GetGlyph / E85C10）的 48 字节窗口逐字节一致。
  4. 校验 P4 strcmp 调用点：字节为 E8，且 call 目标同样平移了同一差值。
  5. 计算新 .zh2 段 RVA（取 SizeOfImage，页对齐），输出可直接粘贴的常量块。
"""
import argparse
import struct
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = 0x140000000

# 旧版（2026-09-12 版，v1.6.9.95.3432）常量：新地址 = 旧地址 + 差值
OLD = {
    "AMS2.exe": {
        "path": r"F:\SteamLibrary\steamapps\common\Automobilista 2\AMS2.exe.bak-v4-orig-43185224",
        "GLYPH_FB": 0x140E8AF41,
        "E85C4E": 0x140E8B3CE,
        "FB_STORE": 0x140F089F2,
        "GETGLYPH": 0x140E8AEC0,
        "GLYPH_TAIL": 0x140E8AF4F,
        "GLYPH_RET0": 0x140E8AF4D,
        "E85C10_RECURSE": 0x140E8B3D3,
        "E85C10_RET0": 0x140E8B3E5,
        "P4_CALL1": 0x140F07A11,
        "P4_CALL2": 0x140F088FF,
        "ZH2_RVA": 0x2F13000,
    },
    "AMS2AVX.exe": {
        "path": r"F:\SteamLibrary\steamapps\common\Automobilista 2\AMS2AVX.exe.bak-v4-orig-42979912",
        "GLYPH_FB": 0x140E82F61,
        "E85C4E": 0x140E833EE,
        "FB_STORE": 0x140F00882,
        "GETGLYPH": 0x140E82EE0,
        "GLYPH_TAIL": 0x140E82F6F,
        "GLYPH_RET0": 0x140E82F6D,
        "E85C10_RECURSE": 0x140E833F3,
        "E85C10_RET0": 0x140E83405,
        "P4_CALL1": 0x140EFF8A1,
        "P4_CALL2": 0x140F0078F,
        "ZH2_RVA": 0x2EE0000,
    },
}

SIG_GLYPH_FB = "74 0A 0F B7 D7"
SIG_E85C4E = "48 8B 8B 58 03 00 00 48 85 C9 74 12"
SIG_FB_STORE = "49 89 85 58 03 00 00"


class PE:
    def __init__(self, path):
        self.path = path
        self.data = open(path, "rb").read()
        d = self.data
        e = struct.unpack_from("<I", d, 0x3C)[0]
        self.nsec = struct.unpack_from("<H", d, e + 6)[0]
        optsize = struct.unpack_from("<H", d, e + 20)[0]
        self.opt = e + 24
        self.size_of_image = struct.unpack_from("<I", d, self.opt + 56)[0]
        self.sec_tab = self.opt + optsize
        self.secs = []
        for i in range(self.nsec):
            o = self.sec_tab + i * 40
            name = d[o:o + 8].rstrip(b"\x00").decode("latin1")
            vsize, va, rsize, roff = struct.unpack_from("<IIII", d, o + 8)
            self.secs.append(dict(name=name, va=va, vsize=vsize, rsize=rsize, roff=roff))

    def va2file(self, va):
        rva = va - BASE
        for s in self.secs:
            if s["va"] <= rva < s["va"] + max(s["vsize"], s["rsize"]):
                return s["roff"] + (rva - s["va"])
        return None

    def file2va(self, f):
        for s in self.secs:
            if s["roff"] <= f < s["roff"] + s["rsize"]:
                return BASE + s["va"] + (f - s["roff"])
        return None

    def find(self, pattern):
        """C 级搜索：无通配符用 bytes.find，有通配符用正则（DOTALL）。"""
        import re
        toks = pattern.split()
        pb = [None if t == "??" else int(t, 16) for t in toks]
        if all(b is not None for b in pb):
            needle = bytes(pb)
            out, i = [], self.data.find(needle)
            while i != -1:
                out.append(i)
                i = self.data.find(needle, i + 1)
            return out
        rx = re.compile(b"".join(b"." if b is None else re.escape(bytes([b]))
                                 for b in pb), re.DOTALL)
        return [m.start() for m in rx.finditer(self.data)]

    def va_find(self, pattern):
        return [self.file2va(f) for f in self.find(pattern)]

    def call_target(self, va):
        f = self.va2file(va)
        if f is None or self.data[f] != 0xE8:
            return None
        rel = struct.unpack_from("<i", self.data, f + 1)[0]
        return va + 5 + rel

    def window(self, va, n=48):
        f = self.va2file(va)
        return self.data[f:f + n]


def analyse(name, old_cfg, new_path):
    print("=" * 72)
    print("%s" % name)
    print("  旧原版: %s" % old_cfg["path"])
    print("  新版本: %s" % new_path)
    old = PE(old_cfg["path"])
    new = PE(new_path)

    print("  [sections] old SizeOfImage=%X  new SizeOfImage=%X" % (
        old.size_of_image, new.size_of_image))

    deltas = {}
    for key, sig in (("GLYPH_FB", SIG_GLYPH_FB), ("E85C4E", SIG_E85C4E),
                     ("FB_STORE", SIG_FB_STORE)):
        ho = old.va_find(sig)
        hn = new.va_find(sig)
        if len(ho) != 1 or len(hn) != 1:
            print("  !! %s 特征命中数异常: old=%d new=%d" % (key, len(ho), len(hn)))
            return None
        deltas[key] = hn[0] - ho[0]
        print("  %-9s old=%X  new=%X  delta=%+#x" % (key, ho[0], hn[0], deltas[key]))

    uniq = set(deltas.values())
    if len(uniq) != 1:
        print("  !! 差值不统一 %s —— 代码非整体平移，需要逐站点重新定位" % (
            ["%+#x" % d for d in uniq]))
        return None
    delta = uniq.pop()
    print("  ==> 统一差值 delta = %+#x" % delta)

    out = {}
    for key in ("GETGLYPH", "GLYPH_TAIL", "GLYPH_RET0", "E85C10_RECURSE",
                "E85C10_RET0", "P4_CALL1", "P4_CALL2"):
        out[key] = old_cfg[key] + delta
    out["GLYPH_FB"] = old_cfg["GLYPH_FB"] + delta
    out["E85C4E"] = old_cfg["E85C4E"] + delta
    out["FB_STORE"] = old_cfg["FB_STORE"] + delta
    out["FB_NEXT"] = out["FB_STORE"] + 7

    # 校验：派生函数入口 48 字节窗口一致
    ok = True
    for key in ("GETGLYPH",):
        wo = old.window(old_cfg[key]); wn = new.window(out[key])
        same = wo == wn
        ok &= same
        print("  [check] %-14s window 48B %s" % (key, "identical" if same else "DIFFERENT"))
    for key, off in (("E85C10", 0),):
        # E85C10 入口 = E85C4E - 0x3E（AMS2/AVX 同规律）
        eo = old_cfg["E85C4E"] - 0x3E
        en = out["E85C4E"] - 0x3E
        same = old.window(eo) == new.window(en)
        ok &= same
        print("  [check] %-14s window 48B %s" % (key, "identical" if same else "DIFFERENT"))

    # 校验：P4 strcmp 调用点
    for key in ("P4_CALL1", "P4_CALL2"):
        ov, nv = old_cfg[key], out[key]
        to, tn = old.call_target(ov), new.call_target(nv)
        fo = old.va2file(ov); fn = new.va2file(nv)
        byte_ok = old.data[fo] == 0xE8 and new.data[fn] == 0xE8
        tgt_ok = (to is not None and tn is not None and tn - to == delta)
        ok &= byte_ok and tgt_ok
        print("  [check] %-9s E8=%s  target old=%s new=%s (delta %+#x) %s" % (
            key, byte_ok, hex(to) if to else "?", hex(tn) if tn else "?",
            (tn - to) if (to and tn) else 0, "OK" if tgt_ok else "MISMATCH"))
        # 上下文一致（调用点前后 8 字节，跳过 rel32）
        if fo is not None and fn is not None:
            ctx_o = old.data[fo - 8:fo] + old.data[fo + 5:fo + 13]
            ctx_n = new.data[fn - 8:fn] + new.data[fn + 5:fn + 13]
            same = ctx_o == ctx_n
            ok &= same
            print("            context %s" % ("identical" if same else "DIFFERENT"))

    zh2 = new.size_of_image
    zh2 = (zh2 + 0xFFF) & ~0xFFF
    new_soi = (zh2 + 0x800 + 0xFFF) & ~0xFFF
    out["ZH2_RVA"] = zh2
    print("  [zh2] RVA=%X  new SizeOfImage=%X (%.1f KB 追加)" % (
        zh2, new_soi, 0x800 / 1024.0))

    print("\n  ---- 常量块（复制到 patch 脚本）----")
    for key in ("P4_CALL1", "P4_CALL2", "GLYPH_FB", "E85C4E", "FB_STORE", "FB_NEXT",
                "GETGLYPH", "GLYPH_TAIL", "GLYPH_RET0", "E85C10_RECURSE", "E85C10_RET0"):
        print("    %-15s = 0x%X" % (key, out[key]))
    print("    ZH2_RVA         = 0x%X" % out["ZH2_RVA"])
    print("\n  结论: %s  (delta %+#x)" % ("可用，整体平移" if ok else "需要人工核对！", delta))
    out["_ok"] = ok
    out["_delta"] = delta
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--new", help="只分析这一个 exe（原名匹配 OLD 表）")
    ap.add_argument("--old", help="旧版原版 exe（配合 --new）")
    args = ap.parse_args()

    target = r"F:\SteamLibrary\steamapps\common\Automobilista 2"
    results = {}
    for name, cfg in OLD.items():
        new_path = args.new or (target + "\\" + name)
        if args.new:
            cfg = dict(cfg, path=args.old or cfg["path"])
        results[name] = analyse(name, cfg, new_path)
    print("\n" + "=" * 72)
    for name, r in results.items():
        if r is None:
            print("%s: 定位失败" % name)
        else:
            print("%s: delta=%+#x %s" % (name, r["_delta"], "OK" if r["_ok"] else "CHECK"))


if __name__ == "__main__":
    main()
