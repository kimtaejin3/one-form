from app.core.mock import mock

_NOTIFICATIONS = [
    {"id": 1, "type": "마감", "title": "자소서 마감 임박", "message": "토스 지원 자소서가 D-2입니다. 초안을 마무리해 주세요.", "time": "방금 전", "unread": True},
    {"id": 2, "type": "추천", "title": "새 맞춤 공고 5건", "message": "내 경험과 맞는 백엔드 공고가 도착했어요.", "time": "1시간 전", "unread": True},
    {"id": 3, "type": "합격", "title": "서류 합격", "message": "네이버 검색 플랫폼 백엔드 서류에 합격했습니다.", "time": "3시간 전", "unread": True},
    {"id": 4, "type": "활동", "title": "역량 갭 활동 추천", "message": "부족한 역량을 채울 활동 3건을 확인해보세요.", "time": "어제", "unread": False},
    {"id": 5, "type": "마감", "title": "공고 마감 임박", "message": "라인 메신저 백엔드 공고가 D-5입니다.", "time": "어제", "unread": False},
    {"id": 6, "type": "시스템", "title": "프로필 분석 완료", "message": "업로드한 이력서에서 12개 필드를 추출했어요.", "time": "2일 전", "unread": False},
    {"id": 7, "type": "추천", "title": "기업 브리핑 업데이트", "message": "쿠팡의 최신 사업 동향이 분석에 반영됐어요.", "time": "3일 전", "unread": False},
    {"id": 8, "type": "합격", "title": "면접 일정 등록", "message": "카카오 커머스 1차 면접이 등록되었습니다.", "time": "4일 전", "unread": False},
]


async def list_notifications():
    return await mock(_NOTIFICATIONS)
