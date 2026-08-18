# -*- coding: utf-8 -*-
"""Scan AMS2.exe (non-AVX) for byte patterns to relocate key functions."""
import struct
import sys

EXE = r"F:\SteamLibrary\steamapps\common\Automobilista 2\AMS2.exe"

# patterns (name, hex pattern with ?? wildcards)
PATTERNS = [
    ("glyph_fallback_recursion",  # 0x140E7D8A7 in AVX: mov rcx,[rbx+0x358]; test; je; movzx edx,di; call
     "48 8B 8B 58 03 00 00 48 85 C9 74 ?? 0F B7 D7 E8"),
    ("slot_strcmp_call",          # 0x140EFB0D7 in AVX: mov rcx,[rsp+0x60]; mov rdx,rax; call strcmp
     "48 8B 4C 24 60 48 8B D0 E8"),
    ("cache_strcmp_call",         # 0x140EFA1E1..F1 in AVX: mov rax,[rbp-0x50]; test; cmovne rcx,rax; ...; call strcmp
     "48 8B 45 B0 48 85 C0 48 0F 44 C8 48 85 D2 74 ?? E8"),
    ("reg_count_read",            # 0x140EFA070 in AVX: mov ecx,[rip+disp] ; mov edi,0
     "8B 0D ?? ?? ?? ?? 45 33 FF 48 89 7C 24 40"),
    ("fallback_358_write",        # 0x140EFB1D2 in AVX: mov [r13+0x358],rax
     "49 89 45 58"),
    ("lang_strcmp_call",          # 0x140EFB08C in AVX: mov rdx,rax; call strcmp (language match)
     "48 8B D0 E8"),
    ("font_cache_loop",           # 0x140EF9F50 prologue-ish: mov [rsp+8],rcx; push rbp...
     "48 89 4C 24 08 55 53 56 57 41 55 41 56 41 57"),
]


def find_all(data, pattern):
    toks = pattern.split()
    pbytes = []
    for t in toks:
        pbytes.append(None if t == "??" else int(t, 16))
    n = len(pbytes)
    out = []
    for i in range(len(data) - n + 1):
        ok = True
        for j, b in enumerate(pbytes):
            if b is not None and data[i + j] != b:
                ok = False
                break
        if ok:
            out.append(i)
    return out


def main():
    with open(EXE, "rb") as f:
        data = f.read()
    # section map
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    opt = pe + 24
    nsec = struct.unpack_from("<H", data, pe + 6)[0]
    sec_off = opt + struct.unpack_from("<H", data, pe + 20)[0]
    secs = []
    for i in range(nsec):
        off = sec_off + i * 40
        name = data[off:off + 8].rstrip(b"\x00").decode("latin1")
        vsize, va, rsize, roff = struct.unpack_from("<IIII", data, off + 8)
        secs.append((name, va, vsize, roff, rsize))
        print("%-8s VA=%08X VSize=%08X RawOff=%08X RawSize=%08X" % (name, va, vsize, roff, rsize))
    print("file size:", hex(len(data)))

    def f2va(f):
        for name, va, vsize, roff, rsize in secs:
            if roff <= f < roff + rsize:
                return 0x140000000 + va + (f - roff)
        return None

    print()
    for name, pat in PATTERNS:
        hits = find_all(data, pat)
        print("%-24s %d hits" % (name, len(hits)))
        for h in hits[:12]:
            va = f2va(h)
            print("   file=%#x va=%s" % (h, hex(va) if va else "?"))
        if len(hits) > 12:
            print("   ... (%d more)" % (len(hits) - 12))


if __name__ == "__main__":
    main()
