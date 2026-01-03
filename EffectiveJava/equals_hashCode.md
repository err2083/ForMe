# equals를 재정의하려거든 hashCode도 재정의하라

equals를 재정의한 클래스 모두에서 hashCode도 재정의 해야함. 그렇지 않으면 hashCode 일반 규약을 어기게 되어 해당 클래스의 인스턴스를 HashMap이나 HashSet 같은 컬렉션의 원소로 사용할 때 문제를 일으킴

다음은 Object 명세에서 발췌한 규약

* equals 비교에 사용되는 정보가 변경되지 않았다면, 애플리케이션이 실행되는 동안 그 객체의 hashCode 메소드는 몇 번을 호출해도 일관되게 항상 같은 값을 반환, 단 애플리케이션을 다시 실행한다면 이 값이 달라져도 상관 없음
* equals(Object)가 두 객체를 같다고 판단했다면, 두 객체의 hashCode는 똑같은 값을 반환
* equals(Object)가 두 객체를 다르다고 판단했더라도, 두 객체의 hashCode가 서로 다른 값을 반환할 필요는 없지만, 단 다른 객체에 대해서는 다른 값을 반환해야 해시테이블의 성능이 좋아짐

hashCode 재정의를 잘못했을 때 크게 문제가 되는 조항은 두 번째로, 논리적으로 같은 객체는 같은 해시코드를 반환해야함. equals는 물리적으로 다른 두 객체를 논리적으로 같다고 할 수 있는데, Object의 기본 hashCode 메소드는 이 둘을 전혀 다르다고 판단하여, 구약과 달리 서로 다른 값을 반환

예시로 PhoneNumber 클래스의 인스턴스를 HashMap의 원소로 사용한다고 생각

```java
Map<PhoneNumber, String> m = new HashMap<>();
m.put(new PhoneNumber(707, 867, 5309), "제니");
m.get(new PhoneNumber(707, 867, 5309));
```

이 코드 다음에 m.get(new PhoneNumber(707, 867, 5309));를 실행하면 "제니"가 나와야 할 거 같지만, 실제로는 null을 반환. 여기에는 2개의 PhoneNumber 인스턴스가 사용되었는데, 하나는 HashMap에 넣을때 사용하였고, 두 번째는 꺼내려할 때 사용. PhoneNumber 클래스는 hashCode를 재정의하지 않았기 때문에 논리적 동치인 두 객체가 서로 다른 해시코드를 반환하여 두 번째 규약을 지키지 못함. 참고로 두 인스턴스가 같은 버킷에 담더라도 get은 null을 반환하는데, HashMap은 해시코드가 다른 엔트리끼리는 동치성 비교조차 하지 않도록 최적화가 되어있음

이 문제는 hashCode 메소드만 작성해주면 해결 됨. 다음은 비적적할 구현 방법

```java
-- 최악의 hashCode 구현 - 사용 금지
@Override
public int hashCode() { return 42; }
```

이 코드는 동치인 모든 객체에서 똑같은 해시코드를 반환하니 적법하지만, 모든 객체가 똑같은 값만 내어주므로 모든 객체가 해시테이블의 버킷 하나에 담겨 마치 연결 리스트처럼 동작. 그 결과 평균 수행시간이 O(1)인 해시테이블이 O(n)으로 느려져서, 객체가 많아지면 도저히 쓸 수 없게 됨

이상적인 해시 함수는 서로 다른 인스턴스들읋 32비트 정수 범위에 균일하게 분배해야 함.

다음은 좋은 hashCode를 작성하는 간단한 요령

1. int 변수 result를 선언한 후 값 c로 초기화, 이때 c는 해당 객체의 첫번째 핵심 필드로 이후에 설명
2. 해당 객체의 나머지 핵심 필드 f 각각에 대해 작업 수행
3. 해당 필드의 해시코드 c를 계산
4. 기본 타입 필드라면 Type.hashCode(f)를 수행, 여기서 Type은 해당 기본 타입의 박싱 클래스
5. 참조 타입 필드면서 이 클래스의 equals 메소드가 이 필드의 equals를 재귀적으로 호출해 비교한다면, 이 필드의 hashCode를 재귀적으로 호출. 만약 계산이 복잡해지면, 이 필드의 표준형(canonical representation)을 만들어 그 표준형의 hashCode를 호출. 필드의 값이 null이면 전통적으로 0을 사용(다른 상수여도 괜챃음)
6. 필드가 배열이라면, 핵심 원소 각각을 벼로 필드처럼 다룸. 이상의 규칙을 재귀적으로 적용해 각 핵심 원소의 해시코드를 계산. 만약 배열의 핵심 원소가 하나도 없다면 단순히 상수 사용. 모든 원소가 핵심 원소라면 Arrays.hashCode 사용
7. 계산된 해시코드 c로 result를 갱신 (result = 31 * result + c;)
8. result 반환

hashCode를 다 구현핬다면 이 메소드가 동치인 인스턴스에 대해 똑같은 해시코드를 반환하는지 단위 테스트를 작성 (equals와 hashCode 메소드를 AutoValue로 생성했다면 패스해도 됨)

파생 필드는 해시코드 계산에서 제외해도 됨, 즉 다른 필드로부터 계산해 낼 수 있는 필드는 모두 무시. 또한 equals 비교에 사용되지 않은 필드는 반드시 제외해야하는데 그렇지 않으면 hashCode 규약 두 번째를 어기게 됨

7번에서 곱셉 31 \* result는 필드를 곱하는 순서에 따라 result 값이 달라지는데, 그 결과 클래스에 비슷한 필드가 여러 개일 때 해시 효과를 크게 높여줌. 예를 들어 String의 hashCode를 곱셈 없이 구현한다면 모든 아나그램(anagram, 구성하는 철자가 같고 그 순서만 다른 문자열)의 해시코드가 같아짐. 곱할 숫자 31은 홀수이면서 소수라 정함. 만일 짝수이고 오버플로가 발생하면 정보를 읽게 됨. 2를 곱하는 것은 시프트 연산과 같은결과를 내기 때문이며, 소수를 곱하는 이유는 전통적으로 그리 해왔음. 결과적으로 31을 이용하면 이 곱셈을 시프트 연산과 뺄셈으로 대체해 최적화할 수 있음(31 \* i 는 (i << 5) - i 와 동일). 요즘 vm은 이런 최적화를 자동으로 해줌

```java
-- 전형적인 hashCode 메소드
@Override
public int hashCode() {
    int result = Short.hashCode(areaCode);
    result = 31 * result + Short.hashCode(prefix);
    result = 31 * result + Short.hashCode(lineNum);
    return result;
}
```

이 메소드는 PhoneNumber 인스턴스의 핵심 필드 3개만을 이용하여 간단하게 해시코드를 만드는데, 이 과정에서 비결정적 요소는 전혀 없으므로 동치인 PhoneNumber 인스턴스들은 같은 해시코드를 가질것음

앞서 작성한 해시 함수 제작 요령은 충분히 훌륭하지만, 해시 충돌이 더욱이 적은 방법을 꼭 써야 한다면 구아바의 com.google.common.hash.Hashing을 참고

Object 클래스는 임의의 개수만큼 개게를 받아 해시코드를 계산해주는 정적 메소드는 hash를 제공하는데, 앞서 구현한 코드와 비슷한 수준의 hashCode를 만들수 있지만, 아쉽게도 속도가 느린데, 입력 인수를 담기위한 배열이 만들어지고, 입력중 기본 타입이 있다면 박싱과 언받싱도 거쳐야 하기 때문. 그린 hash 메소드는 성능에 민감하지 않는 상황에서만 사용.

```java
-- 한 줄 짜리 hashCode 메소드 - 성능이 아쉬움
@Override
public int hashCode() {
    return Objects.hash(lineNum, prefix, areaCode);
}
```

클래스가 불변이고 해시코드를 계산하는 비용이 크다면 매번 새오 계산하기 보다는 캐싱하는 방식을 고려. 이 타입의 객체가 주로 해시의 키로 사용될 것 같다면 인스턴스가 만들어질 대 해시코드를 계산, 해시의 키로 사용되지 않는 경우라면 hashode가 처음 불릴 때 계산하는 지연 초기화 전력, 단 필드를 지연 초기화하려면 그 클래스를 스레드 앙ㄴ전하게 만들도록 신경 써야함.

```java
-- 해디코드를 지연 초기화하는 hashCode 메소드 - 스레드 안정성까지 고려
private int hashCode; // 자동으로 0으로 초기화

@Override
public int hashCode() {
    int result = hashCode;
    if (result == 0) {
        result = Short.hashCode(areaCode);
        result = 31 * result + Short.hashCode(prefix);
        result = 31 * result + Short.hashCode(lineNum);
        hashCode = result;
    }
    return result;
}
```

성능을 높인다고 해시코드를 계산할때 핵심 필드를 생략해서는 안됨. 이는 속도는 빨라지지만, 해시 품질이 나빠져서 해시테이블의 성능이 심각하게 떨어짐

이 문제는 자바 2 전의 String이 최대 16문자만으로 해시코드를 계산하였는데, URL처럼 계층적인 이름을 사용할때 해시테이블의 속도가 선형으로 느려지는 심각한 문제가 발생됨

hashCode가 반환하는 값의 생성 규칙을 API 사용자에게 자세히 알려주지 않아야 함. 그래야 클라이언트가 이 값에 의지 안하게 되고, 추후에 계산 방법도 바꿍수 있음. String과 Integer를 포함해, 자바 라이브러리의 많은 클래스에서 hashCode 메소드가 반환하는 정확한 값을 알려주는데, 이는 실수지만 바로잡기에는 너무 늦었고, 향후 일리즈에서 해시 기능을 개선할 여지도 없어짐. 자세한 규칙을 공표하지 않았다면, 해시 기능에서 결함을 발견했거나 더 좋은 해시 방식을 알아낸 경우 수정할 수 있음

equals를 재정의할 때는 hashCode도 반드시 재정의 해야함. 재정의한 hashCode는 Object의 API 문서에 기술된 일반 규약을 따라야 하며, 서로 다른 인스턴스라면 되도록 해시코드도 서로 다르게 구현해야 함. AutoValue 프레임워크를 사용하면 equals와 hashCode를 자동으로 만들어주며, IDE도 일부 이런 기능을 제공함
