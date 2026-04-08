# URL 단축 서비스 설계 (Design a URL Shortener)

1. 요구사항 분석 (Requirements)
    - 시스템 설계에 앞서 기능적/비기능적 요구사항을 정의합니다
    - 기능적 요구사항:
        - 긴 URL을 입력받아 짧은 별칭(Alias) 생성
        - 짧은 URL 접속 시 원래의 긴 URL로 재전송(Redirection)
    - 비기능적 요구사항:
        - 높은 가용성(High Availability) 및 확장성(Scalability)
        - 일부 모듈 장애 시에도 전체 시스템은 유지되어야 함(Fault Tolerance)
2. 개략적인 규모 추정 (Back-of-the-envelope Estimation)
    - 하루 1억 건의 쓰기 요청을 가정할 때의 수치입니다
    - 트래픽:
        - 쓰기(Write): 초당 약 1,160건
        - 읽기(Read): 쓰기의 10배 가정 시 초당 약 11,600건
    - 저장 용량 (10년 운영 기준):
        - 총 3,650억 건의 레코드 발생
        - 평균 URL 길이 100바이트 가정 시 약 36.5TB의 스토리지 필요
3. API 엔드포인트 및 데이터 모델
    - API 설계:
        - POST api/v1/data/shorten: 긴 URL을 인자로 받아 짧은 URL 반환
        - GET api/v1/<shortURL>: 긴 URL로 리디렉션 응답 반환
    - 데이터 모델: Id(PK), shortURL, longURL 컬럼으로 구성된 간단한 테이블 구조를 가짐
4. URL 리디렉션 (Redirection) 상세
    - 301 Redirect (Permanently Moved): 브라우저가 응답을 캐싱함. 이후 동일 요청 시 서버를 거치지 않아 서버 부하 감소에 유리함
    - 302 Redirect (Temporarily Moved): 브라우저 캐싱을 하지 않음. 모든 요청이 서버로 전달되어 **클릭 수 추적 및 분석(Analytics)**에 유리함
5. URL 단축 전략 (URL Shortening Strategies)
    - 방법 A: 해시 함수 + 충돌 해결
        - 원리: 긴 URL을 CRC32, MD5, SHA-1 등의 해시 함수에 넣고 앞의 7자리만 사용
        - 해시 값 길이: 62개 문자(0-9, a-z, A-Z)를 사용할 때 7자리면 약 3.5조 개의 URL 표현 가능
        - 충돌 해결: 생성된 짧은 URL이 DB에 존재할 경우, 긴 URL 뒤에 임의의 문자열을 붙여 다시 해싱함
        - 최적화 (Bloom Filter): 특정 요소가 DB에 존재하는지 빠르게 확인하는 공간 효율적 기술을 사용하여 DB 부하를 줄임
    - 방법 B: 62진법 변환 (Base 62 Conversion)
        - 원리: 유일한 숫자 ID를 생성하고, 이 숫자를 62진법 문자로 변환하여 짧은 URL로 사용
        - 장점: 고유한 ID를 기반으로 하므로 해시 충돌이 발생하지 않음
        - 단점: 유일한 ID 생성기(Unique ID Generator)가 반드시 필요하며, ID가 커질수록 URL 길이도 길어짐
6. 전체 시스템 흐름
    - URL 생성 시: 긴 URL 입력 -> (DB 확인) -> 새 ID 생성 -> 62진법 변환 -> DB 및 캐시 저장 -> 짧은 URL 반환
    - URL 접속 시: 사용자 요청 -> 로드 밸런서 -> 웹 서버 -> (캐시/DB 확인) -> 긴 URL 획득 -> 301/302 응답 및 리디렉션 수행
