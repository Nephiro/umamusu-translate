import sys
from os.path import realpath
sys.path.append(realpath("src"))
import common
import helpers
import sqlite3
from pathlib import Path
import shutil

def translator(srcdir, files):
    for file in files:
        print(f"Importing {file}...")
        try:
            data = common.TranslationFile(Path(srcdir, file + ".json"))
        except FileNotFoundError:
            raise StopIteration
        for k, v in data.textBlocks.items():
            if not v: continue
            yield {'jpText': k, 'enText': v}

def parseArgs():
    ap = common.Args("Imports translations to master.mdb", False)
    ap.add_argument("-src", default="translations/mdb", help="Import path")
    ap.add_argument("-dst", default=common.GAME_MASTER_FILE, help="Path to master.mdb file")
    ap.add_argument("-B", "--backup", action="store_true", help="Backup the master.mdb file")
    ap.add_argument("-R", "--restore", action="store_true", help="Restore the master.mdb file from backup")
    return ap.parse_args()

def main():
    args = parseArgs()
    if args.backup:
        shutil.copyfile(args.dst, args.dst + ".bak")
        print("master.mdb backed up.")
        return
    elif args.restore:
        try:
            shutil.copyfile(args.dst + ".bak", args.dst)
        except FileNotFoundError:
            print("No backup found.")
        else:
            print("master.mdb restored.")
        return

    try:
        with sqlite3.connect(args.dst, isolation_level=None) as db:
            index = helpers.readJson("src/mdb/index.json")
            db.execute("PRAGMA journal_mode = MEMORY;")
            db.execute("BEGIN;")
            for entry in index:
                stmt = f"UPDATE {entry['table']} SET {entry['field']}=:enText WHERE {entry['field']}=:jpText;"
                inputGen = translator(args.src, entry['files'].keys() if entry.get("specifier") else [entry['file']])
                db.executemany(stmt, inputGen)
            # COMMIT; handled by with:
    finally: db.close()

if __name__ == '__main__':
    main()
