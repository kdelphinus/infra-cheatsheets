# HTTPRoute 라우팅 트러블슈팅 가이드

Ingress에서 HTTPRoute로 전환한 후 발생할 수 있는 주요 통신 오류 및 해결 방법을 기술합니다.

---

## 1. 503 / Connection Refused (백엔드 포트 불일치)

Envoy는 Service의 ClusterIP 포트가 아닌 **Pod의 실제 컨테이너 포트**로 직접 연결을 시도합니다. 연결 실패 시 파드의 실제 포트를 확인하십시오.
```bash
# 컨테이너 포트 확인
kubectl get pod <POD_NAME> -n <NS> -o jsonpath='{.spec.containers[*].ports}'
```
확인한 포트로 HTTPRoute의 `backendRefs.port`를 수정합니다.

## 2. 404 Not Found (URL Rewrite 필요)

애플리케이션이 하위 경로(Context Path)를 인식하지 못하는 경우 `URLRewrite` 필터를 적용하여 경로를 보정해야 합니다.
```yaml
filters:
  - type: URLRewrite
    urlRewrite:
      path:
        type: ReplacePrefixMatch
        replacePrefixMatch: /
```
