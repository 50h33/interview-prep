# Claude Interview Prep

Claude Code를 활용한 백엔드 개발자 면접 대비 프로젝트.
이력서와 공고를 등록하면 Claude가 맞춤형 면접 질문을 생성하고, 실전처럼 세션을 진행한 뒤 기술 지식 베이스에 누적한다.

## 특징

- 공고 링크만 주면 기술 스택 분석 + 내 프로필과의 갭 분석 + 준비 주제 생성
- 이력서 기반으로 실제 경험과 연결된 심화/꼬리 질문 생성
- 면접 세션 후 기술별 `concepts.md` / `questions.md` 자동 누적
- 이력서·공고·면접 기록·준비 현황은 gitignore로 로컬에만 보관
- Obsidian Knowledge Graph로 기술 간 연결 시각화

---

## 사용 흐름

```
처음 한 번   공고 링크 붙여넣기 → jobs/에 공고 등록
매일         /오늘질문 → /모의면접 → /보강 → /마무리
수시         /메모 (떠오른 생각)   /주제정리 (원하는 주제 공부)   /포맷   /코딩테스트
매주         /주간회고 (점검 + 다음 주 우선순위)
```

---

## 커맨드

### 매일

| 커맨드 | 타이밍 | 동작 |
|--------|--------|------|
| `/오늘질문` | 하루 시작 | 프로필 + 공고 + 출제 이력 확인 → 오늘의 질문 3개 선정 → `daily/` 기록 |
| `/오늘질문 {회사명}` | 특정 공고 대비 | 해당 공고 기술 스택 기준으로 출제 |
| `/모의면접` | `/오늘질문` 후 (오늘 daily 파일 필요) | 오늘의 질문 3개로 실전 면접 (질문 → 답변 → 꼬리 질문 → 피드백·채점) |
| `/모의면접 {주제}` | 특정 주제 연습 (daily 없이 가능) | 해당 topic의 질문으로 면접 진행 (예: `/모의면접 cs`) |
| `/보강` | `/모의면접` 후 (오늘 면접 기록 사용) | 부족했던 키워드를 웹 검색해 `topics/`에 정리 |
| `/마무리` | 하루 끝 (마지막에 실행) | 오늘 수정된 문서 linter → memo 점검 → `progress/` 준비 수준·세션 요약 갱신 → 내일 추천 주제 |

### 필요할 때

| 커맨드 | 동작 |
|--------|------|
| `/주제정리 {주제}` | 주제를 웹 검색해 `topics/`에 개념 + 면접 질문으로 정리 (`/보강`은 오늘 틀린 것, `/주제정리`는 원하는 주제) |
| `/코딩테스트 [easy\|medium\|hard]` | Java 라이브 코딩 / 화이트보드 테스트 연습 (면접 흐름과 별개) |
| `/메모` | 떠오른 아이디어를 `memo/`에 빠르게 캡처 (7일 안에 `/마무리`·`/주간회고`에서 정리) |
| `/주간회고` | 주 1회. 한 주 점검 + 엔트로피 정리 + 다음 주 우선순위 (다시 풀어보기는 `/모의면접 {주제}`) |
| `/포맷` | 마크다운 포맷만 정리 (내용 변경 없음) |

---

## 시작하기

### 1. 저장소 클론
```bash
git clone {repo_url}
cd {repo}
```

### 2. 프로필 등록
`resume/` 폴더를 만든다. (gitignore 대상이라 git에 올라가지 않는다)

**방법 A — 이력서 원본으로 생성 (추천)**
이력서·포트폴리오(docx 또는 pdf)를 `resume/`에 넣고 Claude에게 요청한다.
```
resume에 넣은 이력서로 profile.md 만들어줘
```

**방법 B — 직접 작성**
`resume/profile.md`를 아래 형식으로 작성한다.

```markdown
# 지원자 프로필

## 기본 정보
- 이름: 홍길동
- 직무: Backend Developer
- 경력: 신입 / N년

## 핵심 강점
- ...

## 기술 스택
- Back-end: ...
- Database: ...
- DevOps: ...

## 프로젝트
### 프로젝트명 (기간)
| 문제 | 원인 | 해결 | 결과 |
|---|---|---|---|
| ... | ... | ... | ... |
```

> 스킬은 `resume/profile.md`만 읽는다. 원본 파일만 두면 이력서 연계 질문이 생성되지 않는다.

### 3. 공고 등록
Claude Code에 공고 링크를 붙여넣는다.

```
https://www.wanted.co.kr/wd/xxxxxx
```

Claude가 자동으로 수행한다:
- 공고 크롤링 → `jobs/{회사명-포지션}/job.md` 생성
- 내 프로필과 비교한 갭 분석
- 면접 준비 주제 목록 작성

### 4. 면접 준비 루틴
```
/오늘질문 → /모의면접 → /보강 → /마무리
```

단계별로 쌓이는 기록:
- `/모의면접` → `daily/YYYY-MM-DD.md`에 Q&A 전문 + 피드백 + 점수, 피드백에서 관련 `topics/` 섹션으로 wikilink 연결
- `/보강` → 관련 `topics/` 파일에 새 개념·질문 누적
- `/마무리` → `progress/status.md` 기술별 준비 수준, `progress/memory.md` 세션 요약 갱신

> 처음 클론하면 `progress/` 폴더(status.md, entropy.md, memory.md)가 없다 (gitignore). 첫 세션에서 Claude가 빈 템플릿으로 생성한다.

---

## 디렉토리 구조

```
{repo}/
├── CLAUDE.md                  # Claude Code 동작 지침
├── AGENTS.md                  # 다른 AI 에이전트용 진입점
├── README.md                  # 이 파일
├── home.md                    # Obsidian Knowledge Graph 허브
├── CONSTRAINTS.md             # 파일 형식·네이밍·링크 규칙
├── progress/                  # 🔒 진행 기록
│   ├── status.md              # 기술별 준비 수준, 우선순위
│   ├── entropy.md             # 채워야 할 gaps, 불일치 추적
│   └── memory.md              # 세션 간 연속성
├── .claude/skills/            # 커맨드 정의 (오늘질문, 모의면접, 마무리 …)
├── topics/                    # 기술별 지식 베이스 (자동 누적)
│   └── {기술명}/
│       ├── concepts.md        # 핵심 개념
│       └── questions.md       # 면접 질문 + 모범 답변
├── memo/                      # 🔒 빠른 메모 (README만 공개)
├── daily/                     # 🔒 일일 면접 기록
├── resume/                    # 🔒 이력서 원본 + profile.md
└── jobs/                      # 🔒 공고별 준비
    └── {회사명-포지션}/
        ├── job.md
        └── sessions/
```

🔒 = `.gitignore` 대상. 개인 정보와 준비 현황(지원 회사, 취약 기술, 점수)은 로컬에만 저장된다.

---

## topics/ 기술 목록

| 분류 | 폴더 | 다루는 내용 |
|------|------|------------|
| CS | `cs` | 운영체제, 자료구조, DB 기초, 네트워크(TCP/IP, HTTP/TLS, Nginx) |
| Language | `java` | JVM, Spring, JPA, WebFlux, 동시성 |
| Database | `mysql` | 인덱스, 실행 계획, 트랜잭션 |
| | `redis` | 자료구조, 캐싱 전략, 분산락 |
| | `elasticsearch` | 역인덱스, nori Analyzer |
| Messaging | `kafka` | 파티션, 컨슈머 그룹, Outbox/Inbox |
| Infra | `kubernetes` | Probe, HPA, 배포 전략 |
| | `aws` | EC2, ECR, Route 53, IAM/OIDC 배포 |
| Architecture | `architecture` | CAP, 분산 트랜잭션, Circuit Breaker, Rate Limiting, 대기열·채팅 설계 |
| AI | `ai` | RAG, LLM Hallucination, Claude Code 워크플로우 |

---

## Obsidian으로 보기

1. [Obsidian](https://obsidian.md) 설치
2. **Open folder as vault** → 이 저장소 폴더 선택
3. `home.md`에서 시작하거나 Graph View(`Ctrl/Cmd + G`)로 전체 연결 확인

wikilink는 `[[topics/{기술}/questions#섹션]]`처럼 vault 기준 전체 경로를 쓴다. `.obsidian/app.json`에 새 링크도 전체 경로로 생성되도록 설정되어 있다.
