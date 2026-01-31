# 택ㅐ 상자 꺼내기

## 문제

<https://school.programmers.co.kr/learn/courses/30/lessons/389478>

## 내 풀이

```java
// 구현으로 해결한 코드
import java.util.Arrays;
import java.util.Collections;

class Solution {

    private static int MAX_VALUE = Integer.MAX_VALUE;

    public int solution(int n, int w, int num) {
        Integer[] maps = generateMaps(n, w);
        int cursor = 0;
        for (int i = 1; i <= n; i++) {
            if (maps[i] == num) {
                cursor = i;
            }
        }
        int answer = 1;
        while (cursor <= n) {
            if (maps[cursor + w] != MAX_VALUE && maps[cursor + w] > num) {
                answer++;
            }
            cursor += w;
        }
        return answer;
    }

    private Integer[] generateMaps(int n, int w) {
        Integer[] maps = new Integer[n + w + 1];
        for (int i = 1; i <= n + w; i++) {
            maps[i] = i <= n ? i : MAX_VALUE;

            if (i % w == 0) {
                int floor = i / w;
                if (floor % 2 == 0) {
                    Arrays.sort(maps, i - w + 1, i + 1, Collections.reverseOrder());
                }
            }
        }
        return maps;
    }
}

// 수학으로 해결한 코드
class Solution {

    public int solution(int n, int w, int num) {
        int floor = (num % w) > 0 ? (num / w) + 1 : (num / w);
        int topFloor = (n % w) > 0 ? (n / w) + 1 : (n / w);

        int answer = 0;
        int gap = topFloor - floor;
        if ((gap) % 2 == 0) {
            if (gap * w + num <= n) {
                answer = gap + 1;
            } else {
                answer = gap;
            }
        } else {
            int x = w - (num % w) + 1;
            if (x > w) x = x % w;
            if (num + (gap - 1) * w + 2 * x - 1 <= n) {
                answer = gap + 1;
            } else {
                answer = gap;
            }
        }
        return answer;
    }
}
```

## 해답

```java
// 해석 필요
public int solution(int n, int w, int num) {
    int cnt = 0;
    while(num <= n) {
        num += (w - ((num-1) % w) -1) * 2 + 1;
        cnt++;
    }

    return cnt;
}
```

## note

```java
// 자바 부분 정렬
// maps 타입을 int로 하니까 컴파일 에러가 발생, Collections.reverseOrder() 여기서 제너릭 타입을 요구함 
Integer[] maps = new Integer[];
Arrays.sort(maps, i - w + 1, i + 1, Collections.reverseOrder());
```
