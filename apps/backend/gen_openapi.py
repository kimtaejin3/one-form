"""FastAPI OpenAPI 스키마를 openapi.json으로 덤프. 서버 없이 오프라인 생성.
web의 gen:types가 이 파일을 openapi-typescript로 변환한다."""
import json

from app.main import app

with open("openapi.json", "w", encoding="utf-8") as f:
    json.dump(app.openapi(), f, ensure_ascii=False, indent=2)

print("wrote apps/backend/openapi.json")
