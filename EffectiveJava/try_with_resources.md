# try-finally 보다는 try-with-resources를 사용하라

자바 라이브러리에는 close 메소드를 호출해 직접 닫아줘야하는 InputStream, OutputStream, java.sql.Connection등 자원이 많음. 이는 클라이언트가 놓치기 쉬워서 예측할 수 없는 성능 문제로 이어지기도 하는데, 이런 자원중 상당수가 안전망으로 finalizer를 활용하지만 이는 그리 믿을만 하지 못함

전통적으로 자원이 제대로 닫힘을 보장하는 수단으로 try-finally를 사용하였음

```java
static String firstLineOfFile(String path) throws IOException {
    BufferedReader br = new BufferedReader(new FileReader(path));
    try {
        return br.readLine();
    } finally {
        br.close();
    }
}
```

이 상황에서 자원을 하나 더 사용하면 어떻게 될까?

```java
static void copy(String src, String dst) throws IOException {
    InputStream in = new FileInputStream(src);
    try {
        OutputStream out = new FileOutputStream(dst);
        try {
            byte[] buf = new byte[BUFFER_SIZE];
            int n;
            while((n = in.read(buf)) >= 0) {
                out.write(buf, 0, n);
            }
        } finally {
            in.close();
        }
    } finally {
        out.close();
    }
}
```

이는 미묘한 결점이 존재하는데, 예를 들어 물리적인 문제로 firstLineOfFile 메소드 안의 readLine 메소드가 예외를 던지고, 같은 이유로 close도 실패하는데, 이러면 두 번째 예외가 첫 번째 예외를 삼켜서 스택 추적 내역에 첫 번째 예외에 관한 정보가 남지 않게 되어 실제 시스템에서의 디버깅을 어렵게 함. 일반적으로 문제를 진단하려면 첫 번째 예외를 보고 싶을것

이러한 문제는 자바 7의 try-with-resources(JLS, 14.20.3) 덕에 모두 해결되었는데, 이 구조를 사용하려면 단순히 void를 반환하는 close메소드가 하나 있는 AuthCloseable 인터페이스를 구현해야 함

자바 라이브러리와 서드파티 라이브러리들의 수많은 클래스들도 AutoCloseable을 구현하거나 확장했으니 자원을 뜻하는 클래스를 작성한다면 이는 꼭 작성을 해야하 됨

다음은 try-with-resources를 사용하는 예시

```java
static String firstLineOfFile(String path) throws IOException {
    try (BufferedReader br = new BufferedReader(new FileReader(path))) {
        return br.readLine();
    }
}
```

```java
static void copy(String src, String dst) throws IOException {
    try (InputStream in = new FileInputStream(src);
        OutputStream out = new FileOutputStream(dst)) {
        byte[] buf = new byte[BUFFER_SIZE];
        int n;
        while((n = in.read(buf)) >= 0) {
            out.write(buf, 0, n);
        }
    }
}
```

try-with-resources 버전이 훨씬 잛고 읽기 수월할 뿐 아니라 문제를 진단하기도 훨씬 좋음.

firstLineOfFile 메소드를 생각해보면 readLine와 close 호출 양쪽에서 예외가 발생하면, close에서 발생한 예외는 숨겨지고 readLine에서 발생한 예외가 기록되는데, 만일 두번째 예외를 보고 싶다면, 이는 스택 추적 내역에 suppressed라는 꼬리표를 달고 출력이 됨(java 7 에서 추가된 Throwable의 getSuppressed 메소드)

try-with-resources는 catch절도 사용할수 있는데, 이를 통해 try문을 더 중첩하지 않고도 다수의 예외를 처리 할 수 있음

```java
static String firstLineOfFile(String path, String defaultVal) {
    try (BufferedReader br = new BufferedReader(new FileReader(path))) {
        return br.readLine();
    } catch (IOException e) {
        return defaultVal;
    }
}
```

꼭 회수해야 하는 자원을 다룰 때는 try-finally 보다는 try-with-resources를 사용. 예외는 없음 코드는 더 짧고 분명해지며, 예외 정보도 훨신 유용함.

try-finally로 작성하면 실용적이지 못할 만큼 코드가 지저분해지는 경우라도 try-with-resources로는 정확하고 쉽게 자원을 회수할 수 있음.
