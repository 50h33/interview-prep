@AGENTS.md

# Interview Prep Vault — Claude Code 진입점

이 프로젝트는 Claude Code 혹은 Codex 기반 면접 준비 Vault다. 공통 프로젝트 규칙은 위에서 불러오는 `AGENTS.md`, 파일 형식은 `CONSTRAINTS.md`, 기능별 절차는 `workflows/`를 따른다.

- Claude Code에서는 `.claude/skills/`의 기존 한국어 커맨드를 사용한다. 예: `/오늘질문`, `/모의면접 java`, `/마무리`.
- 스킬의 `$ARGUMENTS`는 공통 워크플로우의 입력으로 전달한다. 다른 도구가 이 치환 문법을 지원한다고 가정하지 않는다.
- 스킬을 실행할 때 해당 SKILL에 연결된 공통 본문을 파일 읽기 도구로 읽는다. SKILL 내부 링크가 자동 import된다고 가정하지 않는다.
- 웹 조회와 파일 작업은 현재 세션에 제공된 도구를 사용한다. 공통 절차와 기록 형식을 여기서 중복 정의하지 않는다.
- Codex 호출과 도구 전환 방법은 `README.md`를 참고한다.
