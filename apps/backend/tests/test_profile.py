from io import BytesIO
from pathlib import Path
import re

import pytest

from pypdf import PdfWriter
from pypdf.generic import (
    ArrayObject,
    DecodedStreamObject,
    DictionaryObject,
    NameObject,
    NumberObject,
    TextStringObject,
)

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


def _flate_image_pdf(width: int, height: int, data: bytes) -> bytes:
    writer = PdfWriter()
    page = writer.add_blank_page(width=612, height=792)
    image = DecodedStreamObject()
    image.set_data(data)
    image.update(
        {
            NameObject("/Type"): NameObject("/XObject"),
            NameObject("/Subtype"): NameObject("/Image"),
            NameObject("/Width"): NumberObject(width),
            NameObject("/Height"): NumberObject(height),
            NameObject("/ColorSpace"): NameObject("/DeviceRGB"),
            NameObject("/BitsPerComponent"): NumberObject(8),
        }
    )
    page[NameObject("/Resources")] = DictionaryObject(
        {
            NameObject("/XObject"): DictionaryObject(
                {NameObject("/Photo"): writer._add_object(image.flate_encode())}
            )
        }
    )
    stream = BytesIO()
    writer.write(stream)
    return stream.getvalue()


def _supported_and_larger_unsupported_pdf() -> bytes:
    writer = PdfWriter()
    page = writer.add_blank_page(width=612, height=792)

    supported = DecodedStreamObject()
    supported.set_data(b"\xff\x00\x00" * 4)
    supported.update(
        {
            NameObject("/Type"): NameObject("/XObject"),
            NameObject("/Subtype"): NameObject("/Image"),
            NameObject("/Width"): NumberObject(2),
            NameObject("/Height"): NumberObject(2),
            NameObject("/ColorSpace"): NameObject("/DeviceRGB"),
            NameObject("/BitsPerComponent"): NumberObject(8),
        }
    )
    unsupported = DecodedStreamObject()
    unsupported.set_data(b"not-jp2")
    unsupported.update(
        {
            NameObject("/Type"): NameObject("/XObject"),
            NameObject("/Subtype"): NameObject("/Image"),
            NameObject("/Width"): NumberObject(3),
            NameObject("/Height"): NumberObject(3),
            NameObject("/Filter"): NameObject("/JPXDecode"),
        }
    )
    page[NameObject("/Resources")] = DictionaryObject(
        {
            NameObject("/XObject"): DictionaryObject(
                {
                    NameObject("/Supported"): writer._add_object(supported.flate_encode()),
                    NameObject("/Unsupported"): writer._add_object(unsupported),
                }
            )
        }
    )
    stream = BytesIO()
    writer.write(stream)
    return stream.getvalue()


def _inline_image_pdf() -> bytes:
    writer = PdfWriter()
    page = writer.add_blank_page(width=612, height=792)
    content = DecodedStreamObject()
    content.set_data(b"BI /W 2 /H 2 /CS /RGB /BPC 8 ID " + b"\xff\x00\x00" * 4 + b" EI")
    page[NameObject("/Contents")] = writer._add_object(content)
    stream = BytesIO()
    writer.write(stream)
    return stream.getvalue()


def _text_pdf_with_catalog_startxref(text: str) -> bytes:
    writer = PdfWriter()
    page = writer.add_blank_page(width=612, height=792)
    cmap = DecodedStreamObject()
    cmap.set_data(
        b"""/CIDInit /ProcSet findresource begin
12 dict begin begincmap
/CIDSystemInfo << /Registry (Adobe) /Ordering (UCS) /Supplement 0 >> def
/CMapName /Adobe-Identity-UCS def /CMapType 2 def
1 begincodespacerange <0000> <ffff> endcodespacerange
3 beginbfchar <0001> <ae40> <0002> <d0dc> <0003> <c9c4> endbfchar
endcmap CMapName currentdict /CMap defineresource pop end end"""
    )
    descendant = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/CIDFontType2"),
            NameObject("/BaseFont"): NameObject("/NotoSansCJKkr-Regular"),
            NameObject("/CIDSystemInfo"): DictionaryObject(
                {
                    NameObject("/Registry"): TextStringObject("Adobe"),
                    NameObject("/Ordering"): TextStringObject("Identity"),
                    NameObject("/Supplement"): NumberObject(0),
                }
            ),
        }
    )
    font = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type0"),
            NameObject("/BaseFont"): NameObject("/NotoSansCJKkr-Regular"),
            NameObject("/Encoding"): NameObject("/Identity-H"),
            NameObject("/DescendantFonts"): ArrayObject([writer._add_object(descendant)]),
            NameObject("/ToUnicode"): writer._add_object(cmap),
        }
    )
    page[NameObject("/Resources")] = DictionaryObject(
        {NameObject("/Font"): DictionaryObject({NameObject("/F1"): writer._add_object(font)})}
    )
    content = DecodedStreamObject()
    content.set_data(b"BT /F1 12 Tf 72 720 Td <000100020003> Tj ET")
    page[NameObject("/Contents")] = writer._add_object(content)
    stream = BytesIO()
    writer.write(stream)
    damaged = stream.getvalue()
    root_number = int(re.search(rb"/Root (\d+) 0 R", damaged).group(1))
    catalog_offset = damaged.index(f"{root_number} 0 obj".encode())
    return re.sub(rb"(startxref\s+)\d+(\s+%%EOF\s*)$", rb"\g<1>" + str(catalog_offset).encode() + rb"\g<2>", damaged)


def test_profile_from_pdf_extracts_safe_contact_fields(monkeypatch):
    # PDF 텍스트 추출은 app.core.pdf로 옮겼다(companies 공고 수집과 공유).
    monkeypatch.setattr(pdf, "PdfReader", _Reader)

    profile = service.profile_from_pdf(b"pdf bytes")

    assert profile["registered"] is True
    assert profile["personal"]["name"] == "홍길동"
    assert profile["personal"]["email"] == "gil@example.com"
    assert profile["personal"]["phone"] == "010-1234-5678"
    assert profile["personal"]["photo"] == ""
    assert profile["personal"]["headline"] == ""
    assert profile["personal"]["summary"] == ""
    assert profile["skill_groups"] == []
    assert profile["open_source_contributions"] == []
    assert profile["links"][0] == {"label": "GitHub", "url": "https://github.com/gildong"}


def test_profile_from_pdf_uses_extracted_photo(monkeypatch):
    monkeypatch.setattr(pdf, "PdfReader", _Reader)
    monkeypatch.setattr(
        service,
        "pdf_photo_data_url",
        lambda _content: "data:image/jpeg;base64,cGhvdG8=",
    )

    profile = service.profile_from_pdf(b"pdf bytes")

    assert profile["personal"]["photo"] == "data:image/jpeg;base64,cGhvdG8="


def test_pdf_photo_extracts_real_pypdf_image():
    photo = pdf.pdf_photo_data_url(_flate_image_pdf(2, 2, b"\xff\x00\x00" * 4))

    assert photo.startswith("data:image/png;base64,")


def test_pdf_photo_skips_larger_unsupported_format():
    photo = pdf.pdf_photo_data_url(_supported_and_larger_unsupported_pdf())

    assert photo.startswith("data:image/png;base64,")


def test_pdf_photo_extracts_safe_inline_image():
    photo = pdf.pdf_photo_data_url(_inline_image_pdf())

    assert photo.startswith("data:image/png;base64,")


def test_pdf_photo_skips_oversized_image(monkeypatch):
    calls = 0
    original = pdf._xobj_to_image

    def tracked(xobject):
        nonlocal calls
        calls += 1
        return original(xobject)

    monkeypatch.setattr(pdf, "_xobj_to_image", tracked)

    assert pdf.pdf_photo_data_url(_flate_image_pdf(3_000, 3_000, b"compressed")) == ""
    assert calls == 0


def test_pdf_photo_stops_when_decode_budget_is_exhausted(monkeypatch):
    class _PageOnlyReader:
        is_encrypted = False
        pages = [object()]

        def __init__(self, _stream):
            pass

    calls = 0

    def broken_image(_candidate):
        nonlocal calls
        calls += 1
        raise ValueError("broken image")

    monkeypatch.setattr(pdf, "PdfReader", _PageOnlyReader)
    monkeypatch.setattr(
        pdf,
        "_photo_candidates",
        lambda _page: [(8_000_000, "xobject", object())] * 4,
    )
    monkeypatch.setattr(pdf, "_xobj_to_image", broken_image)

    assert pdf.pdf_photo_data_url(b"pdf bytes") == ""
    assert calls == 2


def test_pdf_pages_repairs_wrong_final_startxref():
    damaged = _text_pdf_with_catalog_startxref("김태진")

    assert pdf.pdf_pages(damaged) == ["김태진"]


def test_pdf_pages_rejects_unrepairable_bytes():
    with pytest.raises(ValueError, match="읽을 수 없는 PDF"):
        pdf.pdf_pages(b"%PDF-not-a-real-document")


def test_pdf_pages_rejects_wrong_startxref_in_incremental_pdf():
    base = _text_pdf_with_catalog_startxref("김태진")
    damaged = base + b"\n4 0 obj\n<<>>\nendobj\nxref\n4 1\n0000000000 00000 n \ntrailer\n<< /Size 5 /Prev 0 >>\nstartxref\n" + str(base.index(b"3 0 obj")).encode() + b"\n%%EOF\n"

    with pytest.raises(ValueError, match="읽을 수 없는 PDF"):
        pdf.pdf_pages(damaged)


def test_pdf_pages_rejects_ambiguous_xref_tail():
    damaged = _text_pdf_with_catalog_startxref("김태진") + b"\n5 0 obj\n<</Type /XRef>>\nendobj\n"

    with pytest.raises(ValueError, match="읽을 수 없는 PDF"):
        pdf.pdf_pages(damaged)


def test_pdf_pages_rejects_xref_stream_trailer():
    damaged = _text_pdf_with_catalog_startxref("김태진").replace(
        b"/Info 1 0 R", b"/Info 1 0 R /XRefStm 42"
    )

    with pytest.raises(ValueError, match="읽을 수 없는 PDF"):
        pdf.pdf_pages(damaged)


def test_pdf_pages_rejects_non_catalog_startxref_target():
    damaged = _text_pdf_with_catalog_startxref("김태진")
    pages_offset = damaged.index(b"2 0 obj")
    damaged = re.sub(
        rb"(startxref\s+)\d+(\s+%%EOF\s*)$",
        rb"\g<1>" + str(pages_offset).encode() + rb"\g<2>",
        damaged,
    )

    with pytest.raises(ValueError, match="읽을 수 없는 PDF"):
        pdf.pdf_pages(damaged)


def test_pdf_pages_rejects_string_key_decoys():
    damaged = _text_pdf_with_catalog_startxref("김태진").replace(
        b"/Info 1 0 R", b"/Dummy (/Root 99 0 R) /Info 1 0 R"
    )

    with pytest.raises(ValueError, match="읽을 수 없는 PDF"):
        pdf.pdf_pages(damaged)


def test_pdf_pages_rejects_catalog_generation_mismatch():
    damaged = _text_pdf_with_catalog_startxref("김태진").replace(b"3 0 obj", b"3 1 obj", 1)

    with pytest.raises(ValueError, match="읽을 수 없는 PDF"):
        pdf.pdf_pages(damaged)


@pytest.mark.parametrize("replacement", [b"00001 n", b"0000000114 00000 n"])
def test_pdf_pages_rejects_mismatched_xref_entry(replacement):
    damaged = _text_pdf_with_catalog_startxref("김태진")
    catalog_offset = damaged.index(b"3 0 obj")
    entry = f"{catalog_offset:010d} 00000 n".encode()
    damaged = damaged.replace(entry, replacement, 1)

    with pytest.raises(ValueError, match="읽을 수 없는 PDF"):
        pdf.pdf_pages(damaged)


def test_pdf_repair_allows_only_line_break_before_catalog():
    damaged = _text_pdf_with_catalog_startxref("김태진")
    root_number = int(re.search(rb"/Root (\d+) 0 R", damaged).group(1))
    catalog_offset = damaged.index(f"{root_number} 0 obj".encode())
    entry = f"{catalog_offset:010d} 00000 n".encode()
    damaged = damaged.replace(entry, f"{catalog_offset - 1:010d} 00000 n".encode(), 1)
    damaged = re.sub(
        rb"(startxref\s+)\d+(\s+%%EOF\s*)$",
        rb"\g<1>" + str(catalog_offset - 1).encode() + rb"\g<2>",
        damaged,
    )

    assert damaged[catalog_offset - 1 : catalog_offset] in (b"\n", b"\r")
    assert pdf.pdf_pages(damaged) == ["김태진"]


@pytest.mark.parametrize(
    "old,new",
    [
        (b"/Type /Catalog", b"% /Type /Catalog"),
        (b"/Type /Catalog", b"%% /Type /Catalog"),
        (b"/Info 1 0 R", b"/Info 1 0 R /Prev abcdef"),
        (b"/Info 1 0 R", b"/Info 1 0 R /Prev 1abc"),
        (b"xref\n0 9", b"xref\n4 9"),
    ],
)
def test_pdf_repair_rejects_unverified_xref_tokens(old, new):
    damaged = _text_pdf_with_catalog_startxref("김태진").replace(old, new, 1)

    assert pdf._repair_final_startxref(damaged) == damaged


@pytest.mark.parametrize("suffix", [b"Real", b"R.", b"R_", b"R-"])
def test_pdf_repair_rejects_root_token_prefix(suffix):
    damaged = _text_pdf_with_catalog_startxref("김태진")
    damaged = re.sub(rb"(/Root\s+\d+\s+0\s+)R", rb"\1" + suffix, damaged, count=1)

    assert pdf._repair_final_startxref(damaged) == damaged


def test_pdf_reader_retries_once_without_mutating_input(monkeypatch):
    damaged = _text_pdf_with_catalog_startxref("김태진")
    original = bytes(damaged)
    attempts = []

    class RetryReader:
        def __init__(self, stream):
            attempts.append(stream.read())
            if len(attempts) == 1:
                raise ValueError("bad startxref")

    monkeypatch.setattr(pdf, "PdfReader", RetryReader)

    pdf._pdf_reader(damaged)

    assert damaged == original
    assert len(attempts) == 2
    assert attempts[0] == original
    assert attempts[1] != original


def test_profile_from_pdf_rejects_empty_file():
    try:
        service.profile_from_pdf(b"")
    except ValueError as exc:
        assert "비어" in str(exc)
    else:
        raise AssertionError("empty PDF must be rejected")


def test_profile_can_be_updated(client):
    profile = client.get("/api/profile").json()
    profile["personal"]["headline"] = "Node.js 기반 풀스택 개발자"
    profile["skill_groups"] = [{"category": "언어", "skills": ["TypeScript", "Python"]}]
    profile["open_source_contributions"] = [{
        "repository": "nodejs/node",
        "url": "https://github.com/nodejs/node",
        "highlights": ["vm.compileFunction 매개변수 검증 개선"],
    }]

    response = client.put("/api/profile", json=profile)

    assert response.status_code == 200
    assert response.json()["personal"]["headline"] == "Node.js 기반 풀스택 개발자"
    assert response.json()["skill_groups"] == [{"category": "언어", "skills": ["TypeScript", "Python"]}]
    assert response.json()["open_source_contributions"] == [{
        "repository": "nodejs/node",
        "url": "https://github.com/nodejs/node",
        "highlights": ["vm.compileFunction 매개변수 검증 개선"],
    }]


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


def test_v3_extracts_section_based_resume():
    from app.profile.extractors.registry import get_profile_extractor
    from app.profile.extractors.v1 import V1ProfileExtractor
    from app.profile.extractors.v2 import V2ProfileExtractor
    from app.profile.extractors.v3 import V3ProfileExtractor

    fixture = (Path(__file__).parent / "fixtures" / "modern_resume.txt").read_text()
    profile = V3ProfileExtractor().extract(fixture.split("\f"))

    assert profile["personal"]["name"] == "김태진"
    assert profile["personal"]["name_en"] == "Taejin Kim"
    assert profile["personal"]["headline"] == "Node.js 기반 풀스택 개발자"
    assert profile["personal"]["summary"].startswith("Node.js 생태계를 중심으로")
    assert profile["personal"]["address"] == "서울특별시 예시구"
    assert profile["personal"]["phone"] == "010-0000-0000"
    assert profile["personal"]["email"] == "developer@example.com"
    assert profile["links"] == [
        {"label": "GitHub", "url": "https://github.com/kimtaejin3"},
        {"label": "LinkedIn", "url": "https://linkedin.com/in/example-developer"},
        {"label": "포트폴리오", "url": "https://portfolio.example.com"},
        {"label": "GitHub", "url": "https://github.com/eslint/eslint"},
    ]
    assert profile["skill_groups"] == [
        {"category": "언어", "skills": ["TypeScript", "JavaScript", "Python"]},
        {"category": "프론트엔드", "skills": ["React", "Vite"]},
        {"category": "백엔드", "skills": ["Node.js", "FastAPI"]},
        {"category": "데이터베이스", "skills": ["PostgreSQL", "MySQL"]},
        {"category": "도구", "skills": ["Docker", "Git"]},
    ]
    assert [career["company"] for career in profile["careers"]] == ["라인월드", "그린다에이아이"]
    assert any(project["name"] == "push-on" for project in profile["projects"])
    assert any(project["organization"] == "라인월드" for project in profile["projects"])
    assert [item["repository"] for item in profile["open_source_contributions"]] == [
        "nodejs/node",
        "eslint/eslint",
    ]
    assert len(profile["activities"]) == 3
    assert profile["activities"][1]["description"] == "기술 세미나를 진행했습니다."
    assert profile["activities"][2]["title"] == "웹 접근성 과정"
    assert profile["activities"][2]["period"] == "2021.07"
    assert profile["educations"][0]["school"] == "충남대학교"
    assert profile["educations"][1] == {
        "school": "예시대학교",
        "major": "소프트웨어학과",
        "period": "2019.03 ~ 2023.02",
        "status": "졸업",
        "gpa": "",
    }
    assert len(profile["awards"]) == 2
    assert profile["languages"][0]["test"] == "TOEIC Speaking"
    assert profile["certificates"][0]["name"] == "정보처리기능사"
    assert isinstance(get_profile_extractor("v1"), V1ProfileExtractor)
    assert isinstance(get_profile_extractor("v2"), V2ProfileExtractor)
    assert isinstance(get_profile_extractor("v3"), V3ProfileExtractor)


def test_v3_keeps_bare_repository_names():
    from app.profile.extractors.v3 import V3ProfileExtractor

    profile = V3ProfileExtractor().extract(["""오픈소스 기여
react-hook-form
- 성능을 개선했습니다.
react-icons
- 아이콘을 갱신했습니다.
"""])

    assert [item["repository"] for item in profile["open_source_contributions"]] == [
        "react-hook-form",
        "react-icons",
    ]


def test_v3_preserves_v2_certificate_when_credentials_are_unrecognized():
    from app.profile.extractors.v3 import V3ProfileExtractor

    profile = V3ProfileExtractor().extract(["""예시 자격증 2024.01 최종합격 예시기관
학력 · 수상 · 자격
Certifications
"""])

    assert profile["certificates"] == [{"name": "예시 자격증", "issuer": "예시기관", "date": "2024.01"}]


def test_v3_maps_career_projects_to_their_career_organization():
    from app.profile.extractors.v3 import V3ProfileExtractor

    fixture = (Path(__file__).parent / "fixtures" / "career_projects.txt").read_text()
    profile = V3ProfileExtractor().extract([fixture])

    assert [(project["name"], project["organization"]) for project in profile["projects"]] == [
        ("주문 API 재구축", "알파소프트"),
        ("운영 대시보드 개선", "베타랩"),
        ("독립 배포 도구", "개인 프로젝트"),
    ]


def test_v3_preserves_v2_activities_when_pipe_activity_is_malformed():
    from app.profile.extractors.v3 import V3ProfileExtractor

    profile = V3ProfileExtractor().extract(["""경험/활동/교육
2024.01 ~ 2024.02  기존 교육 활동  교육
자격/어학/수상
외부 활동
교육 |  | 예시기관 | 2024.03
"""])

    assert profile["activities"] == [{
        "type": "교육", "title": "기존 교육 활동", "org": "",
        "period": "2024.01 ~ 2024.02", "description": "",
    }]
