import os

from tests.conftest import requires_db
from warehouse.apply_migrations import apply_migrations


@requires_db
def test_apply_all_versions():
    applied_once = apply_migrations(os.environ["DATABASE_URL"])
    applied_twice = apply_migrations(os.environ["DATABASE_URL"])
    assert applied_twice == []
    import psycopg

    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        versions = [row[0] for row in conn.execute("SELECT version FROM ops.schema_migrations ORDER BY version")]
    for expected in [
        "001_schemas",
        "002_ops",
        "003_bronze",
        "004_silver",
        "005_gold_dims",
        "006_gold_facts",
        "007_gold_marts",
        "008_ui_fields",
    ]:
        assert expected in versions
    assert isinstance(applied_once, list)
