# 숫자 야구

## 문제

<https://school.programmers.co.kr/learn/courses/30/lessons/451808>

## 내 풀이

```java
import java.util.LinkedList;
import java.util.Queue;
import java.util.function.Function;

class Solution {
    public int solution(int n, Function<Integer, String> submit) {
        Queue<Integer> queue = cases();
        int[] quick = {1123, 6445, 7798};
        int i = 0;
        Integer poll;
        while (queue.size() > 1) {
            if (i < 3) {
                poll = quick[i];
                i++;
            } else {
                poll = queue.poll();
            }
            String apply = submit.apply(poll);

            if (apply.equals("4S 0B")) return poll;
            removeCases(queue, poll, apply);
        }

        return queue.poll();
    }

    private void removeCases(Queue<Integer> queue, int expected, String apply) {
        int size = queue.size();
        for (int i = 0; i < size; i++) {
            Integer poll = queue.poll();
            if (checkApply(expected, poll, apply)) {
                queue.add(poll);
            }
        }
    }

    private boolean checkApply(int expected, int actual, String apply) {
        int[] actualArray = convertArray(actual);
        int[] expectedArray = convertArray(expected);

        int strike = 0;
        int ball = 0;

        for (int i = 0; i < actualArray.length; i++) {
            if (actualArray[i] == expectedArray[i]) {
                strike++;
            }

            for (int j = 0; j < expectedArray.length; j++) {
                if (i == j) continue;
                if (actualArray[i] == expectedArray[j]) {
                    ball++;
                }
            }
        }

        StringBuilder sb = new StringBuilder().append(strike).append("S").append(" ").append(ball).append("B");
        return apply.equals(sb.toString());
    }

    private int[] convertArray(int number) {
        int[] array = new int[4];
        int temp = number;
        for (int i = 3; i >= 0; i--) {
            array[i] = temp % 10;
            temp = temp / 10;
        }
        return array;
    }



    private Queue<Integer> cases() {
        Queue<Integer> queue = new LinkedList<>();
        for (int i = 1234; i <= 9876; i++) {
            // 자리수에 동일한 숫자가 있다거나
            // 0이 있다거나
            if (sameDigit(i)) {
                continue;
            }

            if (Integer.toString(i).contains("0")) {
                continue;
            }
            queue.add(i);
        }
        return queue;
    }

    private boolean sameDigit(int n) {
        boolean[] digits = new boolean[10];
        while (n > 0) {
            int digit = n % 10;
            if (digits[digit]) {
                return true;
            }
            digits[digit] = true;
            n /= 10;
        }
        return false;
    }
}
```

## 해답

```java
// 경우의 수를 구할때 다음과 같이 하면 구현하기 쉬움
private List<Integer> cases() {
    List<Integer> cases = new ArrayList<>();
    for (int i = 1; i < 10; i++) {
        for (int j = 1; j < 10; j++) {
            if (i == j) continue;
            for (int k = 1; k < 10; k++) {
                if (i == k || k == j) continue;
                for (int l = 1; l < 10; l++) {
                    if (i == l || k == l || l == j) continue;
                        cases.add(1000 * i + 100 * j + 10 * k + l);
                }
            }
        }
    }
    return cases;
}

// strike, ball 계산하는 부분도 integer가 아니라 String 으로 변환하면 쉽게 구현 가능
```

## note

```java
// 처음에 for문을 돌릴때 조건무에 queue.size() 이거를 넣어서 실패함
// 이는 큐에 넣고 사이즈가 다시 늘고 이를 반복해서 틀렸음
for (int i = 0; i < queue.size(); i++);

// 큐 생성
import java.util.LinkedList;
import java.util.Queue;

Queue<Integer> queue = new LinkedList<>();
```
