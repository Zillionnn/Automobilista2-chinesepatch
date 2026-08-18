# -*- coding: utf-8 -*-
"""deploy.py — End-to-end: translate .tdb → repack .bff → deploy to game.

Uses kap_all.py for key scanning and kap_repack.py for repacking.
Entry indices come from extraction filenames (file_XXXX.ext → index XXXX).
"""
import json
import os
import struct
import sys

sys.path.insert(0, r"F:\Game\AMS2-ZH\tools")
from tdb_repack import parse_tdb, build_tdb
from kap_all import scan_key, rc4, BLOBS, derive_key
from kap_repack import parse_pak, build_pak

GAME = r"F:\SteamLibrary\steamapps\common\Automobilista 2"
PAK_DIR = os.path.join(GAME, "Pakfiles")
EXTRACT = r"F:\Game\AMS2-ZH\work\extract"
TRANS_PATH = r"F:\Game\AMS2-ZH\work\translations\translations.json"
OUT_DIR = r"F:\Game\AMS2-ZH\work\translated"
DEPLOY_DIR = r"F:\Game\AMS2-ZH\work\deploy"

# .bff paks containing .tdb files (pak_name → extract_folder)
PAK_TDB_MAP = {
    "BOOTFLOW.bff": "BOOTFLOW",
    "BOOTSPLASH.bff": "BOOTSPLASH",
    "IGPHASEACTIVATE.bff": "IGPHASEACTIVATE",
    "MenuSetup.bff": "MenuSetup",
}


def step1_translate_tdb(translations):
    """Apply translations to all original .tdb files."""
    print("--- Step 1: Translate .tdb files ---")
    os.makedirs(OUT_DIR, exist_ok=True)
    results = {}  # extract_folder -> {entry_index: translated_path}

    if not os.path.isdir(EXTRACT):
        # extract dir missing (cleaned up): reuse previously translated .tdb
        print("  (extract dir missing — reusing translated .tdb from %s)" % OUT_DIR)
        for root, dirs, files in os.walk(OUT_DIR):
            for f in sorted(files):
                if not f.endswith(".tdb") or "_" not in f:
                    continue
                rel = os.path.relpath(os.path.join(root, f), OUT_DIR)
                folder = rel.split(os.sep)[0]
                idx = int(f.split("_")[1].split(".")[0])
                results.setdefault(folder, {})[idx] = os.path.join(root, f)
        print("  entries:", {k: len(v) for k, v in results.items()})
        return results

    for root, dirs, files in os.walk(EXTRACT):
        for f in sorted(files):
            if not f.endswith(".tdb"):
                continue
            if any(x in f for x in ("_test", "_new", "_zh")):
                continue

            tdb_path = os.path.join(root, f)
            rel = os.path.relpath(tdb_path, EXTRACT)
            folder = rel.split(os.sep)[0]

            data = open(tdb_path, "rb").read()
            tdb = parse_tdb(data)
            table_trans = translations.get(tdb["tname"], {})

            if not table_trans:
                continue

            # Count applied translations
            applied = 0
            for lname, entries in tdb["lang_blocks"]:
                if lname == "Chinese-Simple":
                    for i, key in enumerate(tdb["keys"]):
                        if i < len(entries) and key in table_trans and table_trans[key]:
                            applied += 1

            if applied == 0:
                continue

            new_data = build_tdb(tdb, translations)
            out_path = os.path.join(OUT_DIR, rel)
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            with open(out_path, "wb") as fout:
                fout.write(new_data)

            # Extract entry index from filename (file_XXXX.tdb → XXXX)
            idx = int(f.split("_")[1].split(".")[0])
            if folder not in results:
                results[folder] = {}
            results[folder][idx] = out_path

            print("  %s/%s: table=%s applied=%d (%d→%d bytes)" % (
                folder, f, tdb["tname"], applied, len(data), len(new_data)))

    return results


def step2_repack_paks(translated_entries):
    """Repack .bff paks with translated .tdb files."""
    print("\n--- Step 2: Repack .bff paks ---")
    os.makedirs(DEPLOY_DIR, exist_ok=True)

    for pak_name, extract_folder in PAK_TDB_MAP.items():
        if extract_folder not in translated_entries:
            print("  %s: no translated files" % pak_name)
            continue

        pak_path = os.path.join(PAK_DIR, pak_name)
        if not os.path.exists(pak_path):
            print("  %s: pak not found" % pak_name)
            continue

        # Scan for key
        data = open(pak_path, "rb").read()
        nfiles = struct.unpack_from("<I", data, 8)[0]
        x118 = struct.unpack_from("<I", data, 0x118)[0]
        key, dir_dec = scan_key(data[0x130:0x130 + x118], nfiles, len(data))

        if key is None:
            print("  %s: KEY NOT FOUND" % pak_name)
            continue

        # Build replacement map
        entries_map = translated_entries[extract_folder]
        repl = {}
        for idx, trans_path in entries_map.items():
            repl[str(idx)] = trans_path

        print("  %s: key=%r, %d entries to replace" % (pak_name, key, len(repl)))

        # Set key for kap_repack
        import kap_repack
        kap_repack.KEY = key

        # Repack
        out_pak = os.path.join(DEPLOY_DIR, pak_name)
        new_data = build_pak(data, repl)
        with open(out_pak, "wb") as fout:
            fout.write(new_data)
        print("    → %s (%d → %d bytes)" % (out_pak, len(data), len(new_data)))

    return True


def step3_deploy():
    """Copy repacked .bff files to game directory with backup."""
    print("\n--- Step 3: Deploy to game ---")
    backup_dir = os.path.join(DEPLOY_DIR, "backup")
    os.makedirs(backup_dir, exist_ok=True)

    for pak_name in PAK_TDB_MAP:
        src = os.path.join(DEPLOY_DIR, pak_name)
        dst = os.path.join(PAK_DIR, pak_name)
        bak = os.path.join(backup_dir, pak_name + ".bak")

        if not os.path.exists(src):
            print("  %s: no repacked file" % pak_name)
            continue

        # Backup original
        if not os.path.exists(bak):
            import shutil
            shutil.copy2(dst, bak)
            print("  %s: backed up to %s" % (pak_name, bak))

        # Copy repacked to game
        import shutil
        shutil.copy2(src, dst)
        print("  %s: deployed" % pak_name)

    print("\n=== Deployment complete ===")
    print("Backup: %s" % backup_dir)
    print("Launch with: -novr -lang Chinese-Simple")


def main():
    print("=== AMS2 Chinese Localization Pipeline ===\n")

    translations = json.load(open(TRANS_PATH, encoding="utf-8"))
    total_trans = sum(len(v) for v in translations.values())
    print("Loaded %d translations across %d tables\n" % (total_trans, len(translations)))

    # Step 1: Translate .tdb files
    translated_entries = step1_translate_tdb(translations)

    # Step 2: Repack .bff paks
    step2_repack_paks(translated_entries)

    # Step 3: Deploy (only with --deploy flag)
    if "--deploy" in sys.argv:
        step3_deploy()
    else:
        print("\n--- Step 3: Deploy (skipped, use --deploy to deploy) ---")
        print("Repacked .bff files ready in: %s" % DEPLOY_DIR)
        print("To deploy: python deploy.py --deploy")


if __name__ == "__main__":
    main()
