# -*- coding: utf-8 -*-
"""Runtime verification for the V4 static patch (run while the game is up).

适用版本：2026-09-12 Steam 更新版
  AMS2.exe     原始 43,185,224 → 补丁后 43,187,712
  AMS2AVX.exe  原始 42,979,912 → 补丁后 42,982,400
（补丁地址 = 旧版地址 + 0x5780 / +0x56B0）

Checks:
  1. hooks live in memory (glyph-fb / E85C4E / fb-store / P4 sites + .zh2 code)
  2. slot table (.zh2 + 0x300): s12 / s17 / s31 是否已捕获中文字体
  3. font registry（仅 AMS2.exe，地址按 .data 段位移推算，仅供参考）

用法: python tools/verify_v4.py [ams2|avx]
"""
import ctypes
import struct
import sys

import psutil

k32 = ctypes.windll.kernel32

PROFILES = {
    "ams2": {
        "process": "ams2.exe",
        "slots": 0x142F13300,          # .zh2 (RVA 0x2F13000) + 0x300
        "hooks": ((0x140E8AF41, 5, "glyph-fb"), (0x140E8B3CE, 5, "E85C4E"),
                  (0x140F089F2, 7, "fb-store"),
                  (0x140F07A11, 5, "p4-cache"), (0x140F088FF, 5, "p4-slot")),
        "base_va": 0x142744A90,        # 字体注册表 vector（.data +0xA000 推算）
        "count_va": 0x142744AB8,
    },
    "avx": {
        "process": "ams2avx.exe",
        "slots": 0x142EE0300,          # .zh2 (RVA 0x2EE0000) + 0x300
        "hooks": ((0x140E82F61, 5, "glyph-fb"), (0x140E833EE, 5, "E85C4E"),
                  (0x140F00882, 7, "fb-store"),
                  (0x140EFF8A1, 5, "p4-cache"), (0x140F0078F, 5, "p4-slot")),
        "base_va": None,
        "count_va": None,
    },
}


def main():
    want = sys.argv[1].lower() if len(sys.argv) > 1 else None
    prof = None
    pid = None
    for p in psutil.process_iter(["name", "pid"]):
        name = (p.info["name"] or "").lower()
        for key, pr in PROFILES.items():
            if name == pr["process"] and (want is None or want == key):
                prof, pid = pr, p.info["pid"]
                break
        if prof:
            break
    if prof is None:
        print("游戏未运行（可用参数指定 ams2 / avx）")
        return

    slots = prof["slots"]
    h = k32.OpenProcess(0x1F0FFF, False, pid)
    if not h:
        print("OpenProcess 失败（需要与游戏相同的权限级别运行）")
        return

    def rd(a, n):
        b = ctypes.create_string_buffer(n)
        c = ctypes.c_size_t()
        if k32.ReadProcessMemory(h, ctypes.c_void_p(a), b, n, ctypes.byref(c)):
            return b.raw[:c.value]
        return None

    def u64(a):
        raw = rd(a, 8)
        return struct.unpack("<Q", raw)[0] if raw else None

    def u32(a):
        raw = rd(a, 4)
        return struct.unpack("<I", raw)[0] if raw else None

    def cstr(a, maxn=128):
        raw = rd(a, maxn)
        if not raw:
            return None
        return raw.split(b"\x00")[0].decode("latin1", "replace")

    print("进程: %s (pid=%d)" % (prof["process"], pid))
    print("--- 钩子（内存中实际字节）---")
    for va, n, name in prof["hooks"] + (
            (slots - 0x300, 8, "shared"), (slots - 0x280, 8, "stub")):
        b = rd(va, n)
        ok = ""
        if b and b[:1] in (b"\xe9", b"\xe8", b"\x48", b"\x49"):
            ok = "OK"
        print("  %-9s @%X: %-24s %s" % (name, va, b.hex() if b else "<读取失败>", ok))

    print("--- 槽位（中文字体指针，游戏加载中文后应非 0）---")
    for i, nm in enumerate(("s12", "s17", "s31")):
        v = u64(slots + i * 8)
        nm2 = ""
        if v:
            nm2 = cstr(u64(v + 0x340) or 0) or "?"
        print("  slot %-3s = %-14s %s" % (nm, hex(v) if v else "0", nm2))

    if prof["base_va"]:
        print("--- 字体注册表（推算地址，仅供参考）---")
        vec = u64(prof["base_va"])
        arr = u64(vec) if vec else 0
        count = u32(prof["count_va"]) or 0
        print("  vec=%s arr=%s count=%d" % (hex(vec) if vec else "0",
                                            hex(arr) if arr else "0", count))
        if arr and count and count < 0x200:
            for i in range(count):
                v = u64(arr + i * 8)
                if not v:
                    continue
                nm = cstr(u64(v + 0x340) or 0) or "?"
                print("  [%2d] %-46s size=%-3d fb=%s" % (
                    i, nm[:46], u32(v + 0x44), hex(u64(v + 0x358) or 0)))


if __name__ == "__main__":
    main()
