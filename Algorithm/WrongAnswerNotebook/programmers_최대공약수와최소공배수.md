# 최대공약수와 최소공배수

## 문제

<https://school.programmers.co.kr/learn/courses/30/lessons/12940>

## 풀이

```java
class Solution {
    public int[] solution(int n, int m) {
        int[] answer = new int[2];
        answer[0] = gcd(m, n);
        answer[1] = (n / gcd(m, n)) * m; // 최소 공배수
        return answer;
    }

    // 최대 공약수
    private int gcd(int a, int b) {
        if (b == 0) return a;
        return gcd(b, a % b);
    }
}
```

## note

* (n \* m) 연산을 먼저 한 이후에 gcd(m, n) 나누면 (n \* m) 결과에서 overflow가 발생할수 있음
