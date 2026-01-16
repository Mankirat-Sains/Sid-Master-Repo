import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS_DIR = ROOT / "Local Agent" / "info_retrieval" / "migrations"
RUNNER = MIGRATIONS_DIR / "run.sh"


def _allow_skip() -> bool:
    return os.getenv("ALLOW_SKIP_MIGRATION_TEST", "").lower() == "true"


@pytest.mark.migrations
def test_migrations_idempotent():
    if _allow_skip():
        pytest.skip("ALLOW_SKIP_MIGRATION_TEST=true set; skipping migration idempotency test by explicit override.")

    db_url = os.getenv("SUPABASE_DB_URL")
    if not db_url:
        pytest.fail("SUPABASE_DB_URL not set and ALLOW_SKIP_MIGRATION_TEST not true; migration test must run or be explicitly skipped.")

    env = os.environ.copy()
    env["SUPABASE_DB_URL"] = db_url

    # Run migrations twice; expect no errors
    subprocess.check_call([str(RUNNER)], cwd=str(MIGRATIONS_DIR), env=env)
    subprocess.check_call([str(RUNNER)], cwd=str(MIGRATIONS_DIR), env=env)
