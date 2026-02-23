# BossHelp 작업 로그 (WORKLOG)

> 모든 요청사항, 수정사항, 버그 수정을 기록하여 중복 작업을 방지합니다.

---

## 2026-02-23

### [WL-007] 프로덕션 환경변수 설정 수정
- **요청**: Railway 환경변수가 반영되지 않는 문제 해결
- **원인**: pydantic-settings에서 `.env` 파일이 환경변수보다 우선됨
- **수정 파일**:
  - `backend/app/config.py` - ENV=development일 때만 .env 로드
  - `backend/app/api/v1/games.py` - 디버그 엔드포인트 제거
- **커밋**: `1f52d1d`
- **상태**: ✅ 완료

### [WL-006] .dockerignore 추가
- **요청**: Docker 이미지에서 .env 파일 제외
- **수정 파일**: `backend/.dockerignore` 생성
- **커밋**: `41e7b13`
- **상태**: ✅ 완료

### [WL-005] Frontend 게임 목록 DB 연동
- **요청**: 하드코딩된 게임 목록 대신 DB에서 로드
- **수정 파일**:
  - `frontend/src/stores/game-store.ts` - API 호출 추가
  - `frontend/src/lib/api.ts` - snake_case → camelCase 변환
  - `frontend/src/app/page.tsx` - useGames 훅 사용
- **커밋**: `c5bd7c9` ~ `e5e4cd1`
- **상태**: ✅ 완료

### [WL-004] 다크소울 시리즈 데이터 추가
- **요청**: Dark Souls 1/2/3 게임 데이터 크롤링 및 DB 저장
- **수정 파일**:
  - `crawler/crawl_dark_souls_json.py` - 크롤러 스크립트
  - `crawler/crawlers/wiki.py` - Wiki 크롤러 개선
  - Supabase games 테이블 - 3개 게임 추가
- **커밋**: `394fb5a`
- **상태**: ✅ 완료

---

## 2026-02-22

### [WL-003] Railway 배포 설정
- **요청**: Backend를 Railway에 배포
- **수정 파일**:
  - `backend/railway.json` - Railway 설정
  - `backend/Dockerfile` - Docker 빌드 설정
  - `railway.json` (root) - 모노레포 지원
- **커밋**: `ccd6774`, `ae6d334`
- **상태**: ✅ 완료

### [WL-002] Vercel 배포 수정
- **요청**: Frontend Vercel 배포 오류 수정
- **수정 파일**: `frontend/next.config.ts` - standalone 제거
- **커밋**: `55d3138`
- **상태**: ✅ 완료

---

## 2026-02-15

### [WL-001] MVP 초기 릴리스
- **요청**: BossHelp MVP 개발 및 배포
- **내용**: Frontend, Backend, Crawler, Database 전체 구현
- **커밋**: `cfbf650`
- **상태**: ✅ 완료

---

## 미해결 이슈 (TODO)

| ID | 설명 | 우선순위 | 상태 |
|----|------|----------|------|
| TODO-001 | Frontend Mock 데이터 제거 (ask.py, chat-store.ts) | 중간 | 대기 |
| TODO-002 | 게임 상세 페이지 하드코딩 제거 | 낮음 | 대기 |
| TODO-003 | 인기 질문 DB 연동 (현재 Mock) | 낮음 | 대기 |

---

## 기록 규칙

1. **새 작업 시작 시**: 이 파일에 새 항목 추가 (WL-XXX)
2. **작업 완료 시**: 상태를 ✅ 완료로 변경, 커밋 해시 기록
3. **버그 발견 시**: 미해결 이슈에 TODO-XXX로 추가
4. **중요 변경 시**: changelog.md도 함께 업데이트

---

Last updated: 2026-02-23
