# Interview Prep Vault — 공통 프로젝트 지침

## 세션 시작 시 읽을 것 (Harness Layer)

모든 세션 시작 시 아래 4개 파일을 **병렬로** 읽는다:
1. `progress/status.md` — 현재 준비 수준, 취약 기술, 우선순위
2. `CONSTRAINTS.md` — 파일 형식 규칙 (파일 생성 전 체크)
3. `progress/entropy.md` — 채워야 할 gaps, 처리할 불일치
4. `progress/memory.md` — 마지막 세션 요약, 미결 사항, 인수인계 메모

`progress/`는 gitignore 대상이라 새로 클론하면 없다. 누락된 파일만 생성하고 기존 기록은 보존한다.
- `status.md`: `type: harness-status`, `updated` frontmatter와 기술별 준비 수준·진행 중인 공고·누적 세션 수·다음 우선순위·Harness 신호의 빈 표/목록.
- `entropy.md`: `type: harness-entropy`, `updated`와 즉시 처리 필요·지식 Gaps·Broken/Orphan Links·Harness 신호·완료 항목의 빈 표.
- `memory.md`: `type: session-memory`, `updated`와 마지막 세션 요약·미결 결정사항·인수인계 메모.
준비 수준, 점수, 이력은 자료가 없으면 빈 값으로 둔다. 프로필 원본을 자동 생성하거나 찾아 읽지 않는다.

세션 종료 시:
- 면접 점수·세션 수는 `workflows/wrap-up.md`의 미처리 완료 회차만 집계하는 규칙으로 갱신
- `progress/memory.md` 마지막 세션 요약 갱신
- 발견된 문제는 `progress/entropy.md`에 기록
- 새 개념/질문은 즉시 해당 `topics/` 파일에 반영

## 파일 접근 범위

- `resume/profile.md`: 요청받은 면접 준비에 필요한 범위에서 읽는다. 이력서 원본(docx/pdf)은 사용자가 요약·프로필 생성을 요청한 경우에만 읽고 `profile.md`를 생성/갱신한다. 원본은 변경하지 않는다.
- `jobs/`: 요청받은 공고 등록·회사별 면접 준비에 필요한 공고를 읽고, 등록·갱신 요청 시 해당 `job.md`를 작성한다. 회사별 면접을 요청하면 해당 회사의 세션 기록을 작성할 수 있다. 관련 없는 공고를 변경하지 않는다.
- `daily/`, `progress/`, `memo/`: 요청된 워크플로우에 따른 기록만 갱신한다. 개인 기록을 공개 문서나 테스트 fixture로 복사하지 않는다.
- `CONSTRAINTS.md`: 파일 형식 규칙의 기준이다. 규칙 자체 변경은 사용자의 명시적 요청/확인이 필요하다.
- 메모 이동은 대상 topics 저장을 확인한 후 원본 삭제를 처리한다. 삭제 요청 또는 해당 삭제에 대한 사용자 확인 없이 자료를 삭제하지 않는다.

---

## 프로젝트 목적
개발자의 취업 면접 대비를 돕는 Claude Code 혹은 Codex 기반 프로젝트.
공고 링크를 받으면 `jobs/` 폴더에 공고별 디렉토리를 만들고, 지원자 프로필과 비교해 맞춤형 면접 준비를 진행한다.

---

## 지원자 프로필

→ `resume/profile.md` 참조 (gitignore 대상 — 직접 작성하거나, 이력서 원본을 넣고 생성 요청)

면접 준비 시 지원자 프로필이 필요하면 `resume/profile.md`를 읽어서 사용한다.
파일이 없으면 프로필 제공 또는 원본 요약 요청이 필요함을 알린다. 사용자가 일반 주제 연습을 요청하면 경험 연결 없이 진행할 수 있으며, 경력·성과·지원 회사를 지어내지 않는다.

---

## 공고 등록 방법
공고 링크를 주면 다음을 자동으로 수행한다:
1. 사용 가능한 웹 페이지 조회 도구로 공고 내용 확인
2. `jobs/{회사명-포지션}/job.md` 파일 생성
3. 공고 기술 스택과 `resume/profile.md` 비교하여 갭 분석 작성
4. 면접 준비 주제 목록 작성

## 면접 세션 진행 방법
- "{회사명} 면접 시작" → 해당 `jobs/{폴더}/job.md` 읽고 세션 진행
- Q&A 전문은 `daily/YYYY-MM-DD.md`에 회차별로 저장한다. 회사별 세션은 `jobs/{회사}/sessions/YYYY-MM-DD-{주제}.md`에 요약과 해당 daily 회차 링크를 추가한다. 같은 내용을 두 군데서 별도 집계하지 않는다.
- 진행 방식: 질문 → 답변 → 꼬리 질문 → 피드백

## 지식 검색 프로토콜 (Knowledge Retrieval Protocol)

면접 질문 생성, 기술 정리, 면접 세션 진행 시 반드시 아래 순서로 실행한다.
이것이 로컬 Knowledge Graph + 웹 검색을 조합하는 Harness Engineering 워크플로우다.

### Step 1 — 로컬 Knowledge Graph 조회 (항상 먼저)
다음 파일들을 병렬로 읽는다:
1. `resume/profile.md` — 지원자 기술 스택 및 경험
2. `topics/{관련기술}/` — 기존에 정리된 개념 및 질문 (`concepts.md` + `questions.md`)
3. 면접 세션인 경우 `jobs/{회사}/job.md` — 공고 요구사항

→ 이미 정리된 내용은 중복 생성하지 않고 기존 내용 위에 쌓는다.

### Step 2 — 웹 검색으로 최신 정보 보강 (항상 실행)
로컬 파일을 읽은 후 반드시 사용 가능한 웹 검색 도구로 아래를 검색한다:
- `{기술명} 백엔드 개발자 면접 질문 {연도}` — 최신 면접 트렌드
- `{기술명} best practices {연도}` — 최신 실무 관행
- 면접 세션인 경우 `{회사명} 기술 스택 개발 문화` — 회사 특화 정보

→ 로컬에 없는 새로운 내용만 출처와 함께 추가한다. 기술 정보는 공식 문서를 우선한다.
웹 도구나 네트워크를 사용할 수 없으면 그 사실을 알리고, 확인된 로컬 자료만으로 가능한 범위를 진행한다. 최신 확인을 했다고 주장하거나 출처를 만들어내지 않는다.

### Step 3 — 통합 및 생성
로컬 지식 + 웹 검색 결과를 조합해서:
- 지원자 경험과 연결된 질문 우선 생성
- 공고 기술 스택 기준으로 비중 조정
- 출제 구성과 진행 순서는 선택한 워크플로우를 따른다. 오늘질문은 기초 2개·중급 1개, daily 기반 모의면접은 미진행 질문을 섞어 진행한다.

### Step 4 — Feedback Loop (세션/정리 후 항상 실행)
세션이나 기술 정리가 끝난 후:
1. 새로 발견된 개념/질문을 `topics/{기술}/` 파일에 추가
2. 새 wikilink 연결이 생겼으면 `home.md` 업데이트
3. Q&A 전문은 daily 회차에 기록하고, 회사별 면접인 경우에만 jobs 세션 문서에 요약과 daily 링크를 추가한다
4. `daily/YYYY-MM-DD.md` 의 각 Q&A 피드백 하단에 관련 `topics/` 파일 wikilink 추가
   - 형식: `- 관련 개념 상세: [[topics/{기술}/questions#{섹션}]] | [[topics/{기술}/concepts#{섹션}]]`
   - 목적: daily 기록에서 개념 상세 페이지로 바로 이동 가능하게 연결

---

## topics/ 자동 업데이트 규칙

`topics/` 는 기술별 개념 정리 및 면접 질문을 누적하는 지식 베이스다.
면접 세션 중 또는 별도 요청 시 아래 규칙에 따라 자동으로 채운다.

### 디렉토리 구조
각 기술 폴더는 두 파일로 구성된다:
- `concepts.md` — 핵심 개념, 동작 원리, 주의할 점
- `questions.md` — 면접 예상 질문 + 모범 답변 방향

### 자동 업데이트 트리거
- 면접 세션에서 특정 기술 주제를 다룬 후 → 해당 `topics/{기술}/` 파일에 내용 추가
- "{기술} 정리해줘" 요청 시 → 사용 가능한 웹 검색 도구로 최신 정보 검색 후 작성
- 새 공고 등록 시 → 공고의 기술 스택 중 비어있는 topics 파일 우선 채우기

### 업데이트 방식
- 기존 내용이 있으면 **덮어쓰지 않고 추가(append)**
- 중복 항목은 병합
- 외부 정보를 추가할 때 하단에 출처 링크 필수 기재

### Obsidian Knowledge Graph 규칙
이 프로젝트는 Obsidian Vault로 열어 Knowledge Graph로 탐색할 수 있다.
파일 작성/수정 시 반드시 아래 규칙을 따른다.

**1. YAML frontmatter 필수**
모든 topics 파일 최상단에 아래 형식으로 작성:
```yaml
---
tags: [기술명, 카테고리]
related: [연관기술1, 연관기술2]
---
```

**2. wikilink로 관계 명시**
- 다른 기술/개념을 언급할 때는 반드시 vault 기준 전체 경로 wikilink 사용
- topics 내 파일 참조: `[[topics/redis/concepts]]`
- 예: "[[topics/redis/concepts]]의 분산 락은 [[topics/mysql/concepts]]의 낙관적 락과 이중 방어선으로 쓰인다"

**3. 링크 방향 기준**
- concepts.md → 관련 기술, 상위 개념, 연관 개념 링크
- questions.md → 해당 concepts.md, 관련 질문 파일 링크
- job.md → 요구하는 기술 topics 링크
- sessions/ → 해당 세션에서 다룬 topics 링크
- daily/ → 각 Q&A 피드백에서 관련 topics/concepts, topics/questions 섹션으로 링크

**4. home.md 업데이트**
새 topics가 추가되거나 job이 등록될 때마다 `home.md`의 해당 섹션에 링크 추가

### 기술 폴더 목록

모든 폴더는 `concepts.md` + `questions.md` 구조
- cs: 운영체제(프로세스/스레드, 컨텍스트 스위칭, 동기화, 가상 메모리, I/O 모델), 자료구조, DB 기초, 네트워크 기초, HTTP/TLS, Nginx vs Tomcat
- java: Java, JVM, Spring Boot, JPA, WebFlux, 동시성
- mysql: 인덱스, 실행 계획, 트랜잭션, 복제
- redis: 자료구조, 캐싱 전략, 분산락(Redisson), pub/sub
- elasticsearch: 역인덱스, 검색 쿼리, nori/Analyzer, RDB와의 차이
- kafka: 메시징 패턴, 파티션, 컨슈머 그룹, Outbox/Inbox, 재처리
- aws: EC2, ECR, S3, Route 53, IAM/OIDC(GitHub Actions 배포)
- kubernetes: 아키텍처(k3s/Helm), 배포 전략, HPA, 장애 대응
- architecture: 분산 시스템(CAP, 분산 트랜잭션, Saga, Outbox, Circuit Breaker) + 시스템 설계(Rate Limiting, 대기열, 실시간 채팅, API 설계)
- ai: RAG, LLM (AX 직무 대비) + Claude Code 워크플로우(서브에이전트, 훅, MCP)

---

## 워크플로우 선택

상세 절차는 아래 공통 본문을 **실제로 읽은 뒤** 실행한다. 기능별 질문 수·순서·채점·저장 규칙은 해당 본문을 기준으로 한다. `CONSTRAINTS.md`의 파일 형식 규칙도 함께 적용한다.

| 자연어 요청/기능 | Claude Code | Codex | 공통 본문 |
|---|---|---|---|
| 오늘 질문 뽑아줘 / 오늘질문 | `/오늘질문` | `$prep-today` | [today](workflows/today.md) |
| 모의면접 시작 / 특정 주제 면접 | `/모의면접` | `$prep-interview` | [interview](workflows/interview.md) |
| 오늘 틀린 것 보강 / 보강 | `/보강` | `$prep-reinforce` | [reinforce](workflows/reinforce.md) |
| 오늘 마무리 / 마무리 | `/마무리` | `$prep-wrap-up` | [wrap-up](workflows/wrap-up.md) |
| 주제 정리 / 기술 정리해줘 | `/주제정리` | `$prep-topic` | [topic](workflows/topic.md) |
| Java 코딩테스트 연습 | `/코딩테스트` | `$prep-coding` | [coding](workflows/coding.md) |
| 마크다운 포맷만 정리 | `/포맷` | `$prep-format` | [format](workflows/format.md) |
| 메모해줘 | `/메모` | `$prep-memo` | [memo](workflows/memo.md) |
| 이번 주 회고 / 주간회고 | `/주간회고` | `$prep-weekly` | [weekly](workflows/weekly.md) |

명령 뒤의 회사명·주제·난이도 등은 워크플로우의 입력이다. 자연어 요청에서는 해당 값만 추출하며 불명확한 필수 입력만 질문한다. 사용자가 이미 대상을 제공하면 다시 묻지 않는다.

## 두 도구 사이 인수인계

- 같은 저장소의 파일을 기준으로 이어간다. 이전 도구의 대화 내역을 알고 있다고 가정하지 않는다.
- 완료된 회차와 저장된 질문·답변만 재개 기준으로 사용한다. 저장되지 않은 답변이나 피드백은 만들지 않는다.
- 같은 날짜의 daily는 읽고 이어 쓰며 기존 질문·답변을 덮어쓰지 않는다.
- 마무리·주간회고의 점수와 세션 수 집계는 `workflows/wrap-up.md`의 처리 내역을 공유한다. 같은 회차를 다시 반영하지 않는다.
- 두 도구가 같은 파일을 동시에 수정하지 않도록 한 작업을 저장한 뒤 전환한다.
- 프로젝트의 면접 워크플로우는 OMX 설치나 tmux 없이도 동작한다. 개인 런타임 설정은 공유 절차에 복사하지 않는다.

## 도구와 운영체제

웹 검색/페이지 조회/파일 읽기·수정은 현재 에이전트에 제공된 도구를 사용한다. 특정 제품의 내부 도구 이름이 없다는 이유로 다른 도구에서 가능한 작업을 중단하지 않는다.

날짜는 실행 환경의 사용자 로컬 날짜를 사용한다. 아래 읽기 전용 명령은 저장소 루트에서 Python 3.9 이상으로 실행하며 PowerShell/Bash에 공통이다:

```text
python scripts/vault_tools.py count-text "답변본문.txt"
python scripts/vault_tools.py changed-topics --date YYYY-MM-DD
python scripts/vault_tools.py check
```

- `count-text`: 모범 답변 본문만 담은 UTF-8 파일을 읽고 BOM·끝 줄바꿈을 제외한다. CRLF는 LF로 정규화하고 공백·문장부호를 포함한 유니코드 문자 수를 센다. 개인정보가 있는 임시 답변 파일은 gitignore된 `daily/` 아래에 둔다.
- `changed-topics`: 파일 수정 시각이 지정한 로컬 날짜인 topics Markdown 경로를 출력한다. Git 변경 목록과는 의미가 다르다.
- 사용자 입력을 셸 명령에 삽입하거나 실행하지 않는다. 파일 내용을 도구로 저장한 뒤 파일 경로만 전달한다.
- Python이 없으면 사용 가능한 도구로 같은 기준을 측정하고 사용한 방법을 알린다. 측정 없이 통과했다고 기록하지 않는다.

## 파일 구조

```text
AGENTS.md                  공통 규칙과 워크플로우 색인
CLAUDE.md                  공통 규칙을 불러오는 Claude Code 진입점
CONSTRAINTS.md             파일 형식·네이밍·링크 규칙
workflows/                 9개 기능의 공통 본문
.claude/skills/            Claude Code 한국어 커맨드 진입점
.agents/skills/            Codex prep-* 스킬 진입점
scripts/vault_tools.py     읽기 전용 검증·측정 도구
tests/                    검증 도구 회귀 테스트
home.md                   Obsidian 허브
topics/{기술}/             concepts.md + questions.md (공개)
daily/                    일일 질문·면접 전문 (비공개)
progress/                 status.md, entropy.md, memory.md (비공개)
memo/                     임시 메모 (README만 공개)
resume/                   이력서 원본과 profile.md (비공개)
jobs/{회사}/               job.md와 sessions/ (비공개)
.omx/                     로컬 OMX 실행 상태 (비공개)
```
