---
tags: [aws, ec2, ecr, s3, route53, iam, oidc, cicd, interview-questions]
related: [aws/concepts, kubernetes, kafka]
---

# AWS — 면접 질문

→ [[home]] | 개념 정리: [[topics/aws/concepts]]

---

## GitHub Actions에서 AWS로 배포할 때 Access Key 대신 OIDC를 사용한 이유와 동작 원리를 설명해주세요.

**난이도**: 중급

**핵심 키워드**: 장기 자격 증명, OIDC, JWT, STS, AssumeRoleWithWebIdentity, trust policy, `sub`/`aud` 조건, `id-token: write`, 최소 권한

**경험 연결 힌트**: TicketRush — GitHub Actions(OIDC) → ECR → EC2 배포 파이프라인 구축

**모범 답변 방향**:

GitHub Secrets에 Access Key를 넣는 방식은 만료되지 않는 자격 증명을 외부 시스템에 저장한다는 점이 가장 큰 문제입니다. 키가 한 번 유출되면 누군가 회수하기 전까지 계속 쓸 수 있고, 주기적으로 키를 교체하는 운영 부담도 생깁니다. 그래서 TicketRush 배포 파이프라인은 OIDC로 구성했습니다. 워크플로우에 `id-token: write` 권한을 주면 GitHub OIDC Provider가 실행마다 JWT를 발급하고, `configure-aws-credentials` 액션이 이 토큰으로 STS에 역할 가정을 요청합니다. AWS는 IAM에 등록한 OIDC Provider와 역할의 trust policy를 기준으로 토큰을 검증한 뒤, 짧게 유효한 임시 자격 증명을 돌려줍니다. 여기서 핵심은 trust policy의 조건입니다. `aud`는 `sts.amazonaws.com`인지, `sub`는 `repo:{org}/{repo}:ref:refs/heads/main`처럼 허용한 저장소와 브랜치인지 확인해야 합니다. `sub` 조건을 느슨하게 두면 의도하지 않은 워크플로우가 배포 역할을 가정할 수 있기 때문입니다. 역할에는 ECR push처럼 배포에 필요한 권한만 붙여 최소 권한 원칙을 지켰고, EC2가 ECR에서 이미지를 pull할 때도 키를 두지 않고 Instance Profile 역할을 사용하는 것이 같은 원칙입니다. 결과적으로 저장소 어디에도 장기 키가 남지 않고, 권한 범위도 저장소·브랜치 단위로 좁힐 수 있습니다.

**꼬리 질문 예시**:
- trust policy에 `sub` 조건이 없으면 어떤 위험이 있나요?
- PR에서 실행되는 워크플로우에도 배포 권한을 줘야 하나요? → environment·브랜치로 `sub`를 분리
- EC2에서 AWS API를 호출할 때 키 없이 인증되는 원리는? → Instance Profile + 인스턴스 메타데이터로 임시 자격 증명 발급
- 관련 개념 상세: [[topics/aws/concepts#2. IAM과 GitHub Actions OIDC]]

> 출처: https://docs.github.com/en/actions/security-for-github-actions/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services

---

## 컨테이너 이미지 태그는 어떻게 관리했고, 배포와 롤백은 어떻게 하나요?

**난이도**: 중급

**핵심 키워드**: ECR, Git SHA 태그, `latest` 문제, Tag immutability, Lifecycle Policy, Helm 롤링 업데이트, 롤백

**경험 연결 힌트**: 뭐든사 — 모듈별 태그 푸시 → Helm 롤링 업데이트, GitHub Actions CI(빌드/테스트 게이트)

**모범 답변 방향**:

이미지 태그의 목적은 "지금 운영에 떠 있는 코드가 정확히 무엇인지"를 추적하는 것입니다. `latest`만 쓰면 어떤 커밋이 배포됐는지 알 수 없고, 문제가 생겼을 때 돌아갈 대상도 모호합니다. 그래서 커밋 SHA나 버전처럼 코드와 1:1로 대응하는 태그를 쓰는 것이 기본입니다. ECR에서는 저장소에 Tag immutability를 켜면 이미 존재하는 태그로 다시 push할 때 `ImageTagAlreadyExistsException`이 발생하므로, 한 번 배포한 태그가 다른 이미지로 바뀌는 사고를 막을 수 있습니다. 뭐든사에서는 모듈마다 이미지를 따로 태그해 push하고 Helm으로 롤링 업데이트했기 때문에, 변경된 모듈만 새 태그로 교체되고 나머지는 그대로 유지됐습니다. CI에서는 빌드와 테스트를 통과해야만 이미지가 만들어지도록 게이트를 두었습니다. 롤백은 이전 태그로 다시 배포하면 되고, Helm을 쓰면 릴리스 이력을 기준으로 이전 리비전으로 되돌릴 수 있습니다. 태그를 계속 쌓으면 저장 비용이 늘어나므로 Lifecycle Policy로 최신 N개만 유지하거나 태그 없는 이미지를 정리합니다. 다만 롤백 가능성을 위해 운영에 배포했던 최근 버전은 충분히 남겨 두는 기준이 필요합니다.

**꼬리 질문 예시**:
- 롤링 업데이트 중 새 버전과 이전 버전이 동시에 떠 있을 때 생길 수 있는 문제는? → API·DB 스키마 하위 호환
- DB 마이그레이션이 포함된 배포는 어떻게 롤백하나요?
- Lifecycle Policy 때문에 롤백할 이미지가 지워지면 어떻게 하나요?
- 관련 개념 상세: [[topics/aws/concepts#3. ECR (Elastic Container Registry)]] | [[topics/kubernetes/questions]]

> 출처: https://docs.aws.amazon.com/AmazonECR/latest/userguide/image-tag-mutability.html
> 출처: https://docs.aws.amazon.com/AmazonECR/latest/userguide/LifecyclePolicies.html

---

## 단일 EC2 인스턴스에 여러 서비스를 올려 운영할 때 주의할 점과, 트래픽이 늘면 어떻게 확장하겠나요?

**난이도**: 심화

**핵심 키워드**: 컨테이너 메모리 한도, JVM 비힙, OOM Kill, T3 unlimited 크레딧, 단일 장애점, ALB + Auto Scaling, 관리형 DB 분리

**경험 연결 힌트**: TicketRush — 단일 EC2(2 vCPU / 7.6 GiB)에 앱 8개 + Kafka/MySQL/Redis/관측 도구, 640MiB 컨테이너 OOM 해결 / 뭐든사 — EC2 t3.xlarge 단일 노드 k3s

**모범 답변 방향**:

단일 인스턴스에 여러 서비스를 올리면 자원 경합이 가장 먼저 문제가 됩니다. TicketRush는 2 vCPU, 7.6GiB EC2 한 대에 애플리케이션 8개와 Kafka, MySQL, Redis, 관측 도구를 함께 올렸는데, 한 컨테이너가 640MiB 한도를 넘어 커널에 강제 종료되는 문제가 있었습니다. 원인을 보니 힙이 아니라 Direct Memory, Code Cache, 스레드 스택 같은 비힙 영역이 과하게 예약되어 있었고, 비힙 상한을 두고 Tomcat 스레드를 200에서 50으로 줄여 재시작 0회, 최대 RSS 571.8MiB로 안정화했습니다. 이때 스레드를 줄여도 처리량이 떨어지지 않았는데, 실측해 보니 CPU가 스레드보다 먼저 포화되고 있었기 때문입니다. 즉 단일 인스턴스에서는 컨테이너별 메모리 한도를 JVM 비힙까지 포함해 산정하고, 무엇이 먼저 포화되는지 측정해서 설정을 정해야 합니다. 인스턴스 유형도 봐야 합니다. 뭐든사에서 쓴 T3는 기본이 unlimited 모드라 부하 테스트처럼 CPU를 오래 높게 쓰면 성능은 유지되지만 초과 크레딧 비용이 발생할 수 있습니다. 가장 큰 한계는 단일 장애점입니다. 인스턴스 하나가 죽으면 전체가 멈추고, 저도 수평 확장은 검증하지 못한 부분으로 명시했습니다. 트래픽이 늘면 먼저 상태를 가진 컴포넌트부터 분리하겠습니다. MySQL과 Redis는 RDS, ElastiCache 같은 관리형 서비스로 옮기고, 애플리케이션은 무상태로 만든 뒤 ALB 뒤에 Auto Scaling Group을 다중 AZ로 두는 구조로 확장합니다.

**꼬리 질문 예시**:
- 컨테이너 메모리 한도를 JVM 힙 크기와 같게 잡으면 어떤 문제가 생기나요?
- 애플리케이션을 수평 확장할 때 세션·대기열 상태는 어디에 두나요?
- RDS로 옮기면 어떤 운영 부담이 줄고, 무엇을 새로 신경 써야 하나요?
- 관련 개념 상세: [[topics/aws/concepts#4. EC2]] | [[topics/cs/questions]]

> 출처: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/burstable-performance-instances-unlimited-mode.html

---

## Route 53에서 Alias 레코드와 CNAME 레코드의 차이는 무엇인가요?

**난이도**: 기초

**핵심 키워드**: Hosted Zone, Zone apex, Alias, CNAME, 조회 비용, TTL, 라우팅 정책

**경험 연결 힌트**: 뭐든사 — Route 53 → k3s Ingress(cert-manager) → Gateway

**모범 답변 방향**:

CNAME은 표준 DNS 레코드로, 어떤 도메인 이름을 다른 도메인 이름으로 연결합니다. 대상에 제한이 없지만 `example.com` 같은 zone apex에는 만들 수 없고, Route 53에서 조회 비용이 과금됩니다. Alias는 Route 53의 확장 기능으로 ELB, CloudFront, S3 정적 웹사이트 같은 선택된 AWS 리소스나 같은 Hosted Zone의 레코드를 가리킵니다. Alias는 zone apex에도 만들 수 있고, AWS 리소스를 가리키는 Alias 조회는 과금되지 않습니다. 또 대상 리소스의 IP가 바뀌어도 Route 53이 알아서 새 값을 응답합니다. 그래서 루트 도메인을 로드밸런서에 연결할 때는 Alias가 사실상 표준입니다. 반면 EC2 한 대에 직접 연결하는 구성이라면 고정 IP(Elastic IP)를 A 레코드로 가리키는 방식을 씁니다. 뭐든사는 Route 53에서 k3s Ingress로 트래픽을 보내고, TLS 인증서는 cert-manager가 Ingress에서 관리하도록 구성했습니다.

**꼬리 질문 예시**:
- DNS TTL을 너무 길게 잡으면 배포·장애 전환 시 어떤 문제가 생기나요?
- Weighted 라우팅으로 카나리 배포를 한다면 어떻게 구성하나요?
- 관련 개념 상세: [[topics/aws/concepts#5. Route 53]]

> 출처: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/resource-record-sets-choosing-alias-non-alias.html

---

## AWS 백엔드 인프라 아키텍처

### AWS 주요 서비스(EC2, S3, RDS, ElastiCache)의 역할 차이를 설명해주세요. 백엔드 배포 시 일반적인 아키텍처는 어떻게 구성하나요?

**난이도**: 기초

**경험 연결 힌트**: 단일 EC2 구성(TicketRush·뭐든사)을 운영 환경으로 옮긴다면 → Public/Private Subnet 분리, ALB + ASG 다중 AZ, RDS·ElastiCache 분리

**핵심 키워드**: EC2(VM), S3(Object Storage), RDS(Managed RDBMS), ElastiCache(Redis/Memcached), VPC, Public/Private Subnet, ALB, NAT Gateway, Security Group, ASG, Multi-AZ

**모범 답변 방향**:
AWS 주요 서비스는 역할이 명확하게 구분됩니다. EC2는 하이퍼바이저 위에서 실행되는 가상 머신(VM)입니다. 물리 서버가 아니라는 점이 면접에서 자주 구분되는 포인트입니다. S3는 객체 스토리지로 이미지, 로그, 영상 같은 비정형 데이터 저장에 쓰고 정적 웹사이트 호스팅이나 데이터 레이크로도 활용됩니다. RDS는 패치, 백업, Multi-AZ 복제를 AWS가 관리해주는 관계형 DB 서비스로 MySQL, Aurora, PostgreSQL 등을 지원합니다. ElastiCache는 Redis나 Memcached 엔진의 관리형 캐시 서비스인데, 단순 캐싱 외에도 분산락, pub/sub, 세션 스토어 용도로도 활용됩니다. 백엔드 배포 시 일반적인 아키텍처는 인터넷 → ALB(Public Subnet) → EC2(Private Subnet) → RDS/ElastiCache(Private Subnet) 구조이고, EC2에서 외부로 나가는 아웃바운드 트래픽은 NAT Gateway를 경유합니다. Security Group은 ALB에서 EC2로의 트래픽만 허용해서 DB는 외부에 직접 노출되지 않습니다.

**일반적인 아키텍처 (트래픽 흐름)**:
```
인터넷 → [Internet Gateway] → ALB (Public Subnet)
         → EC2 (Private Subnet) ← Security Group: ALB SG만 허용
         → RDS / ElastiCache (Private Subnet)
Private Subnet → NAT Gateway (Public Subnet) → 인터넷 (아웃바운드)
```

**핵심 포인트**:
- **Public Subnet**: ALB, NAT Gateway, Bastion Host
- **Private Subnet**: EC2, RDS, ElastiCache
- **Security Group**: ALB SG에서만 EC2 인바운드 허용. "인증·인가"와 다름 — SG는 IP/포트 기반 방화벽
- **NAT Gateway**: Private Subnet EC2의 아웃바운드(패키지 설치, 외부 API 호출) 통신 담당
- **ALB 라우팅 기준**: path (`/api/*`), header, host — 지리적 위치 라우팅은 **Route 53**이 담당
- **ASG**: CPU 사용률, 커스텀 CloudWatch 메트릭 기준으로 최소/최대/희망 인스턴스 수 관리. Multi-AZ 배포로 가용성 확보

**꼬리 질문 예시**:
- EC2가 외부 npm 패키지를 설치해야 하는데 Private Subnet에 있다면 어떻게 구성하나요? → NAT Gateway
- ALB에서 특정 경로를 다른 Target Group으로 보내려면? → Listener Rule (path-based routing)
- Route 53과 ALB의 역할 차이는? → Route 53: DNS 레벨 라우팅(지리, 가중치, Failover). ALB: HTTP 레벨 라우팅(path, header)

---

## SQS와 Kafka를 비교했을 때 각각 어떤 상황에 선택하나요? (왜 Kafka를 썼나요?)

**난이도**: 심화

**핵심 키워드**: 메시지 리플레이, 파티션, 소비자 그룹, 관리 비용, 처리량

**경험 연결 힌트**: TicketRush·뭐든사 모두 Kafka 사용 — Saga 보상 트랜잭션, Outbox/Inbox(재전달 134,196건 중 중복 실행 0), 파티션 3개에 컨슈머 concurrency 3으로 처리량 43 → 96.6건/s → [[topics/kafka/questions]]

**모범 답변 방향**:

SQS와 Kafka의 선택은 메시지 리플레이 필요성과 운영 부담을 기준으로 결정합니다. SQS는 완전 관리형 서비스로 운영 부담이 없고 AWS 생태계(Lambda, SNS)와 긴밀하게 연동됩니다. 메시지를 소비자가 처리 완료 후 삭제하는 단순 큐 패턴에 적합하며, 과거 이벤트 재처리(리플레이)가 불필요한 환경에 잘 맞습니다. 반면 Kafka는 메시지를 보존 기간 동안 유지하기 때문에 리플레이가 가능하며, 여러 Consumer Group이 같은 메시지를 독립적으로 소비하는 패턴을 지원합니다. 파티션을 통해 순서를 보장하면서도 높은 처리량을 낼 수 있어 대용량 스트리밍 처리에 강합니다. 반면 SQS FIFO는 순서를 보장하지만 TPS 제한이 있습니다. 운영 측면에서 SQS는 AWS가 전적으로 관리하지만 Kafka는 클러스터를 직접 운영해야 하며, AWS MSK를 사용하면 관리형으로 운영할 수 있습니다. 이벤트 리플레이 요구사항이 크지 않은 환경에서는 SNS+SQS가 Kafka보다 운영 부담이 적어 적합합니다.

**꼬리 질문 예시**:
- 실시간 채팅 메시지 저장/전달 시스템을 설계한다면 SQS와 Kafka 중 무엇을 선택하고 그 이유는?
- SQS에서 메시지 리플레이가 필요한 상황이 생기면 어떻게 대응하나요?

> 출처: https://aws.amazon.com/ko/blogs/korea/choosing-between-messaging-services-for-serverless-applications/
> 출처: https://reintech.io/blog/building-resilient-systems-aws-sqs-sns
