# 🍎 Redis Stream (HA) 개요

본 컴포넌트는 단일 Kafka/Zookeeper 아키텍처를 대체하기 위해 구성된 **Redis Stream 7.2.4 (Master-Replica-Sentinel HA)** 클러스터입니다.

## 1. 주요 특징

- **고가용성 (High Availability)**: Master 1 + Replica 2 + Sentinel 3 구성을 통한 자동 장애 조치(Failover)를 지원합니다.
- **환경 최적화**: 운영(Harbor) 및 로컬(ctr import) 환경에 최적화된 통합 설치 스크립트를 제공합니다.
- **데이터 보전**: AOF(Append Only File) 기반 영속성 및 HostPath/NFS PV를 통한 데이터 보존을 지원합니다.
- **OOM 방지**: `MAXLEN` 기반 스트림 로그 트리밍 전략이 기본적으로 적용되어 메모리 고갈을 방지합니다.

## 2. 디렉토리 구조

서비스 구성 요소 및 스크립트 위치는 다음과 같습니다.

```text
redis-stream-7.2/
├── charts/redis/           # Bitnami Redis Helm 차트
├── images/                 # Redis 이미지 및 Harbor 업로드 스크립트
├── manifests/              # PV 매니페스트 및 테스트 파드
├── scripts/                # 설치(install.sh), 테스트(test-stream.sh) 등 운영 스크립트
├── examples/spring-boot/   # At-Least-Once 구현 예제 프로젝트
├── values.yaml             # 운영 환경 설정
├── values-local.yaml       # 로컬 테스트 환경 설정 (Override)
└── README.md               # 서비스 명세
```

## 3. 접속 정보 및 포트

| 항목 | 정보 | 설명 |
| :--- | :--- | :--- |
| **Sentinel 엔드포인트** | `redis-stream.redis-stream.svc:26379` | 클라이언트 접속 지점 |
| **Master Set 이름** | `mymaster` | Sentinel 식별자 |
| **기본 포트** | `6379` (Redis), `26379` (Sentinel) | 서비스 포트 |

!!! note
    Sentinel을 통해 Master의 위치를 동적으로 파악하므로, 애플리케이션에서는 Sentinel 주소와 Master Set 이름을 사용하여 접속해야 합니다.

---

다음 단계: [Redis Stream 설치 및 운영 가이드](./002-redis-stream-install.md)
