"""v2: 레이아웃 보존 텍스트를 이용하는 한국형 이력서 추출기.

사람인·잡코리아처럼 표와 섹션이 있는 PDF에서 이름, 학력, 경력, 프로젝트, 기술을 우선 구조화한다.
불확실한 값은 추측하지 않고 비워 편집 화면에서 보완하게 한다.
"""
import re

from app.profile.extractors.v1 import V1ProfileExtractor

_DATE_RANGE = r"\d{4}\.\d{2}\s*~\s*(?:\d{4}\.\d{2}|재직중)"
_SKILLS = [
    "JavaScript", "TypeScript", "PostgreSQL", "React Native", "Node.js", "FastAPI", "Docker",
    "Kubernetes", "MySQL", "Supabase", "NestJS", "Express", "WebSocket", "TanStack Query",
    "Python", "React", "Java", "C++", "Swift", "Git", "Vite", "Jest", "MariaDB", "C#", "WPF",
    "mysql2", "Joi", "Ajv", "Kysely", "Harbor", "GitLab", "nginx", "TLS", "mTLS", "OCPP",
    "JSON", "SSE", "Jenkins", "ARKit", "RCTEventEmitter", "SwiftUI", "HTML", "CSS",
]


def _skills(text: str) -> list[str]:
    found: list[str] = []
    for skill in _SKILLS:
        # React Native를 찾았으면 그 안의 React를 별도 기술로 중복 기록하지 않는다.
        if any(skill.lower() in existing.lower() for existing in found):
            continue
        if re.search(re.escape(skill), text, re.IGNORECASE):
            found.append(skill)
    return found


def _clean_lines(text: str) -> list[str]:
    return [re.sub(r"\s+", " ", line).strip() for line in text.splitlines() if line.strip()]


def _normalize_soft_wraps(text: str) -> str:
    """PDF가 단어 중간에서 끊은 줄만 합친다. 불릿 줄과 섹션 줄바꿈은 보존한다."""
    return re.sub(r"(?<=[A-Za-z가-힣])\s*\n\s*(?=[A-Za-z가-힣])", "", text)


def _project_blocks(text: str) -> list[str]:
    matches = list(re.finditer(r"(?:^|\n|경력기술서\s+)\s*\d+\)\s*프로젝트명\s*:\s*(.+)", text))
    section_end = re.compile(r"\n\s*(?:경험/활동/교육|자격/어학/수상|자기소개서|사람인 인[·.]적성검사)")
    blocks = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        boundary = section_end.search(text, match.end(), end)
        if boundary:
            end = boundary.start()
        blocks.append(text[match.start():end])
    return blocks


class V2ProfileExtractor:
    version = "v2"

    def extract(self, pages: list[str]) -> dict:
        profile = V1ProfileExtractor().extract(pages)
        first_page = pages[0] if pages else ""
        all_text = "\n".join(pages)
        personal = profile["personal"]

        name = re.search(r"(?m)^\s*([가-힣]{2,5})\s+(?:신입|경력)", first_page)
        if name:
            personal["name"] = name.group(1)
        address = re.search(r"(?m)^\s*주소\s+(.+)$", first_page)
        if address:
            personal["address"] = address.group(1).strip()

        skill_section = re.search(r"나의 스킬(?P<body>.*?)(?:\n\s*학력|$)", first_page, re.DOTALL)
        profile["projects"] = self._projects(all_text)
        profile["careers"] = self._careers(pages[1] if len(pages) > 1 else "")
        profile["educations"] = self._educations(first_page)
        profile["activities"] = self._activities(pages)
        profile["languages"] = self._languages(all_text)
        profile["awards"] = self._awards(all_text)
        profile["certificates"] = self._certificates(all_text)
        # 스킬은 프로필 전체 매칭의 핵심이므로 경력·프로젝트가 비어도 활동 가능한 형태로 붙인다.
        skills = _skills(skill_section.group("body") if skill_section else all_text)
        if skills and not profile["projects"] and not profile["careers"]:
            profile["projects"] = [{
                "name": "이력서에서 추출한 기술", "role": "", "period": "", "summary": "",
                "highlights": [], "stack": skills,
            }]
        return profile

    def _educations(self, text: str) -> list[dict]:
        result = []
        pattern = re.compile(
            rf"(?m)^\s*({_DATE_RANGE})\s+(.+?대학교(?:\([^)]*\))?)\s{{2,}}(.+)$"
        )
        for match in pattern.finditer(text):
            period, school, major = match.groups()
            tail = text[match.end(): match.end() + 160]
            gpa = re.search(r"학점\s*(\d+(?:\.\d+)?\s*/\s*\d+(?:\.\d+)?)", tail)
            result.append({
                "school": school.strip(), "major": major.strip(), "period": period,
                "status": "졸업" if re.search(r"\n\s*졸업\s*\n", tail) else "",
                "gpa": gpa.group(1) if gpa else "",
            })
        return result

    def _careers(self, text: str) -> list[dict]:
        text = text.split("경력기술서", maxsplit=1)[0]
        lines = [line.rstrip() for line in text.splitlines() if line.strip()]
        result: list[dict] = []
        for index, line in enumerate(lines):
            match = re.match(rf"\s*({_DATE_RANGE})\s+(.+?)\s{{2,}}(.+)$", line)
            if not match:
                continue
            period, company, role = match.groups()
            highlights = []
            for following in lines[index + 1:]:
                if re.match(rf"{_DATE_RANGE}\s+", following) or "프로젝트명:" in following:
                    break
                if following and not following.lstrip().startswith("경력기술서"):
                    highlights.append(re.sub(r"\s+", " ", following).lstrip("- "))
            result.append({
                "company": company.strip(), "role": role.strip(" ·"), "period": period,
                "highlights": highlights[:6], "stack": _skills(" ".join(highlights)),
            })
        return result

    def _projects(self, text: str) -> list[dict]:
        result = []
        for block in _project_blocks(text):
            block = _normalize_soft_wraps(block)
            title = re.search(r"프로젝트명\s*:\s*(.+)", block)
            period = re.search(r"수행 기간\s*:\s*([^\n]+)", block)
            role = re.search(
                r"주요 역할\s*:\s*(.*?)(?=\n\s*-\s*(?:업무 성과|수행 회사|수행 기간)|\n\s*(?:업무 성과|수행 회사|수행 기간)|$)",
                block,
                re.DOTALL,
            )
            if not title:
                continue
            stack_section = re.search(
                r"사용 언어 및 프레임워크\s*:\s*(.*?)(?=\n\s*-\s*주요 역할|\n\s*주요 역할|$)",
                block,
                re.DOTALL,
            )
            stack_text = stack_section.group(1) if stack_section else ""
            stack_lines = {
                re.sub(r"\s+", " ", line).strip().lstrip("- ")
                for line in stack_text.splitlines()
                if line.strip()
            }
            highlights = []
            for line in _clean_lines(block):
                clean = line.lstrip("- ").strip()
                if not clean or "프로젝트명:" in clean:
                    continue
                achievement = re.match(r"(?:업무 성과)\s*:\s*(.+)$", clean)
                if achievement:
                    highlights.append(achievement.group(1).strip())
                    continue
                if re.match(r"(?:수행 기간|수행 회사|사용 언어 및 프레임워크|주요 역할)\s*:", clean):
                    continue
                if clean in stack_lines or clean.startswith("경력기술서"):
                    continue
                highlights.append(clean)
            result.append({
                "name": title.group(1).strip(), "role": "프로젝트",
                "period": period.group(1).strip() if period else "",
                "summary": re.sub(r"\s+", " ", role.group(1)).strip() if role else "",
                "highlights": highlights,
                "stack": _skills(stack_text),
            })
        return result

    def _languages(self, text: str) -> list[dict]:
        match = re.search(r"(\d{4}\.\d{2})\s+(TOEIC\s*Speaking\s*Test)\s+(\d+점/[^\n]+)", text)
        if not match:
            return []
        date, test, score = match.groups()
        return [{"language": "영어", "test": test, "score": score.strip(), "date": date}]

    def _activities(self, pages: list[str]) -> list[dict]:
        text = "\n".join(pages)
        section = re.search(r"경험/활동/교육(?P<body>.*?)자격/어학/수상", text, re.DOTALL)
        if not section:
            return []
        lines = [line.rstrip() for line in section.group("body").splitlines() if line.strip()]
        result = []
        for index, line in enumerate(lines):
            match = re.match(rf"\s*({_DATE_RANGE})\s+(.+?)\s{{2,}}([^\n]+)$", line)
            if not match:
                continue
            period, title, kind = match.groups()
            descriptions = []
            for following in lines[index + 1:]:
                if re.match(rf"\s*{_DATE_RANGE}\s+", following):
                    break
                descriptions.append(re.sub(r"\s+", " ", following).lstrip("- "))
            result.append({
                "type": "교육" if "교육" in kind else "활동", "title": title.strip(), "org": "",
                "period": period, "description": " ".join(descriptions[:4]),
            })
        return result

    def _awards(self, text: str) -> list[dict]:
        result = []
        for line in text.splitlines():
            match = re.match(r"\s*(\d{4}\.\d{2})\s+(.+?)\s{2,}(.+)$", line)
            if not match:
                continue
            date, title, org = match.groups()
            if any(word in title for word in ("대상", "최우수상", "우수상", "장려상")):
                result.append({"title": title.strip(), "org": org.strip(), "date": date})
        return result

    def _certificates(self, text: str) -> list[dict]:
        result = []
        for name, date, issuer in re.findall(r"(?m)^\s*([^\n]+?)\s+(\d{4}\.\d{2})\s+최종합격\s*([^\n]+)", text):
            result.append({"name": name.strip(), "issuer": issuer.strip(), "date": date})
        return result
