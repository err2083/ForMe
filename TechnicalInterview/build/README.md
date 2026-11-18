# 포트폴리오·이력서 빌드

이 폴더만으로 `TechnicalInterview/` 의 포트폴리오(.key·PDF)와 이력서(PDF)를 다시 만들 수 있다.

| 파일 | 역할 |
|---|---|
| `build_portfolio.py` | 포트폴리오 원본. python-pptx 로 23장 PPTX 생성 (1920×1080, 흰 배경 + 파란 포인트, Helvetica Neue) |
| `resume.html` | 이력서 원본. A4, 헤드리스 Chrome 으로 PDF 인쇄 |
| `build.sh` | 위 둘을 빌드해 `TechnicalInterview/` 에 결과 저장 |

## 실행

```bash
./build.sh            # 둘 다
./build.sh portfolio  # 포트폴리오만: PPTX → Keynote 로 열어 .key 저장 + PDF 내보내기
./build.sh resume     # 이력서만
```

필요: macOS, Keynote, Google Chrome, [uv](https://docs.astral.sh/uv/). 사내망이면 uv 에 `--system-certs`(안 되면 `--native-tls`)가 필요해 스크립트에 넣어 둠.
처음 실행 시 터미널이 Keynote 를 제어하도록 권한 허용 창이 뜰 수 있다.

## 수정 방법 (Claude 세션에서)

- 문구 수정은 `build_portfolio.py` 의 슬라이드별 텍스트, `resume.html` 본문을 고친 뒤 `./build.sh` 실행.
- 포트폴리오 텍스트 표기: `**굵게**`, 목록 항목 앞 `H:` 는 소제목.
- 고친 뒤 `pdftotext <pdf> - | grep <단어>` 로 결과 PDF 에 반영됐는지 확인.
- 이력서와 포트폴리오는 같은 사실·표현을 쓴다 (기술 목록, 수치, "모든 고객사 반영" 등). 한쪽만 고치지 말 것.
