from app.core.mock import mock


async def convert_form():
    return await mock({
        "form_name": "지원서_양식.docx",
        "mappings": [
            {"form_field": "성명", "profile_field": "이름", "confidence": 100},
            {"form_field": "학력 사항", "profile_field": "학력", "confidence": 97},
            {"form_field": "경력 및 프로젝트", "profile_field": "STAR 경험 2건", "confidence": 91},
            {"form_field": "자격증", "profile_field": "자격증 3건", "confidence": 99},
            {"form_field": "자기소개", "profile_field": "자소서 허브 초안", "confidence": 78},
        ],
    })
