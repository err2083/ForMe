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

Object에 명세에서 말하는 동치관계란 쉽게 말해 집합을 서로 같은 원소들로 이루어진 부분집합으로 나누는 연산이며, 이 부분집합을 동치류(equivalence calss; 동치 클래스)라 함. equals 메소드가 쓸모 있으며녀 모든 원소가 같은 동치류에 속한 어떤 원소와도 서로 교환이 가능

동치관계를 만족시키기 위한 다섯 요건을 살펴보면

반사성은 객체는 자기 자신과 같아야함. 만일 이 요건을 어긴 클래스릐 인스턴스를 컬렉션에 넣은 다음 contains 메소드를 호출하면 방금 넣은 인스턴스가 없다고 나올 것임

대칭성은 두 객체는 서로에 대한 동치 여부에 똑같이 답해야함. 대소문자를 구별하지 않는 문자열을 구현한 클래스를 예로 들면, 이 클래스는 toString 메소드는 원본 문자열의 대소문자를 그대로 돌려주지만 equals에서는 대소문자를 무시함

```java
public final class CaseInsensitiveString {
    private final String s;

    public CaseInsensitiveString(String s) {
        this.s = Objects.requireNonNull(s);
    }

    // 대칭성 위배
    @Override
    public public boolean equals(Object o) {
        if (o instanceof CaseInsensitiveString) {
            return s.equalsIgnoreCase(((CaseInsensitiveString) o).s);
        }
        if (o instanceof String) { // 한 방향으로만 작동
            return s.equalsIgnoreCase((String) o);
        }
        return false
    }
}
```

CaseInsensitiveString의 equals는 순진하게 일반 문자열과도 비교를 시도하는데, 다음처럼 CaseInsensitiveString와 String 객체가 있으면

```java
CaseInsensitiveString cis = new CaseInsensitiveString("Polish");
String s = "polish";
```

예상할 수 있듯 cis.equals(s)는 true를 반환하지만 CaseInsensitiveString의 equals는 일반 String을 알고 있지만, String의 equals는 CaseInsensitiveString 존재를 모르기에 s.equals(cis)는 false를 반환

비슷하게 컬렉션을 생각해보면

```java
List<CaseInsensitiveString> list = new ArrayList<>();
list.add(cis);
```

이 다음에 list.contains(s)를 호출하면 openJDK 구현에 따라 false가 나옴, 즉 equals 규약을 어기면 그 객체를 사용하는 다른 객체들이 어떻게 반응할지 알수 없음

이 문제를 하결하려면 CaseInsensitiveString의 equals를 String과 연동하겠다는 요구를 버려야 함. 그러면 다음과 같은 간단한 코드가 나옴

```java
@Override
    public public boolean equals(Object o) {
        return o instanceof CaseInsensitiveString && s.equalsIgnoreCase(((CaseInsensitiveString) o).s);
        
    }
```

추이성은 첫 번째 객체와 두 번째 객체가 같고, 두 번째 객체와 세 번째 객체가 같으면 첫 번째 객체와 세 번째 객체도 같아야 한다는 뜻으로, 상위 클래스에는 없는 새로운 필드를 하위 클래스에 추가하는 상황을 보면

```java
public class Point {
    private final int x;
    private final int y;

    public Point(int x, int y) {
        this.x = x;
        this.y = y;
    }

    @Override
    public boolean equals(Object o) {
        if (!(o instanceof Point)) {
            return false;
        }
        Point p = (Point)o;
        return p.x == x && p.y == y;
    }
}

public class ColorPoint extends Point {
    private final Color color;

    public ColorPoint(int x, int y, Color color) {
        super(x, y);
        this.color = color;
    }
}
```

equals를 그대로 둔다면, Point의 구현이 상속되어 색상 정보는 무시한 채 비교를 수행. 이는 중요한 정보를 놓치게 되므로 다음 코드처럼 비교 대상이 또 다른 ColorPoint이고 위치와 색상이 같을 때만 true를 반환하는 equals를 생각

```java
@Override
public boolean equals(Object o) {
    if (!(o instanceof ColorPoint)) {
        return false;
    }
    return super.equals(0) && ((ColorPoint) o).color == color;
}
```

이 메소드는 일 반 Point를 ColorPoint와 비교한 결과와 그 둘을 바꾸어 비교한 결과가 다른데, Point의 equals는 색상을 무시하고, ColorPoint의 equals는 입력 매개 변수가 다르니 false를 반환함

```java
Point p = new Point(1, 2);
ColorPoint cp = new ColorPoint(1, 2, Color.RED);
```

p.equals(cp)는 true를, cp.equals(p)는 false를 반환, 그렇다면 ColorPoint.equals가 Point와 비교할 때는 색상을 무시하게 하면 어떻게 될까?

```java
@Override
public boolean equals(Object o) {
    if (!(o instanceof Print)) {
        return false;
    }
    // o가 일반 Point면 색상을 무시하고 비교
    if (!(o instanceof ColorPoint)) {
        return o.equals(this);
    }
    return super.equals(0) && ((ColorPoint) o).color == color;
}
```

이 방식은 대칭성을 지켜주지만, 추이성이 위반됨

```java
ColorPoint p1 = new ColorPoint(1, 2, Color.RED);
Point p2 = new Point(1, 2);
ColorPoint p3 = new ColorPoint(1, 2, Color.BLUE);
```

p1.equals(p2)와 p2.equals(p3)는 true를 반환하지만 p1.equals(p3) 가 false를 반환, 이는 p1과 p2, p2와 p3를 비교할때는 색상을 무시했지만, p1과 p2는 색상까지 고려했기 때문

또한, 이 방식은 Point의 또 다른 하위 클래스 SmellPoint를 만들고 equals를 같은 방식으로 구현했을때 myColrPoint.equals(mySmellPoint)를 호출하면 무한 재귀에 빠질수 있음

이 현상은 모든 객체 지향 언어의 동치관계에서 나타나는 근본적인 문제로 구체 클래스를 확장해 새로운 값을 추가하면서 equals 규약을 만족하는 방법은 존재하지 않음.

이는 마치 equals 안의 instanceof 검사를 getClass 검사로 바꾸면 규약도 지키고 값도 추가하면서 구체 클래스를 상속 가능한거처럼 보이지만

```java
@Override
public boolean equals(Objevt o) {
    if (o == null || o.getClass() != getClass()) {
        return false;
    }
    Point p = (Point) o;
    return p.x == x && p.y == y;
}
```

이번 equals는 같은 구현 클래스의 객체와 비교할 때만 true를 반환하지만, 실제로는 사용이 불가능한데, Point의 하위 클래스는 정의상 여전히 Point이므로 어디서든 Point로 사용되어야 하는데, 이 방식은 그렇지 못함

예를 들어 주어진 점이 (반지름이 1인) 단위 원 안에 있는지를 판별하는 메소드가 필요하다고 해보면

```java
private static final Set<Point> unitCircle = Set.of(
    new Point(1, 0), new Point(0, 1), new Point(-1, 0), new Point(0, -1)
);

public static boolean onUnitCircle(Point p) {
    return unitCircle.contains(p);
}
```

가장 빠른 방법은 아니지만, 이렇게 구현을 하고 값을 추가하지 않는 방식으로 Point를 확장하면

```java
public class CounterPoint extends Point {
    private static final AtomicInteger counter = new AtomicInteger();

    public CounterPoint(int x, int y) {
        super(x, y);
        counter.incrementAndGet();
    }
    public static int numberCreated() {
        return counter.get();
    }
}
```

리스코프 치환 원칙에 따르면, 어떤 타입에 있어 중요한 속성이라면 그 하위 타입에서도 마찬가지로 중요함. 따라서 그 타입의 모든 메소드가 하위 타입에서도 똑같이 잘 작동해야함. 이는 앞서 말한 "Point의 하위 클래스는 정의상 여전히 Point이므로 어디서든 Point로 사용"를 격식 있게 표현한 말임

만약 CounterPoint의 인스턴스를 onUnitCircle 메소드에 넘기면 어떻게 될까? Point 클래스의 equals를 getClass를 사용해 작성했다면 CounterPoint 인스턴스의 x, y 값과는 무관하게 onUnitCircle은 false를 반환

원인은 컬렉션 구현체에서 주어진 원소를 담고 있는지 확인하느 방법에 있는데, onUnitCircle에서 사용한 Set을 포함하여 대부분의 컬렉션은 이 작업에 equals 메소드를 이용하는데, CounterPoint의 인스턴스는 어떤 Point와도 같을수가 없음

반면 Point의 equals를 instanceof 기반으로 구현했다면 CounterPoint 인스턴스를 건네줘도 onUnitCircle 메소드가 제대로 동작할 것임

구체 클래스의 하위 클래스에서 값을 추가하는 방법은 없지만 괜찮은 우회 방법이 있는데, 상속 대신 컴포지션을 사용하면 됨

Point를 상속하는 대신 Point를 ColorPoint의 private 필드로 두고 ColorPoint와 같은 위치의 일반 Point를 반환하는 view 메소드를 public으로 추가하는 방식임

```java
public class ColorPoint {
    private final Point point;
    private final Color color;

    public ColorPoint(int x, int y, Color color) {
        point = new Point(x, y);
        this.color = Objects.requireNonNull(color);
    }

    // 이 ColorPoint의 Point view를 반환
    public Point asPoint() {
        return point;
    }

    @Override
    public boolean equals(Object o) {
        if (!(o instanceof ColorPoint)) {
            return false;
        }
        ColorPoint cp = (ColorPoint) o;
        return cp.point.equals(point) && cp.color.equals(color);
    }
}
```

자바 라이브러리에도 구체 클래스를 확장해 값을 추가한 클래스가 종종 있는데, 예시로 java.sql.Timestamp는 java.util.Date를 확장한 후 nanoseconds 필드를 추가했는데, 그 결과로 Timestamp의 equals는 대칭성를 위배했으며, Date 객체와 한 컬렉션에 넣거나 서로 썩어 사용하면 엉뚱하게 동작 할 수 있음. 그래서 Timestamp의 API 설명에는 Date와 섞어 쓸 때는 주위사항을 언급하고 있음. Timestamp를 이렇게 설계한 것은 실수니 절대 따라해서는 안됨.

> 추상 클래스의 하위 클래스라면 equals 규약을 지키면서 값을 추가할수 있는데 클래스 계층 구조를 활용하면 됨. 예를 들어 아무런 값을 갖지 않는 추상 클래스인 Shape를 위에 두고, 이를 확장하여 radius 필드를 추가한 Circle 클래스와, length와 width 필드를 추가한 Rectangle 클래스를 만들면, 상위 클래스를 직접 인스턴스를 만드는게 불가하다면 지금까지 말한 문제는 발생하지 않음

일관성은 두 객체가 같다면 수정이 없는 한 영원히 같아야 한다는 뜻, 가변 객체는 비교 시점에 따라 서로 다를 수도 혹은 같은 수도 있는 반면, 불면 객체는 한번 다르면 끝까지 달라야 함

클래스가 불변이든 가변이든 equals의 판단에 신뢰할 수 없는 자원이 끼어들어서는 안됨. 이 제약을 어기면 일관성 조건을 만족시키가 어려운데, 예를 들어 java.net.URL의 equals는 주어진 URL과 매핑된 호스트의 IP 주소를 이용해 비교하는데, 호스트 이름을 IP 주소로 바꾸려면 네트워크를 통해야 하는데 그 결과가 항상 같다고 보장할수가 없음. 이는 URL의 equals가 일반 규약을 어기게 하고 실무에서도 문제를 발생시킴. 이런 문제를 피하려면 equals는 항시 메모리에 존재하는 객체만을 사용한 결정적 계산만 수행해야 함

null-아님의 경우 이름처럼 모든 객체가 null과 같지 않아야 한다는 뜻으로, 의도하지 않았음에도 o.equals(null)이 true를 반환하는 상황은 어렵지만 NPE를 던지는 코드는 흔할 것임. 이 일반 규약은 이런 경우도 허용하지 않음. 수 많은 클래스가 다음 코드처럼 입력이 null 인지 확인해 자신을 보호해는데, 이러한 검사는 필요치 않음

```java
// 명시적 null 검사 - 필요 없음
@Override
public boolean equals(Object o) {
    if (o == null) {
        return false;
    }
}
```

동치성을 검사하려면 equals는 건네받은 객체를 형변환한 후 필수 필드들의 값을 알아내야 하고, 그러려면 형변환에 앞서 instanceof 연산자로 입력 매개변수가 올바른 타입인지 검사해야 함

```java
// 묵시적 null 검사 - 이쪽이 나음
@Override
public boolean equals(Object o) {
    if (!(o instanceof MyType)) {
        return false;
    }
    MyType mt = (MyType) o;
}
```

equals가 타입을 확인하지 않으면 잘못된 타입이 인수로 주어질때 ClassCastException을 던져서 일반 규약을 위배하게 됨. instanceof는 (두 번째 피연산자와 무관하게) 첫 번째 피연산잦가 null이면 false를 반환, 따라서 입력이 null 이면 타입 확인 단계에서 false를 반환하기 때문에 null 검사를 명시적으로 하지 않아도 됨.

지금까지의 내용을 종합해서 양질의 equals 메소드 구현 방법을 단계별로 정리하면

1. == 연산자를 사용해 입력이 자기 자신의 참조인지 확인. 자기 자신이면 true를 반환하는데, 이는 단순한성능 최적화용으로 비교 작업이 복잡한 상황일 때 값어치를 함
2. instanceof 연산자로 입력이 올바른 타입인지 확인. 그렇지 않으면 false를 반환. 이때의 올바른 타입은 equals가 정의된 클래스인 것이 보통이지만, 가끔은 그 클래스가 구현한 특정 인터페이스가 될 수도 있음. 어떤 인터페이스는 자신을 구현한 (서로 다른) 클래스끼리도 비교할 수 있도록 equals 규약을 수정하기도 함. 이런 인터페이스를 구현한 클래스라면 equals 에서 (클래스가 아닌) 인터페이스를 사용하는데 Set, List, Map, Map.Entry 등의 컬렉션 인터페이스들이 해당
3. 입력이 올바른 타입으로 형변환함. 이는 앞서 2번에서 instanceof 검사를 했기 때문엔 이 단계는 100% 성공
4. 입력 객체와 자기 자신의 대응되는 핵심 필드들이 모두 일치하는지 하나씩 검사. 모든 필드가 일치하면 true를, 하나라도 다르면 false를 반환. 만일 인터페이스를 사용했다면 입력의 필드를 가져올 때도 그 인터페이스의 메소드를 사용해야 함. 타입이 클래스라면 (접근 권한에 따라) 해당 필드에 직접 접근할 수도 있음.

float와 double을 제외한 기본 타입 필드는 == 연산자로 비교하고, 참조 타입 필드는 각각의 equals 메소드로, float와 double 필드는 각각 정적 메소드인 Float.compare(float, float)와 Double.compare(double, double)로 비교. float와 double를 특수 취급하는 이유는 Float.NaN, -0.0f, 특수한 부동소수 값 등을 다뤄야 하기 때문. Float.equals와 Double.equals 메소드를 대신 사용할 수도 있지만, 이 메소드들은 오토박싱을 수반할 수 있으니 성능상 좋지 않음. 배열 필드는 원소 각각을 앞서 지침대로 비교하는데, 배열의 모든 원소가 핵심 필드라면 Arrays.equals 메소드들 중 하나를 사용

때로는 null도 정상 값으로 취급하는 참조 타입의 필드도 있으니, 이런 필드는 Objects.equals(Object, Object)로 비교하여 NPE 발생을 예방

앞선 CaseInsensitiveString 예처럼 비교하기 복잡한 필드를 가진 클래스도 있는데, 이때는 그 필드의 표준형을 저장해둔 후 표준형끼리 비교하는게 훨신 경제적임. 이 기법은 특히 불변 클래스에 제격이며, 가변 객체라면 값이 바뀔때마다 표준형을 최산 상태로 갱신해야함.

어떤 필드를 먼저 비교하느냐가 equals의 성능을 좌우하기도 하는데, 최상의 성능을 바란다면 다를 가능성이 더 크거나 비교하난 비용이 싼 (또는 둘 다 해당하는) 필드를 먼저 비교. 동기화용 락 필드 같이 객체의 논리적 상태와 관련 없는 필드는 비교하면 안됨. 핵심 필드로부터 계산해낼 수 있는 파생 필드 역시 굳이 비교할 필요는 없지만, 파생 필드가 객체 전체의 상태를 대표하는 경우 파생 필드를 비교하는 쪽이 더 빠름. 예를 들어 자신의 영역을 캐시해두는 Polygon 클래스가 있다면 모든 정점을 일일이 비교할 필요 없이 캐시해둔 영약만 비교하면 결과를 바로 알수 있음.

equals을 다 구현했다면 세 가지를 꼭 기억해야함. 대칭적인가? 추이성이 있는가? 일관적인가? 자문에서 끝나지 말고 단위 테스트를 작성도 필요 (단, equals 메소드를 AutoValue를 이용해 작성했다면 테스트를 생략해도 됨).

다음은 비법에 따라 작성한 PhoneNumber 클래스용 equals 메소드

```java
public final class PhoneNumber {
    private final short areaCode, prefix, lineNum;

    public PhoneNumber(int areaCode, int prefix, int lineNum) {
        this.areaCode = rangeCheck(areaCode, 999, "지역코드");
        this.prefix = rangeCheck(prefix, 999, "프리픽스");;
        this.lineNum = rangeCheck(lineNum, 9999, "가입자 번호");;
    }

    private static short rangeCheck(int val, int max, String arg) {
        if (val < 0 || val > max) {
            throw new IllegalArgumentException(arg + ": " + val);
        }
        return (short) val;
    }

    @Override
    public boolean equals(Object o) {
        if (o == this) {
            return true;
        }
        if (!(o instanceof PhoneNumber)) {
            return false;
        }
        PhoneNumber pn = (PhoneNumber)o;
        return pn.lineNum == lineNum && pn.prefix == prefix && pn.areaCode == areaCode;
    }
}
```

다음은 마지막 주의사항으로

* equals을 재정의할 땐 hashCode도 반드시 재정의 해야함
* 너무 복잡하게 해결할 필요가 없음. 필드들의 동치성만 검새해도 equals 규약을 어렵지 않게 지킬수 있는데, 오히려 공격적으로 파고들다가 문제를 발생하기도 함. 일반적으로 별칭(alias)은 비교하지 않는 게 좋음. 예를 들어 File 클래스 라면 심볼릭 링크를 비교해 같은 파일을 가리키는지를 확인하려 들면 안됨. 다행이 File 클래스는 이런 시도를 하지 않음.
* Object 외의 타입을 매개변수로 받은 equals 메소드는 선언하지 말아야하는데, 많은 프로그래머가 다음과 같이 코드를 작성하고 문제의 원인을 헤맴. 이는 Object.equals를 재정의한게 아닌 다중 정의를 한 케이스이며, 타입을 구체적으로 명시한 equals는 오히려 해가 됨. @Override 애너테이션을 붙이면 긍정 오류를 발생하므로 이러한 실수를 예방할수도 있음

```java
// 잘못된 예 - 입력 타임은 반드시 Object여야 함
public boolean equals(MyClass o) {

}

// 잘못된 예 - 컴파일 안됨
@Override
public boolean equals(MyClass o) {

}
```

equals 메소드를 작성하고 테스트하는 일은 지루하며 뻔한 작업인데, 이를 대신해줄 오픈소스가 있으니 구글이 만든 AutoValue 프레임워크로, 클래스에 애노테이션 하나만 추가하면 AutoValue가 이 메소드들을 알아서 작성해주며, 직접 작성하는 것과 근본적으로 똑같은 코드를 만들어 줌

대다수의 IDE도 같은 기능을 제공하지만 생성된 코드가 AutoValue만큼 깔끔하거나 읽기 좋지는 않고, 클래스가 수정된 걸 자동으로 알아채지는 못하니 테스트 코드를 작성해야 하지만, 이런 단점을 감안하더라도 사람이 직접 작성하는것보다 IDE에 맡기는 편지 좋음. 적어도 사람의 부주의한 실수를 저지르지는 않음

꼭 필요한 경우가 아니면 equals를 재정의 하는것은 비추천함. 많은 경우에 Object의 equals가 원하는 비교를 정확히 수행해줌. 재정의해야 할 때는 그 클래스의 핵심 필드 모두를 빠짐없이, 다섯 가지 규약을 확실히 지켜가며 비교해야 함
