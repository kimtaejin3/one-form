export { api, post, put } from './client'
// OpenAPI에서 생성된 백엔드 계약 타입. entities는 이걸 재-export해 손으로 타입을 두지 않는다.
// 갱신: pnpm gen:api (백엔드 스키마 변경 시 프론트가 컴파일 에러로 어긋남을 드러냄).
export type { components } from './schema'
