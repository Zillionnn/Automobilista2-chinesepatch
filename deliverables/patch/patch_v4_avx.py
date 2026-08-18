# -*- coding: utf-8 -*-
"""V4 static patch for AMS2AVX.exe (AVX build) — mirrors patch_v4.py.

The user's Steam launch actually runs AMS2AVX.exe (AMS2.exe is a
bootstrapper that re-launches AMS2AVX.exe on AVX-capable CPUs). This
applies the same CJK-fallback patch to the AVX build.

AVX addresses (pattern-verified against AMS2):
  GetGlyph            0x140E7D830
  glyph-fb hook       0x140E7D8B1   (74 0A 0F B7 D7)
  GetGlyph epilogue   0x140E7D8BF
  GetGlyph ret0       0x140E7D8BD
  E85C10 (measure)    0x140E7DD00
  E85C10 fb hook      0x140E7DD3E   (48 85 C9 74 12)
  E85C10 recurse      0x140E7DD43
  E85C10 ret0         0x140E7DD55
  fb-store            0x140EFB1D2   (49 89 85 58 03 00 00)
  fb-store next       0x140EFB1D9
  P4 cache strcmp     0x140EFA1F1
  P4 slot strcmp      0x140EFB0DF

New .zh2 section @ RVA 0x2ED7000 (right after .bind end), 0x800 bytes:
  +0x000 shared routine (87 B)
  +0x080 stub (49 B)
  +0x100 P4 variant-tolerant strcmp helper (303 B)
  +0x200 slots[3] (24 B)

Run with the game CLOSED.
"""
import os
import struct

EXE = r"F:\SteamLibrary\steamapps\common\Automobilista 2\AMS2AVX.exe"
BAK = EXE + ".bak-v4-orig"

ZH2_RVA = 0x2ED7000
ZH2_VA = 0x140000000 + ZH2_RVA
ZH2_RAWSIZE = 0x800
SHARED_VA = ZH2_VA + 0x000
STUB_VA = ZH2_VA + 0x080
P4_VA = ZH2_VA + 0x100
SLOTS_VA = ZH2_VA + 0x300

GLYPH_FB = 0x140E7D8B1
E85C4E = 0x140E7DD3E
FB_STORE = 0x140EFB1D2
FB_NEXT = 0x140EFB1D9
GETGLYPH = 0x140E7D830
GLYPH_TAIL = 0x140E7D8BF
GLYPH_RET0 = 0x140E7D8BD
E85C10_RECURSE = 0x140E7DD43
E85C10_RET0 = 0x140E7DD55
P4_CALL1_VA = 0x140EFA1F1
P4_CALL2_VA = 0x140EFB0DF


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
    disp = dst_va - (from_va + 7)
    assert -0x80000000 <= disp <= 0x7FFFFFFF, hex(disp)
    return bytes([0x48, 0x8D, reg]) + struct.pack("<i", disp)


def build_shared():
    o = bytearray()
    o += bytes.fromhex("48 85 C9")
    jnz = len(o); o += b"\x75\x00"
    o += bytes.fromhex("8B 43 44")
    o += bytes.fromhex("31 D2")
    o += bytes.fromhex("83 F8 17")          # size<=0x17(23) -> s12
    jle1 = len(o); o += b"\x7E\x00"
    o += bytes.fromhex("BA 01 00 00 00")
    o += bytes.fromhex("83 F8 20")          # size<=0x20(32) -> s17
    jle2 = len(o); o += b"\x7E\x00"
    o += bytes.fromhex("BA 02 00 00 00")
    gotidx = len(o)
    o += rip_lea(0x05, SLOTS_VA, ZH2_VA + len(o))
    o += bytes.fromhex("48 8B 0C D0")       # rcx = slots[tier]
    o += bytes.fromhex("48 85 C9")
    jnz2 = len(o); o += b"\x75\x00"         # jnz done
    o += bytes.fromhex("48 8B 48 08")       # fallback slots[1]
    o += bytes.fromhex("48 85 C9")
    jnz3 = len(o); o += b"\x75\x00"
    o += bytes.fromhex("48 8B 48 10")       # fallback slots[2]
    done = len(o)
    o += bytes.fromhex("48 39 D9")
    je1 = len(o); o += b"\x74\x00"
    o += bytes.fromhex("48 85 C9")
    jz1 = len(o); o += b"\x74\x00"
    o += bytes.fromhex("85 FF")
    js1 = len(o); o += b"\x78\x00"
    o += bytes.fromhex("0F B7 D7")
    o += rel_call(GETGLYPH, ZH2_VA + len(o))
    o += rel_jmp(GLYPH_TAIL, ZH2_VA + len(o))
    doM = len(o)
    o += rel_jmp(E85C10_RECURSE, ZH2_VA + len(o))
    ret0 = len(o)
    o += bytes.fromhex("85 FF")
    js2 = len(o); o += b"\x78\x00"
    o += rel_jmp(GLYPH_RET0, ZH2_VA + len(o))
    ret0M = len(o)
    o += rel_jmp(E85C10_RET0, ZH2_VA + len(o))

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


def build_stub():
    o = bytearray()
    o += bytes.fromhex("49 89 85 58 03 00 00")
    o += bytes.fromhex("41 8B 4D 44")
    o += bytes.fromhex("31 D2")
    o += bytes.fromhex("83 F9 17")          # size<=0x17(23) -> s12
    jle1 = len(o); o += b"\x7E\x00"
    o += bytes.fromhex("BA 01 00 00 00")
    o += bytes.fromhex("83 F9 20")          # size<=0x20(32) -> s17
    jle2 = len(o); o += b"\x7E\x00"
    o += bytes.fromhex("BA 02 00 00 00")
    sidx = len(o)
    o += rip_lea(0x0D, SLOTS_VA, STUB_VA + len(o))
    o += bytes.fromhex("48 89 04 D1")
    o += rel_jmp(FB_NEXT, STUB_VA + len(o))
    o[jle1 + 1] = rel8(sidx, jle1)[0]
    o[jle2 + 1] = rel8(sidx, jle2)[0]
    return bytes(o)


# P4 helper (identical to patch_v4.py / patch_p4_ams2.py)
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
    assert len(shared) <= 0x80 and len(stub) <= 0x80
    assert 0x100 + len(p4) + 24 <= ZH2_RAWSIZE

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

    # 1. P4 call sites -> helper in .zh2
    for cva, label in ((P4_CALL1_VA, "cache"), (P4_CALL2_VA, "slot")):
        f = va2f_text(cva)
        data[f:f + 5] = rel_call(P4_VA, cva)
        print("p4-%s @ %X -> %s" % (label, cva, data[f:f + 5].hex(" ")))

    # 2. hooks
    for va, new, label, orig in (
        (GLYPH_FB, rel_jmp(SHARED_VA, GLYPH_FB), "glyph-fb", "74 0A 0F B7 D7"),
        (E85C4E, rel_jmp(SHARED_VA, E85C4E), "E85C4E", "48 85 C9 74 12"),
        (FB_STORE, rel_jmp(STUB_VA, FB_STORE) + b"\x90\x90", "fb-store",
         "49 89 85 58 03 00 00"),
    ):
        f = va2f_text(va)
        old = bytes(data[f:f + len(new)]).hex(" ")
        if old != orig.replace(" ", ""):
            print("ABORT %s @ %X: got %s, expected %s — 游戏版本不匹配，"
                  "请更新补丁地址后重试" % (label, va, old, orig))
            return
        data[f:f + len(new)] = new
        print("%s @ %X: %s -> %s" % (label, va, old, new.hex(" ")))

    # 3. append .zh2
    file_end = len(data)
    ro = (file_end + 0x1FF) & ~0x1FF
    size_of_image = struct.unpack_from("<I", data, e + 24 + 56)[0]
    new_size_of_image = (ZH2_RVA + ZH2_RAWSIZE + 0xFFF) & ~0xFFF
    assert new_size_of_image >= size_of_image
    data += b"\x00" * (ro - file_end)
    secdata = bytearray(ZH2_RAWSIZE)
    secdata[0x000:0x000 + len(shared)] = shared
    secdata[0x080:0x080 + len(stub)] = stub
    secdata[0x100:0x100 + len(p4)] = p4
    data += secdata
    nh = bytearray(40)
    nh[0:4] = b".zh2"
    struct.pack_into("<I", nh, 8, ZH2_RAWSIZE)
    struct.pack_into("<I", nh, 12, ZH2_RVA)
    struct.pack_into("<I", nh, 16, ZH2_RAWSIZE)
    struct.pack_into("<I", nh, 20, ro)
    struct.pack_into("<I", nh, 36, 0xE0000020)
    data[sec + nsec * 40:sec + (nsec + 1) * 40] = nh
    struct.pack_into("<H", data, e + 6, nsec + 1)
    struct.pack_into("<I", data, e + 24 + 56, new_size_of_image)
    print(".zh2 @ RVA %X raw %X size %X; SizeOfImage %X -> %X" % (
        ZH2_RVA, ro, ZH2_RAWSIZE, size_of_image, new_size_of_image))

    with open(EXE, "wb") as fh:
        fh.write(data)
    print("written:", EXE, hex(len(data)))

    try:
        import capstone
        md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
        print("--- shared ---")
        for i in md.disasm(shared, SHARED_VA):
            print("  %08X: %-26s %s %s" % (i.address, i.bytes.hex(),
                                           i.mnemonic, i.op_str))
        print("--- stub ---")
        for i in md.disasm(stub, STUB_VA):
            print("  %08X: %-26s %s %s" % (i.address, i.bytes.hex(),
                                           i.mnemonic, i.op_str))
    except ImportError:
        pass


if __name__ == "__main__":
    main()
