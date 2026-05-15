# 🚀 Nexus Repository 오프라인 설치 가이드 (ctr 기반)

본 문서는 폐쇄망 Kubernetes 환경에서 **Nexus v3.71.0**을 설치하고 사내 통합 아티팩트 저장소(Repository)를 구성하는 절차를 정의합니다.


## 0. 오프라인 설치 자산 준비 (인터넷 환경)

폐쇄망에 반입할 Helm 차트와 컨테이너 이미지(.tar)가 `charts/` 및 `images/` 디렉토리에 없는 경우, **인터넷이 연결된 외부 PC(리눅스)**에서 아래 스크립트를 실행하여 자산을 다운로드해야 합니다.

> **주의**: 이 작업은 폐쇄망 내부가 아닌, 외부망에서 사전에 수행되어야 합니다. (Docker 또는 containerd(`ctr`), `helm` CLI 설치 필수)

```bash
# 컴포넌트 스크립트 디렉토리로 이동
cd scripts/

# 실행 권한 부여 및 다운로드 스크립트 실행
chmod +x download_assets_offline.sh
sudo ./download_assets_offline.sh
```

스크립트 실행이 완료되면 `charts/` 디렉토리에 `.tgz` 차트 파일이, `images/` 디렉토리에 `.tar` 이미지 파일들이 생성됩니다. 전체 프로젝트 폴더를 압축하여 폐쇄망 내부로 반입하십시오.

---

## 📋 구성 명세

| 항목 | 버전 | 용도 |
| :--- | :--- | :--- |
| **Nexus Repository** | **v3.71.0** | 바이너리 아티팩트 저장소 (Helm) |
| **Storage** | 20Gi+ | hostPath 또는 PV 권장 |

---

## 🛠️ 설치 전제 조건

- Kubernetes 클러스터 구성 완료
- Helm v3.x 설치 완료
- Harbor 레지스트리 접근 가능 (`<NODE_IP>:30002`)
- (도메인 접속 시) Envoy Gateway 설치 완료

---

## 1단계: 이미지 Harbor 업로드

모든 작업은 컴포넌트 루트 디렉토리에서 실행합니다.

```bash
# upload_images_to_harbor_v3-lite.sh 상단 Config 수정
# HARBOR_REGISTRY: <NODE_IP>:30002

chmod +x images/upload_images_to_harbor_v3-lite.sh
./images/upload_images_to_harbor_v3-lite.sh
```

---

## 2단계: 설치 실행

모든 작업은 컴포넌트 루트 디렉토리에서 실행합니다.

```bash
# 헬름 설치 (루트의 values.yaml 자동 반영)
chmod +x scripts/install.sh
./scripts/install.sh
```

**스크립트 자동 처리 항목:**

- 네임스페이스 (`nexus`) 생성 및 PV/PVC 적용
- Helm 배포 (Harbor 이미지 경로 자동 생성)
- 서비스 (NodePort: 30003) 생성

---

## 3단계: 초기 비밀번호 확인 및 접속

설치 완료 후 파드가 `Running` 상태가 되면 아래 명령어로 초기 `admin` 비밀번호를 확인합니다.

```bash
# Nexus Pod 내의 데이터 경로에서 비밀번호 확인
kubectl exec -it nexus-0 -n nexus -- cat /nexus-data/admin.password && echo
```

### 💡 접속 정보

| 항목 | 주소 / 값 |
| :--- | :--- |
| **접속 주소** | `http://<NODE_IP>:30003` (NodePort) |
| **기본 계정** | `admin` |
| **초기 비밀번호** | 위 명령어로 확인한 문자열 |

> !!! warning "보안 권고"
> 최초 로그인 후 마법사에 따라 비밀번호를 즉시 변경하십시오. 변경 후 `admin.password` 파일은 자동으로 삭제됩니다.

---

## 🗑️ 삭제 (Uninstall)

```bash
./scripts/uninstall.sh
```
