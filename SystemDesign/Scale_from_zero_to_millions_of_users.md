# 사용자 수에 따른 시스템 확장 (Scale from 0 to Millions of Users)

1. 단일 서버 설정 (Single Server Setup)
DNS 서버: 사용자가 도메인 이름을 입력하면 이를 IP 주소로 변환하여 웹 서버에 접속할 수 있게 합니다
.
웹 서버: IP 주소를 통해 접속한 사용자에게 HTML이나 JSON 형태의 API Payload를 리턴합니다
.
데이터베이스 (DB): 웹 서버 뒷단에서 데이터의 CRUD(Create, Read, Update, Delete) 통신을 담당합니다
.
RDBMS (관계형): MySQL, Oracle, PostgreSQL 등
.
NoSQL (비관계형): 초저지연(Super Low Latency)이 필요하거나, 비정형 데이터(Unstructured Data), 대량의 데이터를 다룰 때 사용합니다
.
2. 스케일링 전략 (Scaling)
수직적 스케일링 (Vertical Scaling / Scale Up): CPU, 메모리 등 하드웨어 사양을 업그레이드하는 방식입니다. 트래픽이 낮을 때 유리하나 한계가 있고 장애 조치(Failover)가 어렵습니다
.
수평적 스케일링 (Horizontal Scaling / Scale Out): 서버의 개수를 늘려 **클러스터(서버 그룹)**를 만드는 방식입니다
.
고려 사항: 데이터 파편화(Sharding), 데이터 재분배(Re-sharding), 특정 데이터에 트래픽이 몰리는 핫스팟 키 문제(Celebrity Problem) 등을 관리해야 합니다
.
3. 가용성 및 성능 최적화
로드 밸런서 (Load Balancer): 트래픽을 여러 서버로 고르게 분산하며, 사설 IP(Private IP)를 사용해 보안을 강화합니다
.
오토 스케일링 그룹 (Auto Scaling Group): CPU나 메모리 부하가 높아지면(예: 90% 이상) 자동으로 서버를 늘려 부하를 조절합니다
.
데이터베이스 복제 (Replication): 쓰기 전용인 **마스터(Master)**와 읽기 전용인 **슬레이브(Slave)**로 나누어 DB 부하를 줄입니다
.
캐시 (Cache): 자주 읽지만 자주 수정되지 않는 데이터를 임시 저장하여 레이턴시를 최적화합니다
.
CDN (Content Delivery Network): 이미지, 비디오 등 정적 콘텐츠를 지리적으로 가까운 서버에서 제공하여 지연 시간을 단축합니다
.
4. 확장 가능한 아키텍처 설계
무상태 웹 계층 (Stateless Web Tier): 서버가 세션이나 프로필 데이터를 직접 저장하지 않고 공유 DB에 저장하는 방식입니다. 이를 통해 서버 확장이 용이해집니다
.
메시지 큐 (Message Queue): 프로듀서(발행), 브로커(저장), 컨슈머(구독) 구조를 통해 비동기 작업 및 데이터 프로세싱을 효율적으로 처리합니다
.
5. 운영 자동화 (Logging, Metrics, Automation)
로깅 및 매트릭: 서버 이벤트를 기록하고 리소스 상태를 시각화하여 DevOps나 SRE 팀이 문제를 확인하게 합니다
.
자동화 도구
:
Jenkins: 작업(Job) 자동화 수행.
Terraform: 스크립트로 클라우드 인프라 관리.
Ansible: 서버 설정 및 애플리케이션 설치 자동화.
