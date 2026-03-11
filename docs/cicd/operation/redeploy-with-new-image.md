# Harbor 기반 이미지 업데이트 및 재배포 운영 가이드

Harbor 레지스트리에 신규 이미지를 업로드하고 쿠버네티스 서비스를 갱신하는 표준 절차입니다.

---

## 1. 현재 구성 정보 확인

배포 전 기존 환경 설정을 파악하여 설정 오류로 인한 장애를 방지합니다.

### 1-1. 이미지 경로 조회

대상 서비스의 `values.yaml`에서 이미지 경로와 태그 형식을 확인합니다.

```bash
grep "image:" ./redis/values.yaml

# 출력 예시
# image: harbor.product.co.kr:30002/goe/redis:7.2
```

### 1-2. Harbor GUI에서 확인

1. `Projects > [프로젝트명] > Repositories > [이미지명]` — 태그가 존재하며 **Push Time**이 최신인지 확인
2. **Pull Count** 컬럼 — 클러스터에서 다운로드된 횟수 확인
3. **Logs** 탭 — 사용자, 시간, 노드 IP별 Pull/Push 이력 상세 확인

---

## 2. 신규 이미지 업로드

### 방법 A: 배치 업로드 스크립트

다수의 이미지를 일괄 처리합니다.

1. 업로드할 이미지(`.tar`)를 `./images/` 경로에 배치합니다.

2. `upload_images_to_harbor_v2.sh` 상단 설정을 수정합니다.

    ```bash
    HARBOR_REGISTRY="<HARBOR_IP>:30002"
    HARBOR_PROJECT="<PROJECT>"
    HARBOR_USER="admin"
    HARBOR_PASSWORD="<PASSWORD>"
    IMAGE_DIR="./images"
    USE_PLAIN_HTTP="true"   # HTTP: true, HTTPS: false
    ```

3. 스크립트를 실행합니다.

    ```bash
    sudo bash upload_images_to_harbor_v2.sh
    ```

### 방법 B: 수동 업로드 (Containerd 기준)

```bash
# 1. 아카이브 로드
sudo ctr -n k8s.io images import <파일명>.tar

# 2. Harbor 경로에 맞는 태그 부여
sudo ctr -n k8s.io images tag redis:latest <HARBOR_IP>:30002/<PROJECT>/redis:7.2.4

# 3. 레지스트리에 Push
# HTTP 환경
sudo ctr -n k8s.io images push --plain-http \
  -u admin:<PASSWORD> <HARBOR_IP>:30002/<PROJECT>/redis:7.2.4

# HTTPS 환경 (--plain-http 제외)
sudo ctr -n k8s.io images push \
  -u admin:<PASSWORD> <HARBOR_IP>:30002/<PROJECT>/redis:7.2.4
```

---

## 3. Pull 정책 설정 (중요)

동일 태그를 유지하며 이미지만 교체할 경우 `imagePullPolicy` 설정이 반영 여부를 결정합니다.

| 정책 | 동작 |
| :--- | :--- |
| `IfNotPresent` | 노드에 해당 태그 이미지가 있으면 레지스트리를 확인하지 않음 (최신 이미지 반영 불가) |
| `Always` | 기동 시마다 레지스트리 Digest를 대조하여 변경 시 강제 Pull |

**태그 고정 운영 시 권장 설정 (`values.yaml`):**

```yaml
image:
  repository: <HARBOR_IP>:30002/<PROJECT>/redis
  tag: "7.2.2"
  pullPolicy: Always
```

---

## 4. 서비스 재배포

### Case 1: 새 태그 적용 (버전 업그레이드)

`helm upgrade`로 롤링 업데이트를 수행합니다.

```bash
helm upgrade <RELEASE_NAME> ./<CHART_DIR> -n <NAMESPACE>
```

### Case 2: 동일 태그 적용 (이미지만 교체)

Helm이 변경 사항을 인지하지 못할 수 있으므로 재설치를 권장합니다.

```bash
helm uninstall <RELEASE_NAME> -n <NAMESPACE>
helm install <RELEASE_NAME> ./<CHART_DIR> -n <NAMESPACE>
```

---

## 5. 배포 결과 검증 및 트러블슈팅

### 5-1. 배포 상태 확인

```bash
kubectl get pods -n <NAMESPACE> -o wide
kubectl describe pod <POD_NAME> -n <NAMESPACE> | grep Image:
```

### 5-2. 트러블슈팅

| 증상 | 원인 및 조치 |
| :--- | :--- |
| `ImagePullBackOff` | `kubectl describe pod` Events 섹션 확인: 401(인증 실패), 404(경로 오류), x509(인증서 미등록) |
| 구버전 이미지가 계속 사용됨 | `pullPolicy: Always` 확인 후 노드 캐시 이미지 강제 삭제 |

**노드 캐시 이미지 강제 제거:**

```bash
# 각 워커 노드에서
sudo ctr -n k8s.io images list | grep <IMAGE_NAME>
sudo ctr -n k8s.io images remove <FULL_IMAGE_NAME>

# 마스터 노드에서 파드 재생성 유도
kubectl delete pod <POD_NAME> -n <NAMESPACE>
```

---

## [부록] HTTPS 인증서 등록 (Harbor HTTPS 사용 시)

Harbor가 HTTPS로 구성된 경우, 이미지를 Push/Pull하는 **모든 노드**에서 인증서를 등록해야 합니다.

### Ubuntu / Debian 계열

```bash
sudo cp harbor.crt /usr/local/share/ca-certificates/
sudo update-ca-certificates
sudo systemctl restart containerd
```

### CentOS / RHEL / Rocky Linux 계열

```bash
sudo cp harbor.crt /etc/pki/ca-trust/source/anchors/
sudo update-ca-trust
sudo systemctl restart containerd
```
