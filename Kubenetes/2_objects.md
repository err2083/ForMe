# Objects 기초

## 1. 컴퓨팅 자원의 제어와 환경 설정 주입의 물리적 메커니즘 분석

쿠버네티스에서 파드는 단순한 실행 단위가 아니라, 클러스터 자원을 효율적으로 분배하고 애플리케이션의 생명주기를 관리하는 논리적 격리 계층입니다. 본 섹션에서 다루는 핵심 컴포넌트들의 동작 원리를 심화 분석합니다.

### 1) 자원 관리의 이중화 정책: Requests vs Limits

파드 내 컨테이너의 `resources` 설정은 노드의 자원 할당 방식(Resource Allocation)을 결정합니다.

* **Requests (예약량):** 스케줄러가 파드를 배치할 노드를 찾는 점수화 과정의 기준입니다. 실제 사용량이 아닌 '최소 보장량'을 의미하며, 노드의 `Allocatable` 자원에서 이 합계를 뺀 나머지 공간에만 새로운 파드가 들어갈 수 있습니다.
* **Limits (상한선):** 물리적 자원 사용의 한계를 설정합니다.
  * **Memory:** 메모리는 압축 불가능한 자원입니다. 설정된 Limits를 초과하면 커널은 프로세스를 즉시 종료(OOM Kill)시켜 노드 전체의 안정성을 보호합니다.
  * **CPU:** 압축 가능한 자원입니다. Limits를 초과하더라도 프로세스를 죽이지 않고 '스로틀링(Throttling)'을 통해 CPU 사이클 점유율을 낮춰 실행 속도만 지연시킵니다.

### 2) 설정 관리의 동적 반영 메커니즘: ConfigMap & Secret

애플리케이션의 바이너리와 설정을 분리하기 위해 사용하는 이 오브젝트들은 파드에 주입되는 방식에 따라 업데이트 메커니즘이 달라집니다.

* **환경 변수(Env) 방식:** 파드가 생성될 때 컨테이너의 프로세스 환경 변수에 값이 고정됩니다. `ConfigMap`의 원본 데이터가 변해도 이미 실행 중인 프로세스의 환경 변수에는 영향이 없으며, 파드를 삭제하고 재생성해야만 변경 사항이 반영됩니다.
* **볼륨 마운트(Volume Mount) 방식:** Kubelet이 노드에 설정 파일을 심볼릭 링크 형태로 생성하고 컨테이너 내부에 마운트합니다. `ConfigMap`이 수정되면 일정 시간 후 컨테이너 내부의 파일 내용도 실시간으로 업데이트됩니다. 이를 통해 파드 재시작 없이 설정값의 동적 변경이 가능해집니다.

### 3) 클러스터 가버넌스: ResourceQuota와 LimitRange

멀티테넌시 환경에서 특정 네임스페이스나 파드가 자원을 독점하는 것을 방지하는 제어 장치입니다.

* **ResourceQuota:** 네임스페이스 전체의 자원 '총량'을 제한합니다. 쿼터가 설정된 네임스페이스 내에서 파드를 생성할 때는 반드시 자원 스펙(Requests/Limits)을 명시해야 하며, 이를 누락하거나 총합을 초과하면 API 서버에서 생성을 거부합니다.
* **LimitRange:** 개별 컨테이너 단위의 '크기'를 제약합니다. 최소(min)/최대(max) 값을 강제할 뿐만 아니라, 자원 스펙을 명시하지 않은 파드에 **기본값(Default)**을 자동으로 할당하여 관리자의 개입 없이 가버넌스를 유지하도록 돕습니다.

---

## 2. 구조적 메커니즘 이해를 위한 핵심 질문 리스트

**질문 1:** 네임스페이스에 `ResourceQuota`가 설정된 상태에서, 자원 스펙(requests/limits)을 정의하지 않은 파드를 생성하려고 시도하면 쿠버네티스 내부에서는 어떤 단계에서 오류를 발생시키며 그 이유는 무엇입니까?

**질문 2:** 한 파드 내에 두 개의 컨테이너가 각각 포트 8080을 사용하도록 설정된 경우, 쿠버네티스 스케줄러가 파드를 배치한 이후 실제 컨테이너 런타임 단계에서 어떤 문제가 발생하며 그 물리적 근거는 무엇입니까?

**질문 3:** `type: NodePort` 서비스를 통해 외부 트래픽이 들어올 때, `externalTrafficPolicy: Local` 옵션이 설정되어 있다면 특정 노드로 들어온 패킷은 어떤 조건에서만 목적지 파드에 도달할 수 있으며, 만약 해당 노드에 파드가 없다면 트래픽은 어떻게 처리됩니까?

<details>
<summary style="cursor: pointer; color: #007bff;">👉 자가 진단 질문 정답 및 해설 보기</summary>

**정답 1:** API 서버의 Admission Control 단계에서 생성이 거부됩니다. `ResourceQuota`가 있는 네임스페이스는 모든 워크로드의 자원 합계를 계산해야 하는데, 자원 명시가 없는 파드는 계산이 불가능하여 정책상 생성을 허용하지 않기 때문입니다. (단, `LimitRange`에 기본값이 설정되어 있다면 자동 주입되어 생성이 가능해집니다.)

**정답 2:** 컨테이너 1은 정상 실행되나 컨테이너 2는 `Port already in use` 에러를 내며 `CrashLoopBackOff` 상태가 됩니다. 파드 내의 모든 컨테이너는 동일한 네트워크 네임스페이스(localhost)를 공유하기 때문에, 한 호스트에서 포트가 중복된 것과 동일한 물리적 충돌이 발생합니다.

**정답 3:** 해당 트래픽을 수신한 노드 내에 대상 파드가 실제로 실행 중인 경우에만 전달됩니다. 만약 해당 노드에 파드가 없다면 다른 노드로 트래픽을 전달(Hop)하지 않고 패킷을 즉시 드랍(Drop)시킵니다. 이는 네트워크 홉을 줄여 성능을 최적화하고 소스 IP를 보존하기 위해 사용됩니다.

</details>

---

## 3. 프로덕션 급 파드 구성 예시와 서비스 장애 해결 프로세스

### [표준 YAML] 리소스 가버넌스와 설정 주입이 포함된 파드 매니페스트

이 예제는 실무에서 권장되는 자원 제한, 노드 배치 전략, 설정 파일 마운트 방식이 통합된 구조입니다.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: api-server-pod
  namespace: production  # 네임스페이스를 통한 논리적 격리
  labels:
    app: api-server
    env: prod
spec:
  nodeSelector:
    hostname: worker-node-1  # 명시적 노드 스케줄링 전략
  containers:
  - name: main-api
    image: my-repo/api:v1.2
    ports:
    - containerPort: 8080
    resources:
      requests:          # 스케줄링 및 자원 예약 기준
        memory: "512Mi"
        cpu: "500m"
      limits:            # 물리적 자원 사용 한계
        memory: "1Gi"    # 초과 시 OOM Kill 대상
        cpu: "1"         # 초과 시 Throttling 발생
    envFrom:             # 상수형 데이터 주입
    - configMapRef:
        name: api-config
    volumeMounts:        # 설정 파일 및 보안 데이터의 동적 업데이트 보장
    - name: config-volume
      mountPath: "/etc/config"
      readOnly: true
  volumes:
  - name: config-volume
    configMap:
      name: api-file-config
```

### [장애 상황] 서비스 생성 후 External-IP가 pending에서 멈추는 경우

* 장애 증상: kubectl get svc 명령 시 type: LoadBalancer 서비스의 외부 IP가 수 분이 지나도 할당되지 않고 pending 상태로 지속됨.
* 해결 프로세스:
  * 환경 점검: 현재 클러스터가 베어메탈(Bare-metal)이나 로컬(Minikube 등) 환경인지 확인합니다. 해당 환경은 로드밸런서를 생성해 줄 클라우드 API 플러그인이 기본적으로 없습니다.
  * 이벤트 확인: kubectl describe svc [서비스명] 명령어를 입력하여 하단 Events 섹션의 메시지를 확인합니다. Pending 원인이 No IP available 혹은 Cloud provider error인지 체크합니다.
  * 임시 조치: 서비스를 NodePort 타입으로 변경하여 노드 IP와 할당된 포트(30000~32767)를 통해 직접 접근하도록 수정합니다.
  * 서비스 타입을 NodePort로 즉시 패치
    * kubectl patch svc [서비스명] -p '{"spec": {"type": "NodePort"}}'
* 근본 해결: 클라우드 환경이라면 해당 프로젝트의 네트워크 쿼터(Quota)를 늘리고, 온프레미스라면 MetalLB와 같은 외부 IP 할당 솔루션을 클러스터에 설치해야 합니다.
