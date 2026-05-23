# Pod

## 1. 파드 생명주기 제어와 자원 최적화 배정의 내부 작동 원리

쿠버네티스에서 **파드(Pod)**는 정적인 컨테이너 모음이 아니라, 클러스터와 끊임없이 상태를 주고받는 동적인 엔티티입니다. 서비스 가용성을 극대화하기 위한 내부 제어 장치들을 심화 분석합니다.

### 1) 단계별 상태 전이와 조건(Conditions)의 논리적 구조

파드의 상태는 전체 상태를 나타내는 **Phase(Pending, Running 등)**와 세부 진행 상황을 나타내는 **Conditions**로 이중화되어 있습니다.

* **Init Container의 역할:** 본 컨테이너 기동 전 보안 설정이나 볼륨 준비와 같은 사전 작업을 수행합니다. 이 단계가 성공(True)해야만 다음 단계로 전이되며, 실패 시 본 컨테이너는 절대 실행되지 않습니다.
* **Status vs Conditions:** 파드가 `Running` 단계라 하더라도 내부 `Ready` 조건이 `False`일 수 있습니다. 이는 컨테이너는 떠 있지만 아직 서비스 트래픽을 받을 준비가 되지 않았음을 의미하며, 쿠버네티스는 이 조건을 기준으로 엔드포인트 연결 여부를 결정합니다.

### 2) 서비스 안정성의 핵심: Readiness vs Liveness Probe

애플리케이션의 '살아있음'과 '준비됨'을 구분하여 장애 연쇄 반응을 차단합니다.

* **Readiness Probe (준비 상태 확인):** 부팅 직후 앱이 대규모 데이터를 로딩하거나 예열(Warm-up) 중일 때 트래픽이 유입되어 에러가 발생하는 것을 방지합니다. 검사 실패 시 서비스 엔드포인트에서 파드 IP를 제거하여 트래픽을 차단합니다.
* **Liveness Probe (활성 상태 확인):** 프로세스는 살아있으나 내부 로직이 교착 상태(Deadlock)에 빠진 경우를 감지합니다. 실패 횟수가 임계치(`failureThreshold`)를 넘으면 Kubelet은 해당 파드를 즉시 재시작(Restart)하여 자가 치유(Self-healing)를 시도합니다.

### 3) 자원 우선순위와 축출 전략: QoS Classes (Guaranteed, Burstable, BestEffort)

노드 자원이 부족할 때 어떤 파드를 먼저 희생시킬지 결정하는 등급 체계입니다.

* **Guaranteed:** 모든 컨테이너의 Request와 Limit이 동일하게 설정된 경우입니다. 가장 높은 우선순위를 가지며 자원 경합 시 마지막까지 보호받습니다.
* **Burstable:** Request가 Limit보다 작거나 최소한의 Request만 설정된 경우입니다. 노드 메모리 부족 시 **OOM Score**가 높은(사용량/예약량 비율이 높은) 파드부터 순차적으로 종료됩니다.
* **BestEffort:** 자원 설정을 아예 하지 않은 파드입니다. 자원이 부족하면 가장 먼저 축출(Eviction)되는 대상입니다.

### 4) 고급 배정 전략: Affinity와 Taint/Toleration

* **Affinity (친밀도):** 파드가 특정 노드나 다른 파드와 "함께 있고 싶어 하는" 성질입니다. `Required`는 강제 조건, `Preferred`는 가중치 기반의 유연한 선택을 지원합니다.
* **Taint & Toleration (결함과 용인):** 노드에 `Taint`를 설정하면 허용되지 않은 파드는 배정될 수 없습니다. `NoSchedule`은 신규 배정만 막고, `NoExecute`는 이미 실행 중인 파드라도 `Toleration`이 없으면 즉시 축출하여 노드의 안정성을 강제합니다.

---

## 2. 장애 가용성 설계를 위한 시니어 엔지니어 자가 진단 질문

**질문 1:** 특정 노드에 `NoExecute` 효과를 가진 `Taint`를 새롭게 설정했습니다. 이때 해당 노드에서 실행 중이던 파드들 중 일부는 즉시 삭제되고, 일부는 일정 시간 후 삭제되며, 일부는 삭제되지 않고 유지됩니다. 이 차이를 만드는 3가지 설정 조건은 무엇입니까?

**질문 2:** `Burstable` 등급의 파드 A(Request 1Gi / Usage 800Mi)와 파드 B(Request 2Gi / Usage 1Gi)가 동일한 노드에서 실행 중입니다. 노드에 메모리 부족(Pressure)이 발생하여 커널이 프로세스를 종료해야 한다면, 어떤 파드가 먼저 종료될 확률이 높으며 그 계산 근거는 무엇입니까?

**질문 3:** 애플리케이션 업데이트 과정에서 신규 파드가 생성되었으나 `Readiness Probe`가 계속 실패하고 있습니다. 이 상황에서 기존 서비스 트래픽과 클러스터 내부의 엔드포인트(Endpoint) 오브젝트는 어떻게 동작하고 있겠습니까?

<details>
<summary style="cursor: pointer; color: #007bff;">👉 자가 진단 질문 정답 및 해설 보기</summary>

**정답 1:**

1. **즉시 삭제:** 노드의 태인트와 매칭되는 `Toleration`이 아예 없는 파드.
2. **지연 삭제:** 태인트에 대응하는 `Toleration`이 있으나 `tolerationSeconds` 옵션이 설정되어 있어 해당 시간이 경과한 파드.
3. **삭제되지 않음:** 태인트에 대응하는 `Toleration`이 완벽히 일치하고 `tolerationSeconds`가 설정되지 않은 파드.

**정답 2:** **파드 A**가 먼저 종료될 확률이 높습니다. `Burstable` 등급 간의 축출 순서는 **OOM Score**에 의해 결정되는데, 이는 예약량 대비 실제 사용 비율을 기준으로 합니다. 파드 A는 예약량의 80%를 사용 중이고, 파드 B는 50%를 사용 중이므로 상대적으로 자원을 과하게 점유하고 있는 파드 A의 점수가 더 높게 측정됩니다.

**정답 3:**
기존 서비스 트래픽은 여전히 정상 상태인 구버전 파드로만 전달됩니다. `Readiness Probe`가 실패하면 해당 파드의 `Ready` 컨디션이 `False`로 유지되며, 엔드포인트 컨트롤러는 해당 파드의 IP를 서비스의 **Endpoints** 리스트에서 제외하거나 `NotReadyAddresses` 섹션으로 분류하여 트래픽 유입을 물리적으로 차단합니다.

</details>

---

## 3. 고가용성 파드 표준 매니페스트 및 트러블슈팅

### [표준 YAML] 가용성 및 배정 전략이 통합된 파드 구성 예제

실무에서 권장되는 자원 할당, 프로브 설정, 노드 선택 전략이 모두 포함된 예제입니다.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: critical-api-pod
  labels:
    app: api-server
spec:
  # 1. 노드 배정 전략: 특정 라벨(kr)이 있는 노드를 선호하며 가중치를 부여
  affinity:
    nodeAffinity:
      preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 80
        preference:
          matchExpressions:
          - key: zone
            operator: In
            values: ["kr-az1"]
  
  containers:
  - name: api-container
    image: my-repo/api-server:latest
    # 2. QoS 등급: Request와 Limit을 동일하게 설정하여 Guaranteed 등급 획득
    resources:
      requests:
        cpu: "500m"
        memory: "1Gi"
      limits:
        cpu: "500m"
        memory: "1Gi"
    
    # 3. 준비 상태 확인: 앱 기동 후 10초 뒤부터 5초 간격으로 확인
    readinessProbe:
      httpGet:
        path: /ready
        port: 8080
      initialDelaySeconds: 10
      periodSeconds: 5
      successThreshold: 3 # 3회 성공 시 준비 완료로 판단

    # 4. 활성 상태 확인: 실패 시 파드 재시작 유도
    livenessProbe:
      tcpSocket:
        port: 8080
      failureThreshold: 5 # 5회 연속 실패 시 Restart
```

### [장애 상황] 파드가 'Running' 상태이나 서비스 접속 시 503 에러 발생

* 장애 증상: kubectl get pods 결과 상태는 Running이지만, 서비스 IP를 통한 접근 시 Service Unavailable (503) 에러가 발생하고 트래픽이 파드로 도달하지 않음.
* 해결 프로세스:
  * 엔드포인트 확인: kubectl get endpoints [서비스명] 명령어로 서비스에 연결된 유효 IP 목록이 있는지 확인합니다. 만약 목록이 비어 있다면 파드가 서비스의 셀렉터에 부합하더라도 'NotReady' 상태인 것입니다.
  * 프로브 상태 점검: kubectl describe pod [파드명] 명령어를 실행하여 Conditions 섹션의 Ready 항목이 False인지 확인하고, Events 섹션에서 Readiness probe failed 메시지를 확인합니다.
  * 원인 파악: 애플리케이션의 /ready 경로가 정상적인 응답(200 OK)을 주지 못하고 있거나, DB 연결 지연 등으로 프로브 타임아웃이 발생하고 있는지 확인합니다.
  * 조치: 앱 내부 로직을 수정하거나, 앱 준비 시간이 길다면 매니페스트의 initialDelaySeconds를 충분히 늘려줍니다.

### 엔드포인트 상태 즉시 확인 명령어

kubectl describe endpoints [서비스명]
