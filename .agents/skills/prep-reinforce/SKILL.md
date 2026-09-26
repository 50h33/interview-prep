---
name: prep-reinforce
description: 면접에서 부족했던 키워드를 조사해 topics에 보강한다. "오늘 피드백 보강해줘", "이 개념 더 자세히 정리해줘" 요청에 사용한다.
---

상대 링크는 이 `SKILL.md`가 있는 디렉터리를 기준으로 해석하고, 공통 워크플로의 셸 명령은 vault 루트에서 실행한다.

먼저 [AGENTS.md](../../../AGENTS.md)와 [보강 공통 워크플로](../../../workflows/reinforce.md)를 실제로 읽고 모두 따른다. 사용자가 `$prep-reinforce` 뒤에 제공한 텍스트나 자연어 요청의 키워드를 공통 워크플로의 "호출 시 전달된 입력"으로 전달한다.
