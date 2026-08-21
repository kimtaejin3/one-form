# Work24 Job Sync Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Do not start Task 2 until the Task 1 access gate is complete.

**Goal:** Import nationwide IT/software postings from Work24 into the existing `job` table once per day, serve only active local rows through the current matching flow, and show the required Work24 source link and attribution on job detail pages.

**Architecture:** A sync-only Work24 module calls the official XML list/detail APIs, compares `wantedAuthNo` and `smodifyDtm` with local rows, then applies changed rows and lifecycle updates in one transaction. The web request path keeps reading the database through the existing repository/source flow; it never calls Work24. An external cron invokes `python -m app.jobs.sync`, so no scheduler service or admin UI is added.

**Tech Stack:** Python 3.11, FastAPI, httpx, stdlib `xml.etree.ElementTree`, SQLAlchemy/Alembic, PostgreSQL, pytest, React 19, TypeScript, TanStack Query, Vitest.

**Spec:** `docs/superpowers/specs/2026-08-21-work24-job-sync-design.md`

## Global Constraints

- This plan is blocked until a Work24 enterprise account, API approval, and API key exist. Do not invent occupation codes or XML shapes.
- Use only the official common-code, list, and detail APIs. Do not scrape Work24 pages.
- Keep `WORK24_API_KEY` server-only. Never print it, add it to a fixture, commit it, or expose it through OpenAPI.
- Store no business registration number or recruiter contact data.
- Use stdlib `xml.etree.ElementTree`; `httpx` is already installed. Add no dependency.
- Work24 is sync-only. Do not add it to `active_sources()` as a request-time HTTP adapter.
- Preserve the current feed response. Add only nullable `source_url` to `JobDetail`.
- Do not add pages, cards, status banners, admin controls, schedulers, queues, or sync-history tables.
- Keep the existing mock fallback when the database has never been seeded or synced. If the DB has rows but none are active, return an empty list instead of resurrecting mock jobs.
- Use Node 22 for every `pnpm` command.
- Follow TDD: add the focused failing test, run it and observe RED, implement the minimum change, then run GREEN.
- Commit after each task using the repository's Conventional Commit rules.

---

### Task 1: Complete the external-access gate and capture real contracts

**Files:**
- Create: `apps/backend/tests/fixtures/work24_list.xml`
- Create: `apps/backend/tests/fixtures/work24_detail.xml`
- Modify: `docs/superpowers/specs/2026-08-21-work24-job-sync-design.md`

**Interfaces:**
- Official common-code endpoint: `GET https://www.work24.go.kr/cm/openApi/call/wk/callOpenApiSvcInfo21L01.do`
- Official list endpoint: `GET https://www.work24.go.kr/cm/openApi/call/wk/callOpenApiSvcInfo210L01.do`
- Official detail endpoint: `GET https://www.work24.go.kr/cm/openApi/call/wk/callOpenApiSvcInfo210D01.do`
- Produces: approved IT/software occupation codes and redacted UTF-8 list/detail XML fixtures.

- [ ] **Step 1: Obtain access outside the repository**

Complete Work24 enterprise membership, Open API application, approval, and key issuance. Read the issued value without putting it in the plan or shell history:

```bash
read -rsp 'WORK24 API key: ' WORK24_API_KEY
export WORK24_API_KEY
test -n "$WORK24_API_KEY"
```

Expected: `WORK24_API_KEY` is non-empty. If approval is still pending, stop here; do not continue with guessed fixtures or codes.

- [ ] **Step 2: Download the authoritative occupation-code response**

```bash
curl --fail --silent --show-error --get \
  'https://www.work24.go.kr/cm/openApi/call/wk/callOpenApiSvcInfo21L01.do' \
  --data-urlencode "authKey=$WORK24_API_KEY" \
  --data-urlencode 'returnType=XML' \
  --data-urlencode 'target=CMCD' \
  --data-urlencode 'dtlGb=2' \
  --output /tmp/work24-occupation-codes.xml
```

Expected: valid UTF-8 XML containing the official occupation hierarchy. Select only codes whose official names are IT/software roles. Join those exact codes with `|`, then read the result into the environment rather than recording an unverified value in this plan:

```bash
read -rp 'Verified IT occupation codes (pipe-separated): ' WORK24_OCCUPATION_CODES
export WORK24_OCCUPATION_CODES
test -n "$WORK24_OCCUPATION_CODES"
```

Replace the explanatory sentence under **고용24 필드 매핑** in the design spec with a table of the selected official code, official name, and one of the existing one-form categories: `백엔드`, `프론트엔드`, `풀스택`, `데브옵스`, `안드로이드`, `iOS`, `데이터`, `ML`. Every selected code must have exactly one category; omit codes that do not map cleanly.

- [ ] **Step 3: Capture one real list page**

```bash
curl --fail --silent --show-error --get \
  'https://www.work24.go.kr/cm/openApi/call/wk/callOpenApiSvcInfo210L01.do' \
  --data-urlencode "authKey=$WORK24_API_KEY" \
  --data-urlencode 'callTp=L' \
  --data-urlencode 'returnType=XML' \
  --data-urlencode 'startPage=1' \
  --data-urlencode 'display=100' \
  --data-urlencode 'sortOrderBy=DESC' \
  --data-urlencode "occupation=$WORK24_OCCUPATION_CODES" \
  --output /tmp/work24-list.xml
```

Expected: the XML includes a total count and at least one item with `wantedAuthNo`, company, title, `wantedInfoUrl`, and `smodifyDtm`. If the selected code set legitimately returns zero rows, choose a narrower official IT code that currently has a posting and record only that verified code.

- [ ] **Step 4: Capture the matching real detail response**

Extract the first `wantedAuthNo` and `infoSvc` without adding a parser dependency:

```bash
export WORK24_SAMPLE_ID="$(python3 -c "import xml.etree.ElementTree as E; r=E.parse('/tmp/work24-list.xml').getroot(); print(next(x.text for x in r.iter('wantedAuthNo') if x.text))")"
export WORK24_INFO_SVC="$(python3 -c "import xml.etree.ElementTree as E; r=E.parse('/tmp/work24-list.xml').getroot(); print(next((x.text for x in r.iter('infoSvc') if x.text), 'VALIDATION'))")"
curl --fail --silent --show-error --get \
  'https://www.work24.go.kr/cm/openApi/call/wk/callOpenApiSvcInfo210D01.do' \
  --data-urlencode "authKey=$WORK24_API_KEY" \
  --data-urlencode 'callTp=D' \
  --data-urlencode 'returnType=XML' \
  --data-urlencode "wantedAuthNo=$WORK24_SAMPLE_ID" \
  --data-urlencode "infoSvc=$WORK24_INFO_SVC" \
  --output /tmp/work24-detail.xml
```

Expected: the detail XML contains the same posting identity plus company, title, job description, closing information, and source URL fields documented by Work24.

- [ ] **Step 5: Redact and minimize the fixtures**

Copy one complete list item and its matching detail structure into the two fixture files. Preserve real element names, nesting, date formats, empty-element behavior, encoding, and the selected `jobsCd`. Replace values for these fields before committing:

- `wantedAuthNo` → `KJ202608210001`
- `smodifyDtm` → the observed format representing `2026-08-21 12:34:56`
- company/title/text values → clearly fictitious Korean values
- business registration number and every recruiter name, phone, email, address detail → remove the elements or leave them empty
- homepage and source URLs → `https://example.com/...`, except when a Work24 URL shape itself is under test

Verify that neither fixture contains the issued key, an email address, a Korean mobile number, or a business registration number:

```bash
rg -n "$WORK24_API_KEY|[[:alnum:]._%+-]+@[[:alnum:].-]+|01[016789]-?[0-9]{3,4}-?[0-9]{4}|[0-9]{3}-[0-9]{2}-[0-9]{5}" apps/backend/tests/fixtures/work24_*.xml
```

Expected: no output.

- [ ] **Step 6: Commit the verified contract artifacts**

```bash
git add apps/backend/tests/fixtures/work24_list.xml apps/backend/tests/fixtures/work24_detail.xml docs/superpowers/specs/2026-08-21-work24-job-sync-design.md
git commit -m "chore(backend): 고용24 실응답 계약 기록"
```

---

### Task 2: Add the Work24 XML client and normalization

**Files:**
- Create: `apps/backend/app/jobs/sources/work24.py`
- Create: `apps/backend/tests/test_work24.py`
- Modify: `apps/backend/app/core/config.py`
- Modify: `apps/backend/.env.example`

**Interfaces:**
- `parse_list(xml: bytes) -> tuple[int, list[dict]]`
- `parse_detail(xml: bytes) -> dict`
- `normalize(list_item: dict, detail: dict, today: date) -> dict`
- `fetch_list(client: httpx.AsyncClient, page: int) -> tuple[int, list[dict]]`
- `fetch_detail(client: httpx.AsyncClient, source_id: str, info_svc: str) -> dict`
- Settings: `WORK24_API_KEY: str | None`, `WORK24_OCCUPATION_CODES: str | None`

- [ ] **Step 1: Write failing fixture-contract tests**

In `test_work24.py`, load both fixture files with `Path`. Assert the exact shapes observed in Task 1, including the real date format:

```python
def test_parse_list_uses_verified_work24_shape():
    total, items = work24.parse_list(_fixture("work24_list.xml"))

    assert total == 1
    assert items[0]["source_id"] == "KJ202608210001"
    assert items[0]["source_updated_at"] == datetime(2026, 8, 21, 12, 34, 56)
    assert items[0]["info_svc"]


def test_normalize_detail_to_existing_job_shape():
    _, items = work24.parse_list(_fixture("work24_list.xml"))
    detail = work24.parse_detail(_fixture("work24_detail.xml"))
    job = work24.normalize(items[0], detail, date(2026, 8, 21))

    assert job["source"] == "고용24"
    assert job["source_id"] == "KJ202608210001"
    assert job["role_category"] in work24.ROLE_CATEGORY_BY_JOB_CODE.values()
    assert job["company"] and job["title"] and job["description"]
    assert job["match_reason"] == ""
```

Add tests for empty optional elements, missing `wantedAuthNo`, missing company/title, an API-error XML from the verified response format, and a `jobsCd` absent from `ROLE_CATEGORY_BY_JOB_CODE`. Mandatory-field and unmapped-code cases must raise `ValueError`.

- [ ] **Step 2: Run the tests and verify RED**

```bash
apps/backend/.venv/bin/pytest apps/backend/tests/test_work24.py -q
```

Expected: collection fails because `app.jobs.sources.work24` does not exist.

- [ ] **Step 3: Add the two settings without changing source selection**

In `app/core/config.py` add:

```python
WORK24_API_KEY: str | None = None
WORK24_OCCUPATION_CODES: str | None = None
```

Add matching empty values and a comment that they are used only by the daily sync CLI to `.env.example`. Do not include `WORK24_API_KEY` in `sources/selector.py` or `tests/test_matching.py::KEYS`; it must not activate request-time fetching.

- [ ] **Step 4: Implement the minimum XML functions**

Use `xml.etree.ElementTree.fromstring`, a local text helper, and the exact paths/formats proven by the fixtures. Keep plain dictionaries to match the existing source adapters; do not introduce a class hierarchy or Pydantic model for upstream XML.

Define the two endpoint constants in `work24.py`:

```python
LIST_URL = "https://www.work24.go.kr/cm/openApi/call/wk/callOpenApiSvcInfo210L01.do"
DETAIL_URL = "https://www.work24.go.kr/cm/openApi/call/wk/callOpenApiSvcInfo210D01.do"
```

Define `ROLE_CATEGORY_BY_JOB_CODE: dict[str, str]` by copying every exact code/category row approved in the Task 1 design-spec table; an empty or guessed mapping is not acceptable. `fetch_list()` must send `callTp=L`, `returnType=XML`, `startPage`, `display=100`, `sortOrderBy=DESC`, and configured `occupation`. `fetch_detail()` must send `callTp=D`, `returnType=XML`, `wantedAuthNo`, and `infoSvc`. Both call `raise_for_status()` before parsing.

Normalize to the existing repository dictionary plus persistence fields:

```python
{
    "company": ..., "domain": ..., "role_category": ..., "experience": ...,
    "employment": ..., "location": ..., "title": ..., "dday": ...,
    "source": "고용24", "description": ..., "company_info": ...,
    "match_reason": "", "tags": ..., "responsibilities": ...,
    "requirements": ..., "preferred": ..., "source_id": ...,
    "source_url": ..., "source_updated_at": ..., "posted_at": ...,
    "closes_at": ..., "active": True,
}
```

Use the list item's official `wantedInfoUrl` for `source_url`; accept only HTTPS URLs on `work24.go.kr`, its subdomains, `work.go.kr`, or its subdomains. Use non-empty `jobCont` lines as `responsibilities`; join unique `jobsNm`/keywords for tags; keep `requirements` and `preferred` as short non-empty source strings. Compute `dday` as `D-Day`, `D-N`, or `상시`; expired rows will be hidden by persistence. Do not generate match text or infer missing values with an LLM.

- [ ] **Step 5: Test HTTP parameters without network access**

Use `httpx.MockTransport` in `test_work24.py`. Assert one list call contains the exact configured pipe-separated codes and `display=100`, and one detail call contains the verified `wantedAuthNo` and `infoSvc`. Assert HTTP 500, malformed XML, and verified API-error XML raise instead of returning an empty page.

- [ ] **Step 6: Verify GREEN and commit**

```bash
apps/backend/.venv/bin/pytest apps/backend/tests/test_work24.py -q
git add apps/backend/app/jobs/sources/work24.py apps/backend/app/core/config.py apps/backend/.env.example apps/backend/tests/test_work24.py
git commit -m "feat(backend): 고용24 XML 어댑터 추가"
```

---

### Task 3: Persist Work24 identities and lifecycle state

**Files:**
- Create: `apps/backend/alembic/versions/0009_work24_jobs.py`
- Create: `apps/backend/tests/test_work24_migration.py`
- Create: `apps/backend/tests/test_work24_repository.py`
- Modify: `apps/backend/app/jobs/models.py`
- Modify: `apps/backend/app/jobs/repository.py`

**Interfaces:**
- `work24_versions() -> dict[str, datetime | None]`
- `apply_work24_sync(changed_jobs: list[dict], seen_ids: set[str], synced_at: datetime) -> None`
- `all_jobs()` returns active DB rows only and includes `source_url`.

- [ ] **Step 1: Write failing migration/model tests**

In `test_work24_migration.py`, load migration `0009_work24_jobs.py` the same way `test_essay_migration.py` loads revision 0008. Record Alembic calls and assert upgrade adds exactly:

- nullable text: `source_id`, `source_url`
- nullable timezone datetime: `source_updated_at`, `last_seen_at`
- nullable date: `posted_at`, `closes_at`
- non-null boolean `active` with server default true
- unique constraint on `("source", "source_id")`
- sequence synchronization after the existing explicit mock IDs

Assert downgrade drops the constraint and columns in reverse order. Also assert the SQLAlchemy `Job` model exposes those fields with `active=True` as its Python default.

- [ ] **Step 2: Write failing repository statement tests**

Add a small recording async session/sessionmaker in `test_work24_repository.py`. Test these behaviors without a real PostgreSQL server:

```python
def test_work24_upsert_targets_source_identity():
    sql = str(
        repository._work24_upsert_statement(_job()).compile(
            dialect=postgresql.dialect()
        )
    )
    assert "ON CONFLICT (source, source_id) DO UPDATE" in sql


def test_all_jobs_filters_inactive_rows():
    sql = str(repository._active_jobs_statement())
    assert "job.active IS true" in sql
```

Test `apply_work24_sync()` through the recording session and assert it emits, in one session transaction: changed-row upsert, `last_seen_at` update for all seen IDs, unseen Work24 deactivation, expired Work24 deactivation, and deletion only for inactive rows older than 30 days. Assert the session commits once after all statements and rolls back/no commit when a statement raises.

- [ ] **Step 3: Run focused tests and verify RED**

```bash
apps/backend/.venv/bin/pytest apps/backend/tests/test_work24_migration.py apps/backend/tests/test_work24_repository.py -q
```

Expected: failures identify the missing migration, columns, and repository functions.

- [ ] **Step 4: Add revision 0009 and keep existing rows valid**

Use:

```python
revision = "0009_work24_jobs"
down_revision = "0008_essay_char_limit"
```

Add the seven columns and unique constraint from the approved spec. Set existing rows to active through a server default and retain that default for future inserts. After adding columns, advance the existing `job.id` sequence to at least `MAX(id)` so Work24 inserts without explicit IDs cannot collide with seeded IDs 1–40:

```sql
SELECT setval(
  pg_get_serial_sequence('job', 'id'),
  COALESCE((SELECT MAX(id) FROM job), 1),
  true
)
```

Do not change `app/seed.py`; nullable fields and the `active` default keep existing seed inserts valid.

- [ ] **Step 5: Implement repository persistence with PostgreSQL upsert**

Use the already-installed PostgreSQL insert dialect. `_work24_upsert_statement()` must omit `id`, insert `source="고용24"`, and call `on_conflict_do_update(index_elements=["source", "source_id"], set_=...)`. Update all normalized content/source fields and `active`; do not overwrite the internal primary key.

`work24_versions()` selects only Work24 rows with non-null `source_id` and returns `{source_id: source_updated_at}`.

`apply_work24_sync()` must obtain one session, execute all mutations, then commit once:

```python
for job in changed_jobs:
    await session.execute(_work24_upsert_statement(job))
# update last_seen_at for seen_ids
# deactivate Work24 rows not in seen_ids
# deactivate closes_at < synced_at.date()
# delete inactive rows with last_seen_at < synced_at - timedelta(days=30)
await session.commit()
```

Skip the `last_seen_at` update when `seen_ids` is empty. A successfully completed zero-result list must still deactivate every existing Work24 row; implement that as an explicit all-Work24 update instead of generating `NOT IN ()`.

If `DATABASE_URL` is absent, raise `RuntimeError("DATABASE_URL이 설정돼 있어야 합니다.")`; never silently sync to in-memory mocks. Roll back and re-raise on failure.

Change `all_jobs()` to query `Job.active.is_(True)`. Include `source_url` in returned dictionaries, and add `source_url: None` to `_build_jobs()` so mock/detail contracts are uniform. Preserve mocks only if the table has no rows at all. If inactive rows exist but the active query is empty, return `[]`.

- [ ] **Step 6: Verify GREEN and current jobs regression**

```bash
apps/backend/.venv/bin/pytest apps/backend/tests/test_work24_migration.py apps/backend/tests/test_work24_repository.py apps/backend/tests/test_jobs.py -q
```

Expected: all focused tests pass; the no-DB mock feed still contains 40 jobs.

- [ ] **Step 7: Commit Task 3**

```bash
git add apps/backend/alembic/versions/0009_work24_jobs.py apps/backend/app/jobs/models.py apps/backend/app/jobs/repository.py apps/backend/tests/test_work24_migration.py apps/backend/tests/test_work24_repository.py apps/backend/tests/test_jobs.py
git commit -m "feat(backend): 고용24 공고 저장 구조 추가"
```

---

### Task 4: Add the atomic daily sync CLI

**Files:**
- Create: `apps/backend/app/jobs/sync.py`
- Create: `apps/backend/tests/test_work24_sync.py`

**Interfaces:**
- `sync_work24() -> None`
- CLI: `cd apps/backend && uv run python -m app.jobs.sync`
- Consumes: `settings.WORK24_API_KEY`, `settings.WORK24_OCCUPATION_CODES`, Work24 client functions, and repository sync functions.

- [ ] **Step 1: Write failing orchestration tests with fakes**

Use monkeypatches for `work24.fetch_list`, `work24.fetch_detail`, `repository.work24_versions`, and `repository.apply_work24_sync`; no test may call the internet or PostgreSQL.

Cover these cases:

1. Two list pages are fetched with `display=100` behavior delegated to the adapter.
2. New ID fetches detail.
3. Changed `smodifyDtm` fetches detail.
4. Unchanged ID does not fetch detail but remains in `seen_ids`.
5. At most five detail coroutines are active concurrently.
6. A list/detail/XML failure prevents any `apply_work24_sync()` call.
7. A complete run calls `apply_work24_sync(changed_jobs, all_seen_ids, synced_at)` exactly once.
8. Missing key, codes, or database produces a clear exception before an HTTP call.
9. A configured occupation code absent from `ROLE_CATEGORY_BY_JOB_CODE` fails before an HTTP call.

The concurrency test should increment/decrement a counter around a fake detail coroutine and assert `peak == 5`; do not add timing sleeps longer than the minimum event-loop yield.

- [ ] **Step 2: Run the tests and verify RED**

```bash
apps/backend/.venv/bin/pytest apps/backend/tests/test_work24_sync.py -q
```

Expected: collection fails because `app.jobs.sync` does not exist.

- [ ] **Step 3: Implement the page/change orchestration**

In `sync_work24()`:

1. Validate key, non-empty pipe-split codes, complete code mapping, and DB availability.
2. Read `existing = await repository.work24_versions()`.
3. Open one `httpx.AsyncClient(timeout=20)`.
4. Fetch page 1, calculate the remaining pages from `total` and page size 100, then fetch through the final page. Reject more than 1000 pages and duplicate/missing IDs.
5. Build `seen_ids` from the complete list.
6. Select items absent from `existing` or with a different `source_updated_at`.
7. Fetch/normalize only those details under one `asyncio.Semaphore(5)`.
8. Only after every fetch and normalization succeeds, call `apply_work24_sync()` once.

Keep the implementation module-level and direct. Do not add a service class, retry framework, event bus, metrics wrapper, or scheduler abstraction.

- [ ] **Step 4: Add the CLI entry point and failure contract**

Use the normal Python module entry point:

```python
async def main() -> None:
    await sync_work24()


if __name__ == "__main__":
    asyncio.run(main())
```

Let validated failures escape so the process exits non-zero. Log only counts (`listed`, `changed`, `unchanged`, `deactivated/deleted` if returned); never log request query strings, response bodies, or the API key. No `package.json` script is needed because the approved cron contract is the Python module command.

- [ ] **Step 5: Verify GREEN and commit**

```bash
apps/backend/.venv/bin/pytest apps/backend/tests/test_work24.py apps/backend/tests/test_work24_repository.py apps/backend/tests/test_work24_sync.py -q
git add apps/backend/app/jobs/sync.py apps/backend/tests/test_work24_sync.py
git commit -m "feat(backend): 고용24 동기화 CLI 추가"
```

---

### Task 5: Serve active rows and add the required detail attribution

**Files:**
- Modify: `apps/backend/app/jobs/schemas.py`
- Modify: `apps/backend/app/jobs/service.py`
- Modify: `apps/backend/app/jobs/sources/mock.py`
- Modify: `apps/backend/app/jobs/sources/selector.py`
- Modify: `apps/backend/tests/test_jobs.py`
- Modify: `apps/backend/tests/test_matching.py`
- Regenerate: `apps/web/src/shared/api/schema.ts`
- Modify: `apps/web/src/pages/job-detail/ui/JobDetailPage.tsx`
- Modify: `apps/web/src/pages/job-detail/ui/JobDetailPage.test.tsx`

**Interfaces:**
- Backend `JobDetail.source_url: str | None = None`
- Frontend shows attribution only when `job.source === '고용24' && job.source_url`.

- [ ] **Step 1: Write failing backend contract tests**

Add `source_url` to `DETAIL_FIELDS` in `test_jobs.py` and assert mock detail returns `None`. Add a repository-monkeypatched Work24 detail test that asserts the API returns its source URL. Keep `JOB_FIELDS` unchanged so list responses do not grow.

Add a selector regression in `test_matching.py`: setting only `WORK24_API_KEY` must still select `MockJobSource`, proving the key does not trigger request-time HTTP.
Add a second selector regression with a configured database and one existing external-source key: the returned sources must contain the local `MockJobSource` plus that external adapter, so synchronized Work24 rows are not hidden merely because another provider is enabled.

- [ ] **Step 2: Write failing frontend attribution tests**

Add `source_url: null` to the base `jobDetail()` fixture so generated typing remains representative. Add one Work24 response test:

```tsx
test('고용24 공고에 원문 링크와 필수 출처 문구를 표시한다', async () => {
  const officialUrl = 'https://www.work24.go.kr/empInfo/empInfoSrch/detail.do'
  // fetch returns source: '고용24' and source_url: officialUrl
  renderPage()

  const link = await screen.findByRole('link', { name: '고용24에서 원문 보기' })
  expect(link).toHaveAttribute('href', officialUrl)
  expect(link).toHaveAttribute('target', '_blank')
  expect(screen.getByText(/본 자료는 고용노동부 고용24/)).toBeInTheDocument()
})
```

Also assert the existing non-Work24 fixture does not show that link or text.

- [ ] **Step 3: Run focused tests and verify RED**

```bash
apps/backend/.venv/bin/pytest apps/backend/tests/test_jobs.py apps/backend/tests/test_matching.py -q
export PATH=/Users/kimtaejin/.nvm/versions/node/v22.22.2/bin:$PATH
pnpm --filter @one-form/web test -- JobDetailPage.test.tsx
```

Expected: backend fails on the missing field; frontend fails on the missing source block.

- [ ] **Step 4: Extend only the detail contract**

In `JobDetail` add:

```python
source_url: str | None = None
```

Pass `job.get("source_url")` when constructing `JobDetail` in `service.get_job_detail()`. Do not add the field to `Job`, feed cards, filters, or source selection.

In `sources/mock.py`, skip `core.mock.mock()` delay when `get_sessionmaker()` is present; keep the existing delay in no-DB mock development. This reuses the current source/repository flow without renaming it or adding a second local source abstraction.

In `sources/selector.py`, include `mock.get_source()` whenever a database is configured, followed by any configured request-time external adapters. Without a database, preserve the current `real or [mock.get_source()]` behavior. Do not treat `WORK24_API_KEY` as a request-time source key.

- [ ] **Step 5: Regenerate OpenAPI TypeScript**

```bash
export PATH=/Users/kimtaejin/.nvm/versions/node/v22.22.2/bin:$PATH
pnpm gen:api
```

Expected: `apps/web/src/shared/api/schema.ts` contains nullable `source_url` on `JobDetail`; no hand-written entity type is added.

- [ ] **Step 6: Render the minimal conditional footer**

After the existing company-information section in `JobDetailPage.tsx`, add one conditional block with:

- external anchor text `고용24에서 원문 보기`
- `target="_blank"` and `rel="noreferrer"`
- exact required sentence: `본 자료는 고용노동부 고용24(www.work24.go.kr)에서 제공된 정보이며, 무단복제 및 배포를 금지합니다.`

Reuse `job-detail__back`/existing typography classes if readable. Do not add a card, badge, icon, heading, modal, or new design-system component. Add CSS only if the existing classes fail readability in the browser.

- [ ] **Step 7: Verify GREEN and commit**

```bash
apps/backend/.venv/bin/pytest apps/backend/tests/test_jobs.py apps/backend/tests/test_matching.py -q
export PATH=/Users/kimtaejin/.nvm/versions/node/v22.22.2/bin:$PATH
pnpm --filter @one-form/web test -- JobDetailPage.test.tsx
pnpm --filter @one-form/web lint
pnpm --filter @one-form/web build
git add apps/backend/app/jobs/schemas.py apps/backend/app/jobs/service.py apps/backend/app/jobs/sources/mock.py apps/backend/app/jobs/sources/selector.py apps/backend/tests/test_jobs.py apps/backend/tests/test_matching.py apps/web/src/shared/api/schema.ts apps/web/src/pages/job-detail/ui/JobDetailPage.tsx apps/web/src/pages/job-detail/ui/JobDetailPage.test.tsx
git commit -m "feat(repo): 고용24 공고 상세 출처 연결"
```

---

### Task 6: Document operations and run the end-to-end acceptance checks

**Files:**
- Modify: `docs/채용공고-api-연동-계획.md`

**Interfaces:**
- Manual command: `cd apps/backend && uv run python -m app.jobs.sync`
- External schedule: once daily after the database migration is deployed.

- [ ] **Step 1: Add the short operator runbook**

Document only:

1. Required env: `DATABASE_URL`, `WORK24_API_KEY`, `WORK24_OCCUPATION_CODES`.
2. Migration command used by the deployment.
3. Manual sync command.
4. A sample daily cron entry using an absolute deployment path.
5. Success criteria: zero exit code and count-only log.
6. Failure behavior: non-zero exit, no lifecycle mutation, web serves last successful snapshot.
7. Key rotation: replace the environment value; no code change.

Do not add deployment-specific cron files until the actual host/runtime is chosen.

- [ ] **Step 2: Run the full automated verification**

```bash
apps/backend/.venv/bin/pytest apps/backend/tests -q
export PATH=/Users/kimtaejin/.nvm/versions/node/v22.22.2/bin:$PATH
pnpm gen:api
git diff --exit-code apps/web/src/shared/api/schema.ts
pnpm --filter @one-form/web test
pnpm --filter @one-form/web lint
pnpm --filter @one-form/web build
git diff --check
```

Expected: all commands pass and regenerating the API produces no diff.

- [ ] **Step 3: Run the real-key two-pass acceptance check**

Against a migrated non-production database, run:

```bash
cd apps/backend
uv run python -m app.jobs.sync
uv run python -m app.jobs.sync
```

Expected:

- First run inserts/updates Work24 IT postings and exits zero.
- Second run reports zero detail fetches for unchanged `smodifyDtm` values.
- `GET /api/jobs` returns active DB rows without waiting on Work24.
- A Work24 `GET /api/jobs/{id}` response contains `source_url`.
- Its web detail page opens the official source in a new tab and shows the exact attribution.
- Temporarily forcing an API error exits non-zero and leaves the prior active row count unchanged.

Do not run the failure check against production; use the test database and restore the valid key immediately afterward.

- [ ] **Step 4: Commit operations documentation**

```bash
git add docs/채용공고-api-연동-계획.md
git commit -m "docs(backend): 고용24 동기화 운영 절차 추가"
```

---

## Final Review Gate

- [ ] Confirm every implemented occupation code appears in the Task 1 official-code response and in `ROLE_CATEGORY_BY_JOB_CODE`.
- [ ] Confirm no secret or personal contact data exists in `git diff --cached`, fixtures, logs, generated schema, or frontend bundle.
- [ ] Confirm no Work24 HTTP call is reachable from `/api/jobs` or `/api/jobs/{id}`.
- [ ] Confirm partial list/detail failure cannot call `apply_work24_sync()`.
- [ ] Confirm a database containing only inactive jobs returns an empty feed, not mock jobs.
- [ ] Confirm no new dependency, scheduler, queue, history table, page, card, or admin UI was added.
- [ ] Confirm `git status --short` is clean after the final commit.
