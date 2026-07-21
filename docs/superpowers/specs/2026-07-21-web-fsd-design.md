# web FSD 재구조화 설계

날짜: 2026-07-21

## 목표

`apps/web`을 Feature-Sliced Design(정석 6레이어)으로 재편하고, oxlint
`no-restricted-imports`로 레이어 경계를 강제한다.

## 레이어 구조

```
src/
  main.tsx                     # 진입점
  app/
    App.tsx                    # 라우팅(AppRoutes)
    providers/queryClient.ts   # QueryClient
    styles/index.css           # 전역 스타일
  pages/<page>/ui/<Page>.tsx + index.ts
    jobs, profile, companies, essays, forms, activities, account, settings
  widgets/header/ui/{Header,TabBar}.tsx + index.ts
  features/<feature>/{ui,model}/… + index.ts
    analyze-company, generate-draft, upload-resume, convert-form
  entities/<entity>/{model,api,ui}/… + index.ts
    job(JobCard,JobLogo), profile, essay, activity(ActivityCard)
  shared/
    api/client.ts(api·post) + index.ts
    ui/{Icon,Loading,AsyncBoundary,Dropzone} + index.ts
```

## 의존 방향

`app → pages → widgets → features → entities → shared` (아래로만 의존).
슬라이스는 `index.ts`(public API)로만 노출한다.

## 경계 강제 (oxlint overrides)

각 레이어 파일 glob에서 상위 레이어 import를 `no-restricted-imports`
패턴으로 금지한다. 예: `entities/**`는 `features|widgets|pages|app` import 금지.
한계: 같은 레이어 슬라이스 격리·public API 우회는 경로 패턴 기반이라 부분적.
정밀 강제가 필요하면 이후 eslint-plugin-boundaries로 승급.

## 매핑 (기존 → FSD)

- `api.ts` → `shared/api/client.ts`
- `components/{Icon,Loading,AsyncBoundary,Dropzone}` → `shared/ui/*`
- `queries/{jobs,profile,essays,activities}` + 타입 → `entities/<e>/{api,model}`
- `components/JobLogo` + Jobs 카드 → `entities/job/ui/*`
- Activities 카드 → `entities/activity/ui/ActivityCard`
- Companies/Essays/Profile/Forms의 mutation+액션 UI → `features/*`
- `components/{Header,TabBar}` → `widgets/header/ui/*`
- `pages/*` → `pages/<page>/ui/<Page>.tsx` (feature/entity 조합)
- `App.tsx`, `queryClient.ts`, `index.css` → `app/*`

## 비목표

- 동작·디자인 변경 없음(순수 구조 이동).
- design-system 패키지는 그대로 외부 의존으로 유지.
