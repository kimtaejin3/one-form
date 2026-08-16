# Master Profile Resume v3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Recover browser-readable PDFs with a bad final `startxref` and populate every supported master-profile section from a modern section-based resume while retaining optional photos.

**Architecture:** Repair only the final classic xref pointer before constructing a shared `PdfReader`, then feed its layout-preserved pages to a new deterministic v3 extractor. Extend the typed Profile contract with only headline, summary, categorized skills, open-source contributions, and project organization; persist new top-level lists in JSONB and render/edit them through the existing profile page.

**Tech Stack:** Python 3.11, FastAPI, pypdf 6.14, Pydantic, SQLAlchemy/Alembic, pytest, React 19, TypeScript, TanStack Query, Vitest.

**Spec:** `docs/superpowers/specs/2026-08-16-master-profile-resume-v3-design.md`

## Global Constraints

- Keep PDF validation at 10MB and 30 pages.
- Keep `personal.photo` optional and preserve the existing image safety budgets.
- Do not add OCR, external LLM calls, generic key-value sections, upload steps, cards, or modals.
- Backend Pydantic schemas remain the FE contract source; regenerate `apps/web/src/shared/api/schema.ts` with `pnpm gen:api`.
- Use Node 22 for every pnpm command.
- Follow TDD: write and observe each failing test before production edits.

---

### Task 1: Repair malformed final startxref once

**Files:**
- Modify: `apps/backend/app/core/pdf.py`
- Test: `apps/backend/tests/test_profile.py`

**Interfaces:**
- Consumes: raw PDF `bytes` accepted by `pdf_pages()` and `pdf_photo_data_url()`.
- Produces: `_pdf_reader(pdf_bytes: bytes) -> PdfReader`, used by both text and photo extraction.

- [ ] **Step 1: Write the failing malformed-xref test**

Add a test helper that creates a one-page text PDF with `PdfWriter`, changes only the final `startxref` number to the Catalog object offset, and asserts:

```python
def test_pdf_pages_repairs_wrong_final_startxref():
    damaged = _text_pdf_with_catalog_startxref("김태진")

    assert pdf.pdf_pages(damaged) == ["김태진"]
```

Add a second boundary test proving arbitrary bytes still fail:

```python
def test_pdf_pages_rejects_unrepairable_bytes():
    with pytest.raises(ValueError, match="읽을 수 없는 PDF"):
        pdf.pdf_pages(b"%PDF-not-a-real-document")
```

- [ ] **Step 2: Run the tests and verify RED**

Run:

```bash
apps/backend/.venv/bin/pytest apps/backend/tests/test_profile.py::test_pdf_pages_repairs_wrong_final_startxref apps/backend/tests/test_profile.py::test_pdf_pages_rejects_unrepairable_bytes -q
```

Expected: malformed-xref test fails with `Trailer cannot be read`; invalid bytes test passes.

- [ ] **Step 3: Implement the single retry reader**

In `app/core/pdf.py`, add:

```python
_FINAL_STARTXREF = re.compile(rb"startxref\s+(\d+)\s+%%EOF\s*$")


def _repair_final_startxref(pdf_bytes: bytes) -> bytes:
    match = _FINAL_STARTXREF.search(pdf_bytes)
    actual = pdf_bytes.rfind(b"\nxref\n") + 1
    if not match or actual <= 0 or int(match.group(1)) == actual:
        return pdf_bytes
    return pdf_bytes[: match.start(1)] + str(actual).encode() + pdf_bytes[match.end(1) :]


def _pdf_reader(pdf_bytes: bytes) -> PdfReader:
    try:
        return PdfReader(BytesIO(pdf_bytes))
    except Exception:
        repaired = _repair_final_startxref(pdf_bytes)
        if repaired == pdf_bytes:
            raise
        return PdfReader(BytesIO(repaired))
```

Use `_pdf_reader()` in both `pdf_pages()` and `pdf_photo_data_url()`. Retain the existing ValueError translation, encryption handling, page limit, text requirement, and photo budgets.

- [ ] **Step 4: Verify GREEN and the real PDF**

Run the focused tests, then:

```bash
cd apps/backend
.venv/bin/python -c "from pathlib import Path; from app.core.pdf import pdf_pages; p=Path('/Users/kimtaejin/dev/resume/dist/김태진_이력서.pdf'); print(len(pdf_pages(p.read_bytes())))"
```

Expected: tests pass and the real PDF prints `3`.

- [ ] **Step 5: Commit Task 1**

```bash
git add apps/backend/app/core/pdf.py apps/backend/tests/test_profile.py
git commit -m "fix(backend): 잘못된 PDF xref 복구"
```

---

### Task 2: Extend and persist the Profile contract

**Files:**
- Create: `apps/backend/alembic/versions/0009_profile_resume_v3.py`
- Create: `apps/backend/tests/test_profile_migration.py`
- Modify: `apps/backend/app/profile/schemas.py`
- Modify: `apps/backend/app/profile/models.py`
- Modify: `apps/backend/app/profile/extractors/profile.py`
- Modify: `apps/backend/app/profile/repository.py`
- Modify: `apps/backend/app/seed.py`
- Modify: `apps/backend/tests/test_profile.py`
- Modify: `apps/backend/tests/test_seed.py`
- Regenerate: `apps/web/src/shared/api/schema.ts`

**Interfaces:**
- Produces: `Personal.headline`, `Personal.summary`, `Project.organization`, `SkillGroup`, `OpenSourceContribution`, `Profile.skill_groups`, and `Profile.open_source_contributions`.
- Persists: `skill_groups` and `open_source_contributions` as non-null JSONB arrays.

- [ ] **Step 1: Write failing schema and persistence tests**

Extend `test_profile.py` to assert an empty extracted profile has all new defaults:

```python
assert profile["personal"]["headline"] == ""
assert profile["personal"]["summary"] == ""
assert profile["skill_groups"] == []
assert profile["open_source_contributions"] == []
```

Add a `client.put('/api/profile')` round-trip containing:

```python
profile["personal"]["headline"] = "Node.js 기반 풀스택 개발자"
profile["skill_groups"] = [{"category": "언어", "skills": ["TypeScript", "Python"]}]
profile["open_source_contributions"] = [{
    "repository": "nodejs/node",
    "url": "https://github.com/nodejs/node",
    "highlights": ["vm.compileFunction 매개변수 검증 개선"],
}]
```

Assert the PUT response returns those exact values. In `test_seed.py`, assert the profile insert contains both arrays. In `test_profile_migration.py`, monkeypatch Alembic `op.add_column`/`drop_column` and assert upgrade adds two JSONB columns with `server_default='[]'` and downgrade removes them.

- [ ] **Step 2: Run focused tests and verify RED**

Run:

```bash
apps/backend/.venv/bin/pytest apps/backend/tests/test_profile.py apps/backend/tests/test_profile_migration.py apps/backend/tests/test_seed.py -q
```

Expected: failures identify absent schema fields, model columns, migration, and seed values.

- [ ] **Step 3: Implement the contract and defaults**

Add these schema shapes:

```python
class Personal(BaseModel):
    photo: str
    name: str
    name_en: str
    name_cn: str
    headline: str = ""
    summary: str = ""
    address: str
    phone: str
    email: str
    emergency_phone: str
    emergency_relation: str


class SkillGroup(BaseModel):
    category: str
    skills: list[str]


class OpenSourceContribution(BaseModel):
    repository: str
    url: str
    highlights: list[str]
```

Add `organization: str = ""` to `Project`, and defaulted lists to `Profile`:

```python
skill_groups: list[SkillGroup] = []
open_source_contributions: list[OpenSourceContribution] = []
```

Use `Field(default_factory=list)` instead of shared list instances. Add matching empty values in `empty_profile()` and `_PROFILE`. Add JSONB mapped columns in `models.Profile`; include them in repository read/write and `seed_profile()`.

Migration `0009_profile_resume_v3` must use `down_revision = "0008_essay_char_limit"` and add/drop exactly `skill_groups` and `open_source_contributions`.

- [ ] **Step 4: Regenerate the API contract and verify GREEN**

Run:

```bash
export PATH=/Users/kimtaejin/.nvm/versions/node/v22.22.2/bin:$PATH
pnpm gen:api
apps/backend/.venv/bin/pytest apps/backend/tests/test_profile.py apps/backend/tests/test_profile_migration.py apps/backend/tests/test_seed.py -q
```

Expected: generated TypeScript contains the new fields and all focused tests pass.

- [ ] **Step 5: Commit Task 2**

```bash
git add apps/backend/alembic/versions/0009_profile_resume_v3.py apps/backend/tests/test_profile_migration.py apps/backend/app/profile/schemas.py apps/backend/app/profile/models.py apps/backend/app/profile/extractors/profile.py apps/backend/app/profile/repository.py apps/backend/app/seed.py apps/backend/tests/test_profile.py apps/backend/tests/test_seed.py apps/web/src/shared/api/schema.ts
git commit -m "feat(repo): 마스터 프로필 항목 확장"
```

---

### Task 3: Add the deterministic section-based v3 extractor

**Files:**
- Create: `apps/backend/app/profile/extractors/v3.py`
- Create: `apps/backend/tests/fixtures/modern_resume.txt`
- Modify: `apps/backend/app/profile/extractors/registry.py`
- Modify: `apps/backend/app/core/config.py`
- Modify: `apps/backend/tests/test_profile.py`

**Interfaces:**
- Consumes: `list[str]` layout-preserved page text.
- Produces: a complete Profile dict through `V3ProfileExtractor.extract(pages)`.
- Preserves: `V2ProfileExtractor` as the base fallback and registered `v1`/`v2` behavior.

- [ ] **Step 1: Add a representative fixture and failing extraction test**

Create a redacted three-page text fixture using the approved headings and representative values for two careers, two projects, two open-source repositories, three activities, one education, two awards, one language, and one certificate. The test must assert literal results, including:

```python
profile = V3ProfileExtractor().extract(fixture.split("\f"))

assert profile["personal"]["name"] == "김태진"
assert profile["personal"]["name_en"] == "Taejin Kim"
assert profile["personal"]["headline"] == "Node.js 기반 풀스택 개발자"
assert profile["personal"]["summary"].startswith("Node.js 생태계를 중심으로")
assert profile["links"] == [{"label": "GitHub", "url": "https://github.com/kimtaejin3"}]
assert profile["skill_groups"][0] == {
    "category": "언어",
    "skills": ["TypeScript", "JavaScript", "Python"],
}
assert [career["company"] for career in profile["careers"]] == ["라인월드", "그린다에이아이"]
assert any(project["name"] == "push-on" for project in profile["projects"])
assert any(project["organization"] == "라인월드" for project in profile["projects"])
assert [item["repository"] for item in profile["open_source_contributions"]] == [
    "nodejs/node",
    "eslint/eslint",
]
assert len(profile["activities"]) == 3
assert profile["educations"][0]["school"] == "충남대학교"
assert len(profile["awards"]) == 2
assert profile["languages"][0]["test"] == "TOEIC Speaking"
assert profile["certificates"][0]["name"] == "정보처리기능사"
```

- [ ] **Step 2: Run the v3 test and verify RED**

Run:

```bash
apps/backend/.venv/bin/pytest apps/backend/tests/test_profile.py -q
```

Expected: import or registry failure because v3 does not exist.

- [ ] **Step 3: Implement section parsing without resume-specific names**

Create `V3ProfileExtractor(V2ProfileExtractor)` with small module-level helpers:

```python
SECTION_NAMES = (
    "소개",
    "기술 스택",
    "경력",
    "프로젝트",
    "오픈소스 기여",
    "외부 활동",
    "학력 · 수상 · 자격",
)


def _sections(text: str) -> dict[str, str]:
    headings = list(re.finditer(
        rf"(?m)^({'|'.join(map(re.escape, SECTION_NAMES))})\s*$",
        text,
    ))
    return {
        match.group(1): text[match.end(): headings[index + 1].start() if index + 1 < len(headings) else len(text)].strip()
        for index, match in enumerate(headings)
    }
```

Implement focused helpers `_identity`, `_links`, `_skill_groups`, `_careers_and_projects`, `_open_source`, `_activities`, and `_credentials`. Reuse `_skills()` only for free-text career/project stacks; preserve skill table categories directly. Normalize bullet lines, page form-feed boundaries, bare GitHub URLs, and date separators. Do not infer absent phone, address, GPA, issuer, or URL values.

Start with `profile = super().extract(pages)` and replace a section only when v3 recognizes that section. Register `v3` in `registry.py` and change `RESUME_EXTRACTOR_VERSION` default to `v3`.

- [ ] **Step 4: Verify v1/v2/v3 and the real PDF**

Run:

```bash
apps/backend/.venv/bin/pytest apps/backend/tests/test_profile.py -q
cd apps/backend
.venv/bin/python -c "from pathlib import Path; from app.profile.service import profile_from_pdf; p=Path('/Users/kimtaejin/dev/resume/dist/김태진_이력서.pdf'); x=profile_from_pdf(p.read_bytes()); print(x['personal']['name'], len(x['careers']), len(x['projects']), len(x['open_source_contributions']))"
```

Expected: tests pass; real PDF prints `김태진 2 6 6` or a larger project count without losing any named project.

- [ ] **Step 5: Commit Task 3**

```bash
git add apps/backend/app/profile/extractors/v3.py apps/backend/tests/fixtures/modern_resume.txt apps/backend/app/profile/extractors/registry.py apps/backend/app/core/config.py apps/backend/tests/test_profile.py
git commit -m "feat(backend): 섹션형 이력서 v3 파싱"
```

---

### Task 4: Display and edit only the new populated fields

**Files:**
- Create: `apps/web/src/pages/profile/ui/ProfilePage.test.tsx`
- Modify: `apps/web/src/pages/profile/ui/ProfilePage.tsx`
- Modify: `apps/web/src/features/edit-profile/ui/ProfileEditor.tsx`

**Interfaces:**
- Consumes: generated `ProfileData` fields from Task 2.
- Produces: existing-page rendering and editing for headline, summary, skill groups, open-source contributions, and project organization.

- [ ] **Step 1: Write the failing profile rendering/editing test**

Mock `/api/profile` with a complete generated-contract-shaped profile and assert:

```tsx
expect(await screen.findByText('Node.js 기반 풀스택 개발자')).toBeTruthy()
expect(screen.getByText('TypeScript')).toBeTruthy()
expect(screen.getByText('nodejs/node')).toBeTruthy()
expect(screen.getByText('라인월드 · csms_sim3d')).toBeTruthy()

fireEvent.click(screen.getByRole('button', { name: '프로필 편집' }))
expect(screen.getByLabelText('직무 제목')).toHaveValue('Node.js 기반 풀스택 개발자')
expect(screen.getByText('오픈소스 기여 추가')).toBeTruthy()
```

The fixture must include every existing required profile field; do not cast a partial object.

- [ ] **Step 2: Run the page test and verify RED**

Run:

```bash
export PATH=/Users/kimtaejin/.nvm/versions/node/v22.22.2/bin:$PATH
pnpm --filter @one-form/web test -- src/pages/profile/ui/ProfilePage.test.tsx
```

Expected: new text and editor controls are absent.

- [ ] **Step 3: Extend existing page and generic editor only**

In `ProfilePage.tsx`:

- render headline and summary below personal details only when non-empty;
- render `skill_groups` with existing `.resume-list`, `.resume-entry`, and `.of-chip` classes only when the list is non-empty;
- render `open_source_contributions` with repository link and highlight list only when non-empty;
- show `project.organization` in the existing project metadata only when non-empty.

In `ProfileEditor.tsx`, add `skill_groups` and `open_source_contributions` to `ListKey`/`LIST_SECTIONS`, use the existing string-array editing behavior, and add labels:

```typescript
headline: '직무 제목',
summary: '소개',
category: '분류',
skills: '기술',
repository: '저장소',
organization: '소속',
```

Do not add CSS or new UI components unless an existing class cannot represent the content legibly.

- [ ] **Step 4: Verify GREEN**

Run:

```bash
pnpm --filter @one-form/web test -- src/pages/profile/ui/ProfilePage.test.tsx
pnpm --filter @one-form/web lint
pnpm --filter @one-form/web build
```

Expected: page test, lint, and build pass.

- [ ] **Step 5: Commit Task 4**

```bash
git add apps/web/src/pages/profile/ui/ProfilePage.test.tsx apps/web/src/pages/profile/ui/ProfilePage.tsx apps/web/src/features/edit-profile/ui/ProfileEditor.tsx
git commit -m "feat(web): 확장 프로필 항목 표시"
```

---

### Task 5: Full contract and regression verification

**Files:**
- No planned production edits; generated contract drift is handled in Step 5.

**Interfaces:**
- Verifies the complete browser → API → parser → persisted Profile contract.

- [ ] **Step 1: Regenerate the contract once more**

```bash
export PATH=/Users/kimtaejin/.nvm/versions/node/v22.22.2/bin:$PATH
pnpm gen:api
git diff --check
```

- [ ] **Step 2: Run all backend tests**

```bash
apps/backend/.venv/bin/pytest apps/backend/tests
```

Expected: zero failures. The public URL DNS test may require network-enabled execution.

- [ ] **Step 3: Run all web checks**

```bash
pnpm --filter @one-form/web test
pnpm lint
pnpm build
```

Expected: zero test, lint, type, or build failures.

- [ ] **Step 4: Compare the real PDF result**

Run a local JSON summary that omits photo bytes and verify all source sections are represented:

```bash
cd apps/backend
.venv/bin/python -c "from pathlib import Path; from app.profile.service import profile_from_pdf; import json; p=Path('/Users/kimtaejin/dev/resume/dist/김태진_이력서.pdf'); x=profile_from_pdf(p.read_bytes()); x['personal']['photo']=bool(x['personal']['photo']); print(json.dumps(x, ensure_ascii=False, indent=2))"
```

Require: correct Korean/English name, headline, full summary, GitHub, five skill groups, two careers, every named project, six open-source repositories, three external activities, education, three awards, TOEIC Speaking, and 정보처리기능사. Photo must remain `False` for this PDF because it has no image object.

- [ ] **Step 5: Commit any generated contract drift**

If `pnpm gen:api` changed only `apps/web/src/shared/api/schema.ts`, commit it:

```bash
git add apps/web/src/shared/api/schema.ts
git commit -m "chore(repo): 프로필 API 계약 동기화"
```

If there is no diff, do not create an empty commit.
