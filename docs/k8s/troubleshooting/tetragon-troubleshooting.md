# Tetragon 런타임 차단 트러블슈팅 가이드

Tetragon 구동 및 차단 정책 적용 과정에서 발생할 수 있는 주요 장애 및 해결 방법을 기술합니다.

---

## 1. 차단이 동작하지 않는 경우

### 1) 커널 함수 심볼 확인
```bash
grep -w fd_install /proc/kallsyms | head -3
grep -w security_file_open /proc/kallsyms | head -3
```
`fd_install` 심볼이 없으면 `manifests/block-sensitive-read.yaml`의 `call` 값을 `security_file_open`으로 변경 후 재적용합니다.

### 2) `CONFIG_BPF_KPROBE_OVERRIDE` 확인
```bash
grep CONFIG_BPF_KPROBE_OVERRIDE /boot/config-$(uname -r) 2>/dev/null \
  || zcat /proc/config.gz 2>/dev/null | grep CONFIG_BPF_KPROBE_OVERRIDE
```
`=y`가 아니면 Sigkill 차단이 불가합니다. WSL2의 경우 `wsl --update` 후 재시작하면 해결되는 경우가 있습니다.

## 2. Tetragon 파드가 Pending인 경우

```bash
kubectl describe pod -n kube-system -l app.kubernetes.io/name=tetragon
```
이미지 pull 실패라면 Harbor 업로드 및 `values.yaml` 이미지 경로를 재확인합니다.
