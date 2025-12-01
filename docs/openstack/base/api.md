# Openstack API Basic

## 1\. 베이스 URL 확인 (전제 조건)

먼저 각 서비스의 포트와 주소를 알아야 합니다. (보통 `cstation` 노드 IP)

- **Keystone (Identity):** `http://<IP>:5000/v3`
- **Neutron (Network):** `http://<IP>:9696`
- **Nova (Compute):** `http://<IP>:8774/v2.1`
- **Glance (Image):** `http://<IP>:9292`
- **Placement:** `http://<IP>:8778`

-----

## 2\. 핵심 서비스 조회 API 목록

### 🌐 네트워크 (Neutron) - VPC, Subnet 관련

가장 궁금해하시는 부분입니다. 베이스 URL(`:9696`) 뒤에 붙습니다.

| 리소스 | API 경로 (URI) | 설명 (AWS 대응) |
| :--- | :--- | :--- |
| **Network** | **`GET /v2.0/networks`** | VPC 전체 목록 조회 |
| **Subnet** | **`GET /v2.0/subnets`** | 서브넷 전체 목록 조회 |
| **Router** | **`GET /v2.0/routers`** | 라우터(Gateway) 목록 조회 |
| **Port** | **`GET /v2.0/ports`** | 인터페이스(ENI) 목록 조회 |
| **Sec Group** | **`GET /v2.0/security-groups`** | 보안 그룹 목록 조회 |
| **Floating IP** | **`GET /v2.0/floatingips`** | 공인 IP 목록 조회 |

### 💻 컴퓨트 (Nova) - 인스턴스, 하이퍼바이저

베이스 URL(`:8774/v2.1`) 뒤에 붙습니다.

| 리소스 | API 경로 (URI) | 설명 |
| :--- | :--- | :--- |
| **Server** | **`GET /servers/detail`** | 인스턴스(VM) 전체 상세 조회 |
| **Flavor** | **`GET /flavors/detail`** | 인스턴스 타입(스펙) 조회 |
| **Hypervisor** | **`GET /os-hypervisors/detail`** | 물리 노드(Compute Node) 상태 조회 |
| **Usage** | **`GET /os-simple-tenant-usage`** | 프로젝트별 자원 사용량 조회 |

### 💿 이미지 (Glance)

베이스 URL(`:9292`) 뒤에 붙습니다.

| 리소스 | API 경로 (URI) | 설명 |
| :--- | :--- | :--- |
| **Image** | **`GET /v2/images`** | 이미지(AMI) 목록 조회 |

### 🔑 자원 관리 (Placement) - GPU 디버깅용

베이스 URL(`:8778`) 뒤에 붙습니다.

| 리소스 | API 경로 (URI) | 설명 |
| :--- | :--- | :--- |
| **Res Provider**| **`GET /resource_providers`** | 자원 제공자(Compute Node) 목록 |
| **Inventory** | **`GET /resource_providers/{uuid}/inventories`** | 특정 노드의 자원(GPU, vCPU) 재고 |
| **Usage** | **`GET /resource_providers/{uuid}/usages`** | 특정 노드의 자원 사용량 |

-----

## 🚀 `curl`로 조회하기 (예시)

CLI에서 토큰을 뽑아서 바로 `curl`로 날리는 스크립트입니다.

**1. 환경변수 세팅 (Controller Node에서):**

```bash
# 관리자 토큰 추출
export OS_TOKEN=$(openstack token issue -f value -c id)

# Neutron(네트워크) URL 추출
export NET_URL=$(openstack endpoint list --service network --interface public -f value -c URL)
```

**2. API 호출 테스트:**

```bash
# 1. VPC (Network) 전체 조회
curl -s -X GET "$NET_URL/v2.0/networks" -H "X-Auth-Token: $OS_TOKEN" | python3 -m json.tool

# 2. Subnet 전체 조회
curl -s -X GET "$NET_URL/v2.0/subnets" -H "X-Auth-Token: $OS_TOKEN" | python3 -m json.tool

# 3. Router 전체 조회
curl -s -X GET "$NET_URL/v2.0/routers" -H "X-Auth-Token: $OS_TOKEN" | python3 -m json.tool
```

이 주소들로 호출했을 때 응답이 잘 오면 백엔드는 건강한 것입니다. Horizon 에러는 아까 조치(Memoized Patch)로 해결되었을 테니, API도 정상적으로 나올 겁니다.
