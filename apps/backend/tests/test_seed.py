import asyncio

from sqlalchemy.sql.dml import Delete

from app.seed import seed_essays, seed_profile


class RecordingSession:
    def __init__(self):
        self.statements = []

    async def execute(self, statement):
        self.statements.append(statement)


def test_seed_essays_replaces_stale_references_without_deleting_answers():
    session = RecordingSession()
    asyncio.run(seed_essays(session))

    deletes = [s for s in session.statements if isinstance(s, Delete)]
    assert [s.table.name for s in deletes] == ["essay_company", "essay_question"]
    assert all(s.table.name != "essay_answer" for s in deletes)


def test_seed_profile_includes_resume_v3_arrays():
    session = RecordingSession()

    asyncio.run(seed_profile(session))

    params = session.statements[0].compile().params
    assert "skill_groups" in params
    assert "open_source_contributions" in params
