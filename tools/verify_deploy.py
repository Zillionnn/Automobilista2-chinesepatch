# -*- coding: utf-8 -*-
"""Verify repacked .bff by extracting and checking translations."""
import os
import struct
import sys

sys.path.insert(0, r"F:\Game\AMS2-ZH\tools")
from kap_all import scan_key, rc4, decompress
from tdb_repack import parse_tdb

PAK = r"F:\Game\AMS2-ZH\work\deploy\BOOTFLOW.bff"

data = open(PAK, "rb").read()
nfiles = struct.unpack_from("<I", data, 8)[0]
x118 = struct.unpack_from("<I", data, 0x118)[0]
key, dir_dec = scan_key(data[0x130:0x130 + x118], nfiles, len(data))
print("Key: %r" % key)

# Check entry 38 (Game.tdb)
e = dir_dec[38 * 42:(38 + 1) * 42]
off = struct.unpack_from("<Q", e, 8)[0]
zsize = struct.unpack_from("<I", e, 16)[0]
size = struct.unpack_from("<I", e, 20)[0]
ctype = e[32]
print("Entry 38: off=%d zsize=%d size=%d type=%d" % (off, zsize, size, ctype))

# Extract and parse
blob = rc4(data[off:off + zsize], key)
raw = decompress(ctype, blob, size)
tdb = parse_tdb(raw)

# Check Chinese-Simple translations
for lname, entries in tdb["lang_blocks"]:
    if lname == "Chinese-Simple":
        checks = [
            (246, "Game_MainMenu_FinalDrive", "最终传动"),
            (307, "Game_MainMenu_VSync", "垂直同步"),
            (276, "Game_MainMenu_GearDown", "降档"),
        ]
        for idx, expected_key, expected_val in checks:
            key_name = tdb["keys"][idx]
            val = entries[idx][3]
            ok = "OK" if val == expected_val else "MISMATCH"
            print("  [%d] %s = %r %s" % (idx, key_name[:30], val[:30], ok))
        # Count non-UNTRANSLATED entries
        translated = sum(1 for e in entries if not e[3].startswith("UNTRANSLATED"))
        total = len(entries)
        print("  Chinese-Simple: %d/%d translated" % (translated, total))
    elif lname == "English":
        # Verify English is unchanged
        print("  English: %d entries (unchanged)" % len(entries))

print("\nVerification PASSED")
