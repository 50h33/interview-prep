---
tags: [aws, ec2, ecr, s3, route53, iam, oidc, cicd, cloud]
related: [kubernetes, architecture, cs]
---

# AWS — 핵심 개념 (EC2 · ECR · S3 · Route 53 · IAM/OIDC)

→ [[home]] | 질문 모음: [[topics/aws/questions]] | 연관: [[topics/kubernetes/concepts]]

> `resume/profile.md`에서 사용한 서비스(EC2, ECR, S3, Route 53, IAM/OIDC) 중심으로 정리.

---

## 1. 내 프로젝트의 AWS 배포 흐름

### TicketRush — 단일 EC2 + Docker Compose
```
GitHub Actions (OIDC로 임시 자격 증명)
  → Docker 이미지 빌드 → ECR push
  → EC2 (2 vCPU / 7.6 GiB)에서 이미지 pull → 앱 8개 + Kafka/MySQL/Redis/관측 도구 기동
```
- 설계 기준: 회당 1만 명 티켓 오픈을 단일 인스턴스에서 측정
- 스스로 명시한 한계: 수평 확장 미검증, Redis 단일 장애점 수용

### 뭐든사 — 단일 EC2 + k3s
```
Route 53 → k3s Ingress (cert-manager로 TLS) → Spring Cloud Gateway → 모듈들
GitHub Actions: 빌드/테스트 게이트 → 모듈별 이미지 태그 push → Helm 롤링 업데이트
```
- 설계 기준: DAU 1만(일 30만 요청, 피크 200 TPS), EC2 t3.xlarge 단일 노드
- Docker Compose → k3s(Helm) 이전, SSL을 k3s Ingress/Secret으로 전환 → [[topics/kubernetes/concepts]]

---

## 2. IAM과 GitHub Actions OIDC

### 왜 Access Key 대신 OIDC인가
| | 장기 Access Key (GitHub Secrets) | OIDC |
|---|---|---|
| 자격 증명 | 만료 없는 키를 저장 | 워크플로우 실행마다 **임시 자격 증명** 발급 |
| 유출 위험 | 키 유출 시 회수 전까지 계속 사용 가능 | 짧게 유효, 저장할 비밀 없음 |
| 권한 범위 | 키에 붙은 권한 전체 | trust policy 조건으로 **repo·브랜치·environment 제한** |
| 운영 | 주기적 키 교체 필요 | 교체할 키 없음 |

### 동작 흐름
```
1. 워크플로우가 GitHub OIDC Provider에서 JWT 발급 (permissions: id-token: write)
2. aws-actions/configure-aws-credentials 가 JWT로 STS에 역할 가정 요청
3. IAM이 trust policy 조건(aud, sub) 검증
4. STS가 임시 자격 증명 반환 → 이후 ECR push 등 수행
```

### Trust Policy 핵심 조건
```json
"Condition": {
  "StringEquals": {
    "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
    "token.actions.githubusercontent.com:sub": "repo:{org}/{repo}:ref:refs/heads/main"
  }
}
```
- Provider URL: `https://token.actions.githubusercontent.com`
- **`sub` 조건이 핵심** — 어떤 저장소·브랜치의 워크플로우만 역할을 가정할 수 있는지 제한 (조건이 느슨하면 의도하지 않은 워크플로우가 역할을 가정할 수 있음)
- 역할 권한은 **최소 권한**: 배포용이면 ECR push에 필요한 권한만

### 워크플로우 예시
```yaml
permissions:
  id-token: write   # OIDC 토큰 발급에 필요
  contents: read

steps:
  - uses: aws-actions/configure-aws-credentials@v4
    with:
      role-to-assume: arn:aws:iam::{account}:role/{deploy-role}
      aws-region: ap-northeast-2
  - uses: aws-actions/amazon-ecr-login@v2
```

### EC2에서 AWS 리소스 접근
- EC2에 **IAM Role(Instance Profile)** 을 연결하면 키 없이 ECR pull·S3 접근 가능
- 원칙: 어디에도 장기 키를 두지 않는다 (CI는 OIDC, 서버는 Instance Profile)

---

## 3. ECR (Elastic Container Registry)

- AWS 관리형 **프라이빗 컨테이너 이미지 저장소** (리전 단위)
- 인증: `aws ecr get-login-password | docker login ...` 또는 `amazon-ecr-login` 액션

### 이미지 태그 전략
| 태그 | 장점 | 단점 |
|---|---|---|
| `latest` | 단순 | 어떤 코드인지 추적 불가, 롤백 대상이 모호 |
| **Git SHA / 버전** | 배포 이미지 = 커밋 1:1 추적, 롤백 시 이전 태그로 재배포 | 태그 관리 필요 |

- **Tag immutability(IMMUTABLE)**: 같은 태그로 다시 push하면 `ImageTagAlreadyExistsException` → 한 번 배포한 태그가 다른 이미지로 바뀌는 사고 방지
- 뭐든사: **모듈별 태그 push → Helm 롤링 업데이트** → 변경된 모듈만 배포

### Lifecycle Policy
- 규칙에 맞는 오래된 이미지를 자동 만료 (적용 후 24시간 이내)
- `countType: imageCountMoreThan` — 최신 N개만 유지
- `countType: sinceImagePushed` — push 후 N일 지난 이미지 만료
- `tagStatus: untagged` 규칙으로 태그 없는 이미지 정리 → 저장 비용 관리

---

## 4. EC2

### 인스턴스 선택
- 계열: 범용(t, m), 컴퓨팅(c), 메모리(r)
- **T 계열(버스터블)**: 기준 CPU 사용률 이하에서 크레딧 적립, 초과 시 크레딧 소모
  - **T3는 기본 `unlimited` 모드** — 24시간 평균이 기준치를 넘으면 초과 크레딧 비용 발생
  - 부하 테스트를 오래 돌리면 성능은 유지되지만 비용이 늘 수 있음 → CloudWatch `CPUSurplusCreditBalance` 확인

### 단일 인스턴스에 여러 서비스를 올릴 때
- 컨테이너별 **메모리 한도**를 두지 않으면 한 서비스가 전체를 잠식
- JVM은 힙 외에 **비힙(Direct Memory, Code Cache, 스레드 스택)** 도 사용 → 컨테이너 한도 산정 시 포함
- TicketRush 경험: 640MiB 한도 초과로 커널 강제 종료 → 비힙 상한 + Tomcat 스레드 200 → 50 → 재시작 0회, 최대 RSS 571.8MiB, CPU가 스레드보다 먼저 포화됨을 실측 → [[topics/cs/concepts#컨테이너와 메모리 한도]]

### 네트워크 보안
- **Security Group**: 인스턴스 단위 **stateful** 방화벽 (허용 규칙만, 응답 트래픽 자동 허용)
- 외부에 여는 포트는 80/443(Nginx·Ingress)만, DB·Redis·Kafka 포트는 외부 비공개
- SSH(22)는 특정 IP로 제한하거나 SSM Session Manager 사용

---

## 5. Route 53

- AWS 관리형 **DNS 서비스** — 도메인의 Hosted Zone에 레코드 관리
- 주요 레코드: `A`(IPv4), `AAAA`(IPv6), `CNAME`(다른 도메인 이름), **Alias**(Route 53 확장)

### Alias vs CNAME
| | Alias | CNAME |
|---|---|---|
| 대상 | 선택된 AWS 리소스(ELB, CloudFront, S3 웹사이트 등), 같은 Hosted Zone 레코드 | 모든 DNS 이름 |
| Zone apex (`example.com`) | 생성 가능 | **불가** |
| 조회 비용 | AWS 리소스 대상 Alias 조회는 무료 | 과금 |
| TTL | AWS 리소스 대상이면 설정 불가(리소스 기본값) | 직접 설정 |

### 라우팅 정책
- Simple / Weighted(가중치, 카나리) / Latency(지연 기반) / Failover(헬스 체크 기반) / Geolocation

---

## 6. S3

- **객체 스토리지** — 파일을 버킷/키 단위로 저장, 사실상 무제한 용량, 높은 내구성
- 백엔드 활용: 이미지·첨부 파일, 정적 리소스, 로그·백업
- **Presigned URL**: 서버가 서명한 임시 URL로 클라이언트가 직접 업로드/다운로드 → 앱 서버 트래픽·대역폭 절감
- **Block Public Access** 기본 활성 → 버킷을 직접 공개하지 않고 Presigned URL 또는 CloudFront로 제공
- 스토리지 클래스: Standard / Standard-IA / Glacier — 접근 빈도에 따라 비용 최적화

---

## 참고 링크

- GitHub Actions OIDC + AWS: https://docs.github.com/en/actions/security-for-github-actions/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services
- ECR Lifecycle Policy: https://docs.aws.amazon.com/AmazonECR/latest/userguide/LifecyclePolicies.html
- ECR Tag Immutability: https://docs.aws.amazon.com/AmazonECR/latest/userguide/image-tag-mutability.html
- EC2 Burstable Unlimited 모드: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/burstable-performance-instances-unlimited-mode.html
- Route 53 Alias vs CNAME: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/resource-record-sets-choosing-alias-non-alias.html
