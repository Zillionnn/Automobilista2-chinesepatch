# -*- coding: utf-8 -*-
"""V4 static patch for AMS2.exe — fixes the V2/V3 crash root cause.

Diagnosis (from crash dumps AMS2.exe.*.dmp, e.g. 0xCB2E57CF NX fault):
  The previous patch wrote its 23-byte stub at file 0x1E471DE, but ext
  (53 bytes at 0x1E471AB) ends at 0x1E471E0 — the stub's first two bytes
  (49 89) overwrote the trailing `jmp 0x140E857CF` displacement, turning
  it into `jmp 0xCB2E57CF` (execution on heap -> c0000005 NX fault on
  every CJK font-fallback at startup).

V4 layout (all new code goes into an appended RWX section ".zh2" so it
can never overlap anything):
  .zh2 @ VA 0x142F13000 (RVA 0x2F13000), RawOff after file end, 0x800 B:
    +0x000  shared routine (87 B): GetGlyph-fallback + E85C10-fallback
    +0x080  stub (49 B): fb-store capture -> tier slots
    +0x100  P4 variant-tolerant strcmp helper (303 B)
    +0x300  slots[3] (24 B): s12 / s17 / s31 asian font pointers

  2026-09 游戏更新后：新版 .text 尾部只剩 244 B 零填充，放不下 303 B 的
  P4 helper，因此 P4 也移入 .zh2 段（不再使用 .text tail cave，也不再需要
  .text VSize 修补）。所有代码地址 = 旧版地址 + 0x5780。

Hooks (新版地址):
  0x140E8AF41  glyph-fb   (74 0A 0F B7 D7) -> E9 shared        [only when +0x358==0]
  0x140E8B3CE  E85C10 fb  (48 85 C9 74 12) -> E9 shared        [rcx=[rbx+0x358] preset]
  0x140F089F2  fb-store   (49 89 85 58 03 00 00) -> E9 stub + 2 NOP
  0x140F07A11  P4 cache strcmp   -> E8 helper
  0x140F088FF  P4 slot strcmp    -> E8 helper

Shared routine (entered with rbx=font, rcx=[rbx+0x358], rdi=glyphcode
(glyph entry, bit31 clear) or rdi=glyph-record (measure entry, bit31 set)):
  test rcx,rcx ; jnz done          ; use game's own +0x358 link if set
  tier = (size<=0x11 ? 0 : size<=0x17 ? 1 : 2);  rcx = slots[tier]
done:
  cmp rcx,rbx ; je ret0            ; anti-recursion (asian font self-check)
  test rcx,rcx ; jz ret0
  test edi,edi ; js measure        ; dispatch on record-vs-code bit31
  glyph: movzx edx,di ; call GetGlyph ; jmp GetGlyph-epilogue
  measure: jmp 0x140E8B3D3         ; original tail-recursion into E85C10
  ret0:  jmp 0x140E8AF4D / 0x140E8B3E5 depending on entry

Stub (r13=slot font, rax=asian font just loaded by fallback):
  mov [r13+0x358],rax              ; original instruction (kept)
  tier = f([r13+0x44]);  slots[tier] = rax ; jmp 0x140F089F9 (lock inc)

Run with the game CLOSED.
"""
import os
import struct

EXE = r"F:\SteamLibrary\steamapps\common\Automobilista 2\AMS2.exe"
# 备份名按未打补丁的文件大小区分版本，游戏更新后不会覆盖老版本的原版备份
BAK = "%s.bak-v4-orig-%d" % (EXE, os.path.getsize(EXE))

# ---------- constants ----------
# 游戏版本：2026-09-12 Steam 更新版（AMS2.exe 43,185,224 字节）
# 新地址 = 旧版 V4 地址 + 0x5780（引擎代码整体后移；GetGlyph/E85C10 函数
# 入口 48 字节窗口在新版中逐字节一致，glyph-fb / fb-store 指纹唯一命中）
P4_CALL1_VA = 0x140F07A11
P4_CALL2_VA = 0x140F088FF

ZH2_RVA = 0x2F13000
ZH2_VA = 0x140000000 + ZH2_RVA
ZH2_RAWSIZE = 0x800
SHARED_VA = ZH2_VA + 0x000
STUB_VA = ZH2_VA + 0x080
P4_VA = ZH2_VA + 0x100
SLOTS_VA = ZH2_VA + 0x300

GLYPH_FB = 0x140E8AF41
E85C4E = 0x140E8B3CE
FB_STORE = 0x140F089F2
FB_NEXT = 0x140F089F9
GETGLYPH = 0x140E8AEC0
GLYPH_TAIL = 0x140E8AF4F
GLYPH_RET0 = 0x140E8AF4D
E85C10_RECURSE = 0x140E8B3D3
E85C10_RET0 = 0x140E8B3E5


def rel_jmp(to_va, from_va):
    r = to_va - (from_va + 5)
    assert -0x80000000 <= r <= 0x7FFFFFFF, hex(r)
    return b"\xE9" + struct.pack("<i", r)


def rel_call(to_va, from_va):
    r = to_va - (from_va + 5)
    assert -0x80000000 <= r <= 0x7FFFFFFF, hex(r)
    return b"\xE8" + struct.pack("<i", r)


def rel8(to_off, from_off):
    r = to_off - (from_off + 2)
    assert -128 <= r <= 127, r
    return struct.pack("<b", r)


def rip_lea(reg, dst_va, from_va):
    """48 8D <modrm 05|0D> disp32 — lea reg,[rip+disp32]"""
    disp = dst_va - (from_va + 7)
    assert -0x80000000 <= disp <= 0x7FFFFFFF, hex(disp)
    return bytes([0x48, 0x8D, reg]) + struct.pack("<i", disp)


# ---------- shared routine ----------
def build_shared():
    o = bytearray()
    o += bytes.fromhex("48 85 C9")                      # 0  test rcx,rcx
    jnz = len(o); o += b"\x75\x00"                      # 3  jnz done
    o += bytes.fromhex("8B 43 44")                      # 5  mov eax,[rbx+0x44]
    o += bytes.fromhex("31 D2")                         # 8  xor edx,edx
    o += bytes.fromhex("83 F8 17")                      # 10 cmp eax,0x17 (23)
    jle1 = len(o); o += b"\x7E\x00"                     # 13 jle gotidx
    o += bytes.fromhex("BA 01 00 00 00")                # 15 mov edx,1
    o += bytes.fromhex("83 F8 20")                      # 20 cmp eax,0x20 (32)
    jle2 = len(o); o += b"\x7E\x00"                     # 23 jle gotidx
    o += bytes.fromhex("BA 02 00 00 00")                # 25 mov edx,2
    gotidx = len(o)                                     # 30
    o += rip_lea(0x05, SLOTS_VA, ZH2_VA + len(o))       # 30 lea rax,[rip+slots]
    o += bytes.fromhex("48 8B 0C D0")                   # 37 mov rcx,[rax+rdx*8]
    o += bytes.fromhex("48 85 C9")                      # 41 test rcx,rcx
    jnz2 = len(o); o += b"\x75\x00"                     # 44 jnz done
    o += bytes.fromhex("48 8B 48 08")                   # 46 fallback slots[1]
    o += bytes.fromhex("48 85 C9")                      # 49 test rcx,rcx
    jnz3 = len(o); o += b"\x75\x00"                     # 52 jnz done
    o += bytes.fromhex("48 8B 48 10")                   # 54 fallback slots[2]
    done = len(o)                                       # 57
    o += bytes.fromhex("48 39 D9")                      # 57 cmp rcx,rbx
    je1 = len(o); o += b"\x74\x00"                      # 60 je ret0
    o += bytes.fromhex("48 85 C9")                      # 62 test rcx,rcx
    jz1 = len(o); o += b"\x74\x00"                      # 65 jz ret0
    o += bytes.fromhex("85 FF")                         # 67 test edi,edi
    js1 = len(o); o += b"\x78\x00"                      # 69 js doM
    o += bytes.fromhex("0F B7 D7")                      # 71 movzx edx,di
    o += rel_call(GETGLYPH, ZH2_VA + len(o))            # 74 call GetGlyph
    o += rel_jmp(GLYPH_TAIL, ZH2_VA + len(o))           # 79 jmp epilogue
    doM = len(o)                                        # 84
    o += rel_jmp(E85C10_RECURSE, ZH2_VA + len(o))       # 84 jmp 0x140E8B3D3
    ret0 = len(o)                                       # 89
    o += bytes.fromhex("85 FF")                         # 89 test edi,edi
    js2 = len(o); o += b"\x78\x00"                      # 91 js ret0M
    o += rel_jmp(GLYPH_RET0, ZH2_VA + len(o))           # 93 jmp 0x140E8AF4D
    ret0M = len(o)                                      # 98
    o += rel_jmp(E85C10_RET0, ZH2_VA + len(o))          # 98 jmp 0x140E8B3E5

    o[jnz + 1] = rel8(done, jnz)[0]
    o[jle1 + 1] = rel8(gotidx, jle1)[0]
    o[jle2 + 1] = rel8(gotidx, jle2)[0]
    o[jnz2 + 1] = rel8(done, jnz2)[0]
    o[jnz3 + 1] = rel8(done, jnz3)[0]
    o[je1 + 1] = rel8(ret0, je1)[0]
    o[jz1 + 1] = rel8(ret0, jz1)[0]
    o[js1 + 1] = rel8(doM, js1)[0]
    o[js2 + 1] = rel8(ret0M, js2)[0]
    return bytes(o)


# ---------- stub ----------
def build_stub():
    o = bytearray()
    o += bytes.fromhex("49 89 85 58 03 00 00")          # 0  mov [r13+0x358],rax
    o += bytes.fromhex("41 8B 4D 44")                   # 7  mov ecx,[r13+0x44]
    o += bytes.fromhex("31 D2")                         # 11 xor edx,edx
    o += bytes.fromhex("83 F9 17")                      # 13 cmp ecx,0x17 (23)
    jle1 = len(o); o += b"\x7E\x00"                     # 16 jle sidx
    o += bytes.fromhex("BA 01 00 00 00")                # 18 mov edx,1
    o += bytes.fromhex("83 F9 20")                      # 23 cmp ecx,0x20 (32)
    jle2 = len(o); o += b"\x7E\x00"                     # 26 jle sidx
    o += bytes.fromhex("BA 02 00 00 00")                # 28 mov edx,2
    sidx = len(o)                                       # 33
    o += rip_lea(0x0D, SLOTS_VA, STUB_VA + len(o))      # 33 lea rcx,[rip+slots]
    o += bytes.fromhex("48 89 04 D1")                   # 40 mov [rcx+rdx*8],rax
    o += rel_jmp(FB_NEXT, STUB_VA + len(o))             # 44 jmp 0x140F089F9

    o[jle1 + 1] = rel8(sidx, jle1)[0]
    o[jle2 + 1] = rel8(sidx, jle2)[0]
    return bytes(o)


# ---------- P4 helper (from patch_p4_ams2.py) ----------
INSNS = [
    ("start", "56 57 48 83 EC 28"),
    (None, "48 89 4C 24 20"), (None, "48 89 54 24 18"), (None, "48 89 CF"),
    (None, "31 C0"), (None, "B9 FF FF FF FF"), (None, "F2 AE"), (None, "F7 D1"),
    (None, "FF C9"), (None, "89 4C 24 10"), (None, "48 8B 7C 24 18"),
    (None, "B9 FF FF FF FF"), (None, "31 C0"), (None, "F2 AE"), (None, "F7 D1"),
    (None, "FF C9"), (None, "89 4C 24 08"), (None, "48 8B 44 24 20"),
    (None, "8B 4C 24 10"), (None, "83 F9 06"), ("JB_STRIPB", "72 00"),
    (None, "48 8D 54 08 FA"), (None, "81 3A 5F 69 6C 67"), ("JNE_ADARK", "75 00"),
    (None, "81 7A 03 67 68 74 00"), ("JNE_ADARK2", "75 00"), (None, "83 E9 06"),
    (None, "89 4C 24 10"), ("JMP_STRIPB", "EB 00"), ("a_dark", "81 3A 5F 64 61 72"),
    ("JNE_ABFONT", "75 00"), (None, "81 7A 02 61 72 6B 00"), ("JNE_ABFONT2", "75 00"),
    (None, "83 E9 05"), (None, "89 4C 24 10"), ("JMP_STRIPB2", "EB 00"),
    ("a_bfont", "81 3A 2E 62 66 6F"), ("JNE_STRIPB", "75 00"),
    (None, "66 81 7A 04 6E 74"), ("JNE_STRIPB2", "75 00"), (None, "80 7A 06 00"),
    ("JNE_STRIPB3", "75 00"), (None, "83 E9 06"), (None, "89 4C 24 10"),
    ("stripb", "48 8B 44 24 18"), (None, "8B 4C 24 08"), (None, "83 F9 06"),
    ("JB_CMPLEN", "72 00"), (None, "48 8D 54 08 FA"), (None, "81 3A 5F 69 6C 67"),
    ("JNE_BDARK", "75 00"), (None, "81 7A 03 67 68 74 00"), ("JNE_BDARK2", "75 00"),
    (None, "83 E9 06"), (None, "89 4C 24 08"), ("JMP_CMPLEN", "EB 00"),
    ("b_dark", "81 3A 5F 64 61 72"), ("JNE_BBFONT", "75 00"),
    (None, "81 7A 02 61 72 6B 00"), ("JNE_BBFONT2", "75 00"), (None, "83 E9 05"),
    (None, "89 4C 24 08"), ("JMP_CMPLEN2", "EB 00"), ("b_bfont", "81 3A 2E 62 66 6F"),
    ("JNE_CMPLEN", "75 00"), (None, "66 81 7A 04 6E 74"), ("JNE_CMPLEN2", "75 00"),
    (None, "80 7A 06 00"), ("JNE_CMPLEN3", "75 00"), (None, "83 E9 06"),
    (None, "89 4C 24 08"), ("cmplen", "8B 44 24 10"), (None, "3B 44 24 08"),
    ("JNE_FAIL", "75 00"), (None, "48 8B 74 24 20"), (None, "48 8B 7C 24 18"),
    (None, "89 C1"), (None, "F3 A6"), ("JNE_FAIL2", "75 00"), (None, "31 C0"),
    ("RESTORE", "48 83 C4 28 5F 5E C3"), ("fail", "83 C8 FF"),
    ("RESTORE2", "48 83 C4 28 5F 5E C3"),
]
JUMPS = {"JB_STRIPB": "stripb", "JNE_ADARK": "a_dark", "JNE_ADARK2": "a_dark",
         "JMP_STRIPB": "stripb", "JNE_ABFONT": "a_bfont", "JNE_ABFONT2": "a_bfont",
         "JMP_STRIPB2": "stripb", "JNE_STRIPB": "stripb", "JNE_STRIPB2": "stripb",
         "JNE_STRIPB3": "stripb", "JB_CMPLEN": "cmplen", "JNE_BDARK": "b_dark",
         "JNE_BDARK2": "b_dark", "JMP_CMPLEN": "cmplen", "JNE_BBFONT": "b_bfont",
         "JNE_BBFONT2": "b_bfont", "JMP_CMPLEN2": "cmplen", "JNE_CMPLEN": "cmplen",
         "JNE_CMPLEN2": "cmplen", "JNE_CMPLEN3": "cmplen",
         "JNE_FAIL": "fail", "JNE_FAIL2": "fail"}


def assemble_p4():
    labels = {}
    off = 0
    for label, hx in INSNS:
        if label and label.islower() and label != "start":
            labels[label] = off
        off += len(bytes.fromhex(hx))
    out = bytearray()
    off = 0
    for label, hx in INSNS:
        b = bytearray(bytes.fromhex(hx))
        if label in JUMPS:
            rel = labels[JUMPS[label]] - (off + 2)
            assert -128 <= rel <= 127, (label, rel)
            b[1] = rel & 0xFF
        out += b
        off += len(b)
    return bytes(out)


def va2f_text(va):
    return va - 0x140000000 - 0x1000 + 0x600


def main():
    shared = build_shared()
    stub = build_stub()
    p4 = assemble_p4()
    print("shared %d B, stub %d B, p4 %d B" % (len(shared), len(stub), len(p4)))
    assert len(shared) <= 0x80, "shared overlaps stub"
    assert len(stub) <= 0x80, "stub overlaps P4"
    assert 0x100 + len(p4) + 24 <= ZH2_RAWSIZE, "P4 overlaps slots"

    with open(EXE, "rb") as f:
        data = bytearray(f.read())

    # idempotency: abort if .zh2 section already present
    e = struct.unpack_from("<I", data, 0x3C)[0]
    nsec = struct.unpack_from("<H", data, e + 6)[0]
    opt = struct.unpack_from("<H", data, e + 20)[0]
    sec = e + 24 + opt
    for i in range(nsec):
        nm = bytes(data[sec + i * 40:sec + i * 40 + 4])
        if nm == b".zh2":
            print("already patched (.zh2 present), skipping.")
            return

    # backup pristine state (only on first run)
    if not os.path.exists(BAK):
        with open(BAK, "wb") as fh:
            fh.write(bytes(data))
        print("backup:", BAK)
    else:
        print("backup exists, keeping:", BAK)

    # ---- 1. P4 call sites -> helper in .zh2 ----
    for cva, label in ((P4_CALL1_VA, "cache"), (P4_CALL2_VA, "fallback")):
        f = va2f_text(cva)
        data[f:f + 5] = rel_call(P4_VA, cva)
        print("%s strcmp @ %X -> %s" % (label, cva, data[f:f + 5].hex(" ")))

    # ---- 2. hooks ----
    for va, new, label, orig in (
        (GLYPH_FB, rel_jmp(SHARED_VA, GLYPH_FB), "glyph-fb",
         "74 0A 0F B7 D7"),
        (E85C4E, rel_jmp(SHARED_VA, E85C4E), "E85C4E",
         "48 85 C9 74 12"),
        (FB_STORE, rel_jmp(STUB_VA, FB_STORE) + b"\x90\x90", "fb-store",
         "49 89 85 58 03 00 00"),
    ):
        f = va2f_text(va)
        old = bytes(data[f:f + len(new)]).hex(" ")
        if old.replace(" ", "").lower() != orig.replace(" ", "").lower():
            print("ABORT %s @ %X: got %s, expected %s — 游戏版本不匹配，"
                  "请更新补丁地址后重试" % (label, va, old, orig))
            return
        data[f:f + len(new)] = new
        print("%s @ %X: %s -> %s" % (label, va, old, new.hex(" ")))

    # ---- 3. append .zh2 section (shared + stub + P4 + slots) ----
    file_end = len(data)
    ro = (file_end + 0x1FF) & ~0x1FF
    size_of_image = struct.unpack_from("<I", data, e + 24 + 56)[0]
    new_size_of_image = ZH2_RVA + ZH2_RAWSIZE
    new_size_of_image = (new_size_of_image + 0xFFF) & ~0xFFF
    assert new_size_of_image >= size_of_image, (hex(new_size_of_image),
                                                hex(size_of_image))
    # zero-fill gap to RawOff, then section content
    data += b"\x00" * (ro - file_end)
    secdata = bytearray(ZH2_RAWSIZE)
    secdata[0x000:0x000 + len(shared)] = shared
    secdata[0x080:0x080 + len(stub)] = stub
    secdata[0x100:0x100 + len(p4)] = p4
    # slots stay zero
    data += secdata
    # new section header (name .zh2)
    nh = bytearray(40)
    nh[0:4] = b".zh2"
    struct.pack_into("<I", nh, 8, ZH2_RAWSIZE)          # VirtualSize
    struct.pack_into("<I", nh, 12, ZH2_RVA)             # VirtualAddress
    struct.pack_into("<I", nh, 16, ZH2_RAWSIZE)         # SizeOfRawData
    struct.pack_into("<I", nh, 20, ro)                  # PointerToRawData
    struct.pack_into("<I", nh, 36, 0xE0000020)          # code|exec|read|write
    data[sec + nsec * 40:sec + (nsec + 1) * 40] = nh
    struct.pack_into("<H", data, e + 6, nsec + 1)       # section count
    struct.pack_into("<I", data, e + 24 + 56, new_size_of_image)
    print(".zh2 @ RVA %X raw %X size %X; SizeOfImage %X -> %X" % (
        ZH2_RVA, ro, ZH2_RAWSIZE, size_of_image, new_size_of_image))

    with open(EXE, "wb") as fh:
        fh.write(data)
    print("written:", EXE, "new size", hex(len(data)))

    # ---- verify ----
    print("\n--- shared disasm ---")
    try:
        import capstone
        md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
        for i in md.disasm(shared, SHARED_VA):
            print("  %08X: %-26s %s %s" % (i.address, i.bytes.hex(),
                                           i.mnemonic, i.op_str))
        print("--- stub disasm ---")
        for i in md.disasm(stub, STUB_VA):
            print("  %08X: %-26s %s %s" % (i.address, i.bytes.hex(),
                                           i.mnemonic, i.op_str))
    except ImportError:
        print("(capstone unavailable)")


if __name__ == "__main__":
    main()
