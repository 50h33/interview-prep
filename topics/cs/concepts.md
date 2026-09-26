---
tags: [cs, operating-system, data-structure, database, network, networking, http, tls, nginx]
related: [java, mysql, redis, architecture, aws]
---

# CS 기초 — 운영체제 · 자료구조 · DB · 네트워크

→ [[home]] | 질문 모음: [[topics/cs/questions]] | [[topics/java/concepts]] | [[topics/mysql/concepts]]

## 1. 프로세스 vs 스레드

| 항목 | 프로세스 | 스레드 |
|---|---|---|
| 정의 | 실행 중인 프로그램 (OS 자원 할당 단위) | 프로세스 내 실행 흐름 (CPU 스케줄링 단위) |
| 메모리 | Code / Data / Heap / Stack 독립 | **Stack만 독립**, Code / Data / Heap 공유 |
| 통신 | IPC 필요 (파이프, 소켓, 공유 메모리) | 같은 메모리 직접 접근 (동기화 필요) |
| 장애 격리 | 한 프로세스가 죽어도 다른 프로세스 영향 없음 | 한 스레드 크래시가 프로세스 전체를 죽일 수 있음 |
| 생성·전환 비용 | 큼 | 작음 |

- 멀티스레드는 자원 공유로 효율적이지만 **경쟁 상태(race condition)** 위험 → 동기화 필요 ([[topics/java/concepts]] 동시성 참고)
- JVM에서 스레드 1개 = OS 스레드 1개 (플랫폼 스레드). Java 21 Virtual Thread는 여러 가상 스레드를 소수의 캐리어 스레드에 올린다.

---

## 2. 컨텍스트 스위칭 (Context Switching)

CPU가 실행 중인 작업의 상태(레지스터, PC, 스택 포인터 → PCB/TCB)를 저장하고 다른 작업의 상태를 복원하는 과정.

| 구분 | 비용 | 이유 |
|---|---|---|
| 프로세스 간 | 큼 | 주소 공간(페이지 테이블) 교체 + **TLB 플러시** → 캐시 미스 증가 |
| 스레드 간 (같은 프로세스) | 작음 | 주소 공간 공유 → 레지스터·스택만 교체 |

- 전환 중에는 CPU가 유용한 일을 하지 않음 → **스레드가 너무 많으면 처리량이 오히려 떨어진다**
- 스레드 수 기준
  - CPU bound: 코어 수 ≈ 스레드 수 (N 또는 N+1)
  - I/O bound: 대기 시간이 길수록 더 많이 (`코어 수 × (1 + 대기시간/연산시간)`)
  - 결국 공식보다 **부하 테스트로 CPU·지연 시간을 실측해 결정**

---

## 3. 동기화 — 임계 영역, Mutex, Semaphore, 데드락

### 용어
- **경쟁 상태**: 여러 스레드가 공유 자원에 동시에 접근해 실행 순서에 따라 결과가 달라지는 상태
- **임계 영역**: 공유 자원에 접근하는 코드 구간 — 한 번에 하나만 진입해야 함

### Mutex vs Semaphore vs Monitor

| 도구 | 동시 진입 | 소유권 | Java 대응 |
|---|---|---|---|
| Mutex | 1개 | 잠근 스레드만 해제 | `ReentrantLock` |
| Semaphore | N개 (카운터) | 없음 (누구나 release) | `java.util.concurrent.Semaphore` |
| Monitor | 1개 + 조건 대기(wait/notify) | 있음 | `synchronized` |

### 데드락 (Deadlock)
4가지 조건이 **모두** 성립할 때 발생 → 하나만 깨면 예방된다.

| 조건 | 깨는 방법 |
|---|---|
| 상호 배제 | 공유 가능한 자원으로 (현실적으로 어려움) |
| 점유 대기 | 필요한 자원을 한 번에 모두 요청 |
| 비선점 | 획득 실패 시 가진 자원 반납 (`tryLock(timeout)`) |
| 순환 대기 | **자원에 순서를 매겨 항상 같은 순서로 획득** (실무에서 가장 흔한 해법) |

- 대응 전략: 예방(조건 제거) / 회피(은행원 알고리즘) / 탐지 후 회복(DB는 탐지 후 한쪽 트랜잭션 롤백)
- DB 데드락은 [[topics/mysql/questions#Deadlock 감지·방지]] 참고

---

## 4. 가상 메모리 (Virtual Memory)

각 프로세스에 독립된 가상 주소 공간을 주고, **페이지 테이블**로 물리 주소에 매핑한다.

- **페이징**: 메모리를 고정 크기 페이지(보통 4KB)로 나눔 → 외부 단편화 없음
- **TLB**: 페이지 테이블 조회 결과를 캐시하는 하드웨어 → 주소 변환 속도 향상
- **페이지 폴트**: 접근한 페이지가 물리 메모리에 없을 때 발생 → 디스크(스왑)에서 적재
  - 폴트가 과도하면 **스래싱(thrashing)** — CPU가 페이지 교체만 하느라 처리량 급락
- **요구 페이징**: 실제 접근할 때 물리 메모리 할당 → 예약(VSZ)과 실사용(RSS)이 다름

### 컨테이너와 메모리 한도
- 컨테이너 메모리 한도는 cgroup이 **RSS 기준**으로 제한 → 초과 시 커널 OOM Killer가 프로세스 종료 (exit code 137)
- JVM 메모리 = Heap + **비힙**(Metaspace, Code Cache, Direct Memory, 스레드 스택 × 스레드 수)
  - `-Xmx`만 맞추면 비힙 때문에 한도를 넘을 수 있다 → `MaxDirectMemorySize`, `ReservedCodeCacheSize`, 스레드 수(`-Xss` × N)까지 합산해야 함

---

## 5. I/O 모델과 I/O 멀티플렉싱

| 모델 | 설명 |
|---|---|
| Blocking I/O | I/O 완료까지 스레드 대기 → 연결 1개당 스레드 1개 (Tomcat thread-per-request) |
| Non-blocking I/O | 데이터 없으면 즉시 반환 → 계속 확인(polling)해야 함 |
| I/O 멀티플렉싱 | 하나의 스레드가 여러 소켓의 **준비 이벤트**를 한 번에 감시 |
| Async I/O | I/O 완료 후 커널이 콜백/통지 |

### select / poll / epoll

| 항목 | select | poll | epoll (Linux) |
|---|---|---|---|
| 감시 FD 수 | 보통 1024 제한 | 제한 없음 | 제한 없음 |
| 준비된 FD 찾기 | 매번 전체 순회 O(n) | 전체 순회 O(n) | 준비된 것만 반환 |
| FD 목록 전달 | 매 호출마다 커널로 복사 | 매 호출마다 복사 | 커널에 한 번 등록 |

- epoll 트리거: Level-Triggered(데이터 남아 있으면 계속 통지) / Edge-Triggered(상태 변할 때 1회 → 끝까지 읽어야 함)
- 사용처: Nginx, Netty(Spring WebFlux, Spring Cloud Gateway), Redis → 적은 스레드로 대량 연결 처리
- 연결 차이: [[topics/cs/concepts#Nginx 요청 처리 모델 — Event-Driven]]

---

## 6. CPU 스케줄링 (요약)

| 알고리즘 | 특징 | 문제 |
|---|---|---|
| FCFS | 도착 순서 | 긴 작업 뒤 짧은 작업 대기 (convoy effect) |
| SJF | 짧은 작업 우선 | 긴 작업 **기아(starvation)** |
| Round Robin | 타임 슬라이스 단위로 선점 | 슬라이스가 짧으면 컨텍스트 스위칭 증가 |
| 우선순위 | 우선순위 높은 작업 먼저 | 기아 → **에이징**으로 해결 |

- Linux CFS: 실행 시간이 가장 적은 태스크를 먼저 실행 (공정성 기반, 레드블랙 트리)

---

## 7. 자료구조 핵심

### 시간 복잡도

| 자료구조 | 조회 | 삽입/삭제 | 비고 |
|---|---|---|---|
| 배열 (`ArrayList`) | O(1) 인덱스 | O(n) 중간 | 연속 메모리 → 캐시 친화적 |
| 연결 리스트 (`LinkedList`) | O(n) | O(1) 위치를 알 때 | 노드 분산 → 캐시 미스 |
| 해시 테이블 (`HashMap`) | 평균 O(1) | 평균 O(1) | 최악 O(n), Java 8+는 O(log n) |
| 균형 BST (`TreeMap`) | O(log n) | O(log n) | 정렬·범위 조회 |
| 힙 (`PriorityQueue`) | 최솟값 O(1) | O(log n) | 우선순위 큐, Top-K |
| B+Tree | O(log n) | O(log n) | 디스크 기반 인덱스 |
| Skip List | 평균 O(log n) | 평균 O(log n) | Redis Sorted Set ([[topics/redis/concepts]]) |

### 해시 테이블과 충돌
- 해시 함수로 버킷 인덱스 계산 → 서로 다른 키가 같은 버킷에 오면 **충돌**
- 해결: **체이닝**(버킷에 리스트) / **개방 주소법**(빈 칸 탐사)
- Java `HashMap`: 체이닝 + 버킷 노드 8개 이상(테이블 크기 64 이상)이면 레드블랙 트리로 변환, 6개 이하로 줄면 리스트 복귀
- 부하율 0.75 초과 시 용량 2배 **리사이징** → 재해싱 비용 → 크기를 알면 초기 용량 지정
- `equals`를 재정의하면 `hashCode`도 재정의해야 함
- 멀티스레드 환경은 [[topics/java/questions#ConcurrentHashMap]]

### B-Tree vs B+Tree (DB 인덱스)
- **B+Tree**: 데이터(또는 PK)는 리프에만, 내부 노드는 키만 → 한 노드(페이지)에 더 많은 키 → **트리 높이가 낮아 디스크 I/O 감소**
- 리프 노드끼리 연결 리스트 → **범위 조회·정렬에 유리**
- 해시 인덱스는 등치 조회 O(1)이지만 범위·정렬 불가 → RDB 기본 인덱스는 B+Tree
- InnoDB 세컨더리 인덱스 리프에는 PK가 저장 → 커버링 인덱스 원리 ([[topics/mysql/concepts]])

---

## 8. 데이터베이스 기초

### ACID
| 속성 | 의미 | 보장 수단 (InnoDB) |
|---|---|---|
| Atomicity | 전부 성공 or 전부 실패 | Undo Log |
| Consistency | 제약 조건을 항상 만족 | 제약 조건 + 애플리케이션 규칙 |
| Isolation | 동시 트랜잭션 간섭 차단 | 락 + MVCC |
| Durability | 커밋된 데이터는 유지 | Redo Log (WAL) |

- 격리 수준·이상 현상: [[topics/mysql/questions#데이터베이스 동시성 문제 유형과 트랜잭션 격리 수준으로 어떻게 해결하나요?]]

### 정규화
| 단계 | 조건 |
|---|---|
| 1NF | 컬럼 값이 원자값 (반복 그룹 없음) |
| 2NF | 1NF + 기본키 일부에만 종속된 컬럼 제거 (부분 함수 종속 제거) |
| 3NF | 2NF + 기본키가 아닌 컬럼에 종속된 컬럼 제거 (이행 함수 종속 제거) |
| BCNF | 모든 결정자가 후보키 |

- **반정규화**: 조회 성능을 위해 의도적으로 중복 허용 (집계 컬럼, JSON 캐시 등) → 쓰기 시 정합성 유지 비용 발생

---

## 9. 네트워크 기초

### TCP/IP 4계층
| 계층 | 프로토콜 | 단위 |
|---|---|---|
| 응용 | HTTP, DNS, TLS | 메시지 |
| 전송 | TCP, UDP | 세그먼트 / 데이터그램 |
| 인터넷 | IP, ICMP | 패킷 |
| 네트워크 접근 | Ethernet | 프레임 |

### TCP vs UDP
| 항목 | TCP | UDP |
|---|---|---|
| 연결 | 연결 지향 (3-way handshake) | 비연결 |
| 신뢰성 | 순서 보장, 재전송, 흐름·혼잡 제어 | 보장 없음 |
| 속도 | 상대적으로 느림 | 빠름, 헤더 작음 |
| 사용처 | HTTP/1.1·2, DB 연결 | DNS, 스트리밍, HTTP/3(QUIC) |

### 연결 수립과 종료
- **3-way handshake**: SYN → SYN+ACK → ACK
- **4-way handshake**: FIN → ACK → FIN → ACK
- **TIME_WAIT**: 먼저 종료한 쪽이 2MSL 동안 대기 (늦게 도착한 패킷 처리·마지막 ACK 유실 대비)
  - 짧은 연결을 대량으로 맺으면 TIME_WAIT가 쌓여 포트 고갈 → **커넥션 풀·Keep-Alive**로 재사용

### 주소창에 URL 입력 시 흐름
1. DNS 조회 (브라우저 캐시 → OS → 리졸버 → 루트 → TLD → 권한 DNS)
2. TCP 연결 (3-way handshake)
3. TLS 핸드셰이크 ([[topics/cs/concepts#TLS Handshake 과정]])
4. HTTP 요청 → 로드밸런서 / Nginx → 애플리케이션 서버 → DB
5. 응답 수신 → 브라우저 렌더링

---

## 10. HTTP / HTTPS와 TLS

### HTTP vs HTTPS 핵심 차이

| 항목 | HTTP | HTTPS |
|---|---|---|
| 암호화 | 평문 전송 (없음) | TLS로 암호화 |
| 포트 | 80 | 443 |
| 보안 | 도청·위변조 가능 | 기밀성·무결성·인증 보장 |
| 성능 | 오버헤드 없음 | TLS 핸드셰이크 오버헤드 |

**HTTPS가 보장하는 세 가지:**
- **기밀성(Confidentiality)**: 제3자가 내용을 읽을 수 없음
- **무결성(Integrity)**: 전송 중 데이터 변조 감지
- **인증(Authentication)**: 서버가 실제 그 서버임을 증명 (인증서)

### SSL / TLS 개념

- **SSL**: Netscape가 개발한 초기 프로토콜 (SSL 2.0, 3.0)
- **TLS**: SSL 3.0을 계승한 IETF 국제 표준 (TLS 1.0 → 1.1 → 1.2 → 1.3)
- 현재는 TLS가 표준이지만 관례상 SSL/TLS로 혼용
- TLS 1.0, 1.1, SSL 2.0, 3.0은 보안 취약점으로 사용 금지
- **2025년 기준 권장**: TLS 1.3 (TLS 1.2는 허용, 이하 금지)

### TLS Handshake 과정

#### TLS 1.2 (4-Way Handshake, 2 RTT)

```
Client                          Server
  │──── Client Hello ──────────→│  (지원 암호화 방식 목록 + 랜덤값)
  │←─── Server Hello ───────────│  (선택 암호화 방식 + 서버 랜덤값 + 인증서)
  │──── Key Exchange ──────────→│  (Pre-Master Secret, 공개키로 암호화)
  │──── Change Cipher Spec ────→│
  │←─── Change Cipher Spec ─────│
  │     [암호화 통신 시작]        │
```

1. **Client Hello**: 지원 가능 암호화 방식(Cipher Suite) + 클라이언트 랜덤값
2. **Server Hello**: 선택한 Cipher Suite + 서버 랜덤값 + **서버 인증서**
3. **Key Exchange**: 클라이언트가 인증서의 공개키로 Pre-Master Secret 암호화 전송
4. **Session Key 생성**: 클라이언트 랜덤 + 서버 랜덤 + Pre-Master Secret → **대칭키(Session Key)** 생성
5. 이후 Session Key로 대칭 암호화 통신

#### TLS 1.3 (1 RTT, 더 빠르고 안전)

- 핸드셰이크 왕복 횟수 감소 (2 RTT → 1 RTT)
- 취약한 암호화 방식(RSA 키 교환 등) 지원 제거
- **0-RTT 재연결** 지원 (세션 재개 시 handshake 없이 바로 통신)
- Perfect Forward Secrecy 기본 적용

### 암호화 방식 조합

TLS는 **공개키 + 대칭키** 두 방식을 조합해 사용:

| 방식 | 장점 | 단점 | TLS에서의 역할 |
|---|---|---|---|
| 대칭키 | 빠름 | 키 배송 문제 | 실제 데이터 암호화 |
| 공개키 | 안전한 키 교환 | 느림 | Session Key 교환 단계 |

→ 공개키로 안전하게 Session Key를 교환한 뒤, 이후 통신은 빠른 대칭키로 처리

### 서버 인증서 (X.509)

- **CA(Certificate Authority)**: 인증서를 발급·서명하는 신뢰 기관 (DigiCert, Let's Encrypt 등)
- 인증서에 포함된 정보: 도메인, 공개키, 유효기간, CA 서명
- 클라이언트(브라우저)는 CA 루트 인증서를 미리 신뢰 목록에 보유 → 서버 인증서 검증
- **인증서 유효기간**: 2025년 이후 점진적 단축 (398일 → 목표 47일, 2029년)

**인증서 체인 검증 순서:**
```
서버 인증서 → 중간 CA → 루트 CA (브라우저 신뢰 저장소)
```

### 실무 주의사항

- TLS 1.3 사용 권장, TLS 1.2는 허용, 1.1 이하 비활성화
- Cipher Suite: ECDHE + AES-GCM 또는 ChaCha20-Poly1305 권장 (PFS 보장)
- 인증서 만료 모니터링 필수 (자동 갱신 설정 권장 — Let's Encrypt + certbot)
- 세션 재개(Session Resumption) 활성화로 핸드셰이크 오버헤드 감소
- HTTP → HTTPS 리다이렉트 설정 + HSTS(HTTP Strict Transport Security) 적용

> 출처: https://www.cloudflare.com/learning/ssl/what-happens-in-a-tls-handshake/
> 출처: https://aws.amazon.com/compare/the-difference-between-https-and-http/
> 출처: https://community.citrix.com/tech-zone/build/tech-papers/networking-tls-best-practices-2025/

---

## 11. 웹 서버 — Nginx vs Tomcat

### Nginx vs Tomcat — 역할과 아키텍처

#### 역할 차이

| 항목 | Nginx | Tomcat |
|---|---|---|
| 분류 | 웹 서버 (Web Server) | 웹 애플리케이션 서버 (WAS) |
| 핵심 기능 | 정적 파일 서빙, 리버스 프록시, 로드 밸런싱 | 서블릿 컨테이너, 동적 Java 애플리케이션 실행 |
| 동적 처리 | 불가 (백엔드로 위임) | 가능 (JVM 위에서 실행) |

### Nginx 요청 처리 모델 — Event-Driven

#### Master-Worker 구조

```
Master Process
  ├── Worker Process 1  ← 수천 개의 커넥션 동시 처리
  ├── Worker Process 2
  └── Worker Process N  (보통 CPU 코어 수와 동일)
```

- **Non-blocking I/O + epoll(Linux)**: I/O 대기 중 다른 요청 처리 가능
- Worker 1개가 1,000+ 커넥션 동시 처리 (스레드 생성 없음)
- Context Switching 최소화 → CPU 효율 극대화
- **C10K 문제** 해결을 위해 설계된 아키텍처
- 정적 콘텐츠 응답시간: 1ms 미만, 워커당 100,000 req/s 처리 가능

### Tomcat 요청 처리 모델 — Thread-Per-Request

- 요청마다 **스레드 할당** (Thread Pool에서 꺼내서 사용)
- I/O 대기 시 스레드 점유 → 동시 연결 수 = 스레드 수에 비례
- Context Switching 오버헤드 발생 (고부하 시 성능 저하)
- JVM GC로 인한 100~500ms 지연 가능
- NIO 커넥터로 튜닝 시 10,000~50,000 req/s

### 정적 파일 전송 효율 — sendfile (Zero-Copy)

#### 전통 방식 (복사 발생)
```
디스크 → 커널 버퍼 → 유저 스페이스 → 소켓 버퍼 → 네트워크
         ↑ 복사 1      ↑ 복사 2       ↑ 복사 3
```

#### sendfile (Zero-Copy)
```
디스크 → 커널 버퍼 ──────────────────→ 소켓 버퍼 → 네트워크
         (유저 스페이스 우회, 복사 없음)
```

- Nginx: `sendfile on` 설정으로 OS 레벨 zero-copy 활용
- Tomcat: sendfile 미지원 → 정적 파일 전송 효율 열위
- **주의**: sendfile은 정적 파일에만 적용. 프록시된 동적 콘텐츠는 해당 없음

```nginx
# Nginx 권장 설정
sendfile        on;
sendfile_max_chunk 1m;   # 워커 독점 방지
tcp_nopush      on;      # 패킷 최적화 (sendfile과 함께 사용)
tcp_nodelay     on;      # Keep-alive 연결 지연 최소화
```

### Nginx + Tomcat 조합 아키텍처

```
클라이언트 → Nginx (80/443)
               ├── 정적 파일 요청 → Nginx 직접 서빙 (sendfile)
               └── 동적 요청 → Tomcat (8080) 프록시
```

**조합하는 이유:**
1. **역할 분리**: 정적 파일은 Nginx(빠름), 동적 처리는 Tomcat(Java)
2. **TLS 처리**: Nginx에서 TLS 종료 → Tomcat은 평문으로 처리 (부하 감소)
3. **부하 분산**: 여러 Tomcat 인스턴스에 로드 밸런싱
4. **보안**: Tomcat 포트를 외부에 직접 노출하지 않음

> 출처: https://technicalustad.com/nginx-vs-tomcat/
> 출처: https://www.getpagespeed.com/server-setup/nginx/nginx-sendfile-tcp-nopush-tcp-nodelay
> 출처: https://engineeringatscale.substack.com/p/nginx-millions-connections-event-driven-architecture

---

## 12. 수 표현

- 정수: Java `int` 32비트(약 ±21억), `long` 64비트
- 부동소수점(IEEE 754): 0.1 같은 값을 정확히 표현 못 함 → **금액은 `BigDecimal` 또는 정수(원 단위)**
- JavaScript `Number`는 64비트 부동소수점 → 안전 정수 한계 **2^53 − 1**
  - 64비트 ID(Snowflake 등)를 JSON 숫자로 내려주면 끝자리가 손실 → **문자열로 직렬화**

---

## 참고 링크

- https://man7.org/linux/man-pages/man7/epoll.7.html
- https://dev.mysql.com/doc/refman/8.0/en/innodb-index-types.html
- https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/HashMap.html
- https://www.techprep.app/blog/operating-systems-interview-questions
- https://www.interviewbit.com/operating-system-interview-questions/
- https://liamkwo.github.io/interview2/
