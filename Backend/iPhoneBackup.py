import os
import shutil
import sqlite3
import subprocess
import shlex
import platform
from pathlib import Path
from typing import Optional
import sys
import tempfile

# ============================================================
# Configuration
# ============================================================

IMESSAGE_DB_REL_PATH = "Library/SMS/sms.db"
CONTACTS_DB_REL_PATH = "Library/AddressBook/AddressBook.sqlitedb"


# ============================================================
# Dependency bootstrap
# ============================================================

def ensure_idevicebackup2_installed():
    """
    Ensures idevicebackup2 is installed on macOS.
    Handles Apple Silicon vs Intel Homebrew paths.
    """

    if shutil.which("idevicebackup2"):
        print("idevicebackup2 already installed.")
        return

    if sys.platform != "darwin":
        raise RuntimeError("iPhone backups are only supported on macOS.")

    arch = platform.machine()
    print(f"Detected architecture: {arch}")

    if arch == "arm64":
        brew_bin = "/opt/homebrew/bin/brew"
        brew_prefix = "/opt/homebrew"
    else:
        brew_bin = "/usr/local/bin/brew"
        brew_prefix = "/usr/local"

    # Install Homebrew if missing
    if not os.path.exists(brew_bin):
        print("Homebrew not found. Installing Homebrew...")

        subprocess.run(
            [
                "/bin/bash",
                "-c",
                "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            ],
            check=True
        )

        print("Homebrew installation complete.")

    if not os.path.exists(brew_bin):
        raise RuntimeError(
            f"Homebrew expected at {brew_bin} but not found. "
            "Restart your session and try again."
        )

    # Install libimobiledevice
    print("Installing libimobiledevice...")
    subprocess.run(
        [brew_bin, "install", "libimobiledevice"],
        check=True
    )

    if not shutil.which("idevicebackup2"):
        raise RuntimeError(
            "libimobiledevice installed but idevicebackup2 not found in PATH.\n"
            f"Expected prefix: {brew_prefix}"
        )

    print("idevicebackup2 successfully installed.")


# ============================================================
# Backup
# ============================================================

def backup_iphone(backup_dir: Path, password: Optional[str] = None, verbose: bool = False, log_only: bool = False):
    """
    Creates a local iPhone backup using idevicebackup2.
    """
    backup_dir.mkdir(parents=True, exist_ok=True)

    # prepare command with verbose output
    base = ["idevicebackup2"]
    if password:
        base += ["--password", password]
    # request debug output to aid troubleshooting (use -d for libimobiledevice)
    base += ["backup", str(backup_dir)]

    log_path = backup_dir / "idevicebackup2.log"
    print(f"Starting iPhone backup (logging to {log_path})...")
    # Run idevicebackup2 directly and let its standard output/stderr flow to the console
    # while also saving a copy to the log file using `tee` so we avoid parsing output here.
    args = ["idevicebackup2"]
    if password:
        args += ["--password", password]
    args += ["backup", str(backup_dir)]

    # Build a safely-quoted shell command and use `tee` to write to the log while showing stdout.
    cmd = " ".join(shlex.quote(a) for a in args) + " 2>&1 | tee " + shlex.quote(str(log_path))

    ret = subprocess.run(cmd, shell=True, executable="/bin/bash")
    if ret.returncode != 0:
        raise subprocess.CalledProcessError(ret.returncode, cmd)

    print(f"Backup complete. Log written to {log_path}")


# ============================================================
# Manifest helpers
# ============================================================

def get_manifest_db(backup_dir: Path) -> Path:
    """
    Locate the Manifest.db for a backup.

    If `Manifest.db` exists at `backup_dir`, return it. Otherwise search
    subdirectories and return the first match. Raises FileNotFoundError if
    not found.
    """
    manifest = backup_dir / "Manifest.db"
    def _is_sqlite(path: Path) -> bool:
        try:
            with open(path, "rb") as fh:
                header = fh.read(16)
                return header.startswith(b"SQLite format 3")
        except Exception:
            return False

    if manifest.exists() and _is_sqlite(manifest):
        return manifest

    # Search recursively for Manifest.db and return the first found match.
    for root, dirs, files in os.walk(str(backup_dir)):
        if "Manifest.db" in files:
            candidate = Path(root) / "Manifest.db"
            if _is_sqlite(candidate):
                print(f"Located Manifest.db at {candidate}", flush=True)
                return candidate
            else:
                # skip non-sqlite candidate (some backups may include other files named Manifest.db)
                print(f"Found Manifest.db at {candidate} but it is not a SQLite DB — skipping", flush=True)

    raise FileNotFoundError(f"Manifest.db not found in {backup_dir} or its subdirectories.")


def extract_file_from_backup(
    backup_dir: Path,
    relative_path: str,
    output_path: Path,
    password: Optional[str] = None
):
    """
    Extracts a file from an iOS backup using Manifest.db.
    """
    validate_backup_directory(backup_dir)  # Ensure backup directory is valid

    # Verbose progress reporting for extraction
    print(f"Starting extraction of '{relative_path}' from backup at {backup_dir}", flush=True)
    try:
        manifest_db = get_manifest_db(backup_dir)
        manifest_dir = manifest_db.parent
        print(f"Using Manifest.db at {manifest_db}")
    except FileNotFoundError:
        print("Manifest.db not found or not a valid SQLite DB. Attempting prioritized search for the requested file...", flush=True)

        # Prioritized search: try common paths and shallow scans before full walk
        target_name = os.path.basename(relative_path)

        def _try_common_paths() -> Optional[Path]:
            # When requested file is chat.db, also consider common sms.db locations
            alt_names = [target_name]
            if target_name != "sms.db":
                alt_names.insert(0, "sms.db")

            common_bases = [
                Path(relative_path).parent,
                Path("Library/SMS"),
                Path("var/mobile/Library/SMS"),
                Path("Library"),
                Path("HomeDomain/Library/SMS"),
                Path("AppDomain-com.apple.MobileSMS"),
                Path("Library/AddressBook"),
                Path("Snapshot"),
            ]

            for base in common_bases:
                for name in alt_names:
                    c = base / name
                    p = backup_dir / c
                    print(f"Checking common path: {p}", flush=True)
                    if p.exists():
                        return p
            return None

        def _shallow_scan(max_depth: int = 8) -> Optional[Path]:
            base = str(backup_dir)
            # Also accept sms.db as a valid candidate when searching for chat.db
            alt_names = [target_name]
            if target_name != "sms.db":
                alt_names.insert(0, "sms.db")

            for root, dirs, files in os.walk(base):
                rel = os.path.relpath(root, base)
                depth = 0 if rel == "." else rel.count(os.sep) + 1
                if depth > max_depth:
                    # prune deeper directories to keep shallow scan fast
                    dirs[:] = []
                    continue
                print(f"Shallow scanning {root} for {target_name}...", flush=True)
                for name in alt_names:
                    if name in files:
                        return Path(root) / name
                for f in files:
                    for name in alt_names:
                        if f.endswith(name):
                            return Path(root) / f
            return None

        # 1) Try common well-known locations
        found = _try_common_paths()
        if found:
            print(f"Found candidate at common path {found} — copying to {output_path}", flush=True)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(found, output_path)
            print(f"Copied {found} -> {output_path}", flush=True)
            return

        # 2) Do a shallow prioritized scan (fast)
        found = _shallow_scan(max_depth=2)
        if found:
            print(f"Found candidate via shallow scan: {found} — copying to {output_path}", flush=True)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(found, output_path)
            print(f"Copied {found} -> {output_path}", flush=True)
            return

        # 3) Fall back to full recursive scan with verbose updates
        for root, dirs, files in os.walk(str(backup_dir)):
            # Frequent progress updates while scanning
            print(f"Scanning {root} for {target_name}...", flush=True)
            if target_name in files:
                candidate = Path(root) / target_name
                print(f"Found candidate file at {candidate} — copying to {output_path}", flush=True)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(candidate, output_path)
                print(f"Copied {candidate} -> {output_path}", flush=True)
                return
            # Also check for files whose filename ends with the requested name
            for f in files:
                if f.endswith(target_name):
                    candidate = Path(root) / f
                    print(f"Found potential match {candidate} (endswith {target_name}) — copying to {output_path}", flush=True)
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(candidate, output_path)
                    print(f"Copied {candidate} -> {output_path}", flush=True)
                    return

        # If direct file scan didn't find anything, attempt decryption/unpack if a password was provided
        if password:
            print("Attempting to decrypt/unpack with provided password to locate files...")
            with tempfile.TemporaryDirectory() as tmpdir:
                decrypted_dir = Path(tmpdir) / "decrypted_backup"
                decrypted_dir.mkdir(parents=True, exist_ok=True)
                cmd = ["idevicebackup2", "decrypt", str(backup_dir), str(decrypted_dir), "--password", password]
                try:
                    proc = subprocess.run(cmd, check=False, capture_output=True, text=True)
                except FileNotFoundError:
                    raise FileNotFoundError(
                        "idevicebackup2 not found in PATH. Install libimobiledevice and ensure idevicebackup2 is available."
                    )

                if proc.returncode != 0:
                    stderr = proc.stderr or proc.stdout or ""
                    if "Unsupported command 'decrypt'" in stderr or "Unsupported command decrypt" in stderr:
                        print("'decrypt' unsupported — attempting 'unback' fallback using BACKUP_PASSWORD env var (may unpack into the original backup directory)")
                        env = os.environ.copy()
                        env['BACKUP_PASSWORD'] = password
                        try:
                            unback_proc = subprocess.run(["idevicebackup2", "unback", str(backup_dir)], check=False, capture_output=True, text=True, env=env)
                        except FileNotFoundError:
                            raise FileNotFoundError(
                                "idevicebackup2 not found in PATH. Install libimobiledevice and ensure idevicebackup2 is available."
                            )

                        if unback_proc.returncode != 0:
                            raise FileNotFoundError(
                                f"Failed to unpack encrypted backup using idevicebackup2 unback: {unback_proc.stderr or unback_proc.stdout}\n"
                                "Ensure the password is correct and idevicebackup2 supports this backup format."
                            )

                        decrypted_candidate = Path(backup_dir) / "_unback_"
                        if decrypted_candidate.exists():
                            try:
                                manifest_db = get_manifest_db(decrypted_candidate)
                                manifest_dir = manifest_db.parent
                                print(f"Located Manifest.db after unpack at {manifest_db}")
                            except FileNotFoundError as e:
                                raise FileNotFoundError(f"Unpacked backup found but no valid Manifest.db inside: {e}")
                        else:
                            raise FileNotFoundError("idevicebackup2 unback succeeded but _unback_ directory not found in backup directory")
                    else:
                        raise FileNotFoundError(
                            f"Failed to decrypt backup using idevicebackup2: {stderr}\n"
                            "Ensure the password is correct and idevicebackup2 supports decrypting this backup."
                        )
                # proceed with decrypted_dir
                try:
                    manifest_db = get_manifest_db(decrypted_dir)
                    manifest_dir = manifest_db.parent
                    print(f"Using Manifest.db at {manifest_db} after decryption")
                except FileNotFoundError:
                    raise FileNotFoundError(
                        f"Manifest.db for backup at {backup_dir} could not be located as a valid SQLite database even after decryption."
                    )
        else:
            raise FileNotFoundError(
                f"Manifest.db for backup at {backup_dir} could not be located as a valid SQLite database.\n"
                "If this backup is encrypted, provide --password to attempt decryption or decrypt it manually first.\n"
            )

    try:
        conn = sqlite3.connect(manifest_db)
        cur = conn.cursor()
    except sqlite3.DatabaseError as e:
        # Provide clearer diagnostics when Manifest.db isn't a valid SQLite DB
        raise FileNotFoundError(
            f"Manifest.db at {manifest_db} is not a valid SQLite database: {e}.\n"
            "This can happen if the backup is encrypted, corrupted, or the wrong file was located.\n"
            "Verify the backup using `sqlite3` or re-create the backup with idevicebackup2 (unencrypted)."
        )

    cur.execute(
        """
        SELECT fileID
        FROM Files
        WHERE relativePath = ?
        """,
        (relative_path,)
    )

    row = cur.fetchone()
    if not row:
        # try a fallback by searching for files whose path ends with the filename
        suffix = os.path.basename(relative_path)
        cur.execute(
            "SELECT fileID, relativePath FROM Files WHERE relativePath LIKE ? ORDER BY LENGTH(relativePath) LIMIT 1",
            (f"%{suffix}",),
        )
        alt = cur.fetchone()
        conn.close()
        if not alt:
            raise FileNotFoundError(f"{relative_path} not found in backup.")
        file_id = alt[0]
        found_relative = alt[1]
        print(f"Using fallback relativePath from manifest: {found_relative}")
    else:
        conn.close()
        file_id = row[0]
    file_subdir = file_id[:2]
    source_file = manifest_dir / file_subdir / file_id

    if not source_file.exists():
        raise FileNotFoundError(f"Backup file missing: {source_file}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_file, output_path)

    print(f"Extracted {relative_path} → {output_path}")


# ============================================================
# Public extraction APIs
# ============================================================

def extract_imessage_db(backup_dir: Path, output_dir: Path, password: Optional[str] = None) -> Path:
    # Always output as chat.db for compatibility with downstream tools
    output_path = output_dir / "chat.db"
    candidates = [
        IMESSAGE_DB_REL_PATH,
        "sms.db",
        "chat.db",
        "ChatStorage.sqlite",
        "ExtChatDatabase.sqlite",
        "ExtChatDB",
    ]

    last_err = None
    for cand in candidates:
        try:
            # If cand looks like a path (contains '/'), use it directly; otherwise search manifest suffix
            if "/" in cand:
                extract_file_from_backup(backup_dir, cand, output_path, password=password)
            else:
                alt = find_relative_path_by_suffix(backup_dir, cand)
                if not alt:
                    print(f"No manifest entry for '{cand}'. Attempting filesystem fallback search...", flush=True)
                    # attempt a direct filesystem search for common locations (use shallow scan)
                    fs_found = None
                    def _fs_shallow_search(max_depth: int = 8):
                        base = str(backup_dir)
                        for root, dirs, files in os.walk(base):
                            rel = os.path.relpath(root, base)
                            depth = 0 if rel == "." else rel.count(os.sep) + 1
                            if depth > max_depth:
                                dirs[:] = []
                                continue
                            if cand in files:
                                return Path(root) / cand
                            for f in files:
                                if f.endswith(cand):
                                    return Path(root) / f
                        return None

                    fs_found = _fs_shallow_search(max_depth=4)
                    if fs_found:
                        print(f"Found '{cand}' at {fs_found} — copying to {output_path}", flush=True)
                        output_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(fs_found, output_path)
                        print(f"Copied {fs_found} -> {output_path}", flush=True)
                        return output_path
                    # fallback to manifest-based extraction if found later
                else:
                    extract_file_from_backup(backup_dir, alt, output_path, password=password)
            return output_path
        except FileNotFoundError as e:
            last_err = e
            continue

    # If we get here nothing matched
    raise last_err or FileNotFoundError("iMessage DB not found in backup")


def extract_contacts_db(backup_dir: Path, output_dir: Path, password: Optional[str] = None) -> Path:
    output_path = output_dir / "contacts.db"
    try:
        extract_file_from_backup(
            backup_dir,
            CONTACTS_DB_REL_PATH,
            output_path,
            password=password,
        )
        return output_path
    except FileNotFoundError:
        alt = find_relative_path_by_suffix(backup_dir, "AddressBook.sqlitedb")
        if alt:
            extract_file_from_backup(backup_dir, alt, output_path, password=password)
            return output_path
        raise


def find_relative_path_by_suffix(backup_dir: Path, suffix: str) -> Optional[str]:
    """Search the backup's Manifest.db for a file whose relativePath ends with `suffix`.

    Returns the matching relativePath or None if not found.
    """
    try:
        manifest_db = get_manifest_db(backup_dir)
    except FileNotFoundError:
        return None

    conn = sqlite3.connect(manifest_db)
    cur = conn.cursor()
    cur.execute(
        "SELECT relativePath FROM Files WHERE relativePath LIKE ? LIMIT 1",
        (f"%{suffix}",),
    )
    row = cur.fetchone()
    conn.close()

    if row:
        return row[0]
    return None


# ============================================================
# Cleanup
# ============================================================

def validate_backup_directory(backup_dir: Path):
    """
    Ensure the backup directory exists and is accessible.
    """
    if not backup_dir.exists():
        raise FileNotFoundError(f"Backup directory not found: {backup_dir}")
    if not backup_dir.is_dir():
        raise NotADirectoryError(f"Backup path is not a directory: {backup_dir}")

# ============================================================
# Cleanup
# ============================================================

def delete_backup(backup_dir: Path):
    if backup_dir.exists():
        shutil.rmtree(backup_dir)
        print(f"Deleted backup at {backup_dir}")


# ============================================================
# Orchestration
# ============================================================

def run_full_pipeline(
    backup_dir: Path,
    output_dir: Path,
    password: Optional[str] = None,
    cleanup: bool = True,
    verbose: bool = False,
    log_only: bool = False,
):
    """
    Run the full pipeline: create a backup using `idevicebackup2`, then extract
    the iMessage and Contacts databases into `output_dir`.
    """
    ensure_idevicebackup2_installed()

    success = False
    try:
        # report target disk usage before starting so user can detect low space
        try:
            parent = backup_dir if backup_dir.exists() else backup_dir.parent
            usage = shutil.disk_usage(str(parent))
            free_gb = usage.free / (1024 ** 3)
            total_gb = usage.total / (1024 ** 3)
            print(f"Target filesystem: {parent} — free: {free_gb:.2f} GB / total: {total_gb:.2f} GB")
        except Exception as e:
            print(f"Warning: unable to determine disk usage for {backup_dir}: {e}")

        backup_iphone(backup_dir, password=password, verbose=verbose, log_only=log_only)

        output_dir.mkdir(parents=True, exist_ok=True)

        imessage_db = extract_imessage_db(backup_dir, output_dir, password=password)
        contacts_db = extract_contacts_db(backup_dir, output_dir, password=password)

        print("\nExtraction complete:")
        print(f"  iMessage DB:  {imessage_db}")
        print(f"  Contacts DB:  {contacts_db}")

        success = True

    finally:
        if cleanup and success:
            delete_backup(backup_dir)
        elif not success:
            print(f"Backup failed — leaving partial backup at {backup_dir} for inspection. Re-run with --no-cleanup to preserve or remove manually when ready.")


# ============================================================
# CLI Entrypoint
# ============================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Local iPhone backup + iMessage/Contacts extractor (macOS)"
    )

    subparsers = parser.add_subparsers(dest="cmd", required=True)

    # backup command
    p_backup = subparsers.add_parser("backup", help="Create a local iPhone backup using idevicebackup2")
    p_backup.add_argument("--backup-dir", required=True, help="Target directory to write the backup to")
    p_backup.add_argument("--password", help="Encrypted backup password")
    p_backup.add_argument("--verbose", action="store_true", help="Print verbose output to console (also saved to log). If omitted, only progress/errors are printed; full debug still saved to log")
    p_backup.add_argument("--no-cleanup", action="store_true", help="Do not delete the backup after running (not used for standalone backup)")
    p_backup.add_argument("--log-only", action="store_true", help="Do not print any idevicebackup2 output to the console; save full debug to the logfile only")

    # extract command
    p_extract = subparsers.add_parser("extract", help="Extract databases from an existing backup")
    p_extract.add_argument("--backup-dir", required=True, help="Path to the existing backup directory")
    p_extract.add_argument("--output-dir", required=True, help="Directory to write extracted databases into")
    p_extract.add_argument("--imessage", action="store_true", help="Extract only the iMessage database")
    p_extract.add_argument("--contacts", action="store_true", help="Extract only the Contacts database")
    p_extract.add_argument("--password", help="Password for encrypted backup (if applicable)")

    # delete command
    p_delete = subparsers.add_parser("delete", help="Delete a local backup directory")
    p_delete.add_argument("--backup-dir", required=True, help="Backup directory to remove")

    # full pipeline
    p_full = subparsers.add_parser("full", help="Run full pipeline: backup, extract, (optional) delete")
    p_full.add_argument("--backup-dir", required=True, help="Target directory to write the backup to")
    p_full.add_argument("--output-dir", required=True, help="Directory to write extracted databases into")
    p_full.add_argument("--password", help="Encrypted backup password")
    p_full.add_argument("--no-cleanup", action="store_true", help="Do not delete the backup after successful run")
    p_full.add_argument("--verbose", action="store_true", help="Show verbose idevicebackup2 output in console and save full debug to logfile")
    p_full.add_argument("--log-only", action="store_true", help="Do not print any idevicebackup2 output to the console; save full debug to the logfile only")

    args = parser.parse_args()

    if args.cmd == "backup":
        # Ensure idevicebackup2 is available before attempting a backup
        ensure_idevicebackup2_installed()
        backup_iphone(Path(args.backup_dir), password=args.password, verbose=bool(args.verbose), log_only=bool(getattr(args, 'log_only', False)))
        print(f"Backup written to {args.backup_dir}")

    elif args.cmd == "extract":
        backup_dir = Path(args.backup_dir)
        output_dir = Path(args.output_dir)

        # If neither flag specified, extract both
        if not args.imessage and not args.contacts:
            do_imessage = do_contacts = True
        else:
            do_imessage = bool(args.imessage)
            do_contacts = bool(args.contacts)

        if do_imessage:
            try:
                imessage_db = extract_imessage_db(backup_dir, output_dir, password=getattr(args, 'password', None))
                print(f"Extracted iMessage DB to: {imessage_db}")
            except FileNotFoundError as e:
                print(f"iMessage DB not found: {e}")

        if do_contacts:
            try:
                contacts_db = extract_contacts_db(backup_dir, output_dir, password=getattr(args, 'password', None))
                print(f"Extracted Contacts DB to: {contacts_db}")
            except FileNotFoundError as e:
                print(f"Contacts DB not found: {e}")

    elif args.cmd == "delete":
        delete_backup(Path(args.backup_dir))

    elif args.cmd == "full":
        run_full_pipeline(
            backup_dir=Path(args.backup_dir),
            output_dir=Path(args.output_dir),
            password=args.password,
            cleanup=not args.no_cleanup,
            verbose=bool(args.verbose),
            log_only=bool(getattr(args, 'log_only', False)),
        )

    else:
        parser.print_help()
