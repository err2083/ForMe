// 1. 중복을 방지하기 위한 Set 생성 (이미 읽은 텍스트 저장)
const scriptTexts = new Set();

// 2. 텍스트를 추출하는 함수 정의
const collectTexts = () => {
    const elements = document.querySelectorAll('.script-item-text');
    let addedCount = 0;

    elements.forEach(el => {
        const text = el.textContent.trim();
        if (text && !scriptTexts.has(text)) {
            scriptTexts.add(text);
            addedCount++;
        }
    });

    if (addedCount > 0) {
        console.log(`새로운 문장 ${addedCount}개 추가됨. (총 ${scriptTexts.size}개)`);
    }
};

// 3. 스크롤 영역 찾기 (제공해주신 클래스 기반)
// 보통 mantine-ScrollArea의 실제 스크롤은 바로 아래 viewport div에서 일어납니다.
const scrollTarget = document.querySelector('.light-zvuxhh')

if (scrollTarget) {
    // 최초 1회 실행
    collectTexts();

    // 스크롤 이벤트 리스너 등록
    scrollTarget.addEventListener('scroll', () => {
        collectTexts();
    });

    console.log("스크롤 감지 시작! 아래로 천천히 내려주세요.");
    console.log("최종 결과를 보려면 'console.table([...scriptTexts])'를 입력하세요.");
} else {
    console.error("스크롤 영역을 찾을 수 없습니다. 클래스명을 확인해 주세요.");
}

// -------------------------------------------------------------------------------
// 모든 문장을 줄바꿈(\n)으로 연결하여 하나의 변수에 저장
const resultString = [...scriptTexts].join('\n');

// 결과 확인
console.log(resultString);