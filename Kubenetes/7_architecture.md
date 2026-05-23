# Architecture

## 1. 컴포넌트 간 'Watch' 메커니즘과 데이터 평면(Data Plane)의 추상화 동작 원리

쿠버네티스는 단순한 명령 하달 방식이 아니라, 모든 컴포넌트가 **큐브 API 서버(kube-apiserver)**를 중심으로 '원하는 상태'를 유지하기 위해 협력하는 **이벤트 중심 분산 시스템**입니다.

### 1) 제어 평면(Control Plane)의 'Watch' 기반 오케스트레이션

쿠버네티스의 각 컴포넌트(Scheduler, Controller Manager, Kubelet 등)는 API 서버에 **Watch**라는 감시 기능을 걸어둡니다.

* **작동 흐름:** 사용자가 `kubectl`로 파드 생성을 요청하면 API 서버는 이 정보를 **etcd**에 기록합니다. 이때 스케줄러는 Watch 기능을 통해 '노드가 할당되지 않은 파드'의 등장을 즉시 감지합니다.
* **의사결정:** 스케줄러는 노드의 자원 상태를 고려하여 최적의 노드를 선택한 뒤, 파드 정보에 노드 이름을 업데이트합니다. 그러면 해당 노드의 **Kubelet** 역시 Watch 기능을 통해 '자신에게 할당된 파드'를 감지하고 컨테이너 실행을 시작합니다.
* **존재 이유:** 폴링(Polling) 방식의 부하를 줄이고, 클러스터 전체의 상태 변화를 실시간으로 전파하여 동기화 속도를 극대화하기 위함입니다.

### 2) 서비스 네트워킹의 중추: kube-proxy와 Proxy 모드

파드의 IP는 유동적이기 때문에, 고정된 진입점인 서비스를 통해 트래픽을 관리합니다. 이 과정의 실질적인 구현은 각 노드에 데몬셋으로 떠 있는 **kube-proxy**가 담당합니다.

* **iptables 모드:** 큐브프로시가 API 서버로부터 서비스-파드 매핑 정보를 받아 노드의 리눅스 커널 커널 영역인 iptables 규칙을 업데이트합니다. 트래픽이 서비스 IP로 들어오면 커널 단에서 즉시 파드 IP로 **NAT(Network Address Translation)**가 수행됩니다.
* **IPVS 모드:** 부하가 매우 높은 환경에서 사용됩니다. L4 로드밸런서인 IPVS를 사용하여 iptables보다 빠른 성능과 다양한 로드밸런싱 알고리즘을 제공합니다.

### 3) 파드 내 네트워크 공유: Pause 컨테이너의 본질

파드 내의 여러 컨테이너가 동일한 IP(localhost)를 공유할 수 있는 이유는 **Pause 컨테이너(인프라 컨테이너)** 덕분입니다.

* **메커니즘:** 파드 생성 시 가장 먼저 Pause 컨테이너가 실행되어 네트워크 네임스페이스를 생성하고 IP를 할당받습니다. 이후 생성되는 실제 애플리케이션 컨테이너들은 이 Pause 컨테이너의 네트워크 네임스페이스를 공유(join)합니다.
* **결과:** 애플리케이션 컨테이너가 죽고 다시 살아나도 네트워크 환경(IP, 인터페이스)은 Pause 컨테이너 덕분에 그대로 유지됩니다.

---

## 2. 아키텍처의 논리적 연결성 검증을 위한 자가 진단 질문

**질문 1:** 만약 마스터 노드의 `etcd`와 `kube-apiserver`는 정상인데, `kube-scheduler` 파드만 중단된 상황입니다. 이때 사용자가 새로운 Deployment를 배포한다면 클러스터 내부에서는 어떤 상태까지 진행되며, 최종적으로 파드는 어떤 상태(Status)에 머물게 됩니까?

**질문 2:** Calico CNI를 사용하는 환경에서, 서로 다른 노드에 위치한 파드 A가 파드 B로 패킷을 보낼 때 **오버레이(Overlay) 네트워크(IPIP/VXLAN)**는 패킷의 캡슐화(Encapsulation) 과정에서 '실제 파드 IP'와 '물리 노드 IP'를 각각 어떻게 처리합니까?

**질문 3:** 스토리지 관리에서 **CSI(Container Storage Interface)**의 등장이 쿠버네티스 생태계와 3rd 파티 벤더(스토리지 회사)들에게 준 가장 큰 기술적 이점은 무엇이며, 이것이 PV/PVC 생성 흐름에 어떤 변화를 가져왔습니까?

<details>
<summary style="cursor: pointer; color: #007bff;">👉 자가 진단 질문 정답 및 해설 보기</summary>

**정답 1:** API 서버는 배포 요청을 받아 `etcd`에 파드 정보를 기록하는 것까지 성공합니다. 하지만 이 이벤트를 감지하여 노드를 배정해줄 스케줄러가 없기 때문에, 파드 오브젝트에는 노드 정보가 할당되지 않습니다. 결과적으로 파드는 생성은 되었으나 실제 실행될 노드를 찾지 못해 **`Pending`** 상태에서 멈추게 됩니다.

**정답 2:** 패킷이 노드를 빠져나갈 때, Calico의 라우터는 원래의 파드 패킷(Inner IP: 파드 IP)을 감쌉니다. 그 위에 외부 헤더(Outer IP)를 현재 노드의 물리 IP와 목적지 노드의 물리 IP로 씌워 캡슐화합니다. 실제 네트워크망은 노드 간 통신으로 인식하여 패킷을 전달하고, 목적지 노드에 도착하면 겉의 헤더를 벗겨(Decapsulation) 내부의 파드 IP를 확인한 뒤 타겟 파드로 전달합니다.

**정답 3:** 과거에는 스토리지 플러그인 코드가 쿠버네티스 핵심 코드 안에 포함(In-tree)되어 있어, 스토리지 버전 업데이트를 위해 쿠버네티스 전체를 업데이트해야 했습니다. CSI는 이를 표준 인터페이스로 분리(Out-of-tree)하여 벤더들이 독립적으로 플러그인을 개발/배포할 수 있게 했습니다. 이를 통해 사용자는 `StorageClass`와 연동된 CSI 프로비저너를 통해 클라우드나 온프레미스 스토리지를 파드 생성과 동시에 동적으로 할당(Dynamic Provisioning)받는 유연성을 얻었습니다.

</details>

---

## 3. 고가용성 네트워크 및 스토리지 설계를 위한 실무 매니페스트와 장애 대응

### [표준 YAML] 동적 스토리지 할당 및 Calico 네트워크 정책이 포함된 구성

이 예제는 스토리지 클래스를 통한 PV 자동 생성과 서비스 네트워킹 구조를 보여줍니다.

```yaml
# 1. 동적 프로비저닝을 위한 스토리지 클래스 정의 (CSI 연동)
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-csi-storage
provisioner: cluster.local/nfs-dynamic-provisioner # 실제 설치된 CSI 프로비저너 명칭
reclaimPolicy: Retain # PVC 삭제 시 PV 보존 정책
volumeBindingMode: Immediate

---

# 2. 애플리케이션 배포 및 고유 스토리지 요청
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: data-pvc
spec:
  accessModes:
    - ReadWriteOnce # 블록 스토리지 특성상 한 노드만 마운트 가능
  resources:
    requests:
      storage: 10Gi
  storageClassName: fast-csi-storage

---

# 3. 파드 배포 (Pause 컨테이너 기반 네트워크 공유)
apiVersion: v1
kind: Pod
metadata:
  name: backend-api
  labels:
    app: api
spec:
  containers:
  - name: app-container
    image: my-app:v1
    volumeMounts:
    - name: storage-volume
      mountPath: /data
  volumes:
  - name: storage-volume
    persistentVolumeClaim:
      claimName: data-pvc
```

### [장애 대응] 파드 간 통신 불가 및 'No route to host' 발생 시

* 장애 상황: 동일 노드 혹은 타 노드의 파드끼리 핑(Ping)이나 API 호출이 되지 않으며 네트워크 경로 오류가 발생함.
* 해결 프로세스:
  * CNI 에이전트 상태 확인: 각 노드의 Calico 또는 큐브프로시 파드가 정상 작동 중인지 확인합니다.
kubectl get pods -n kube-system -l k8s-app=calico-node
  * 노드 간 연결성 확인: 오버레이 네트워크(BGP, IPIP)가 노드 간에 정상적으로 맺어져 있는지 확인합니다.
calicoctl node status (Calico 설치 시 전용 도구 사용)
  * 커널 포워딩 설정 체크: 노드 레벨에서 IP 포워딩이 꺼져 있으면 파드 패킷이 나가지 못합니다.
sysctl net.ipv4.ip_forward 명령으로 값이 1인지 확인합니다.
  * MTU 값 불일치 검토: 네트워크 터널링 과정에서 패킷 크기가 커져 단편화(Fragmentation) 문제가 생길 수 있습니다. CNI 설정의 MTU 값을 물리 네트워크에 맞춰 조정해야 합니다.

### 긴급 조치: 큐브프로시 로그를 통해 iptables 규칙 생성 오류 확인

kubectl logs -n kube-system -l k8s-app=kube-proxy
