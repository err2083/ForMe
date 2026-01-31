# 약수의 개수와 덧셈

## 문제

<https://school.programmers.co.kr/learn/courses/30/lessons/77884>

## 내 풀이

```java
import java.util.Arrays;

class Solution {
    
    private static final int MAX_VALUE = 1001;
    private Integer[] store = new Integer[MAX_VALUE]; 
    
    public Solution() {
        generateStore();
    }
    
    public int solution(int left, int right) {
        int answer = 0;
        for (int i = left; i <= right; i++) {
            if (store[i] % 2 == 0) {
                answer += i;
            } else {
                answer -= i;
            }
        }
        return answer;
    }
    
    private void generateStore() {
        Arrays.fill(store, 1);
        for (int i = 2; i < MAX_VALUE; i++) {
            for (int j = 1; i * j < MAX_VALUE; j++) {
                store[i * j]++;
            }
        }
    }
}
```

## 해답

```java
import java.lang.Math;

class Solution {
    
    public int solution(int left, int right) {
        int answer = 0;
        for (int i = left; i <= right; i++) {
            if ((i % Math.sqrt(i)) == 0) {
                answer -= i;
            } else {
                answer += i;
            }
        }
        return answer;
    }
}
```

## note

```java
// 패키지
import java.lang.Math;

// 제곱근 구하는 메소드
double result = Math.sqrt(value);

// 제곱 구하는 메소드
double result = Math.pow(value, 2);

// 제곱수 구하는 방법
// 제곱근을 구한 이후 나머지 연산 수행시 0 이면 제곱수
(i % Math.sqrt(i)) == 0
```

* 성급하지 말자
