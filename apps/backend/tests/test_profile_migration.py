import importlib.util
from pathlib import Path

from sqlalchemy.dialects.postgresql import JSONB


def _migration():
    path = Path(__file__).parents[1] / "alembic/versions/0009_profile_resume_v3.py"
    spec = importlib.util.spec_from_file_location("profile_resume_v3", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_profile_resume_v3_migration_adds_and_removes_jsonb_arrays(monkeypatch):
    migration = _migration()
    added = []
    removed = []
    monkeypatch.setattr(migration.op, "add_column", lambda table, column: added.append((table, column)))
    monkeypatch.setattr(migration.op, "drop_column", lambda table, column: removed.append((table, column)))

    migration.upgrade()
    migration.downgrade()

    assert migration.down_revision == "0008_essay_char_limit"
    assert [(table, column.name) for table, column in added] == [
        ("profile", "skill_groups"),
        ("profile", "open_source_contributions"),
    ]
    assert all(isinstance(column.type, JSONB) for _, column in added)
    assert all(column.nullable is False and str(column.server_default.arg) == "[]" for _, column in added)
    assert removed == [("profile", "open_source_contributions"), ("profile", "skill_groups")]
