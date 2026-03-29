import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

try:
    from dotenv import load_dotenv
    load_dotenv(ROOT_DIR / ".env")
except ImportError:
    pass

from flask_migrate import init as migrate_init
from flask_migrate import migrate as migrate_generate
from flask_migrate import upgrade as migrate_upgrade

from app import create_app, db
import app.models

MIGRATIONS_DIR = ROOT_DIR / "migrations"


def run(message: str, upgrade_only: bool, init_only: bool) -> None:
    flask_app = create_app()

    with flask_app.app_context():
        if not MIGRATIONS_DIR.exists():
            print("[migrate] Initialising migrations directory...")
            migrate_init(directory=str(MIGRATIONS_DIR))
            print("[migrate] Migrations folder created.\n")

        if init_only:
            print("[migrate] --init-only flag set. Stopping after init.")
            return

        if not upgrade_only:
            print("[migrate] Detecting ORM changes and generating migration script...")
            migrate_generate(
                directory=str(MIGRATIONS_DIR),
                message=message,
            )
            print("[migrate] Migration generation complete.\n")

        print("[migrate] Applying pending migrations to the database...")
        migrate_upgrade(directory=str(MIGRATIONS_DIR), revision="head")
        print("[migrate] Database is up to date.")


def main() -> None:
    parser = argparse.ArgumentParser(description="HireSense DB migration helper")
    parser.add_argument(
        "--message", "-m",
        default=f"auto_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
        help="Migration message / label (default: auto_<timestamp>)",
    )
    parser.add_argument(
        "--upgrade-only",
        action="store_true",
        help="Skip migration generation; only apply pending migrations",
    )
    parser.add_argument(
        "--init-only",
        action="store_true",
        help="Only initialise the migrations folder; do not generate or apply",
    )
    args = parser.parse_args()

    try:
        run(
            message=args.message,
            upgrade_only=args.upgrade_only,
            init_only=args.init_only,
        )
    except Exception as exc:
        print(f"\n[migrate] ERROR: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
