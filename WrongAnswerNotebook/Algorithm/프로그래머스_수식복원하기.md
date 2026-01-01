# 수식 복원하기

## 문제

<https://school.programmers.co.kr/learn/courses/30/lessons/340210>

## 내 풀이

```java
import java.util.ArrayList;
import java.util.Arrays;

public class Solution {

    public String[] solution(String[] expressions) {
        Operation operation = new Operation(expressions, 9);
        operation.perform();
        return operation.resolveAnswer();
    }

    class Operation {

        private String[] expressions;
        private Boolean[] radix;
        // n진법 (2 ~ 9진법)
        private int n;
        private ArrayList<String> answer = new ArrayList<>();

        public Operation(String[] expression, int n) {
            this.expressions = expression;
            this.n = n;
            fillRadix();
            filterAnswer();
        }

        private void filterAnswer() {
            for (String expression : expressions) {
                if (expression.contains("X")) {
                    answer.add(expression);
                }
            }
        }

        private void fillRadix() {
            this.radix = new Boolean[n + 1];
            Arrays.fill(radix, false);

            for (int i = n - 1; i >= 0; i--) {
                for (String expression : expressions) {
                    if (expression.contains(String.valueOf(i))) {
                        Arrays.fill(radix, i + 1, n + 1, true);
                        return;
                    }
                }
            }
        }

        public void perform() {
            for (String expression : expressions) {
                if (expression.contains("X")) {
                    continue;
                }
                QuestionAndAnswer questionAndAnswer = new QuestionAndAnswer(expression);
                for (int i = 2; i <= n; i++) {
                    if (!radix[i]) {
                        continue;
                    }

                    radix[i] = questionAndAnswer.perform(i);
                }
            }
        }

        public String[] resolveAnswer() {
            String[] result = new String[answer.size()];
            for (int i1 = 0; i1 < answer.size(); i1++) {
                String q = answer.get(i1);
                QuestionAndAnswer questionAndAnswer = new QuestionAndAnswer(q);
                for (int i = 2; i <= n; i++) {
                    if (!radix[i]) {
                        continue;
                    }
                    String resolve = Integer.toString(questionAndAnswer.resolve(i));
                    String replaced = q.replace("X", resolve);

                    if (result[i1] != null && !result[i1].equals(replaced)) {
                        result[i1] = q.replace("X", "?");
                    } else {
                        result[i1] = replaced;
                    }
                }
            }
            return result;
        }
    }

    class QuestionAndAnswer {
        private String expression;
        private String valueA;
        private String valueB;
        private String answer;
        private String op;

        public QuestionAndAnswer(String expression) {
            this.expression = expression;

            String[] questionAndAnswer = expression.split(" ");

            valueA = questionAndAnswer[0].strip();
            op = questionAndAnswer[1].strip();
            valueB = questionAndAnswer[2].strip();
            answer = questionAndAnswer[4].strip();
        }

        public boolean perform(int n) {
            int convertAnswer = convertN(answer, n);
            int resolve = resolveN(n);

            if (resolve == convertAnswer) return true;

            return false;
        }

        public int resolveN(int n) {
            int convertA = convertN(valueA, n);
            int convertB = convertN(valueB, n);

            if ("+".equals(op)) {
                return convertA + convertB;
            } else if ("-".equals(op)) {
                return convertA - convertB;
            }
            throw new IllegalStateException();
        }

        public int resolve(int n) {
            int convertA = convertN(valueA, n);
            int convertB = convertN(valueB, n);

            if ("+".equals(op)) {
                return Integer.parseInt(Integer.toString(convertA + convertB, n));
            } else if ("-".equals(op)) {
                return Integer.parseInt(Integer.toString(convertA - convertB, n));
            }
            throw new IllegalStateException();
        }

        // n -> 10진수
        public int convertN(String value, int n) {
            return Integer.parseInt(value, n);
        }
    }
}
```

## note

```java
// 패키지
import java.util.ArrayList;
import java.util.Arrays;

// array를 fromIndex 부터 toIndex 이전까지 true로 채우는 메소드
Arrays.fill(Object[] array, int fromIndex, int toIndex, Object true);

// n진수 -> 10진수 변환
Integer.parseInt(String value, int n);

// 10진수 -> n진수 변환
Integer.toString(int value, int n)
```
