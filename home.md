---
tags: [home, index]
---

# Interview Prep — Home

> 이 파일이 Knowledge Graph의 중앙 허브입니다.
> Obsidian에서 열면 모든 노트의 연결 관계를 그래프로 볼 수 있습니다.

---

## 진행 기록 / 규칙
- [[progress/status]] — 현재 준비 수준, 취약 기술, 우선순위
- [[progress/entropy]] — 채워야 할 gaps, 불일치 추적
- [[progress/memory]] — 마지막 세션 요약, 미결 사항
- [[CONSTRAINTS]] — 아키텍처 제약, 파일 형식 규칙

## 지원자 프로필
- [[resume/profile]] — 기술 스택, 대표 성과, 경력

---

## 지원 공고
<!-- 공고 등록 시 [[jobs/{회사-포지션}/job]] 형식으로 추가 -->

---

## 기술 지식 베이스

### CS 기초
- [[topics/cs/concepts]] / [[topics/cs/questions]] — 운영체제, 자료구조, 데이터베이스 기초, 네트워크(TCP/IP, HTTP/TLS, Nginx vs Tomcat)

### Backend — Java / Spring
- [[topics/java/concepts]] / [[topics/java/questions]]
- 기초 학습: [[topics/java/concepts#동시성 기초 — 확인과 변경 사이의 경쟁 상태]] → [[topics/java/questions#Java 동시성 제어]]

### Database
- [[topics/mysql/concepts]] / [[topics/mysql/questions]]
- 성능 검증: [[topics/mysql/concepts#3. 커버링 인덱스 (Covering Index)]] → [[topics/mysql/concepts#EXPLAIN과 EXPLAIN ANALYZE의 차이]]
- [[topics/redis/concepts]] / [[topics/redis/questions]]
- 대기열: [[topics/redis/concepts#대기열의 순위와 입장 허용선]] → [[topics/redis/questions#Redis Sorted Set(ZSet)을 활용한 가상 대기열 시스템을 설계해주세요.]]
- 응답 최적화: [[topics/redis/concepts#JSON 문자열 캐싱과 HTTP gzip]] → [[topics/redis/questions#JSON 문자열 캐싱과 gzip의 목적 구분]]
- 캐시 최신성: [[topics/redis/concepts#상태 변경 후 캐시 무효화]] → [[topics/redis/questions#Cache-Aside 패턴과 write-around 캐시 무효화 순서]]
- 기초 학습: [[topics/redis/concepts#락 임대 시간과 업무상 선점 유효 시간]] → [[topics/redis/questions#기초 이해 확인 — 락 만료와 선점 상태]]
- [[topics/elasticsearch/concepts]] / [[topics/elasticsearch/questions]]

### Messaging & Coordination
- [[topics/kafka/concepts]] / [[topics/kafka/questions]]
- 기초 학습: [[topics/kafka/concepts#기초 — DB 저장과 이벤트 전달은 별개다]]
- 후속 학습: [[topics/kafka/concepts#Inbox 패턴 (컨슈머 멱등성)]] → [[topics/kafka/concepts#Outbox와 소비자 처리의 트랜잭션 경계]]
- [[topics/aws/concepts]] / [[topics/aws/questions]] — EC2, ECR, Route 53, IAM/OIDC 배포

### Infrastructure
- [[topics/kubernetes/concepts]] / [[topics/kubernetes/questions]]

### Architecture
- [[topics/architecture/concepts]] / [[topics/architecture/questions]] — CAP, 분산 트랜잭션·Saga·Outbox, Circuit Breaker, Rate Limiting, 채팅·대기열 설계
- 기초 학습: [[topics/architecture/concepts#Saga 보상과 DB 롤백의 차이]]
- 성능 지표: [[topics/architecture/concepts#응답 시간의 평균과 p95]] → [[topics/architecture/questions#응답 시간 p95의 의미]]

### AI
- [[topics/ai/concepts]] / [[topics/ai/questions]] — RAG, LLM, Claude Code 워크플로우

---

## 기술 관계 맵

```
[kubernetes] ──함께사용── [docker]
[redis] ──관련── [분산락]
```
