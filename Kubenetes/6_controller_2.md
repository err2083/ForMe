# Controller 중급

## 1. 정체성 기반의 워크로드 관리와 지능형 트래픽 라우팅의 내부 메커니즘 분석

본 섹션에서는 무상태(Stateless) 애플리케이션의 한계를 넘어, 데이터의 영속성과 파드의 고유 식별자를 보장하는 **StatefulSet**, L7 레이어의 지능형 게이트웨이인 **Ingress**, 그리고 수요에 따라 자원을 탄력적으로 조절하는 **HPA**의 동작 원리를 딥다이브합니다.

### 1) StatefulSet: 고유 식별자와 데이터 영속성의 결합 메커니즘

StatefulSet은 단순한 복제본 생성을 넘어, 각 파드에 '정체성(Identity)'을 부여합니다.

* **고유 정체성(Stable Network ID):** ReplicaSet이 랜덤한 해시값을 붙이는 것과 달리, StatefulSet은 0부터 시작하는 **순차적 인덱스(Ordinal Index)**를 부여합니다. 파드가 삭제 후 재생성되어도 동일한 이름을 유지하며, 이는 분산 시스템(DB 클러스터 등)에서 멤버 식별을 위한 필수 요소입니다.
* **순차적 기동 및 종료:** 파드 간의 의존성을 고려하여 0번 파드가 `Running` 및 `Ready` 상태가 된 후에야 1번 파드를 생성합니다. 삭제 시에는 반대로 가장 높은 인덱스부터 하나씩 제거하여 데이터 정합성을 보호합니다.
* **1:1 전용 스토리지 바인딩:** `volumeClaimTemplates`를 통해 각 파드마다 고유한 PVC를 동적으로 생성합니다. 파드가 재시작되어도 자신의 인덱스에 매칭되는 전용 볼륨(PVC-인덱스)에 자동으로 재연결되어 데이터의 연속성을 보장합니다.

### 2) Ingress: 서비스 추상화와 L7 트래픽 제어의 구현체

Ingress는 클러스터 외부 트래픽을 내부 서비스로 연결하는 가상 호스트 기반의 규칙 집합입니다.

* **컨트롤러 아키텍처:** Ingress는 '규칙'일 뿐이며, 이를 실행하기 위한 엔진(Nginx, Kong 등)인 **Ingress Controller**가 필요합니다. 컨트롤러는 API 서버를 감시하다가 Ingress 규칙이 생성되면 이를 자신의 설정 파일로 동적으로 업데이트하여 트래픽을 라우팅합니다.
* **고급 라우팅 기술:**
  * **Path-based:** 도메인 뒤의 경로(/shopping, /order)에 따라 서로 다른 파드 그룹으로 트래픽을 분산합니다.
  * **Canary Deployment:** 어노테이션(Annotation) 설정을 통해 특정 비율(예: 10%)의 트래픽만 신규 버전으로 흘려보내 안정성을 테스트합니다.
  * **TLS Termination:** 인그레스 레벨에서 인증서(Secret)를 관리하여, 파드 내부 앱 수정 없이 HTTPS 보안 통신을 일괄 적용합니다.

### 3) Horizontal Pod Autoscaler (HPA): 데이터 기반의 탄력적 확장 원리

HPA는 매트릭스 정보를 트리거로 파드의 수를 수평적으로 확장(Scale-out)합니다.

* **매트릭 수집 흐름:** `cAdvisor(Kubelet)` → `Metrics Server` → `HPA Controller` 순으로 자원 사용량 정보가 전달됩니다. HPA 컨트롤러는 15초 주기로 이 데이터를 체크합니다.
* **확장 결정 공식:** `원하는 복제본 수 = ceil[현재 복제본 수 * (현재 메트릭 값 / 타겟 메트릭 값)]`
* **안정화 윈도우(Stabilization Window):** 잦은 확장/축소(Flapping)를 방지하기 위해, 특히 축소(Scale-in) 시에는 기본적으로 5분간의 대기 시간을 가져 급격한 트래픽 변동에도 서비스 가용성을 유지합니다.

---

## 2. 시스템 아키텍처 설계 역량 검증을 위한 자가 진단 질문

**질문 1:** 특정 DB 클러스터를 StatefulSet으로 운영 중입니다. 노드 장애로 인해 `db-1` 파드가 삭제되고 다른 노드에서 재생성되었습니다. 이때 `db-1`이 기존에 사용하던 데이터 볼륨에 자동으로 다시 연결될 수 있는 물리적 근거와 과정은 무엇입니까?

**질문 2:** Ingress를 통해 카나리 배포(Weight 10%)를 적용했습니다. 사용자 트래픽이 유입될 때, Ingress Controller는 내부적으로 서비스(Service) 오브젝트의 ClusterIP를 통해 파드로 트래픽을 보냅니까, 아니면 파드의 개별 IP(Endpoint)로 직접 보냅니까? 그 이유는 무엇입니까?

**질문 3:** HPA가 설정된 Deployment에서 `resources.requests` 설정이 누락되어 있다면 오토스케일링은 어떻게 동작합니까? 또한, 평균 CPU 사용률이 타겟 수치를 넘었음에도 불구하고 파드가 즉시 늘어나지 않는 상황이 발생할 수 있는 주요 원인 한 가지만 서술하십시오.

<details>
<summary style="cursor: pointer; color: #007bff;">👉 자가 진단 질문 정답 및 해설 보기</summary>

**정답 1:** StatefulSet의 `volumeClaimTemplates`에 의해 생성된 PVC는 이름에 파드의 인덱스가 포함(예: `data-db-1`)됩니다. 파드가 재생성되어도 동일한 이름(`db-1`)을 가지므로, 쿠버네티스 컨트롤러는 이 이름을 식별자로 사용하여 기존에 존재하던 동일 이름의 PVC를 찾아 마운트합니다. 파드가 삭제되어도 PVC는 삭제되지 않고 유지되기 때문에 데이터가 보존됩니다.

**정답 2:** **파드의 개별 IP(Endpoint)로 직접 보냅니다.** 대부분의 Ingress Controller(Nginx 등)는 성능 최적화와 세밀한 트래픽 제어(세션 고정, 카나리 비율 조정 등)를 위해 서비스의 ClusterIP를 거치지 않고, 엔드포인트 컨트롤러가 관리하는 파드 IP 목록을 직접 참조하여 로드밸런싱을 수행합니다.

**정답 3:**

1. **동작 불가:** HPA는 사용률(Utilization) 계산 시 `Current Usage / Requests` 공식을 사용합니다. Requests가 없으면 분모가 0이 되어 계산 자체가 불가능하므로 오토스케일링이 작동하지 않습니다.
2. **원인:** 애플리케이션의 **기동 시간(Ready 상태 도달 시간)**이 길 경우입니다. 파드가 생성 중이거나 아직 `Ready` 조건이 `True`가 되지 않았다면, HPA는 확장 결정을 내렸더라도 신규 파드가 트래픽을 받을 준비가 될 때까지 추가 확장을 지연하거나 현재 상태를 유지합니다.

</details>

---

## 3. 실무 지향적 인프라 구성 예시 및 트러블슈팅 가이드

### [표준 YAML] 데이터 영속성과 외부 노출이 통합된 StatefulSet 예제

이 매니페스트는 전용 스토리지 템플릿과 헤드리스 서비스를 통한 고유 도메인 할당 구조를 보여줍니다.

```yaml
# 1. 개별 파드의 도메인 고정을 위한 헤드리스 서비스
apiVersion: v1
kind: Service
metadata:
  name: mysql-headless
spec:
  ports:
  - port: 3306
  clusterIP: None # Headless 설정: 파드 각각의 IP를 DNS A 레코드로 반환
  selector:
    app: mysql
---
# 2. 고유 식별자를 가진 상태 보존형 워크로드
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: mysql
spec:
  serviceName: "mysql-headless" # 위 서비스와 연결하여 고유 FQDN 생성
  replicas: 3
  selector:
    matchLabels:
      app: mysql
  template:
    metadata:
      labels:
        app: mysql
    spec:
      containers:
      - name: mysql
        image: mysql:5.7
        volumeMounts:
        - name: data
          mountPath: /var/lib/mysql
  # 3. 파드별 PVC 자동 생성을 위한 템플릿
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: [ "ReadWriteOnce" ]
      storageClassName: "standard"
      resources:
        requests:
          storage: 10Gi
```

### [장애 상황] Ingress 적용 후 모든 트래픽이 404 Not Found를 반환함

* 장애 증상: 호스트 이름을 호스트 파일에 등록하고 <http://myapp.com/api로> 접속했으나, 서비스 화면 대신 Nginx의 404 Not Found 에러 페이지가 노출됨.
* 해결 프로세스:
  * 컨트롤러 존재 확인: 클러스터에 실제 Ingress 규칙을 처리할 Ingress Controller(Nginx 등) 파드가 실행 중인지 확인합니다.
    * 명령어: kubectl get pods -A | grep ingress
  * 로그 분석: Ingress Controller 파드의 로그를 확인하여 설정 오류가 있는지 체크합니다.
    * 명령어: kubectl logs -n ingress-nginx [컨트롤러_파드명]
  * 경로 설정 오차(Path Matching): Ingress YAML의 path 설정과 실제 요청 경로가 일치하는지 확인합니다. 특히 pathType: ImplementationSpecific이나 Prefix 설정에 따라 뒤에 오는 슬래시(/) 처리가 달라질 수 있습니다.
  * 엔드포인트 매칭: Ingress가 가리키는 서비스와 파드가 정상적으로 연결되어 있는지 확인합니다.
    * 명령어: kubectl get endpoints [서비스명] (IP 목록이 비어있다면 서비스 셀렉터 라벨 오타임)

### 긴급 체크: Ingress 규칙이 컨트롤러에 정상적으로 인식되었는지 확인

kubectl describe ingress [인그레스명]
