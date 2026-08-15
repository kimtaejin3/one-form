from app.core import pdf
from app.profile import service


class _Page:
    def extract_text(self, **_kwargs):
        return """홍길동
이메일: gil@example.com
연락처: 010-1234-5678
https://github.com/gildong
https://portfolio.example.com
"""


class _Reader:
    is_encrypted = False
    pages = [_Page()]

    def __init__(self, _stream):
        pass


def test_profile_from_pdf_extracts_safe_contact_fields(monkeypatch):
    # PDF 텍스트 추출은 app.core.pdf로 옮겼다(companies 공고 수집과 공유).
    monkeypatch.setattr(pdf, "PdfReader", _Reader)

    profile = service.profile_from_pdf(b"pdf bytes")

    assert profile["registered"] is True
    assert profile["personal"]["name"] == "홍길동"
    assert profile["personal"]["email"] == "gil@example.com"
    assert profile["personal"]["phone"] == "010-1234-5678"
    assert profile["links"][0] == {"label": "GitHub", "url": "https://github.com/gildong"}


def test_profile_from_pdf_rejects_empty_file():
    try:
        service.profile_from_pdf(b"")
    except ValueError as exc:
        assert "비어" in str(exc)
    else:
        raise AssertionError("empty PDF must be rejected")


def test_profile_can_be_updated(client):
    profile = client.get("/api/profile").json()
    profile["personal"]["name"] = "수정된 이름"

    response = client.put("/api/profile", json=profile)

    assert response.status_code == 200
    assert response.json()["personal"]["name"] == "수정된 이름"


def test_v2_extracts_structured_saramin_style_resume():
    from app.profile.extractors.v2 import V2ProfileExtractor

    pages = [
        """김태진      신입
주소  (34007) 대전 유성구 봉산로12번길
나의 스킬
Java JavaScript C++ Python TypeScript React Node.js FastAPI Git Docker Kubernetes
MySQL PostgreSQL
학력    대학교(4년) 졸업
2019.03 ~ 2025.08    충남대학교(4년제)         컴퓨터융합학부
""",
        """2026.01 ~ 재직중           라인월드       연구개발팀 · 대리    · SI개발
                        OCPP 기반 전기차 충전소 관제 시스템(CSMS) 유지보수
2024.12 ~ 2025.12       그린다에이아이          개발팀 · 사원   · 프론트엔드
                        다양한 AI 서비스의 프론트엔드 개발 담당
경력기술서                   1) 프로젝트명: AR 얼굴인식 앱 개발
- 수행 기간 : 2025.09 ~ 2026.03
- 사용 언어 및 프레임워크: Swift, TypeScript, React Native, Supabase
- 주요 역할 : 화면 설계 및 서비스 기획
- 업무 성과 : 인식률 약 95% 달성
2) 프로젝트명: OCPP 관제 서버 유지보수
- 수행 기간 : 2026.01 ~ 2026.08
- 주요 역할 : 백엔드 신규 아키텍처 이관 개발
""",
    ]

    profile = V2ProfileExtractor().extract(pages)

    assert profile["personal"]["name"] == "김태진"
    assert profile["personal"]["address"] == "(34007) 대전 유성구 봉산로12번길"
    assert profile["educations"][0]["school"] == "충남대학교(4년제)"
    assert len(profile["careers"]) == 2
    assert profile["careers"][0]["company"] == "라인월드"
    assert len(profile["projects"]) == 2
    assert "React Native" in profile["projects"][0]["stack"]
    assert profile["projects"][0]["role"] == "프로젝트"
    assert "화면 설계" in profile["projects"][0]["summary"]
    assert len(profile["projects"][0]["highlights"]) == 1
    assert profile["projects"][0]["stack"] == ["TypeScript", "React Native", "Supabase", "Swift"]
    assert not any("토스" in highlight for highlight in profile["projects"][1]["highlights"])
