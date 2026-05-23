# Objects 중급

## 1. 서비스 디스커버리의 확장과 동적 스토리지 제어의 내부 메커니즘 분석

쿠버네티스 중급 단계에서는 단순한 파드 실행을 넘어, 워크로드 간의 정교한 연결성(Networking)과 데이터의 영속성(Storage), 그리고 클러스터 자원에 대한 접근 제어(Security)를 다룹니다.

### 1) 서비스 네트워킹의 심화: Headless Service와 DNS FQDN

일반적인 서비스는 ClusterIP를 통해 부하 분산을 수행하지만, **Headless Service**는 `clusterIP: None` 설정을 통해 단일 진입점 없이 파드의 IP들을 직접 노출합니다.

* **동작 원리:** 서비스 생성 시 ClusterIP가 할당되지 않으며, 쿠버네티스 내부 DNS 서버에 서비스 이름으로 질의할 경우 서비스에 연결된 모든 파드의 A 레코드(IP 목록)를 반환합니다.
* **존재 이유:** 파드 각각과 직접 통신해야 하는 상태 기반 애플리케이션(데이터베이스 클러스터 등)에서 개별 노드를 식별하기 위해 사용됩니다. 파드에 `hostname`과 `subdomain`을 설정하면 `[호스트명].[서비스명].[네임스페이스].svc.cluster.local` 형태의 고유한 **FQDN(Fully Qualified Domain Name)**을 부여받아 고정된 주소로 통신이 가능해집니다.

### 2) 외부 연결의 추상화: ExternalName과 Endpoint

애플리케이션 수정 없이 외부 자원과의 연결 정보를 관리하는 메커니즘입니다.

* **ExternalName:** 서비스 내부에서 외부 도메인(예: github.com)을 가리키도록 설정합니다. 파드가 내부 서비스 이름을 호출하면 DNS 단에서 외부 CNAME으로 리다이렉션되므로, 외부 주소가 변경되어도 파드의 재배포 없이 서비스 정의만 수정하면 됩니다.
* **Endpoint:** 서비스와 파드를 연결하는 실제 데이터 객체입니다. 보통 라벨 셀렉터로 자동 생성되지만, 셀렉터 없이 서비스를 만들고 엔드포인트를 수동으로 정의하면 클러스터 외부의 특정 IP/Port를 쿠버네티스 서비스처럼 내부 파드들이 이용할 수 있게 됩니다.

### 3) 스토리지 관리 자동화: Dynamic Provisioning과 Reclaim Policy

관리자가 일일이 PV(Persistent Volume)를 만들지 않아도 되는 **다이나믹 프로비저닝**은 **StorageClass**를 핵심으로 합니다.

* **매커니즘:** 사용자가 PVC(Persistent Volume Claim)를 생성할 때 특정 `StorageClass`를 지정하면, 쿠버네티스는 해당 클래스에 정의된 프로비저너(StorageOS, AWS EBS 등)를 통해 물리적 스토리지를 즉시 생성하고 PV를 자동으로 바인딩합니다.
* **Reclaim Policy (재사용 정책):** PVC가 삭제될 때 PV와 데이터를 처리하는 방식입니다.
  * **Retain:** PV 상태가 `Released`로 변하며 데이터는 유지되지만, 다른 PVC가 재사용할 수 없어 수동 삭제가 필요합니다.
  * **Delete:** PVC 삭제 시 PV와 실제 물리 스토리지까지 모두 자동으로 삭제됩니다.

### 4) 보안 가버넌스: RBAC(Role-Based Access Control)

인증(Authentication)을 거친 사용자나 파드가 어떤 작업을 할 수 있는지 결정하는 권한 관리 모델입니다.

* **구조:** 권한의 집합인 **Role(또는 ClusterRole)**과 이를 주체(User, ServiceAccount)에게 연결하는 **RoleBinding(또는 ClusterRoleBinding)**으로 구성됩니다.
* **논리적 범위:** `Role`은 특정 네임스페이스 내 자원에 국한되며, `ClusterRole`은 노드, PV 등 클러스터 전역 자원이나 모든 네임스페이스에 걸친 공통 권한을 정의할 때 사용됩니다.

---

## 2. 아키텍처 설계 역량 검증을 위한 시니어 엔지니어 자가 진단 질문

**질문 1:** 특정 파드가 외부 DB(IP: 1.2.3.4)와 통신해야 합니다. 보안 정책상 도메인이 아닌 IP로만 접근이 가능한데, 향후 DB의 IP가 변경될 가능성이 큽니다. 파드 내부의 소스 코드를 수정하지 않고 쿠버네티스 오브젝트 설정을 통해 이 문제를 해결하는 가장 적절한 구조를 설명하십시오.

**질문 2:** `StorageClass`를 통해 동적으로 생성된 PV의 `Reclaim Policy`가 `Delete`로 설정되어 있습니다. 실수로 파드와 연결된 PVC를 삭제했을 때, PV의 상태 변화와 실제 데이터의 존속 여부를 단계별로 설명하십시오.

**질문 3:** 네임스페이스 `A`에 존재하는 `ServiceAccount`가 네임스페이스 `B`에 있는 파드의 리스트를 조회해야 합니다. 이때 어떤 종류의 RBAC 오브젝트들을 생성해야 하며, 특히 `RoleBinding`을 어느 네임스페이스에 위치시켜야 하는지 논리적 근거를 제시하십시오.

<details>
<summary style="cursor: pointer; color: #007bff;">👉 자가 진단 질문 정답 및 해설 보기</summary>

**정답 1:** 라벨 셀렉터가 없는 **Service** 오브젝트를 생성하고, 서비스와 동일한 이름의 **Endpoint** 오브젝트를 수동으로 생성하여 `subsets.addresses.ip` 필드에 DB IP(1.2.3.4)를 명시합니다. 파드는 서비스의 이름만 바라보고 통신하며, IP가 변경되면 수동으로 생성한 엔드포인트의 IP 정보만 업데이트하면 됩니다.

**정답 2:**

1. PVC가 삭제되면 해당 PVC와 연결되어 있던 PV와의 바인딩이 끊어집니다.
2. PV의 정책이 `Delete`이므로, 쿠버네티스 컨트롤러는 PV 오브젝트를 즉시 삭제합니다.
3. 이와 동시에 스토리지 프로비저너에 삭제 명령이 전달되어 물리적 디스크에 저장된 데이터까지 영구적으로 소멸됩니다.

**정답 3:** 네임스페이스 `B`에 파드 조회 권한을 가진 **Role**을 생성하고, 동일한 네임스페이스 `B`에 **RoleBinding**을 생성해야 합니다. `RoleBinding`의 `subjects`에는 네임스페이스 `A`의 `ServiceAccount`를 지정합니다. 권한은 '자원이 존재하는 공간(B)'을 기준으로 제어되어야 하므로 바인딩은 네임스페이스 `B`에 위치해야 합니다.

</details>

---

## 3. RBAC 기반 보안 설계 표준 예제 및 연결성 트러블슈팅

### [표준 YAML] 서비스 계정 및 네임스페이스 권한 제어 예제

이 예제는 특정 애플리케이션 파드가 API 서버에 접근하여 자신의 네임스페이스 내 파드 정보를 조회할 수 있도록 구성된 표준 매니페스트입니다.

```yaml
# 1. 애플리케이션용 전용 서비스 계정 생성
apiVersion: v1
kind: ServiceAccount
metadata:
  name: api-reader-sa
  namespace: app-ns

---

# 2. 파드 조회 권한만 정의한 Role 생성
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: pod-reader-role
  namespace: app-ns
rules:
- apiGroups: [""] # 파드는 Core API 그룹에 속함
  resources: ["pods"]
  verbs: ["get", "list", "watch"] # 생성/삭제를 제외한 조회 권한만 부여

---

# 3. 서비스 계정과 Role을 연결
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: read-pods-binding
  namespace: app-ns
subjects:
- kind: ServiceAccount
  name: api-reader-sa
  namespace: app-ns
roleRef:
  kind: Role
  name: pod-reader-role
  apiGroup: rbac.authorization.k8s.io
```

### [장애 상황] 파드 내에서 API 호출 시 '403 Forbidden' 발생

* 장애 증상: 파드 내부의 애플리케이션이 쿠버네티스 API를 호출하여 자원 정보를 가져오려 할 때 is forbidden: User "system:serviceaccount:..." cannot list resource 에러가 발생함.
* 해결 프로세스:
  * 계정 확인: 파드가 어떤 ServiceAccount를 사용 중인지 확인합니다. 명시하지 않았다면 default 계정을 사용합니다.
    * 명령어: kubectl get pod [파드명] -o yaml | grep serviceAccountName
  * 권한 바인딩 점검: 해당 서비스 계정에 적절한 Role 또는 ClusterRole이 바인딩되어 있는지 확인합니다.
    * 명령어: kubectl get rolebindings,clusterrolebindings -A | grep [서비스계정명]
  * 권한 세부 내용 검증: 바인딩된 Role의 rules에 대상 자원(resources)과 작업(verbs)이 정확히 명시되었는지 대조합니다.
  * 토큰 유효성 테스트: kubectl auth can-i 명령어를 사용하여 해당 계정의 권한을 시뮬레이션합니다.

### 특정 서비스 계정이 파드를 리스트할 권한이 있는지 즉시 확인

kubectl auth can-i list pods --as=system:serviceaccount:app-ns:api-reader-sa -n app-ns

만약 'no'라고 나온다면 Role 또는 RoleBinding의 Resource/Verb 오타나 네임스페이스 불일치를 수정해야 합니다
