# 🛠️ Redis Stream 설치 및 운영 가이드

본 가이드는 폐쇄망(Air-gapped) 환경에서 Redis Stream HA 클러스터를 설치하고 운영하는 과정을 설명합니다.

## 1. 전제 조건

- Kubernetes 클러스터 접근 권한 (`kubectl` 설정 완료)
- Helm v3 이상
- Local Harbor 레지스트리 (기본 포트: 30002)

## 2. 이미지 준비

### 운영 환경 (Harbor 레지스트리)

`images/` 디렉토리의 tar 파일을 Harbor에 업로드합니다.

```bash
export HARBOR_REGISTRY="<NODE_IP>:30002"
./images/upload_images_to_harbor_v3-lite.sh
```

!!! warning "Sentinel 이미지 반입 필요"
    `bitnami/redis-sentinel:7.2.4-debian-12-r7` tar 파일은 외부망에서 별도 반입해야 합니다.
    ```bash
    # 외부망에서 실행
    docker pull bitnami/redis-sentinel:7.2.4-debian-12-r7
    docker save bitnami/redis-sentinel:7.2.4-debian-12-r7 -o redis-sentinel.tar
    # tar 파일을 images/ 디렉토리로 반입 후 업로드 스크립트 재실행
    ```

### 로컬 테스트 환경 (ctr import)

tar 파일을 containerd에 직접 임포트합니다.

```bash
sudo ctr -n k8s.io images import images/*.tar
```

## 3. 설치 진행

```bash
# 대화형 설치 스크립트 실행
./scripts/install.sh

# 또는 환경 지정 실행
./scripts/install.sh local   # 로컬 환경 (M1+R1+S2)
./scripts/install.sh prod    # 운영 환경 (M1+R2+S3)
```

### 💾 Storage 설정 주의사항

#### HostPath (정적 노드 할당)
- 스크립트에서 대상 노드를 선택하면 해당 노드에 데이터가 고정됩니다.
- 노드가 다른 경우 SSH로 디렉토리를 수동 생성해야 할 수 있습니다.

#### NFS (공유 스토리지)
- NFS 서버에 디렉토리를 **사전에 직접 생성**해야 합니다.
- `sudo mkdir -p /nfs/redis-stream/{master,replica-0,replica-1}`
- 권한 설정: `sudo chmod -R 777 /nfs/redis-stream`

## 4. 스트림 테스트 및 검증

```bash
./scripts/test-stream.sh local   # 또는 prod
```

### 테스트 체크 포인트 및 기대값

| 단계 | 항목 | 기대값 | 목적 |
| :--- | :--- | :--- | :--- |
| 1 | 그룹 생성 | `OK` 또는 준비 완료 | 반복 실행(멱등성) 보장 확인 |
| 2 | 메시지 생산 | Redis ID (예: `1711...-0`) | OOM 방지: `MAXLEN` 제한 적용 확인 |
| 3 | 동기 복제 | `1` 이상 (Replica 가용 시) | 데이터 유실 방지: 복제본 저장 확인 |
| 4 | 메시지 소비 | 성공 메시지 | Consumer 그룹 읽기 기능 확인 |
| 5 | 미처리 목록 | Pending 건수 > 0 | At-Least-Once: 미완료 작업 보존 확인 |

## 5. 애플리케이션 연동 (Spring Boot)

`examples/spring-boot` 프로젝트를 참조하세요. 빌드 시 내부 Nexus/Artifactory 설정이 필요할 수 있습니다.

```yaml
spring:
  data:
    redis:
      sentinel:
        master: mymaster
        nodes: redis-stream.redis-stream.svc:26379
      password: "${REDIS_PASSWORD}"
```

### 핵심 운영 주의사항

- **MAXLEN 필수 (OOM 방지)**: `XADD` 시 반드시 `MAXLEN`을 지정해야 합니다. 설정 없이 운영 시 스트림이 무한 증가하여 Redis OOM이 발생합니다.
- **리밸런싱 부재 (Zombie 회수)**: Kafka와 달리 Consumer 장애 시 자동 재할당 기능이 없습니다. `autoClaimZombieMessages()` 패턴을 참고하여 앱 레벨에서 주기적으로 `XCLAIM`을 실행해야 합니다.

## 6. 삭제 (Uninstall)

```bash
./scripts/uninstall.sh
```

PV는 `Retain` 정책으로 데이터 디렉토리가 보존되므로, 완전 삭제 시 수동으로 디렉토리를 제거하십시오.
