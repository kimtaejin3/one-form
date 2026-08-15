import asyncio

from sqlalchemy.sql.dml import Delete

from app.seed import seed_essays


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
