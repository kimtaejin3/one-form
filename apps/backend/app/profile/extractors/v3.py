"""v3: 섹션 제목이 있는 현대형 이력서의 보수적 추출기."""
import re

from app.profile.extractors.v2 import V2ProfileExtractor, _skills

SECTION_NAMES = (
    "소개",
    "기술 스택",
    "경력",
    "프로젝트",
    "오픈소스 기여",
    "외부 활동",
    "학력 · 수상 · 자격",
)

_DATE = r"\d{4}\.\d{2}\s*(?:~|–|-)\s*(?:\d{4}\.\d{2}|재직\s*중)"
_PRIVATE_DIGITS = str.maketrans({**{chr(0xE071 + index): str(index) for index in range(10)}, "\uE094": "."})


def _sections(text: str) -> dict[str, str]:
    headings = list(re.finditer(
        rf"(?m)^({'|'.join(map(re.escape, SECTION_NAMES))})\s*$",
        text,
    ))
    return {
        match.group(1): text[match.end(): headings[index + 1].start() if index + 1 < len(headings) else len(text)].strip()
        for index, match in enumerate(headings)
    }


def _text(text: str) -> str:
    return text.translate(_PRIVATE_DIGITS).replace("\f", "\n").replace("재직 중", "재직중")


def _period(text: str) -> str:
    match = re.search(_DATE, text)
    return re.sub(r"\s*(?:~|–|-)\s*", " ~ ", match.group(0)) if match else ""


def _clean(line: str) -> str:
    return re.sub(r"\s+", " ", line).strip().lstrip("-• ").strip()


def _pipe(line: str) -> list[str]:
    return [part.strip() for part in line.split("|")] if "|" in line else []


def _identity(text: str, intro: str) -> dict:
    personal: dict[str, str] = {}
    labeled = {}
    for line in intro.splitlines():
        parts = _pipe(line)
        if len(parts) == 2:
            labeled[parts[0]] = parts[1]
    labels = {"이름": "name", "영문 이름": "name_en", "직무": "headline", "요약": "summary"}
    personal.update({field: labeled[label] for label, field in labels.items() if labeled.get(label)})
    before_intro = text.split("소개", maxsplit=1)[0]
    lines = [_clean(line) for line in before_intro.splitlines() if _clean(line)]
    for index, line in enumerate(lines):
        match = re.fullmatch(r"([가-힣]{2,5})\s+([A-Za-z][A-Za-z .'-]+)", line)
        if match:
            personal.setdefault("name", match.group(1))
            personal.setdefault("name_en", match.group(2).strip())
            if index + 1 < len(lines) and not re.search(r"(?:@|github\.com)", lines[index + 1], re.IGNORECASE):
                personal.setdefault("headline", lines[index + 1])
            break
    if "summary" not in personal:
        summary = " ".join(
            _clean(line) for line in intro.splitlines()
            if _clean(line) and not _pipe(line) and "github.com" not in line.lower()
        )
        if summary:
            personal["summary"] = summary
    return personal


def _links(text: str) -> list[dict]:
    urls = list(dict.fromkeys(re.findall(r"(?i)(?:https?://)?github\.com/[\w.-]+", text)))
    return [{"label": "GitHub", "url": url if url.startswith("http") else f"https://{url}"} for url in urls]


def _skill_groups(text: str) -> list[dict]:
    groups = []
    for raw in text.splitlines():
        parts = _pipe(raw)
        if len(parts) != 2:
            match = re.match(r"^(.+?)\s{2,}(.+)$", raw.strip())
            parts = [match.group(1), match.group(2)] if match else []
        if len(parts) != 2:
            continue
        category, skills = parts
        values = [value.strip() for value in skills.split(",") if value.strip()]
        if category and values:
            groups.append({"category": category, "skills": values})
    return groups


def _highlight_lines(lines: list[str]) -> list[str]:
    return [_clean(line) for line in lines if _clean(line)][:6]


def _careers_and_projects(career_text: str, project_text: str) -> tuple[list[dict], list[dict]]:
    careers: list[dict] = []
    projects: list[dict] = []
    career_lines = career_text.splitlines()
    pipe_rows = [(index, _pipe(line)) for index, line in enumerate(career_lines)]
    for index, parts in pipe_rows:
        if len(parts) != 3 or not _period(parts[0]):
            continue
        end = next((next_index for next_index, next_parts in pipe_rows[index + 1:] if len(next_parts) == 3 and _period(next_parts[0])), len(career_lines))
        highlights = _highlight_lines(career_lines[index + 1:end])
        careers.append({"company": parts[1], "role": parts[2], "period": _period(parts[0]), "highlights": highlights, "stack": _skills(" ".join(highlights))})
    if not careers:
        matches = list(re.finditer(rf"(?m)^(.+?)\s{{2,}}(.+?)\s+({_DATE})\s*$", career_text))
        for index, match in enumerate(matches):
            end = matches[index + 1].start() if index + 1 < len(matches) else len(career_text)
            highlights = _highlight_lines(career_text[match.end():end].splitlines())
            careers.append({"company": match.group(1).strip(), "role": match.group(2).strip(), "period": _period(match.group(3)), "highlights": highlights, "stack": _skills(" ".join(highlights))})
    for index, parts in [(index, _pipe(line)) for index, line in enumerate(project_text.splitlines())]:
        if len(parts) != 4:
            continue
        lines = project_text.splitlines()
        end = next((next_index for next_index in range(index + 1, len(lines)) if len(_pipe(lines[next_index])) == 4), len(lines))
        highlights = _highlight_lines(lines[index + 1:end])
        projects.append({"name": parts[0], "organization": parts[1], "period": _period(parts[2]), "role": parts[3], "summary": highlights[0] if highlights else "", "highlights": highlights, "stack": _skills(" ".join(highlights))})
    if projects:
        return careers, projects
    company = careers[0]["company"] if careers else ""
    for source, organization, indent in ((career_text, company, "  "), (project_text, "", "")):
        lines = source.splitlines()
        starts = [index for index, line in enumerate(lines) if line.startswith(indent) and line[len(indent):].strip() and (indent or _period(line))]
        for position, start in enumerate(starts):
            end = starts[position + 1] if position + 1 < len(starts) else len(lines)
            title = _clean(lines[start])
            highlights = _highlight_lines(lines[start + 1:end])
            projects.append({"name": re.sub(_DATE, "", title).strip(), "organization": organization, "period": _period(title), "role": "프로젝트", "summary": highlights[0] if highlights else "", "highlights": highlights, "stack": _skills(" ".join([title, *highlights]))})
    return careers, projects


def _open_source(text: str) -> list[dict]:
    lines = text.splitlines()
    header = re.compile(r"([\w.-]+(?:/[\w.-]+)?)(?:\s*·.*)?$")
    repository = re.compile(r"[\w.-]+(?:/[\w.-]+)?$")
    starts = [
        index for index, line in enumerate(lines)
        if header.fullmatch(line.strip()) or (len(_pipe(line)) == 2 and repository.fullmatch(_pipe(line)[0]))
    ]
    result = []
    for position, start in enumerate(starts):
        end = starts[position + 1] if position + 1 < len(starts) else len(lines)
        parts = _pipe(lines[start])
        repository = (parts[0] if parts else header.fullmatch(lines[start].strip()).group(1)).strip()
        url = parts[1] if len(parts) > 1 and "github.com/" in parts[1] else ""
        if url and not url.startswith("http"):
            url = f"https://{url}"
        result.append({"repository": repository, "url": url, "highlights": _highlight_lines(lines[start + 1:end])})
    return result


def _activities(text: str) -> list[dict]:
    lines = text.splitlines()
    result = []
    for index, line in enumerate(lines):
        parts = _pipe(line)
        if len(parts) == 4:
            end = next((next_index for next_index in range(index + 1, len(lines)) if len(_pipe(lines[next_index])) == 4), len(lines))
            result.append({"type": parts[0], "title": parts[1], "org": parts[2], "period": _period(parts[3]), "description": " ".join(_highlight_lines(lines[index + 1:end]))})
        elif not line.startswith(" ") and (period := _period(line)):
            title = re.sub(_DATE, "", _clean(line)).strip()
            end = next((next_index for next_index in range(index + 1, len(lines)) if not lines[next_index].startswith(" ") and _period(lines[next_index])), len(lines))
            result.append({"type": "활동", "title": title, "org": "", "period": period, "description": " ".join(_highlight_lines(lines[index + 1:end]))})
    return result


def _credentials(text: str) -> tuple[list[dict], list[dict], list[dict], list[dict]]:
    educations: list[dict] = []
    awards: list[dict] = []
    languages: list[dict] = []
    certificates: list[dict] = []
    for line in text.splitlines():
        parts = _pipe(line)
        if len(parts) == 5 and parts[0] == "학력":
            educations.append({"school": parts[1], "major": parts[2], "period": _period(parts[3]), "status": parts[4], "gpa": ""})
        elif len(parts) == 4 and parts[0] == "수상":
            awards.append({"title": parts[2], "org": parts[3], "date": parts[1]})
        elif len(parts) == 4 and parts[0] == "어학":
            languages.append({"language": "영어", "test": parts[1], "score": parts[2], "date": parts[3]})
        elif len(parts) == 3 and parts[0] == "자격":
            certificates.append({"name": parts[1], "issuer": "", "date": parts[2]})
    if educations or awards or languages or certificates:
        return educations, awards, languages, certificates
    for line in text.splitlines():
        clean = _clean(line)
        if not clean:
            continue
        if (period := _period(clean)) and "대학교" in clean:
            before = re.sub(_DATE, "", clean).replace("졸업", "").strip()
            fields = re.split(r"\s{2,}", before)
            if len(fields) >= 2:
                educations.append({"school": fields[0], "major": fields[1], "period": period, "status": "졸업" if "졸업" in clean else "", "gpa": ""})
        award = re.match(r"(.+?)\s*—\s*(.+?)\s*\((\d{4}\.\d{2})\)", clean)
        if award and any(word in award.group(1) for word in ("대상", "최우수상", "우수상", "장려상")):
            awards.append({"title": award.group(1), "org": award.group(2), "date": award.group(3)})
        language = re.search(r"(TOEIC\s+Speaking)\s+(.+?)\s*\((\d{4}\.\d{2})\)", clean)
        if language:
            languages.append({"language": "영어", "test": language.group(1), "score": language.group(2), "date": language.group(3)})
        certificate = re.search(r"([^·()]+기능사)\s*\((\d{4}\.\d{2})\)", clean)
        if certificate:
            certificates.append({"name": certificate.group(1).strip(), "issuer": "", "date": certificate.group(2)})
    return educations, awards, languages, certificates


class V3ProfileExtractor(V2ProfileExtractor):
    version = "v3"

    def extract(self, pages: list[str]) -> dict:
        profile = super().extract(pages)
        text = _text("\n".join(pages))
        sections = _sections(text)
        if intro := sections.get("소개"):
            profile["personal"].update(_identity(text, intro))
            if links := _links(text.split("소개", maxsplit=1)[0] + "\n" + intro):
                profile["links"] = links
        if skills := _skill_groups(sections.get("기술 스택", "")):
            profile["skill_groups"] = skills
        if "경력" in sections or "프로젝트" in sections:
            careers, projects = _careers_and_projects(sections.get("경력", ""), sections.get("프로젝트", ""))
            if "경력" in sections:
                profile["careers"] = careers
            if "프로젝트" in sections:
                profile["projects"] = projects
        if "오픈소스 기여" in sections:
            profile["open_source_contributions"] = _open_source(sections["오픈소스 기여"])
        if "외부 활동" in sections:
            profile["activities"] = _activities(sections["외부 활동"])
        if "학력 · 수상 · 자격" in sections:
            profile["educations"], profile["awards"], profile["languages"], profile["certificates"] = _credentials(sections["학력 · 수상 · 자격"])
        return profile
