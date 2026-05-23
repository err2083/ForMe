# Controller 기초

## 1. 선언적 상태 유지와 워크로드 생명주기 제어의 내부 작동 원리

쿠버네티스 컨트롤러는 클러스터의 '현재 상태(Current State)'를 사용자가 정의한 '원하는 상태(Desired State)'로 끊임없이 일치시키려는 **조정 루프(Control Loop)**의 핵심입니다. 단순히 파드를 실행하는 것을 넘어, 서비스 가용성을 보장하기 위한 고도의 자동화 메커니즘을 수행합니다.

### 1) 자가 치유(Auto-healing)와 복제본 관리: ReplicaSet

ReplicaSet은 지정된 수의 파드 복제본이 항상 실행되도록 보장합니다.

* **연결 메커니즘:** 컨트롤러와 파드는 서비스와 마찬가지로 **라벨(Label)**과 **셀렉터(Selector)**로 느슨하게 연결됩니다.
* **Selector의 진화:** 과거 Replication Controller는 단순 키-값 일치만 확인했으나, ReplicaSet은 `MatchExpressions`를 통해 `In`, `NotIn`, `Exists` 등 보다 복잡한 조건부 로직으로 파드를 집합(Set) 기반으로 관리할 수 있습니다.
* **동작 흐름:** 노드 장애로 파드가 중단되면, 컨트롤러는 API 서버를 통해 이를 감지하고 내부에 정의된 **파드 템플릿(Template)**을 사용하여 새로운 파드를 즉시 생성합니다.

### 2) 무중단 배포와 버전 관리의 추상화: Deployment

Deployment는 ReplicaSet을 상위에서 관리하며 애플리케이션의 배포 전략과 롤백을 제어합니다.

* **배포 전략의 물리적 차이:**
  * **Recreate:** 기존 ReplicaSet의 복제본 수를 0으로 줄여 모든 파드를 삭제한 후, 새 버전의 ReplicaSet을 생성합니다. 일시적인 **다운타임(Downtime)**이 발생하지만 자원 사용량을 일정하게 유지할 수 있습니다.
  * **RollingUpdate:** 서비스 중단 없이 구 버전 파드를 하나씩 제거하고 신 버전 파드를 하나씩 생성합니다. 이 과정에서 두 버전의 파드가 공존하며 트래픽이 분산됩니다.
* **Revision 관리:** 배포마다 새로운 ReplicaSet을 생성하고 이전 기록을 보존(`revisionHistoryLimit`)하여, 문제 발생 시 특정 시점으로의 **롤백(Rollback)**을 즉각 수행할 수 있게 합니다.

### 3) 특수 목적 컨트롤러: DaemonSet, Job, CronJob

* **DaemonSet:** 클러스터 내의 모든(또는 특정 라벨이 붙은) 노드에 파드를 하나씩 배치합니다. 주로 로그 수집(FluentD), 모니터링 에이전트(Prometheus), 네트워크 프록시와 같이 시스템 전체에 걸쳐 실행되어야 하는 인프라 워크로드에 사용됩니다.
* **Job & CronJob:** 서비스 유지가 아닌 '작업의 완료'에 집중합니다.
  * **Job:** 프로세스가 성공적으로 종료되면 파드를 다시 살리지 않고 종료 상태로 둡니다. `completions`(성공 횟수)와 `parallelism`(병렬 실행 수) 옵션으로 배치 작업의 속도를 조절합니다.
  * **CronJob:** 리눅스의 crontab 포맷을 사용하여 주기적으로 Job을 생성하며, `concurrencyPolicy`(Allow, Forbid, Replace)를 통해 이전 작업이 끝나지 않았을 때의 중복 실행 여부를 정교하게 제어합니다.

---

## 2. 컨트롤러 운영 역량 강화를 위한 구조적 자가 진단 질문

**질문 1:** Deployment가 롤링 업데이트를 수행할 때, 내부적으로 생성되는 ReplicaSet들은 동일한 `Label Selector`를 가지게 됩니다. 이때 각 ReplicaSet이 자신이 관리해야 할 파드와 다른 ReplicaSet의 파드를 물리적으로 어떻게 구분하여 관리합니까?

**질문 2:** `concurrencyPolicy: Forbid` 옵션이 설정된 `CronJob`에서, 1분 주기로 실행되는 작업이 2분 이상 소요되고 있다면 2분째에 도달했을 때 쿠버네티스 내부에서는 어떤 스케줄링 변화가 일어납니까?

**질문 3:** 이미 실행 중인 파드들의 라벨을 수동으로 변경하여 ReplicaSet의 셀렉터 조건에서 벗어나게 만들면, 해당 파드와 ReplicaSet 컨트롤러 사이에는 어떤 연쇄 반응이 발생합니까?

<details>
<summary style="cursor: pointer; color: #007bff;">👉 자가 진단 질문 정답 및 해설 보기</summary>

**정답 1:** Deployment는 ReplicaSet을 생성할 때 사용자가 정의한 라벨 외에 자동 생성된 **`pod-template-hash`** 라벨을 추가로 부여합니다. 이 해시값은 파드 템플릿의 내용을 바탕으로 생성되므로, 버전마다 고유한 값을 가집니다. 이를 통해 각 ReplicaSet은 셀렉터를 통해 정확히 자신의 버전에 해당하는 파드들만 식별하고 관리할 수 있습니다.

**정답 2:** `Forbid` 정책에 따라 새로운 작업(Job) 생성이 **스킵(Skip)**됩니다. 컨트롤러는 현재 실행 중인 파드가 종료될 때까지 대기하며, 해당 작업이 종료된 이후에 돌아오는 다음 스케줄 타임에 맞춰 새로운 작업을 생성합니다. 즉, 작업이 겹쳐서 실행되는 것을 원천 차단합니다.

**정답 3:**

1. **분리(Orphaning):** 해당 파드는 더 이상 컨트롤러의 관리 대상이 아니게 됩니다(삭제되지 않고 그대로 실행됨).
2. **신규 생성:** ReplicaSet 컨트롤러는 자신이 관리해야 할 '원하는 상태(복제본 수)'보다 현재 파드 수가 부족함을 인지하고, 템플릿을 사용하여 새로운 파드를 즉시 생성합니다.
결과적으로 기존 파드는 독립적으로 남고, 클러스터에는 새로운 파드가 추가되어 전체 파드 수가 늘어나게 됩니다.

</details>

---

## 3. 무중단 배포를 위한 표준 Deployment 구성 및 배포 장애 대응 가이드

### [표준 YAML] 안정적인 배포 전략이 반영된 Deployment 예제

이 예제는 롤링 업데이트의 정교한 제어와 이전 버전 기록 보존 설정을 포함합니다.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-server-deployment
spec:
  replicas: 3
  # 배포 이력을 5개까지만 보존 (리소스 낭비 방지)
  revisionHistoryLimit: 5
  selector:
    matchLabels:
      app: api-server
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1       # 업데이트 중 원하는 복제본 수보다 최대 몇 개까지 더 생성할 수 있는지
      maxUnavailable: 0 # 업데이트 중 사용할 수 없는 파드의 최대 개수 (0은 가용성 극대화)
  template:
    metadata:
      labels:
        app: api-server
    spec:
      containers:
      - name: main-api
        image: my-repo/api-server:v2.0
        ports:
        - containerPort: 8080
        # 파드가 생성된 후 서비스 트래픽을 받기 전 대기 시간 (애플리케이션 예열 시간 보장)
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
```

### [장애 상황] 새 버전 배포 후 무한 로딩 및 이전 버전 파드 삭제 중단

* 장애 증상: kubectl apply로 이미지를 업데이트했으나, 신규 파드가 Running으로 넘어가지 않고 구 버전 파드도 삭제되지 않은 채 배포가 멈춰 있음.
* 해결 프로세스:
  * 상태 확인: kubectl rollout status deployment api-server-deployment 명령으로 현재 배포 진행 단계를 확인합니다.
  * 원인 파악: kubectl get pods에서 신규 파드가 CrashLoopBackOff 또는 Pending 상태인지 확인하고, kubectl describe pod [신규파드명]의 Events 섹션에서 이미지 태그 오류나 readinessProbe 실패 여부를 체크합니다.
* 긴급 조치 (롤백): 서비스 가용성을 즉시 복구해야 할 경우, 아래 명령어로 배포를 취소하고 이전 버전으로 되돌립니다.

### 배포 이력 확인

kubectl rollout history deployment/api-server-deployment

### 바로 이전 버전으로 즉시 롤백

kubectl rollout undo deployment/api-server-deployment

### 특정 리비전(예: 버전 2)으로 롤백

kubectl rollout undo deployment/api-server-deployment --to-revision=2
