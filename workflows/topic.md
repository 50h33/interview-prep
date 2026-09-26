# 주제정리 공통 워크플로

호출 시 전달된 주제 또는 기술명을 웹과 로컬 Knowledge Graph에서 조사해 `topics/`에 정리한다. 입력이 없으면 주제를 한 번 확인하고 중단한다.

## Step 1 — 대상 디렉터리

다음 매핑에서 가장 가까운 디렉터리를 고르고, 없으면 `CONSTRAINTS.md` 규칙에 맞는 이름으로 생성한다.

| 키워드 | 디렉터리 |
|---|---|
| java, jvm, gc, spring, webflux, jpa, querydsl, 동시성, completablefuture | java |
| 운영체제, 프로세스, 스레드, 메모리, 자료구조, 알고리즘, 복잡도, http, tcp, tls, dns, 네트워크, nginx | cs |
| mysql, 인덱스, 실행계획, 트랜잭션, 격리수준 | mysql |
| redis, redisson, 캐시, 캐싱, pub/sub, 분산락 | redis |
| kafka, outbox, inbox, 컨슈머, 파티션 | kafka |
| kubernetes, k8s, k3s, helm, hpa, 배포 | kubernetes |
| aws, ec2, ecr, s3, route53, iam, oidc | aws |
| 분산 시스템, cap, 일관성, 분산 트랜잭션, saga, 서킷브레이커, 시스템 디자인, 대용량, 대기열, api 설계, msa | architecture |
| elasticsearch, 역인덱스, 검색, nori | elasticsearch |
| llm, rag, ai, ax, 에이전트, 벡터db, qdrant, claude, codex, mcp | ai |

## Step 2 — 로컬 조회

`concepts.md`와 `questions.md`가 있으면 동시에 읽고 기존 내용을 파악해 중복을 막는다.

## Step 3 — 조사

사용 가능한 웹 검색·페이지 조회 도구로 다음을 확인한다.

1. `{주제} 개념 정리 동작 원리`
2. `{주제} 백엔드 개발자 면접 질문 {현재연도}`
3. `{주제} best practices 실무 {현재연도}`

핵심 내용과 출처 URL을 기록한다. 웹 도구가 없으면 확인하지 않은 최신 정보와 출처를 만들지 않고, 로컬 자료로 가능한 범위만 처리하거나 제한을 알린다.

## Step 4 — concepts.md

로컬에 없는 새 내용만 append한다. 새 파일은 `tags`, `related` frontmatter와 제목·내비게이션 등 `CONSTRAINTS.md` 순서를 따른다. 각 새 개념에는 설명과 다음 섹션을 포함한다.

```markdown
## {개념명}

{동작 원리, 구조, 주의점}

### 💬 면접 답변 형태로 읽기

{핵심 주장 → 원리 → 트레이드오프/주의점 → 확인된 실무 경험 연결 순서의 600자 이상 말하기 줄글}

> 출처: {URL}
```

말하기 본문만 UTF-8 임시 파일에 저장해 `python scripts/vault_tools.py count-text <UTF8파일>`로 측정한다. 사용자 문자열을 명령에 직접 보간하지 않는다.

## Step 5 — questions.md

새 질문만 append하고 기초→중급→심화 순서를 유지한다. 각 질문에는 난이도, 핵심 키워드, 600자 이상 말하기 모범 답변, 꼬리 질문, 출처를 포함한다. 한국 백엔드 면접에서 실제로 물을 개념·원리·트레이드오프·실무 패턴·장애 대응을 우선하고 내부 구현 암기와 학술 수준 세부 질문은 제외한다.

## Step 6 — home과 보고

`home.md`에 디렉터리 링크가 없으면 추가한다. 저장 위치, 추가 섹션·질문 수, 주요 개념과 질문 미리보기를 보고한다.
