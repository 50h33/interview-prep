---
tags: [architecture, distributed-systems, system-design, msa, backend]
related: [kafka, redis, kubernetes, mysql, java, cs, ai]
---

# Architecture — 분산 시스템 & 시스템 설계 핵심 개념

→ [[home]] | 질문 모음: [[topics/architecture/questions]]

---

## CAP 정리 (CAP Theorem)

분산 시스템은 아래 세 속성을 **동시에 모두 만족할 수 없고**, 최대 2개만 선택 가능하다.

| 속성 | 설명 |
|------|------|
| **C — Consistency** | 모든 노드가 동시에 같은 데이터를 봄. 쓰기 후 읽기 시 항상 최신값 반환 |
| **A — Availability** | 모든 요청에 응답 반환 (오류 없이). 단, 최신 데이터가 아닐 수 있음 |
| **P — Partition Tolerance** | 네트워크 단절이 발생해도 시스템이 계속 동작 |

### 왜 2개만 가능한가

네트워크 파티션은 실제로 반드시 발생 → **P는 포기 불가** → CP 또는 AP 선택

```
네트워크 단절 발생
  ├── 일관성 유지 (CP): 일부 노드 응답 거부 → Availability 희생
  └── 가용성 유지 (AP): stale 데이터 반환 → Consistency 희생
```

### CP vs AP 예시

| 분류 | 시스템 | 특징 |
|------|--------|------|
| **CP** | ZooKeeper, HBase, etcd | 파티션 시 쓰기 거부. 리더 선출 중 불가 |
| **AP** | Cassandra, DynamoDB, CouchDB | 파티션 시 계속 응답. eventual consistency |
| **CP** | [[topics/kafka/concepts\|Kafka]] | 리더 복제 완료 후 커밋 → 일관성 우선 |
| **AP** | [[topics/redis/concepts\|Redis Cluster]] | 파티션 시 stale 데이터 반환 가능 |

### 실제 시스템에 적용하면

- **ZooKeeper**: CP 시스템. 리더 선출 중 쓰기 불가 → 일관성 우선 선택
- **[[topics/redis/concepts\|Redis]]**: AP에 가까움. Cluster 파티션 시 stale 데이터 가능 → 캐시 용도에 적합

> 참고: [[topics/architecture/questions#CAP 정리(CAP Theorem)란 무엇인가요? 왜 2개만 선택할 수 있나요?]]

---

## 라이브 스트리밍 채팅 아키텍처

### 기술 선택 기준 (동시 10만 명 기준)

| 컴포넌트 | 선택 | 이유 |
|---|---|---|
| 서버 | **Spring WebFlux(Netty)** 또는 **Spring WebSocket(STOMP)** | 연결은 많고 전송은 적은 채팅은 event loop 모델이 적은 스레드로 커넥션 유지에 유리 |
| 서버간 브로드캐스트 | **[[topics/redis/concepts\|Redis]] pub/sub** | push 기반, 채팅방 = topic, 낮은 지연 |
| 메시지 영속 저장 | **MongoDB** | 메타데이터 스키마 유연성, 날짜/채팅방 인덱스 |
| 오케스트레이션 | **[[topics/kubernetes/concepts\|Kubernetes]]** | active connection 기반 HPA, 수평 확장 |

### [[topics/redis/concepts\|Redis]] pub/sub vs Redis Streams

| | pub/sub | Streams |
|---|---|---|
| 메시지 영속성 | 없음 (구독자 부재 시 유실) | 있음 (log 구조로 저장) |
| 재처리 | 불가 | 가능 (XREAD + consumer group) |
| 사용 시나리오 | 실시간성 우선, 유실 허용 | 메시지 손실 불허 시 |

**유실 허용 시 보완 전략**: 클라이언트 재연결 시 MongoDB에서 최근 N개 메시지 fetch

### K8s WebSocket Graceful Shutdown

WebSocket 서버 Pod 교체 시 기존 커넥션 처리:

```yaml
terminationGracePeriodSeconds: 300  # WebSocket 평균 세션 길이 기준
lifecycle:
  preStop:
    exec:
      command: ["/bin/sh", "-c", "sleep 5"]  # endpoints 제거 시간 확보
```

**흐름:**
1. `kubectl rollout` 시작 → readinessProbe 실패
2. Service endpoints에서 Pod 제거 (신규 연결 차단)
3. 기존 WebSocket 커넥션 자연 종료 대기
4. `terminationGracePeriodSeconds` 초과 시 강제 종료

**실무 포인트**: 결제, 좌석 선점 등 민감한 WebSocket은 강제 종료 절대 불가 → grace period를 충분히 설정

### HPA Scale-out 기준

- **CPU 기준** (권장): 트래픽 부하와 직접 연동
- **active connection 기준**: Custom Metrics 필요하지만 채팅 서버에 직관적
- **Memory 지양**: memory leak 등으로 선형 증가 가능, 트래픽과 무관한 증가 판별 어려움
- k6 부하 테스트로 p95/p99 latency가 늘어나는 RPS 측정 후 임계치 설정

---

## 10만 동시접속 채팅 서버 심화 설계

### 서버 용량 계산

- WebSocket 연결 1개 ≈ 2~4KB 메모리 (헤더, 버퍼 포함)
- 10만 커넥션 ≈ 200~400MB → 메모리는 병목 아님
- **실제 병목: CPU** (브로드캐스트, pub/sub 오버헤드)
- 실무 기준: 서버 1대당 안정적 처리 용량 ≈ 5만~8만 커넥션
- 10만 명 → 최소 2대, 장애 대비 **3대 이상** 권장

OS 레벨 튜닝 (Linux):
```bash
# 파일 디스크립터 한도 증가 (기본 1024 → 100만)
ulimit -n 1000000
# /etc/sysctl.conf
net.core.somaxconn = 65535
net.ipv4.ip_local_port_range = 1024 65535
```

### 서버 간 브로드캐스트 옵션 비교

| | Redis pub/sub | Kafka | NATS |
|---|---|---|---|
| 레이턴시 | 1ms 이하 | 10~50ms | 1ms 이하 |
| 메시지 지속성 | 없음 | 있음 | JetStream으로 가능 |
| 구현 복잡도 | 낮음 | 높음 | 중간 |
| 적합한 케이스 | 라이브 채팅(유실 허용) | 일반 채팅(히스토리 필요) | 경량 고속 브로드캐스트 |

**실제 사례:**
- **LINE LIVE**: Redis pub/sub으로 100대+ 채팅 서버 간 브로드캐스트, MySQL은 배치로 영속 저장
- **Slack**: Kafka로 메시지 순서 보장 + 히스토리

### Hot Partition 문제와 해결

**문제**: 인기 채팅방(아이돌 라이브, 스포츠 중계)에 트래픽 집중 → 특정 서버/Redis 인스턴스 과부하

**해결 전략:**

1. **Consistent Hashing**: 채팅방 ID 해싱으로 여러 서버/Redis에 균등 분산
2. **채팅방 자동 분할**: 동시접속 임계치 초과 시 같은 방을 복수의 서브룸으로 분할 (LINE LIVE 방식)
3. **다중 Redis 샤딩**: 채팅방을 Redis 인스턴스별로 분산
   ```
   Redis1: room_id % 3 == 0
   Redis2: room_id % 3 == 1
   Redis3: room_id % 3 == 2
   ```

### 메시지 순서 보장

**Kafka 사용 시**: `room_id`를 key로 설정 → 같은 채팅방 메시지는 항상 같은 파티션 → 파티션 내 순서 보장

**Redis pub/sub 사용 시**: 애플리케이션 레벨에서 Sequence Number 부여
```java
// 메시지 발행 시 atomic 증가 시퀀스 번호 부여 (Spring Data Redis)
Long seq = redisTemplate.opsForValue().increment("room:" + roomId + ":seq");
ChatMessage msg = new ChatMessage(seq, content);
redisTemplate.convertAndSend("room:" + roomId, msg);
```
- 클라이언트가 seq 기준으로 재정렬
- 갭 발생 시 누락된 메시지를 DB에서 fetch

### 재연결 시 미수신 메시지 처리

**패턴**: 클라이언트가 마지막 수신 seq를 기억 → 재연결 시 서버에 전달 → 그 이후 메시지를 DB/Redis에서 보충

```
클라이언트: { type: "RECONNECT", lastSeq: 1523, roomId: "room_001" }
서버: MongoDB/Redis에서 seq > 1523인 메시지 최대 500개 fetch → 전송
이후: 실시간 pub/sub 구독 재개
```

**버퍼 전략**:
- 인메모리 circular buffer (최근 500~1000개) → 단기 재연결용
- MongoDB/Redis Streams → 장기 히스토리 조회용
- TTL: 인메모리는 5분, DB는 90일

**재연결 백오프 (Thundering Herd 방지)**:
```
1차 재연결: 500ms
2차: 1000ms + random jitter
3차: 2000ms + random jitter
...최대 30초
```

### Sticky Session vs Stateless 선택

| | Sticky Session | Stateless (Redis 공유) |
|---|---|---|
| 규모 | 소규모(~1만) | 중~대규모 |
| 서버 장애 시 | 해당 서버 클라이언트 전부 재연결 | 다른 서버로 자동 이동 |
| 배포 시 | Rolling 중 재연결 강요 | 자연스러운 재연결 |
| 구현 복잡도 | 낮음 | 높음 |

**실무 권장**: 대규모에서는 Redis에 세션 상태 저장 + 어느 서버에서든 처리 가능한 Stateless 설계

> 출처: https://engineering.linecorp.com/ko/blog/the-architecture-behind-chatting-on-line-live

---

## 채팅 서버 동시성 모델 비교 — MVC / WebFlux / Virtual Thread

| | **Spring MVC + STOMP (Tomcat)** | **Spring WebFlux (Netty)** | **MVC + Virtual Thread** |
|---|---|---|---|
| 커넥션 처리 | 요청 스레드 풀 + WebSocket 세션 | event loop 소수 스레드 | 요청당 가상 스레드 |
| 블로킹 코드 | 허용 (스레드 점유) | 금지 — event loop 블로킹 시 전체 지연 | 허용 (가상 스레드만 파킹) |
| 코드 가독성 | 동기 스타일 | Reactive 체인 — 복잡도 높음 | 동기 스타일 |
| 서버 간 확장 | 외부 브로커 relay 또는 Redis pub/sub | Redis pub/sub | 외부 브로커 relay 또는 Redis pub/sub |

**WebFlux의 핵심 위험**: DB/Redis 호출 등 모든 I/O를 non-blocking API로 써야 함. 규칙을 어기면 event loop 블로킹 → 전체 응답 지연.

**경험 연결**: 두드림에서는 DAU 5천(피크 50 RPS) 규모라 Spring WebSocket(STOMP) 단일 서버로 충분했고, 다중 서버 브로드캐스트는 Redis Pub/Sub 경로만 준비(미검증). TicketRush에서는 좌석 상태 SSE 팬아웃이 병목이 되는 것을 대조 테스트로 확인 → 대기열은 서버 지시 폴링 + 지터로 설계.

**결론**: 규모가 작으면 MVC + STOMP가 운영 비용이 낮고, 수만~10만 동시접속이면 WebFlux 또는 Virtual Thread + 외부 브로커로 커넥션당 비용을 낮춘다. 선택 전에 k6로 커넥션 수 대비 p95를 측정한다.

> 관련: [[topics/java/concepts#Spring WebFlux / Spring Cloud Gateway]]

---

## 투표/경매 — 메시지 유실 불허 케이스

채팅(유실 허용)과 투표/경매(유실 불허)를 같은 실시간 시스템에서 처리하는 **이중 채널 전략**.

### 채널 분리 아키텍처

```
클라이언트
  ├── 채팅 메시지       → Redis pub/sub          → 빠른 브로드캐스트 (유실 허용)
  └── 투표/경매 이벤트  → Kafka / Redis Streams  → 전달 보장 (유실 불허)
```

### 투표/경매 전달 보장 3가지 핵심

**1. 멱등 처리 (Idempotent)**
- `event_id` (UUID)를 DB에 저장 → 중복 수신 시 무시
```json
{ "event_id": "uuid-xxx", "user_id": 123, "choice": "A" }
```

**2. Kafka exactly-once (투표/경매)**
- `enable.idempotence=true` + `transactional.id` 설정
- Consumer: `isolation.level=read_committed`
- DB 쓰기 + offset commit → Outbox 패턴으로 원자적 처리

**3. ACK 확인 + 재전송**
- 서버가 처리 완료 후 클라이언트에 명시적 ACK
- 클라이언트는 ACK 미수신 시 타임아웃 후 재전송 (멱등키로 중복 방지)

### 실시간 결과 브로드캐스트 분리

```
투표 이벤트 → Kafka → Consumer 집계 → 결과를 Redis pub/sub으로 브로드캐스트
```

- **"내 투표 접수됐나?"** → Kafka (반드시 보장)
- **"현재 투표 현황"** → Redis pub/sub (유실 허용 — 다음 집계로 덮임)

→ 보장이 필요한 **이벤트 처리**와 빠른 **상태 전파**를 레이어로 분리하는 것이 핵심.

---

## 작성 예정

- API 설계 패턴 (REST vs gRPC vs GraphQL)
- 대용량 파일 업로드 시스템 설계
- 분산 스케줄러 설계

## Saga 보상과 DB 롤백의 차이

Saga에서는 각 단계가 별도의 로컬 DB 트랜잭션으로 커밋된다. 이후 단계가 실패해도 앞서 커밋한 트랜잭션이 자동으로 롤백되지는 않는다. 이미 완료된 작업의 효과를 취소하거나 조정할 필요가 있으면 새로운 업무 작업과 트랜잭션으로 보상한다. 예를 들어 주문을 삭제하는 대신 취소 상태로 변경할 수 있으며, 구체적인 보상은 업무 규칙에 따라 정한다.

보상은 다른 요청의 변경까지 지우며 과거 상태를 그대로 복원하는 작업이 아니다. 보상 자체도 실패하거나 재시도될 수 있으므로 진행 상태를 추적하고 중복 실행에 안전하도록 설계한다. [[topics/kafka/concepts#Outbox와 소비자 처리의 트랜잭션 경계]]에서 다루는 이벤트 전달·멱등 처리와 함께 쓰더라도 전체 업무가 하나의 DB 트랜잭션이 되는 것은 아니다.

## 응답 시간의 평균과 p95

- 평균은 측정한 응답 시간의 합을 요청 수로 나눈 값이다. p95는 응답 시간 분포의 95번째 백분위로, 측정 대상 요청의 약 95%가 그 시간 이내에 응답했다는 뜻으로 해석한다.
- 요청 100개를 빠른 순으로 정렬했을 때 대략 95번째 위치라고 생각하면 쉽다. 실제 도구는 보간이나 히스토그램 추정을 사용할 수 있으므로 항상 정확히 95번째 표본과 같지는 않다.
- p95는 평균이나 최대값이 아니며 성공률도 아니다. 나머지 약 5%의 느린 요청은 별도로 살펴야 한다. 평균만으로는 일부 요청이 겪는 긴 지연을 구분하기 어려워 p95·p99와 오류율을 함께 본다.
- p95는 이상치를 제거하고 남은 응답 시간을 평균 낸 값이 아니다. 예를 들어 요청 100개 중 90개가 0.1초, 10개가 5초라면 평균은 0.59초지만 p95는 5초다. 평균이 1초 미만이어도 요청의 10%가 5초를 기다리는 분포를 구분할 수 있다. 이는 설명용 가상 데이터다.
- 지표의 대상 API·측정 구간·성공 요청만 포함했는지 등의 집계 범위를 확인한다. [[topics/mysql/concepts#EXPLAIN과 EXPLAIN ANALYZE의 차이]]의 DB 실행시간과 API 응답 시간 구분도 적용된다.
- 출처: [Grafana k6 Thresholds](https://grafana.com/docs/k6/latest/using-k6/thresholds/), 확인일 2026-09-30.

## Saga 참고 링크

- [Microsoft — Saga distributed transactions pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/saga)
- [Microsoft — Compensating Transaction pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/compensating-transaction)
