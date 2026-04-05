# 데이터 구조를 활용한 서비스 설계 (Data Structure Service)

시스템 디자인을 이해하기 위해서는 기초적인 데이터 구조가 실제 서비스에서 어떻게 구현되는지 파악하는 것이 중요합니다

1. 선형 자료구조 (Linear Data Structures)
배열(Array) 및 연결 리스트(Linked List)
서비스 예시: 할 일 목록(ToDoList) 애플리케이션
.
특징:
배열: 메모리를 미리 할당하여 고정된 수의 태스크를 관리할 때 적합합니다
.
연결 리스트: 태스크가 추가될 때마다 동적으로 메모리를 할당하므로, 변경이 잦은 리스트 관리에 유리합니다
.
스택(Stack)
서비스 예시: 텍스트 에디터의 되돌리기(Undo) 기능
.
원리: LIFO(Last In, First Out) 구조로, 가장 마지막에 실행된 명령을 가장 먼저 취소하는 역순 실행 방식입니다
.
큐(Queue)
서비스 예시: 은행 번호표 시스템, 콜센터 대기열, 온라인 지원 시스템
.
원리: FIFO(First In, First Out) 구조로, 먼저 들어온 요청이 먼저 서비스를 받는 '선입선출' 방식입니다
.
2. 데이터 검색 및 최적화 (Search & Optimization)
해시 테이블(Hash Table)
서비스 예시: 캐시(Cache) 시스템 (Key-Value 스토어)
.
특징: 반복적으로 액세스되는 데이터를 저장하여 상수 시간(O(1)) 내에 빠르게 데이터를 추출함으로써 DB 부하를 줄이고 성능을 높입니다
.
트라이(Trie) 및 해시 테이블 조합
서비스 예시: 검색 엔진의 자동 완성(Auto-complete) 기능
.
원리: 사용자가 입력하는 글자에 따라 미리 정의된 후보 키워드를 보여주며, 검색 엔진이나 폼 필드 입력 시 효율적으로 사용됩니다
.
3. 우선순위 및 계층 구조 (Priority & Hierarchy)
우선순위 큐(Priority Queue)
서비스 예시: 작업 스케줄러(Task Scheduler) (예: Apache Airflow), OS 프로세스 스케줄링
.
특징: 일반적인 큐와 달리 긴급도(Urgency)나 중요도에 따라 우선순위가 높은 작업을 먼저 실행합니다
.
이진 탐색 트리(Binary Search Tree, BST)
서비스 예시: 데이터베이스 인덱싱(Database Indexing)
.
특징: 데이터를 정렬된 상태로 유지하여 검색, 삽입, 삭제를 빠르게 수행합니다. 균형 잡힌 트리일 경우 **O(log N)**의 속도로 원하는 데이터를 찾을 수 있습니다
.
4. 복잡한 관계 표현 (Complex Relationships)
그래프(Graph)
서비스 예시: 소셜 미디어(Social Media) 관계 서비스
.
구성 요소:
정점(Vertices): 개별 사용자
.
간선(Edges): 사용자 간의 관계(친구, 팔로워 등)
.
유형:
방향 그래프(Directed): 팔로워 관계처럼 방향성이 있는 경우
.
무방향 그래프(Undirected): 서로 친구인 관계(Mutual Friendship)처럼 방향성이 없는 경우
