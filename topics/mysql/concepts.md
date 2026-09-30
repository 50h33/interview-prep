---
tags: [mysql, database, index, query-optimization]
related: [redis, architecture, elasticsearch, java, cs]
---

# MySQL — 핵심 개념 정리

→ [[home]] | 질문 모음: [[topics/mysql/questions]]

---

## 1. 인덱스 기본

인덱스는 **조회 성능과 쓰기 성능의 트레이드오프**.

- 인덱스가 많을수록: 조회 빠름, 쓰기 느림(정렬 저장 비용), 디스크 추가 사용
- 인덱스가 없으면: Full Table Scan → 데이터 증가에 따라 선형적으로 느려짐

### 언제 인덱스를 추가하나
- 자주 사용되는 조회 API의 WHERE, JOIN, ORDER BY 컬럼
- Slow query log에서 발견된 쿼리
- 카디널리티(중복이 적은 값)가 높은 컬럼 우선

---

## 2. 복합 인덱스 (Composite Index)

여러 컬럼을 묶어 하나의 인덱스로 구성.

### 컬럼 순서 기준
1. **등치 조건(=)** 컬럼 먼저
2. **범위 조건(>, <, BETWEEN)** 컬럼 나중에
3. **카디널리티 높은** 컬럼 우선
4. **정렬(ORDER BY)** 방향도 인덱스에 반영

```sql
-- 인덱스: (status, created_at)
-- 잘 활용되는 쿼리
WHERE status = 'active' AND created_at > '2026-01-01' ORDER BY created_at DESC

-- status는 등치(=), created_at은 범위(>) → 올바른 순서
```

---

## 3. 커버링 인덱스 (Covering Index)

커버링 인덱스는 **특정 쿼리에 필요한 컬럼을 모두 인덱스에서 얻을 수 있는 경우**를 말한다. SELECT 결과뿐 아니라 WHERE 조건 등 쿼리에서 사용하는 컬럼도 함께 확인한다. 별도의 인덱스 종류라기보다 해당 쿼리와 인덱스의 관계다.

```sql
-- 인덱스: (user_id, status, created_at)
SELECT user_id, status, created_at FROM orders WHERE user_id = 1;
-- → 필요한 컬럼을 인덱스에서 얻어 테이블 행의 추가 조회를 줄일 수 있음
```

- EXPLAIN에서 `Using index` 가 나오면 커버링 인덱스 활용 중
- 자주 조회하는 컬럼 조합을 인덱스에 포함시켜 I/O 대폭 감소 가능

일반적인 보조 인덱스 조회는 인덱스에서 대상의 PK를 찾은 뒤, 필요한 나머지 값을 얻으려고 테이블 행을 조회할 수 있다. 쿼리에 필요한 값이 인덱스에 모두 있으면 이 추가 조회를 생략할 수 있는 것이 커버링의 이점이다. 다만 인덱스 자체는 읽어야 하고, InnoDB의 MVCC 가시성 확인 때문에 테이블 행을 조회하는 경우도 있으므로 물리 디스크 I/O가 항상 0이라고 설명하지 않는다.

- `Using index condition`은 인덱스 조건 푸시다운 표시로, `Using index`와 같은 뜻이 아니다.
- 출처: [MySQL EXPLAIN Output](https://dev.mysql.com/doc/refman/8.4/en/explain-output.html), [InnoDB Multi-Versioning](https://dev.mysql.com/doc/refman/8.4/en/innodb-multi-versioning.html).

---

## 4. 인덱스가 무력화되는 경우

### 앞 와일드카드 LIKE
```sql
WHERE name LIKE '%검색어%'  -- Full Scan
WHERE name LIKE '검색어%'   -- 인덱스 사용 가능
```

### 인덱스 컬럼에 함수 적용
```sql
WHERE DATE(created_at) = '2026-03-27'  -- Full Scan
-- 개선
WHERE created_at >= '2026-03-27' AND created_at < '2026-03-28'
```

### 암묵적 타입 변환
```sql
-- user_id 컬럼이 INT인데
WHERE user_id = '123'  -- 문자열로 비교 → 타입 변환 → Full Scan
WHERE user_id = 123    -- 올바른 타입
```

### OR 조건
```sql
WHERE status = 'active' OR user_id = 1  -- 인덱스 활용 어려움
-- 개선: UNION 사용 또는 각각 인덱스 설계
```

---

## 5. EXPLAIN으로 실행 계획 확인

인덱스 설계 후 반드시 `EXPLAIN`으로 검증.

```sql
EXPLAIN SELECT * FROM orders WHERE user_id = 1 AND status = 'active';
```

**주요 확인 항목:**
- `type`: ALL(Full Scan) → ref/range/const 로 개선되어야 함
- `key`: 실제로 사용된 인덱스명
- `rows`: 예상 스캔 행 수 (적을수록 좋음)
- `Extra`: `Using index`(커버링), `Using filesort`(정렬 인덱스 미활용) 확인

### EXPLAIN과 EXPLAIN ANALYZE의 차이

일반 `EXPLAIN`은 옵티마이저가 선택한 실행 계획을 보여주며 비용과 행 수는 추정값이다. 쿼리의 실제 경과 시간을 보여주는 도구로 해석하지 않는다. `EXPLAIN ANALYZE`는 쿼리를 실제 실행하고 `actual time`, 실제 행 수, 반복 횟수 등을 보여준다. 각 실행 단계의 시간은 밀리초 단위이며 반복 실행된 단계에서는 루프당 평균이다. 부모 단계에 자식 단계 시간이 포함되므로 모든 단계의 시간을 합산하지 않는다.

두 도구로 보는 DB 실행 경로와 API 응답 시간은 측정 범위가 다르다. 서버 요청에는 DB 연결 대기·애플리케이션 처리·직렬화 등의 시간도 포함될 수 있다. 실행 계획에서 커버링을 확인한 뒤 실제 성능 개선은 데이터량·요청 부하·서버 자원·캐시 조건 등을 맞춘 전후 측정으로 검증한다.

- 출처: [MySQL 8.4 — EXPLAIN Statement / EXPLAIN ANALYZE](https://dev.mysql.com/doc/refman/8.4/en/explain.html). API와 DB의 측정 범위 구분은 문서의 DB 실행 계측 범위를 바탕으로 한 설명이다.

**부하 단위 읽기:** k6에서 iteration은 시나리오 함수를 한 번 실행하는 단위다. arrival-rate 방식의 `240 iters/s` 부하 설정은 매초 240회의 반복을 시작하려는 목표이며, 실제 완료 또는 성공 처리량을 뜻하지 않는다. 한 반복에 HTTP 요청이 여러 개 있으면 반복률과 HTTP 요청률(RPS)은 다르다. 동시에 실행하는 가상 사용자 수(VU)와도 구분한다. 사용 가능한 VU가 부족해 시작하지 못한 반복은 `dropped_iterations`로 나타날 수 있다.

- 출처: [Grafana k6 — Ramping arrival rate](https://grafana.com/docs/k6/latest/using-k6/scenarios/executors/ramping-arrival-rate/), [Arrival-rate VU allocation](https://grafana.com/docs/k6/latest/using-k6/scenarios/concepts/arrival-rate-vu-allocation/).

---

## 6. Slow Query 튜닝 순서

1. Slow query log 활성화 → 임계치 이상 쿼리 수집
2. EXPLAIN으로 실행 계획 분석
3. 인덱스 추가 또는 쿼리 재작성
4. 재실행 후 개선 확인

---

## 참고 링크
- [MySQL EXPLAIN 공식 문서](https://dev.mysql.com/doc/refman/8.0/en/explain-output.html)
- [Use The Index, Luke](https://use-the-index-luke.com/)

---

## 7. Oracle vs MySQL 주요 차이

> Oracle 대비용. 4가지 핵심 차이 암기.

| 항목 | Oracle | MySQL |
|---|---|---|
| **페이징 문법** | `WHERE ROWNUM <= N` (레거시) / `FETCH FIRST N ROWS ONLY` (12c+) | `LIMIT N OFFSET M` |
| **NULL 처리** | 빈 문자열 `''` = NULL 동일 취급 | `''`와 NULL 엄격히 구분 |
| **자동 증가** | SEQUENCE 객체 별도 생성 + `seq.NEXTVAL` 명시 | `AUTO_INCREMENT` 컬럼 선언 |
| **기본 격리 수준** | `READ COMMITTED` (Non-Repeatable Read 발생 가능) | `REPEATABLE READ` (스냅샷 유지) |

**실무 주의 포인트:**
- Oracle → MySQL 마이그레이션 시 `''` = NULL 차이로 데이터 조회 누락 발생 가능
- JPA `@GeneratedValue(strategy = SEQUENCE)`는 Oracle의 SEQUENCE 객체를 활용
- MySQL의 REPEATABLE READ는 MVCC 스냅샷 기반이라 Phantom Read도 대부분 방지됨
