# Interview Prep Vault — Agent Entry Point

> Claude Code 외 다른 AI 에이전트(Gemini CLI, Kiro, Codex 등)를 위한 범용 진입점.
> Claude Code를 사용한다면 `CLAUDE.md`를 읽을 것 (상세 워크플로우와 스킬은 그쪽이 기준).

---

## Vault 목적

백엔드 개발자 취업 면접 대비 지식 시스템.
지원자 프로필 + 채용 공고 + 기술 지식 베이스를 연결해 맞춤형 면접 준비를 지원한다.

---

## 핵심 파일 (항상 먼저 읽을 것)

1. `progress/status.md` — 기술별 준비 수준 + 다음 우선순위
2. `CONSTRAINTS.md` — 파일 형식 규칙 (파일 생성 전 체크)
3. `progress/entropy.md` — 채워야 할 gaps, 불일치
4. `progress/memory.md` — 마지막 세션 요약 + 미결 사항
5. `resume/profile.md` — 지원자 기술 스택과 경험 (질문 생성 시)

> `progress/`와 `resume/`는 gitignore 대상이라 새로 클론하면 없다. 없으면 빈 템플릿으로 생성하고, 프로필은 사용자에게 요청한다.

---

## 디렉토리 구조

```
{repo}/
├── CLAUDE.md              # Claude Code 전용 진입점
├── AGENTS.md              # 범용 에이전트 진입점 (이 파일)
├── home.md                # Knowledge Graph 허브 (모든 주요 파일 링크)
├── CONSTRAINTS.md         # 아키텍처 제약 (기계 판독형)
├── progress/              # 진행 기록 (비공개)
│   ├── status.md          # 준비 수준
│   ├── entropy.md         # 불일치/gaps 추적
│   └── memory.md          # 세션 간 연속성
├── .claude/skills/        # Claude Code 스킬 (워크플로우 정의 참고용)
├── memo/                  # 빠른 메모 (비공개)
├── topics/                # 기술별 지식 베이스
│   └── {기술}/            # concepts.md + questions.md
├── daily/                 # 일일 면접 기록 (비공개)
├── jobs/                  # 공고별 면접 준비 (비공개)
└── resume/                # 이력서 원본 + profile.md (비공개)
```

---

## 기본 워크플로우

1. **출제** — 프로필·공고·`daily/` 출제 이력을 보고 질문 3개 선정 → `daily/YYYY-MM-DD.md`
2. **면접** — 질문 → 답변 → 꼬리 질문(최대 3) → 피드백·채점(10점) → `daily/`에 전문 기록
3. **보강** — 부족한 키워드를 검색해 `topics/{기술}/`에 append (덮어쓰기 금지)
4. **마무리** — `progress/status.md`, `progress/memory.md` 갱신, 문제는 `progress/entropy.md`에 기록

상세 규칙은 `.claude/skills/{오늘질문,모의면접,보강,마무리}/SKILL.md` 참고.

---

## 파일 작성 규칙 요약

- `topics/` 파일: YAML frontmatter 필수 (`tags`, `related`)
- wikilink 형식: `[[topics/기술명/파일명]]` (경로 포함 필수)
- 외부 정보 추가 시 출처 링크 필수
- 파일 수정 전: `CONSTRAINTS.md` 체크

---

## 접근 금지 영역

- `resume/` — 개인 정보. 사용자가 요청할 때만 이력서 원본으로 `profile.md` 생성
- `jobs/` — 공고 정보
- `CONSTRAINTS.md` — 규칙 자체를 수정하려면 먼저 사용자에게 확인
