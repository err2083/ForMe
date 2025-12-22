# equals는 일반 규약을 지켜 재정의하라

equals 메소드는 재정의하기 쉬워보이지만 함정이 많아 자칫하면 끔직한 결과를 초래하므로, 문제를 회피하는 가장 쉬운 길은 아예 재정의 하지 않는 것

재정의 하지 않으면 그 클래스의 인스턴스는 오직 자기 자신과만 같게 되므로, 다음에 열거한 상황 중 하나에 해당한다면 재정의하지 않는 것이 최선임

* 각 인스턴스가 본질적으로 고유함, 값을 표현하는게 아닌 동작하는 개체를 표현하는 클래스가 해당. Thead가 좋은 예로, Object의 equals 메소드는 이러한 클래스에 딱 맞게 구현됨
* 인스턴스의 논리적 동치석을 검사할 일이 없음, 예를 들어 java.util.regex.Pattern은 equals를 재정의해서 두 Pattern의 인스턴스가 같은 정규표현식을 나타내는지를 검사하는, 즉 논리적 동치성을 검사하는 방법이 있지만, 클라이언트는 애초에 필요하지 않다고 판단할 수 있음
* 상위 클래스에서 재정의한 equals가 하위 클래스에도 딱 들어맞음, 예를 들어 대부분의 Set 구현체는 AbstractSet이 구현한 equals를 상속받아 쓰고, List 구현체는 AbstractList로 부터, Map 구현체들은 AbstractMap으로부터 상속 받아 씀
* 클래스가 private이거나 package-private이고 equals 메소드를 호출할 일이 없음. equals가 실수로라도 호출되는 걸 막고 싶다면 equals 메소드를 재정의해서 Excetion을 보내도록 정의

그렇다면 equals를 재정의해야 할때는 언제일까? 객체 식별성이 아닌 논리적 동치성을 확인해야 할때로, 주로 값 클래스(Integer, String)들이 해당, 두 값 객체를 equals로 비교하는 프로그래머는 객체가 같은지가 아니라 값이 같은지를 알고 싶어하며, Map의 Key나 Set의 원소로도 사용할 수 있게 됨

값 클래스라도 해도, 값이 같은 인스턴스가 둘 이상 만들어지지 않음을 보장하는 인스턴스 통제 클래스라면 equals을 재정의 하지 않아도 됨. enum도 여기에 해당하며, 이런 클래스는 논리적으로 같은 인스턴스가 2개 이상 만들어지지 않으니 논리적 동치성과 객체 식별성이 사실상 똑같은 의마

equals 메소드를 재정의할 때는 반드시 다음과 같은 일반 규약을 따라야 함

> equals 메소드는 동치관계를 구현하며 다음을 만족
>>
>> * 반사성(reflexivity): null이 아닌 모든 참조 값 x에 대해, x.equals(x)는 true다
>> * 대칭성(symmetry): null이 아닌 모든 참조 값 x, y에 대해, x.equals(y)가 true면 y.equals(x)도 true다
>> * 추이성(transitivity): null이 아닌 모든 참조 값 x, y, z에 대해 x.equals(y)가 true이고 y.equals(z)도 true면 x.equals(z)도 true다
>> * 일관성(consistency): null이 아닌 모든 참조 값 x, y에 대해, x.equals(y)를 반복해서 호출하면 항상 true를 반환하거나 항상 false를 반환한다
>> * null-아님: null이 아닌 모든 참조 값 x에 대해, x.equals은 false다

Object에 명세에서 말하는 동치관계란 쉽게 말해
