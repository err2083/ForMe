# 커맨드 패턴

## 미리보기

* 커맨드 패턴을 이용하면 요청을 하는 객체와 그 요청을 수행하는 객체를 분리시킬 수 있습니다.
* 이렇게 분리시키는 과정의 중심에는 커맨드 객체가 있으며, 이 객체가 행동이 들어있는 리시버를 캡슐화합니다.
* 인보커에서는 요청을 할 때는 커맨드 객체의 execute() 메소드를 호출하면 됩니다. execute() 메소드에서는 리시버에 있는 행동을 호출합니다.
* 인보커는 커맨드를 통해서 매개변수화될 수 있습니다. 이런 실행중에 동적으로 설정할 수도 있습니다.
* execute() 메소드가 마지막으로 호출되기 전의 기존 상태로 되돌리기 위한 작업취소 메소드를 구현하면 커맨드 패턴을 통해서 작업취소 기능을 지원할 수도 있습니다.
* 매크로 커맨드는 커맨드를 확장해서 여러 개의 커맨드를 한꺼번에 호출할 수 있게 해주는 간단한 방법입니다. 매크로 커맨드에서도 어렵지 않게 작업취소 기능을 지원할 수 있습니다.
* 프로그래밍을 하다 보면 요청자체를 리시버한테 넘기지 않고 자기가 처리하는 스마트 커맨드 객체를 사용하는 경우도 종종 있습니다.
* 커맨드 패턴을 활용하여 로그 및 트랜잭션 시스템을 구현하는 것도 가능합니다.

## 이해하기

일곱가지 프로그래밍이 가능한 슬롯이 있는 기계이 있다고 생각해보자. 각 슬롯에는 원하는 제품을 연결하고 버튼을 가지고 제품을 제어할 수 있도록 되어있어. 그리고 각각의 가전제품 제공사로부터 공급된 클래스들을 슬롯에 연결을 해야해. 예를 들어 전등 제품이 있으면 on/off 버튼을 연결하는 형태가 될거야.

이때 유용하게 사용할 패턴이 커맨드 패턴이야. 이는 어떤 작업을 요청한 쪽하고 그 작업을 처리한 쪽을 분리시킬 수 있어. 리모컨의 버튼을 누르면 커맨드 객체를 통해서 작업을 처리하게 하는 형태지

식당을 예시로 한번 들어볼게. 먼저 식당은 다음과 같은 프로세스를 가지게 되

1. 고객이 웨이트리스에게 주문을 한다.
2. 웨이트리스는 주문을 받아서 카운터에 갖다 줍니다.
3. 주방장이 주문대로 음식을 준비합니다.

이를 객체와 본다면 다음과 같은 프로세스를 가지게 될거야

고객이 원하는것을 주문하는 createOrder() 호출 -> 주문은 계산서와 그 주문한 메뉴 항목으로 구성되고 웨이트리스가 takeOrder() 호출 -> 웨이트리스는 그 주문을 받아서 주문 처리하기 위한 준비를 시작하는 orderUp() 호출 -> Order객체는 주방장에게 요리를 요청하는 makeShake() 호출 -> 주방장은 전달받은 요리를 준비

앞서 본 프로세스를 정리하면 다음과 같아.

* 주문서는 주문한 메뉴를 캡슐화
  * 주문서는 메뉴를 요구하는 객체로 생각할수 있어, 이 객체는 식사를 준비하기 위한 행동을 캡슐화한 orderUp() 이라는 매소드가 포함되어있고, 그 식사를 주문해야하는 대상(주방장)에 대한 래퍼런스도 포함하고 있지. 그러면 웨이트리스는 어떤 내용이 주문되었는지, 누가 식사를 준비할지 몰라도 이 주문서를 가져다 주기만 하면 되는거지
* 웨이트리스는 주문서를 받아 거기에 있는 orderUp() 메소드를 호출하는 일
  * 웨이트리스는 앞서 말했듯이 주문 정보나, 식사에 대한 정보가 없어도 orderUp()만 호출하면 되
* 주방장은 식사를 준비하는데 필요한 정보 소유
  * 주방장은 주문의 orderUp() 메소드 호출을 통해서 음식을 만들기 위한 메소드를 전부 처리해. 여기서 중요한점은 주방장과 웨이트리스는 서로 얘기할 필요가 없다는거지

이 프로세스는 요구하는 객체와 처리하는 객체를 분리시키는 객체지향 디자인 패턴의 한 모델이라고 볼 수 있어. 이를 리모컨으로 생각하면 버튼을 눌렀을때 호출되는 코드와 특정 업체에서 제공한 제품의 일을 처리하는 코드가 분리되어야 하는거지.

이제 이를 커맨드 패턴의 관점으로 한번 바라보자.

1. 클라이언트는 커맨드 객체를 생성하고, 커맨드 객체는 리시버에 대한 정보가 같이 들어있습니다.
2. 커맨드 객체에서 제공하는 메소드는 execute() 하나로 리시버의 특정 행동을 호출하기 위한 메소드 입니다.
3. 클라이언트는 인보커 객체의 setCommand() 메소드를 호출하여 커맨드 객체를 넘겨줍니다.
4. 인보커는 커맨드 객체의 execute()를 호출합니다.
5. 리시버에 있는 특정 행동을 하는 메소드가 호출됩니다.

이제 커맨드 객체를 만들어보자. 커맨드 객체는 모두 같은 인터페이스를 구현해야해.

```java
public interface Command {
    public void execute();
}
```

전등을 켜기 위한 커맨드를 구현하면 다음과 같이 될거야

```java
public class LightOnCommand implements Command {
    Light light;

    public LightOnCommand(Light light) {
        this.light = light;
    }

    public void execute() {
        light.on();
    }
}
```

이제 이 커맨드 객체를 사용해보자. 간단하게 버튼이 하나뿐인 리모컨이 있다면 다음과 같이 사용이 될거야

```java
public class SimpleRemoteControl {
    Command slot;

    public SimpleRemoteControl() {}

    public void setCommand(Command command) {
        slot = command;
    }

    public void buttonWasPressed() {
        slot.execute();
    }
}

public class RemoteControlTest {
    public static void main(Stirng[] args) {
        SimpleRemoteControl remote = new SimpleRemoteControl();
        Light light = new Light();
        Command lightOn = new LightOnCommand(light);

        remote.setCommand(lightOn);
        remote.buttonWasPressed();
    }
}
```

개념: 커맨드 패턴을 이용하면 요구 사항을 객체로 캡슐화할 수 있으며, 매개 변수를 써서 여러 가지 다른 요구 사항을 집어넣을수도 있습니다. 또한 요청 내역을 큐에 저장하거나 로그로 기록할 수도 있으며, 작업 취소 기능도 지원 가능합니다.

앞서 말했듯이 커맨드 객체는 일련의 행동을 특정 리시버하고 연결시킴으로써 요구 사항을 캡슐화한 것이야. 이는 행동과 리시버를 한 객체에 집어넣고, execute()라는 메소드 하나만 외부에 공개하는 방법을 사용해. 외부에서는 리시버가 무엇인지, 어떤 일을 하는지 알 수 없어. 단지 처리된다는 것만 아는거지.

다음은 클래스 다이어그램이야

![커맨드 패턴 클래스 다이어그램](1.png "커맨드 패턴 클래스 다이어그램")

클라이언트는 ConcreteCommand를 생성하고 Receiver를 설정하고, 리시버는 요구사항을 수행하기 위해 어떤 일을 처리해야 하는지 알고있는 객체지. 이들은 Invoker에 의해 호출되어있어.

이제 슬롯이 일곱개인 클래스를 만들어 볼게

```java
public class RemoteControl {
    Command[] onCommands;
    Command[] offCommands;

    public RemoteControl() {
        onCommands = new Command[7];
        offCommands = new Command[7];

        Command noCommand = new noCommand();
        for (int i=0; i<7; i++) {
            onCommands[i] = noCommand;
            offCommands[i] = noCommand;
        }
    }

    public void setCommand(int slot, Command onCommand, Command offCommand) {
        onCommands[slot] = onCommand;
        offCommands[solt] = offCommand;
    }

    public void onButtonWasPushed(int slot) {
        onCommands[slot].execute();
    }

    public void offButtonWasPushed(int slot) {
        offCommands[slot].execute();
    }
}
```

좀더 어려운 커맨드를 한번 만들어보자. 이번에는 오디오 커맨드 클래스를 만들어볼게. 끄는거는 간단한데, 켤때는 좀 더 메소드가 필요하겠지?

```java
public class StereoOnWithCDCommand implements Command {
    Stereo stereo;

    public StereoOnWithCDCommand(Stereo stereo) {
        this.stereo = stereo;
    }

    public execute() {
        stereo.on();
        stereo.setCD();
        stereo.setVolumne(11);
    }
}
```

이제 커맨드를 만드는 작업은 반복작업뿐이야. 여기서 하나만 짚고 넘어가자면 NoCommand 라는 객체를 할당했던 코드가 있어. 이는 널 객체있는데, 버튼에 아무런 커맨드가 연결이 안되어있으면 조건문을 통해 확인을 해야하는 작업이 필요한 부분을 널 객체로 대체한거야 즉, 빈 자리를 채우기 위한 용도지.

```java
public class NoCommand implements Command {
    public void execute();
}
```

다음은 Command 객체에 있던 undo() 메소드에 대해 알아볼거야. 이는 작업을 취소하는 기능이야. 만일 전등을 켜는 Command의 undo() 작업은 전등을 끄는거겠지?

```java
public class LightOnCommand implements Command {
    Light light;

    public LightOnCommand(Light light) {
        this.light = light;
    }

    public void execute() {
        light.on();
    }

    public void undo() {
        light.off();
    }
}
```

전등을 끄는 Command의 undo()는 작업을 키는거겠지. 이는 리모컨에서 가장 마지막으로 작업했던 Command의 상태값만 저장해주면 간단하게 해결될거야

```java
public class RemoteControl {
    // ...
    Command undoCommand;

    // ...

    public void onButtonWasPushed(int slot) {
        onCommands[slot].execute();
        undoCommand = onCommands[slot];
    }

    public void offButtonWasPushed(int slot) {
        offCommands[slot].execute();
        undoCommand = offCommands[slot];
    }

    public void undiButtonWasPushed() {
        undoCommand.undo();
    }
}
```

전등이 아닌 좀더 복잡한 커맨드를 생각해보자. 예를 들어 선풍기를 보면 선풍기는 속도를 선택할 수 있어.

```java
@Getter
public class CeilingFan {
    public static final int HIGH = 3;
    public static final int MEDIUM = 2;
    public static final int LOW = 1;
    public static final int OFF = 0;

    String location;
    int speed;

    public CeilingFan(String location) {
        this.location = location;
        spped = OFF;
    }

    public void high() {
        speed = HIGH;
    }

    public void medium() {
        speed = MEDIUM;
    }

    public void low() {
        speed = LOW;
    }

    public void off() {
        speed = OFF:
    }
}
```

이를 커맨드 패턴으로 만들어보자. 여기서 주의할점은 undo 버튼인데, 선풍기를 이전 상태로 돌려둘려면 이전 상태를 저장하는 방법이 가장 좋을거야

```java
public class CeilingFanHighCommand implements Command {
    CeilingFan ceilingFan;
    int prevSpeed;

    public CeilingFanHighCommand(CeilingFan ceilingFan) {
        this.ceilingFan = ceilingFan;
    }

    public void execute() {
        prevSpeed = ceilingFan.getSpeed();
        ceilingFan.high();
    }

    public void undo() {
        if (prevSpeed == CeilingFan.HIGH) {
            ceilingFan.high();
        } else if () {
            // ...
        }
    }
}
```

이번에는 버튼 하나를 누르면 전등이 어두워지고, TV가 켜지고, DVD 모드로 변경되고 욕조에 물이 채워지는 매크로 커맨드를 한번 만들어볼게.

앞선 기존 커맨드는 리시버의 래퍼런스를 가지고 있었다면 매크로 커맨드는 커맨드의 래퍼런스가 필요할거야

```java
public class MacroCommand implements Command {
    Command[] commands;

    public MacroCommand(Command[] commands) {
        this.commands = commands;
    }

    public void execute() {
        for (int i=0; i< commands.length; i++) {
            commands[i].execute();
        }
    }
}
```

이 패턴을 활용하는 대표적인 예로는 큐를 들수있어. 큐의 경우 전형적인 처리하는 쪽과 요청하는 쪽이 분리되어있는 구조이지. 커맨드 인터페이스를 구현한 객체를 큐에 넣으면 스레드는 큐에 있는 커맨드를 하나씩 꺼내서 execute()만 호출하면 되.
