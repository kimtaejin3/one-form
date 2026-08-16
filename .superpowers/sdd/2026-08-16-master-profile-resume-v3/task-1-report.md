# Task 1 Report

## Changed files

- `apps/backend/app/core/pdf.py`: added one retry path that repairs a malformed final `startxref`; both text and photo extraction use `_pdf_reader`.
- `apps/backend/tests/test_profile.py`: added malformed-xref recovery and unrepairable-bytes boundary tests plus a generated text-PDF helper.

## Verification

- `apps/backend/.venv/bin/pytest apps/backend/tests/test_profile.py::test_pdf_pages_repairs_wrong_final_startxref apps/backend/tests/test_profile.py::test_pdf_pages_rejects_unrepairable_bytes -q` — 2 passed.
- `apps/backend/.venv/bin/pytest apps/backend/tests/test_profile.py -q` — 12 passed (1 existing dependency warning).
- Real PDF check — printed `3` pages.
- `git diff --check` — passed.

## Commit

`fix(backend): 잘못된 PDF xref 복구`

Commit hash: `e8987f6eb02c46f6cf6624677f2ac023d3662353`

## Concerns

None.
