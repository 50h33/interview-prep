---
tags: [ai, llm, rag, vector-db, claude-code, mcp, ax]
related: [elasticsearch, kafka, architecture]
---

# AI (LLM / RAG / Claude Code) — 핵심 개념

→ [[home]] | 질문: [[topics/ai/questions]] | 연관: [[topics/elasticsearch/concepts]]

## 1. RAG (Retrieval-Augmented Generation) 파이프라인

LLM 가중치를 바꾸지 않고, 외부 지식을 검색해 프롬프트 컨텍스트에 주입하는 방식.

```
[색인 단계]
문서 → Chunking → Embedding → Vector DB 저장 (+ 메타데이터)

[질의 단계]
질문 → Embedding → 유사 청크 Top-K 검색 → (Re-ranking) → 프롬프트에 주입 → LLM 답변
```

| 컴포넌트 | 역할 | 백엔드 관점 포인트 |
|---|---|---|
| Chunker | 문서를 검색 단위로 분할 | 크기·오버랩이 검색 품질을 좌우 |
| Embedding Model | 텍스트 → 벡터 | 모델을 바꾸면 전체 재색인 필요 |
| Vector DB | 벡터 저장 + ANN 검색 | Qdrant, pgvector, Elasticsearch kNN |
| Retriever | 질문과 가까운 청크 조회 | 벡터 + 키워드 Hybrid 검색 가능 |
| LLM | 컨텍스트 기반 답변 생성 | 타임아웃, 재시도, 비용(토큰) 관리 |

- 원본 문서가 바뀌면 재임베딩 후 upsert → [[topics/elasticsearch/concepts]]의 "CUD 시 색인 동기화"와 같은 문제
- 동기화는 이벤트 기반(Outbox → 임베딩 워커)으로 구성할 수 있음 → [[topics/kafka/concepts]]

---

## 2. 임베딩과 벡터 검색

- **임베딩**: 의미가 비슷한 텍스트가 벡터 공간에서 가깝게 위치하도록 변환한 고정 길이 실수 벡터
- **유사도**: 코사인 유사도(방향), 내적, 유클리드 거리
- **ANN (Approximate Nearest Neighbor)**: 전수 비교(O(N)) 대신 근사 검색
  - **HNSW**: 여러 층의 근접 그래프를 위층부터 탐색 → 빠르지만 메모리 사용 큼
  - 정확도(recall) ↔ 속도·메모리 트레이드오프를 파라미터로 조정
- **메타데이터 필터링**: "직군=백엔드" 같은 조건과 벡터 검색을 함께 적용 (두드림처럼 필터 + 검색이 필요한 서비스에 중요)

---

## 3. Hybrid 검색 (키워드 + 벡터)

| | 키워드 검색 (BM25) | 벡터 검색 |
|---|---|---|
| 강점 | 고유명사, 기술 스택명, 정확한 용어 | 동의어, 표현이 달라도 의미 매칭 |
| 약점 | 동의어·어순 변화에 약함 (사전 필요) | 정확한 키워드 매칭이 약할 수 있음 |
| 구현 | Elasticsearch + nori | Qdrant, ES kNN |

- 두 결과를 합칠 때 **RRF (Reciprocal Rank Fusion)** 같은 순위 결합 방식을 사용
- 두드림에서 구축한 nori + 동의어 사전 analyzer는 Hybrid 검색의 키워드 측에 그대로 활용 가능

---

## 4. LLM 생성 파라미터와 Hallucination

### temperature
```
temperature = 0   → 매 스텝 최고 확률 토큰 선택 (Greedy Decoding에 가까움) → 재현성 ↑
temperature ↑     → 낮은 확률 토큰도 선택 → 다양성 ↑, 사실 오류 위험 ↑
```
- 사실 기반 답변·데이터 추출 → 낮게 (0~0.3)
- 초안 작성·브레인스토밍 → 상대적으로 높게

### Hallucination 줄이는 방법
- **검색 품질**: 청크 크기·오버랩 조정, Re-ranking, Hybrid 검색
- **프롬프트 제약**: "문서에 없으면 모른다고 답하라", 출처 인용 요구
- **구조화 출력**: JSON 스키마로 응답을 받아 서버에서 검증

---

## 5. LLM API를 백엔드에 통합할 때

외부 LLM API는 **느리고(수 초), 비싸고, 실패할 수 있는 외부 의존성**이다.
TicketRush에서 다룬 장애 격리 패턴이 그대로 적용된다 → [[topics/architecture/concepts]]

| 문제 | 대응 |
|---|---|
| 응답 지연 | 짧은 연결 타임아웃 + 긴 읽기 타임아웃 분리, 스트리밍(SSE) 응답 |
| 스레드 점유 | 동기 호출이면 별도 스레드 풀 격리 (Bulkhead), 또는 WebClient 논블로킹 |
| 연속 실패 | Resilience4j 서킷브레이커 → 폴백 응답 |
| 레이트 리밋(429) | 지수 백오프 + 지터 재시도, 요청 큐잉 |
| 비용 | 토큰 사용량 로깅, 동일 질의 캐싱 |

- 두드림의 AI 모집글 초안 생성(Clova API)도 같은 관점으로 설명 가능

---

## 6. Claude Code

터미널/IDE에서 동작하는 **에이전트형 코딩 도구**.
코드 생성뿐 아니라 파일 탐색·편집, 명령 실행, 외부 도구 연동까지 수행한다.

### 주요 기능
- **코드베이스 탐색** — 사전 인덱싱이 아니라 검색·파일 읽기 도구로 필요한 부분을 찾아 파악
- **Plan Mode** — 실행 전 단계별 계획을 작성하고 사용자 승인 대기
- **Subagent** — 특정 작업을 별도 컨텍스트의 에이전트에게 위임 → [[#9. Agent / Subagent]]
- **Hooks** — 도구 실행 전후 등 특정 시점에 셸 명령을 자동 실행 (로깅, 검증)
- **[[#8. MCP (Model Context Protocol)]] 연동** — 외부 서비스와 연결
- **Permission Mode** — 자동 실행 범위 제한

### CLAUDE.md
- Claude Code가 세션 시작 시 **자동으로 로드**하는 프로젝트 지침 파일
- 반복 설명 없이 프로젝트 컨텍스트를 영구적으로 제공
- 위치: `~/.claude/CLAUDE.md` (전역) → 프로젝트 루트 → 서브디렉토리
- 포함할 내용: 기술 스택, 코딩 규칙, 주요 명령어, 파일 구조, 작업 방식

### 경험 연결 — TicketRush AI 개발 워크플로우
- **서브에이전트 분리**: 조사 · 계획 · 검증 역할을 나눠 메인 컨텍스트 오염 방지
- **컨텍스트 관리**: 컨텍스트 사용량 40% 임계 시 작업 메모를 남기고 세션을 이어감
- **훅 기반 작업 로깅**: 도구 실행 기록을 남겨 작업 이력 추적

---

## 7. Claude API

### Context Window
- 한 번의 요청에서 처리할 수 있는 최대 토큰 수 (모델별 수치는 공식 모델 개요 문서 확인 — 자주 바뀜)
- 크다고 항상 좋은 것은 아님: 비용·지연 증가, 긴 컨텍스트 중간 정보를 놓치는 "Lost in the middle" 경향

### Tool Use (Function Calling)
- Claude가 외부 함수/API를 호출할 수 있는 기능
- 흐름: 사용자 메시지 + 도구 정의 → Claude가 tool 호출 결정 → 앱이 실행 → 결과를 Claude에 전달 → 최종 응답
- 독립적인 도구는 **병렬 호출** 가능

### Multimodal
- 텍스트 + 이미지 + PDF 입력 지원

---

## 8. MCP (Model Context Protocol)

AI 도구 통합을 위한 **오픈 표준 프로토콜**.
USB-C처럼 AI 앱이 다양한 외부 서비스와 표준화된 방식으로 연결할 수 있게 한다.

### 핵심 구성 요소
- **Tools** — 실행 가능한 액션 (예: DB 쿼리, 파일 읽기)
- **Resources** — 데이터 소스 접근 (예: API, 파일 시스템)
- **Prompts** — 재사용 가능한 프롬프트 템플릿

### 활용 사례
- Slack 메시지 전송/읽기, GitHub 이슈/PR 관리, DB 직접 쿼리, 웹 검색

---

## 9. Agent / Subagent

### Subagent란
특정 유형의 작업을 전담하는 **특화된 에이전트**.
- 자체 컨텍스트 윈도우에서 독립적으로 실행
- 사용 가능한 도구 제한 가능
- 작업 완료 후 결과를 메인 에이전트에 반환

### 사용 이점
- **컨텍스트 보호** — 탐색/리서치 작업이 메인 대화 컨텍스트를 오염시키지 않음
- **병렬 실행** — 독립적인 여러 작업을 동시에 처리
- **재사용** — 프로젝트 간 에이전트 구성 재사용

### Foreground vs Background
- **Foreground**: 결과가 다음 단계에 필요한 경우 (순차 처리)
- **Background**: 독립적인 작업을 병렬로 실행할 경우

---

## 10. Prompt Engineering

### 핵심 기법
1. **역할 지정 (Role Prompting)** — 시스템 프롬프트에 구체적인 역할 부여
2. **프롬프트 체이닝** — 복잡한 작업을 하위 작업으로 분해, XML 태그로 출력 전달
3. **Few-shot** — 예시로 원하는 출력 형식 명시
4. **Extended Thinking** — 복잡한 문제를 단계적으로 추론
5. **구조화 출력** — JSON 스키마로 받아 서버에서 검증

### Claude에 효과적인 팁
- 긴 문서는 **앞에**, 질문은 **뒤에** 배치
- XML 태그로 입력 구조화 (`<document>`, `<question>`)
- 모호한 지시보다 **구체적이고 제약 조건이 명확한** 지시
- "하지 마라"보다 "이렇게 해라" 형태가 효과적

---

## 참고 링크

- RAG 원 논문: https://arxiv.org/abs/2005.11401
- Qdrant 인덱싱(HNSW): https://qdrant.tech/documentation/concepts/indexing/
- Elasticsearch kNN 검색: https://www.elastic.co/guide/en/elasticsearch/reference/current/knn-search.html
- Claude 모델 개요: https://docs.anthropic.com/ko/docs/about-claude/models/overview
- Claude Code 공식 문서: https://code.claude.com/docs/ko/overview
- Prompt Engineering 가이드: https://platform.claude.com/docs/ko/build-with-claude/prompt-engineering/overview
- MCP 공식 문서: https://modelcontextprotocol.io/docs/getting-started/intro
