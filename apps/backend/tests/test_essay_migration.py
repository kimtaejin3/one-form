import importlib.util
from pathlib import Path


def _migration():
    path = Path(__file__).parents[1] / "alembic/versions/0008_essay_optional_char_limit.py"
    spec = importlib.util.spec_from_file_location("essay_migration_0008", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def test_migration_syncs_reference_data_and_downgrades_null_safely(monkeypatch):
    migration = _migration()
    calls = []
    monkeypatch.setattr(
        migration.op,
        "alter_column",
        lambda table, column, **kwargs: calls.append(("alter", table, column, kwargs)),
    )
    monkeypatch.setattr(
        migration.op,
        "execute",
        lambda statement: calls.append(("execute", str(statement))),
    )
    monkeypatch.setattr(
        migration.op,
        "bulk_insert",
        lambda table, rows: calls.append(("insert", table.name, rows)),
    )

    migration.upgrade()
    inserts = {call[1]: call[2] for call in calls if call[0] == "insert"}
    assert {row["name"] for row in inserts["essay_company"]} == {
        "삼성전자",
        "현대오토에버",
        "포스코DX",
        "오큘러스에쿼티파트너스",
    }
    assert len(inserts["essay_question"]) == 10
    assert any(row["char_limit"] is None for row in inserts["essay_question"])

    calls.clear()
    migration.downgrade()
    assert [call[0] for call in calls] == ["execute", "execute", "alter"]
    assert calls[-1][-1] == {"nullable": False}
