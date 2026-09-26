# Interview Prep Vault

Claude Code 혹은 Codex 기반의 백엔드 개발자 면접 대비 프로젝트.
이력서와 공고를 등록하면 사용하는 도구가 맞춤형 면접 질문을 생성하고, 실전처럼 세션을 진행한 뒤 같은 기술 지식 베이스에 누적한다.

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
매일         오늘질문 → 모의면접 → 보강 → 마무리
수시         메모 (떠오른 생각)   주제정리 (원하는 주제 공부)   포맷   코딩테스트
매주         주간회고 (점검 + 다음 주 우선순위)
```

---

## Claude Code와 Codex에서 실행하기

Claude Code는 기존 한국어 슬래시 호출을, Codex는 `prep-` 접두어가 붙은 스킬을 사용한다. 두 도구 모두 “오늘 질문 뽑아줘”, “모의면접 시작해줘”처럼 기능을 분명히 적은 자연어 요청으로도 같은 워크플로우를 실행할 수 있다.

새로 추가되거나 변경된 스킬은 각 도구의 **새 세션**에서 로드한다.

| 기능 | Claude Code | Codex |
|------|-------------|-------|
| 오늘 질문 | `/오늘질문 [회사명]` | `$prep-today [회사명]` |
| 모의면접 | `/모의면접 [주제]` | `$prep-interview [주제]` |
| 보강 | `/보강` | `$prep-reinforce` |
| 마무리 | `/마무리` | `$prep-wrap-up` |
| 주제 정리 | `/주제정리 {주제}` | `$prep-topic {주제}` |
| 코딩 테스트 | `/코딩테스트 [easy\|medium\|hard]` | `$prep-coding [easy\|medium\|hard]` |
| 포맷 | `/포맷` | `$prep-format` |
| 메모 | `/메모` | `$prep-memo` |
| 주간 회고 | `/주간회고` | `$prep-weekly` |

### 매일

| 기능 | 타이밍 | 동작 |
|------|--------|------|
| 오늘 질문 | 하루 시작 | 프로필 + 공고 + 출제 이력 확인 → 오늘의 질문 3개 선정 → `daily/` 기록 |
| 오늘 질문 + 회사명 | 특정 공고 대비 | 해당 공고 기술 스택 기준으로 출제 |
| 모의면접 | 오늘 질문 후 (오늘 daily 파일 필요) | 오늘의 질문 3개로 실전 면접 (질문 → 답변 → 꼬리 질문 → 피드백·채점) |
| 모의면접 + 주제 | 특정 주제 연습 (daily 없이 가능) | 해당 topic의 질문으로 면접 진행 (예: `cs` 주제 모의면접) |
| 보강 | 모의면접 후 (오늘 면접 기록 사용) | 부족했던 키워드를 웹 검색해 `topics/`에 정리 |
| 마무리 | 하루 끝 (마지막에 실행) | 오늘 수정된 문서 linter → memo 점검 → `progress/` 준비 수준·세션 요약 갱신 → 내일 추천 주제 |

### 필요할 때

| 기능 | 동작 |
|------|------|
| 주제 정리 | 주제를 웹 검색해 `topics/`에 개념 + 면접 질문으로 정리 (보강은 오늘 틀린 것, 주제 정리는 원하는 주제) |
| 코딩 테스트 | Java 라이브 코딩 / 화이트보드 테스트 연습 (면접 흐름과 별개) |
| 메모 | 떠오른 아이디어를 `memo/`에 빠르게 캡처 (7일 안에 마무리·주간 회고에서 정리) |
| 주간 회고 | 주 1회. 한 주 점검 + 엔트로피 정리 + 다음 주 우선순위 (다시 풀어보기는 주제 모의면접) |
| 포맷 | 마크다운 포맷만 정리 (내용 변경 없음) |

### 도구를 바꿔서 이어하기

Claude Code와 Codex는 `daily/`, `progress/`, `topics/`, `memo/`에 저장된 기록을 함께 사용한다. 한 도구에서 완료한 회차를 파일에 저장한 뒤 다른 도구의 새 세션을 열면, 다음 도구가 기존 기록을 읽고 이어간다.

- 같은 파일을 두 도구에서 동시에 편집하지 않는다.
- 도구를 바꿀 때는 현재 회차의 질문·답변·피드백이 `daily/`에 기록되었는지 확인한다.
- 완료된 면접 회차를 기준으로 전환한다. 중간에 전환하면 파일에 저장된 내용까지만 복구하며, 저장되지 않은 대화는 추정하지 않는다.
- 마무리는 이미 반영된 회차를 다시 집계하지 않고 새로 완료된 회차만 반영한다.

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
이력서·포트폴리오(docx 또는 pdf)를 `resume/`에 넣고 Claude Code 또는 Codex에 요청한다.
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
Claude Code 또는 Codex에 공고 링크를 붙여넣는다.

```
https://www.wanted.co.kr/wd/xxxxxx
```

사용 중인 도구가 자동으로 수행한다:
- 공고 크롤링 → `jobs/{회사명-포지션}/job.md` 생성
- 내 프로필과 비교한 갭 분석
- 면접 준비 주제 목록 작성

### 4. 면접 준비 루틴

Claude Code:

```
/오늘질문 → /모의면접 → /보강 → /마무리
```

Codex:

```
$prep-today → $prep-interview → $prep-reinforce → $prep-wrap-up
```

단계별로 쌓이는 기록:
- 모의면접 → `daily/YYYY-MM-DD.md`에 Q&A 전문 + 피드백 + 점수, 피드백에서 관련 `topics/` 섹션으로 wikilink 연결
- 보강 → 관련 `topics/` 파일에 새 개념·질문 누적
- 마무리 → `progress/status.md` 기술별 준비 수준, `progress/memory.md` 세션 요약 갱신

> 처음 클론하면 `progress/` 폴더(status.md, entropy.md, memory.md)가 없다 (gitignore). 첫 세션에서 Claude Code 또는 Codex가 빈 템플릿으로 생성한다.

---

## 디렉토리 구조

```
{repo}/
├── AGENTS.md                  # Claude Code와 Codex의 공통 프로젝트 지침
├── CLAUDE.md                  # 공통 지침을 불러오는 Claude Code 진입점
├── README.md                  # 이 파일
├── home.md                    # Obsidian Knowledge Graph 허브
├── CONSTRAINTS.md             # 파일 형식·네이밍·링크 규칙
├── progress/                  # 🔒 진행 기록
│   ├── status.md              # 기술별 준비 수준, 우선순위
│   ├── entropy.md             # 채워야 할 gaps, 불일치 추적
│   └── memory.md              # 세션 간 연속성
├── workflows/                 # 9개 기능의 공통 워크플로우 본문
├── .claude/skills/            # Claude Code용 한국어 스킬 진입점
├── .agents/skills/            # Codex용 prep-* 스킬 진입점
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

---

## 저장소 검증

```bash
python -m unittest discover -s tests
python scripts/vault_tools.py check
```

검증·측정 도구는 Python 3.9 이상에서 별도 패키지 설치 없이 실행한다. `check`는 스킬 메타데이터와 공통 본문 참조를 검사하며, 실제 대화 진행을 대신 검증하지는 않는다.

## 지침과 스킬 형식 참고

- [Codex 프로젝트 지침](https://learn.chatgpt.com/docs/agent-configuration/agents-md)
- [Codex 스킬 검색과 호출](https://learn.chatgpt.com/docs/build-skills)
- [Claude Code 공통 지침 import](https://code.claude.com/docs/en/memory)
- [Claude Code 프로젝트 스킬](https://code.claude.com/docs/en/skills)
