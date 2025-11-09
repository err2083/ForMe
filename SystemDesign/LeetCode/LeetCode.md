# 리트 코드

## 인터뷰 프레임워크

* Requirements
  * 기능적 요구사항: 시스템이 반드 제공하야하는 핵심 기능
  * 비기능적 요구사항: 어떤 품질 특성을 갖춰야 하는지를 설명, 예를 들어, 1) 얼마나 확장 가능한지, 지연 시간이 얼마나 낮아야 하는지 2) 일관성을 우선할지 가용성을 우선할지 선택 3) 환경적인 제약, 확장성, 내구성, 보안 까지 고려 대상, 물론 모든 항목이 시스템에서 중요하지만 시스템을 어렵게 만드는 고유의 비기능 요건이 무엇인가에 대한 답이 더 중요
* Core Entities
  * 핵심 엔티티 식별: 시스템이 저장하게 하거나, API를 통해 주고받는 데이터를 의미. 명확히 이해하면 설계해야 할 API의 형태가 보임
* API
  * API는 사용자와 시스템 간의 계약, 즉 사용자는 어떤 요청을 보낼 수 있고 시스템은 어떤 응답을 돌려줘야 하는지 명확히 정의
* Data Flow
  * 제품 중심의 시스템 디자인 문제에서는 중요도 낮음
* High-Level Design
  * 화이트보드의 컴포넌트와 박스를 그려가면서 앞서 정의한 기능적 요구사항을 충족하는지, 간단한 구조의 시스템을 먼저 그려보는것. 아직 확장성이나 장애 허용성 같은 비기능적인 요소는 고려하지 않음
* Deep Dive
  * 앞서 정의한 비기능적 요구사항들을 하나씩 충족시키기 위해서 시스템에 점진적으로 복잡도를 추가. 성능, 보안, 확장성, 내구성 같은 품질 요건들을 모두 충족하는지 실제 운영 가능한 시스템으로 설계할 수 있게 완성해 나가는 부분

## Requirements

* Functional Requirements
  * View a list of problems
  * View a given problem & code a solution
  * Submit solution & get feedback
  * Support competitions with live leaderboard

* Non-functional Requirements
  * CAP Theorem (Availability >> Consistency)
    * 누가 문제를 수정해도 즉시 최신버전을 보거나, 누가 코드를 제출할때 그 결과가 리더보드에 바로 반영하는것보다 사이트 작동하는 것이 더 중여
  * Security & isolation when running users' code
    * 사용자가 제출한 코드를 직접 실행, 이는 악의적인 코드라면 시스템을 손상시킬 위험 존재
    * 사용자의 코드가 시스템이나 다른 사용자에게 영향을 미치지 않도록 완벽하게 격리된 환경 필요
  * Scale to support competitions with 100k users
    * 구체적인 수치로 표현
  * Fresh / near real-time leaderboard
    * 사용자는 브라우저를 새로고침 하지 않고도 누가 1등인지 순위가 어떻게 바뀌는지 실시간처럼 확인 필요

* Scale
  * 1일 활성 사용자 수, 문제 수, 최대 접속자 수 등 스케일을 명확히 해두는것 중요
  * 50k Daily Active Users (5M total accounts)
  * 3,000 problems
  * 100k peak concurrent users during competitions

## System Core Entities

문제를 처음 보거나 시스템에 익숙하지 않다면 이 단계에서 모든 필드나 컬럼을 다 문서화하는것은 부담스러우면 필요도 없음. 이는 나중 하이레벨 설계 단계에서 구체화하면 됨

이 시점에서 중요한건 데이터 모델에 필요한 엔티티의 종류 즉 객체나 테이블을 명확이 이해하는것

예를 들어 중요한 엔티티는 다음과 같음

User, Problem,
 Submission(제출 코드), Competition

엔티티의 스키마는 하이레벨 설계 단계에서 다루며, 여기서 중요한것은 이 API들이 사용자에게 노출되는 인터페이스라는 점 즉, 기능적 요구사항을 실제로 반영하기 위한 수단

## API Design

API를 설계할때 간단한 방법으로 접근 가능한데, 기능적 요구사항 목록의 각 항목을 만족시키는 API 하나를 만드는것. 보통 하나의 기능적 요구사항은 하나의 API로 연결

|Feature|Method|Endpoint|Notes|
|---|---|---|---|
|View problem list|GET|/problems?category&difficulty&page&size|Supports filtering and pagination|
|View problem detail|GET|/problems/{problemId}|Uses Path param to fetch specific problem|
|Submit solution|POST|/problems/{problemId}/submit|Body: code, language, competitionId?|
|Get leaderboard|GET|/leaderboard/{competitionId}?page&size|Large volume -> pagination required|

필수 요소는 path 파라미터 그리고 선택 요소는 query 파라미터 그리고 새로운 리소스를 만들때는 post를 호출하며, 요청 body는 필요한 데이터를 담는데 사용

많은 양의 데이터를 반환할 때는 pagination이 필수

필터링 조건은 유연하게 쿼리로 처리

## High-Level Design: Start Simple, Stay Focused

### Design Goal

하이레벨 디자인의 목적은 기능적 요구사항 충족

앞서 정의한 API들을 다시 살펴보며 각 API가 도작하기 위헤 어떤 컴포넌트를 구성해야 하는지 중심으로 단순한 시스템 구조를 먼저 설계.

이 단계에서는 확장성, 성능, 장애 대응 요소는 고려하지 않음

### Why Simple First?

기능만 제대로 동작하면 되는 수준으로 구조 시작, 이는 순차적으로 작업함으로써 문제의 핵심에 집중하며 불필요한 복잡성으로 흐트러지는 것을 방지

### Common Interview Pitfall

인터뷰시 자주 발생하는 실수로 요구사항에 없는 요소에 몰두, 예를 들어 리뷰 기능만 설계하면 되는 상황에서 댓글이나 알림, 이메일 전송 기능까지 설계하는 경우 이러한 것들이 불필여한 확장에 해당

기능적 요구사항은 명확히 주어지고 인터뷰 시간도 제한이기에 요구사항에만 집중하는 것이 매우 중요

### First API: Problem List

* 요구사항이 단순하기에 클라이언트-서버 방식으로 접근
* 클라이언트로부터 요청을 받아 문제 리스트를 쿼리하고 그 결과를 반환
* 이 구조만으로도 문제 리스트 조회기능은 충분히 구현
* 이런식으로 나머지 API도 하나씩 기능을 만족시키는 방향으로 구조 확장

이제 데이터베이스를 추가

## High-Level Design: Database + API Integration

* 데이터베이스는 현재 단계에서 Problem Entity를 저장하는 용도로 사용
* 실제 설계 과정에서 필요한 데이터 모델을 하나씩 구체화, 예를 들어 사용자가 문제 리스트를 요청하면 아이디,분류 등 필드를 포함하여 응답.
* 추가적인 필드는 점진적으로 확장
* request flow는 매우 단순하게 클라이언트가 problems API를 호출하면 서버는 데이터베이스에 쿼리르 보내 문제 리스트를 가쟈오고 그 결과를 반환
* 이 시스템은 특별히 제약사항이 없기 때문에 특정 DB를 써야할 필요가 없음 PostgreSQL 같은 관계형 DB나 NoSQL DB를 써도 무관, 선호하는 기술에 따라 선택
