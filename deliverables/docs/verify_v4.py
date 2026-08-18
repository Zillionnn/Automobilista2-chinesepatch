# -*- coding: utf-8 -*-
"""Runtime verification V2 for the V4 static patch (run while AMS2.exe is up).

Checks:
  1. hooks live in memory (glyph-fb / E85C4E / fb-store / P4 sites)
  2. slot table 0x142F090C0 (s12/s17/s31)
  3. font registry: names / sizes / +0x358 links
  4. provider table flag for Chinese-Simple
"""
import ctypes
import struct

import psutil

k32 = ctypes.windll.kernel32
COUNT_VA = 0x14273A4B8      # u32 count (vector at 0x14273A490 -> begin)
BASE_VA = 0x14273A490
SLOTS_VA = 0x142F090C0


def main():
    pid = None
    for p in psutil.process_iter(["name", "pid"]):
        if p.info["name"] and p.info["name"].lower() == "ams2.exe":
            pid = p.info["pid"]
            break
    if pid is None:
        print("AMS2.exe not running")
        return
    h = k32.OpenProcess(0x1F0FFF, False, pid)
    w = ctypes.c_size_t()

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

    print("pid:", pid)
    print("--- hooks in memory ---")
    for va, n, name in ((0x140E857C1, 5, "glyph-fb"), (0x140E85C4E, 5, "E85C4E"),
                        (0x140F03272, 7, "fb-store"),
                        (0x140F02291, 5, "p4-cache"), (0x140F0317F, 5, "p4-slot"),
                        (SLOTS_VA - 0x80, 8, "shared"), (SLOTS_VA - 0x40, 8, "stub")):
        b = rd(va, n)
        print("  %-9s @%X: %s" % (name, va, b.hex() if b else "<no read>"))

    print("--- slots ---")
    for i, nm in enumerate(("s12", "s17", "s31")):
        v = u64(SLOTS_VA + i * 8)
        nm2 = ""
        if v:
            p = u64(v + 0x340)
            nm2 = cstr(p) or "?"
        print("  slot %s = %s (%s)" % (nm, hex(v) if v else "0", nm2))

    print("--- registry ---")
    vec = u64(BASE_VA)          # vector object
    arr = u64(vec) if vec else 0   # begin pointer
    count = u32(COUNT_VA) or 0
    print("  vec=%s arr=%s count=%d" % (hex(vec) if vec else "0",
                                        hex(arr) if arr else "0", count))
    if arr and count and count < 0x200:
        for i in range(count):
            v = u64(arr + i * 8)
            if not v:
                continue
            nm = cstr(u64(v + 0x340) or 0) or "?"
            size = u32(v + 0x44)
            fb = u64(v + 0x358)
            fbn = ""
            if fb:
                fbn = cstr(u64(fb + 0x340) or 0) or "?"
            print("  [%2d] %-46s size=%-3d fb=%s (%s)" % (
                i, nm[:46], size, hex(fb) if fb else "0", fbn))

    print("--- provider flags ---")
    for off, nm in ((0x1425EDD40, "Japanese"), (0x1425EDDA8, "Korean"),
                    (0x1425EDE10, "Chinese-Simple")):
        flag = u32(off + 0x10)
        print("  %s flag=%d" % (nm, flag))


if __name__ == "__main__":
    main()
