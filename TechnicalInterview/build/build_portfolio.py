"""포트폴리오 v6 — v5 + 2026-11-16 이력서 확정 사실과 정합 (MCP 제외, 역할 경계, 기술 목록)."""
import re
import sys

from lxml import etree
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Pt

OUT = sys.argv[1]

FONT, FONT_MED = "Helvetica Neue", "Helvetica Neue Medium"
INK = RGBColor(0x21, 0x25, 0x29)
GRAY = RGBColor(0x49, 0x50, 0x57)
MUTE = RGBColor(0x86, 0x8E, 0x96)
LINE = RGBColor(0xCE, 0xD4, 0xDA)
SOFT = RGBColor(0xF5, 0xF6, 0xF8)
BLUE = RGBColor(0x1C, 0x6E, 0xD6)
BLUE_SOFT = RGBColor(0xEB, 0xF4, 0xFF)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

prs = Presentation()
prs.slide_width, prs.slide_height = Pt(1920), Pt(1080)
BLANK = prs.slide_layouts[6]
L, R = 110, 1810          # 좌우 여백
W = R - L


# ───────────── 기본 도구 ─────────────
def runs(p, text, size, color=INK, bold=False, font=FONT):
    """**굵게**, [[파랑 굵게]] 마크업."""
    for part in re.split(r"(\*\*.+?\*\*|\[\[.+?\]\])", text):
        if not part:
            continue
        b, c = bold, color
        if part.startswith("**"):
            part, b = part[2:-2], True
        elif part.startswith("[["):
            part, b, c = part[2:-2], True, BLUE
        r = p.add_run()
        r.text = part
        r.font.name, r.font.size, r.font.bold = font, Pt(size), b
        r.font.color.rgb = c


def tb(slide, x, y, w, h, anchor=MSO_ANCHOR.TOP, margin=2):
    t = slide.shapes.add_textbox(Pt(x), Pt(y), Pt(w), Pt(h)).text_frame
    t.word_wrap = True
    t.vertical_anchor = anchor
    for s in ("margin_left", "margin_right", "margin_top", "margin_bottom"):
        setattr(t, s, Pt(margin))
    return t


def text(slide, x, y, w, h, s, size, color=INK, bold=False, align=PP_ALIGN.LEFT,
         anchor=MSO_ANCHOR.TOP, font=FONT, spacing=None):
    t = tb(slide, x, y, w, h, anchor)
    for i, line in enumerate(s.split("\n")):
        p = t.paragraphs[0] if i == 0 else t.add_paragraph()
        p.alignment = align
        if spacing:
            p.line_spacing = spacing
        runs(p, line, size, color, bold, font)
    return t


def bullet(p, marl=34, indent=-26, char="•"):
    pPr = p._p.get_or_add_pPr()
    pPr.set("marL", str(Pt(marl)))
    pPr.set("indent", str(Pt(indent)))
    for tag in ("a:buNone", "a:buChar", "a:buAutoNum", "a:buClr"):
        for el in pPr.findall(qn(tag)):
            pPr.remove(el)
    clr = etree.SubElement(pPr, qn("a:buClr"))
    srgb = etree.SubElement(clr, qn("a:srgbClr"))
    srgb.set("val", "868E96")
    etree.SubElement(pPr, qn("a:buChar")).set("char", char)


def rect(slide, x, y, w, h, fill=None, line=None, lw=1.5, shape=MSO_SHAPE.RECTANGLE, radius=None):
    sh = slide.shapes.add_shape(shape, Pt(x), Pt(y), Pt(w), Pt(h))
    if radius is not None:
        sh.adjustments[0] = radius
    if fill is None:
        sh.fill.background()
    else:
        sh.fill.solid()
        sh.fill.fore_color.rgb = fill
    if line is None:
        sh.line.fill.background()
    else:
        sh.line.color.rgb = line
        sh.line.width = Pt(lw)
    sh.shadow.inherit = False
    return sh


def hline(slide, x1, y1, x2, y2, color=LINE, width=1.5, arrow=False):
    c = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Pt(x1), Pt(y1), Pt(x2), Pt(y2))
    c.line.color.rgb = color
    c.line.width = Pt(width)
    if arrow:
        tail = etree.SubElement(c.line._get_or_add_ln(), qn("a:tailEnd"))
        tail.set("type", "triangle")
        tail.set("w", "med")
        tail.set("len", "med")
    return c


def slide_base(tag, title, period=None):
    s = prs.slides.add_slide(BLANK)
    if tag:
        text(s, L, 62, 1200, 40, tag, 22, BLUE, bold=True)
    text(s, L, 98, 1500, 90, title, 50, INK, font=FONT_MED)
    if period:
        text(s, R - 520, 66, 520, 40, period, 22, MUTE, align=PP_ALIGN.RIGHT)
    hline(s, L, 196, R, 196, LINE, 1.2)
    return s


def section_list(slide, x, y, w, h, items, size=27, head=29, space=9):
    """items: 'H:제목' 은 소제목, 나머지는 불릿."""
    t = tb(slide, x, y, w, h)
    first = True
    for it in items:
        p = t.paragraphs[0] if first else t.add_paragraph()
        if it.startswith("H:"):
            runs(p, it[2:], head, BLUE, bold=True)
            p.space_before = Pt(0 if first else 22)
        else:
            bullet(p)
            runs(p, it, size, INK)
            p.space_before = Pt(space)
        first = False
    return t


def node(slide, x, y, w, h, title, sub=None, mine=False, size=24, top=False):
    sh = rect(slide, x, y, w, h, BLUE_SOFT if mine else WHITE, BLUE if mine else LINE,
              lw=2 if mine else 1.5, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.10)
    t = sh.text_frame
    t.word_wrap = True
    t.vertical_anchor = MSO_ANCHOR.TOP if top else MSO_ANCHOR.MIDDLE
    for s_ in ("margin_left", "margin_right", "margin_top", "margin_bottom"):
        setattr(t, s_, Pt(8))
    p = t.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    runs(p, title, size, BLUE if mine else INK, bold=True)
    if sub:
        for line in sub.split("\n"):
            q = t.add_paragraph()
            q.alignment = PP_ALIGN.CENTER
            runs(q, line, size - 5, GRAY)
    return sh


def flow_cards(slide, cards, x=L, y=232, w=W, h=650, gap=40, size=27):
    """A안: ① 문제 ② 원인 ③ 해결 ④ 결과. cards=[(label, lines, big_or_None)]"""
    n = len(cards)
    cw = (w - gap * (n - 1)) / n
    for i, (label, lines, big) in enumerate(cards):
        cx = x + i * (cw + gap)
        result = big is not None
        rect(slide, cx, y, cw, h, BLUE_SOFT if result else SOFT)
        rect(slide, cx, y, cw, 7, BLUE if result else RGBColor(0xAD, 0xB5, 0xBD))
        text(slide, cx + 26, y + 30, cw - 52, 44, label, 28, BLUE if result else INK, bold=True)
        ty = y + 92
        if result:
            text(slide, cx + 26, ty, cw - 52, 120, big, 40, BLUE, bold=True, spacing=1.0)
            ty += 64 * (big.count("\n") + 1) + 26
        t = tb(slide, cx + 26, ty, cw - 52, h - (ty - y) - 20)
        for j, line in enumerate(lines):
            p = t.paragraphs[0] if j == 0 else t.add_paragraph()
            bullet(p, marl=24, indent=-22)
            runs(p, line, size, INK)
            p.space_before = Pt(0 if j == 0 else 18)
            p.line_spacing = 1.08
        if i < n - 1:
            ch = rect(slide, cx + cw + gap / 2 - 9, y + h / 2 - 16, 18, 32, RGBColor(0xAD, 0xB5, 0xBD),
                      shape=MSO_SHAPE.CHEVRON)
    return cw


def footnote(slide, s, y=920, size=23):
    rect(slide, L, y, W, 66, SOFT)
    text(slide, L + 24, y, W - 48, 66, s, size, GRAY, anchor=MSO_ANCHOR.MIDDLE)


def table(slide, rows, x, y, w, col_w, row_h=80, size=24):
    shp = slide.shapes.add_table(len(rows), len(rows[0]), Pt(x), Pt(y), Pt(w), Pt(row_h * len(rows)))
    tbl = shp.table
    tblPr = tbl._tbl.tblPr
    tblPr.set("firstRow", "0")
    tblPr.set("bandRow", "0")
    for i, cw in enumerate(col_w):
        tbl.columns[i].width = Pt(cw)
    for r, row in enumerate(rows):
        for c, val in enumerate(row):
            cell = tbl.cell(r, c)
            cell.fill.solid()
            cell.fill.fore_color.rgb = BLUE_SOFT if r == 0 else (SOFT if c == 0 else WHITE)
            cell.margin_left = cell.margin_right = Pt(14)
            cell.margin_top = cell.margin_bottom = Pt(8)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            t = cell.text_frame
            t.word_wrap = True
            for i, line in enumerate(val.split("\n")):
                p = t.paragraphs[0] if i == 0 else t.add_paragraph()
                runs(p, line, size, BLUE if r == 0 else INK, bold=(r == 0 or c == 0))
    return tbl


# ═════════════════════ 1. Summary ═════════════════════
s = prs.slides.add_slide(BLANK)
text(s, L, 70, 1000, 40, "변재혁  ·  다우기술 백엔드 개발자  ·  책임  ·  8년차", 26, MUTE, bold=True)
text(s, L, 118, W, 170,
     "부하 테스트로 병목을 찾아 [[구조를 바꿔]] 해결해 온 백엔드 개발자\n지금은 그룹웨어 LLM 에이전트 서비스를 운영하고 있습니다",
     52, INK, font=FONT_MED, spacing=1.15)
chips = ["Java · Spring", "Python · FastAPI", "LangGraph", "PostgreSQL", "Airflow", "RabbitMQ", "Kubernetes"]
cx = L
for c in chips:
    cw = 26 + len(c) * 15.5
    sh = rect(s, cx, 318, cw, 46, WHITE, LINE, 1.3, MSO_SHAPE.ROUNDED_RECTANGLE, 0.5)
    t = sh.text_frame
    t.margin_top = t.margin_bottom = Pt(0)
    t.vertical_anchor = MSO_ANCHOR.MIDDLE
    t.paragraphs[0].alignment = PP_ALIGN.CENTER
    runs(t.paragraphs[0], c, 21, GRAY)
    cx += cw + 12

KPI = [
    ("3,000VU DB 오류 0", "부하 시작 6분 만에 DB가 끊기던\n체크포인트 저장 구조 재설계", "AI 에이전트 · 2026"),
    ("약 200TB", "클러스터 9개 첨부 이관 파이프라인\n미이관 0.2%는 사용하지 않는 파일", "데이터 마이그레이션 · 2025–26"),
    ("C → Java", "4.0 메일 스토어 신규 구축\n클러스터마다 2대, 증설 가능한 구조", "메일 스토어 · 2024–25"),
    ("8,000명 / 10분", "1만 명 고객사 출근 피크 부하 테스트\n근태 표시 ON 장애 → 정상", "성능 안정화 · 2023–24"),
]
gap = 30
kw = (W - gap * 3) / 4
for i, (n, d, p_) in enumerate(KPI):
    x = L + i * (kw + gap)
    rect(s, x, 410, kw, 260, SOFT)
    rect(s, x, 410, kw, 7, BLUE)
    text(s, x + 26, 440, kw - 52, 60, n, 40, BLUE, bold=True)
    text(s, x + 26, 512, kw - 52, 90, d, 23, INK, spacing=1.1)
    text(s, x + 26, 616, kw - 52, 36, p_, 19, MUTE)

# 타임라인 (과거 → 현재)
Y0, X0, X1 = 760, L, R
def yx(year):
    return X0 + (X1 - X0) * (year - 2019.0) / 8.0
text(s, L, 712, 600, 36, "커리어 타임라인", 22, MUTE, bold=True)
hline(s, X0, Y0 + 150, X1, Y0 + 150, LINE, 1.2)
for yr in range(2019, 2027):
    text(s, yx(yr) - 4, Y0 + 158, 120, 34, str(yr), 20, MUTE)
    hline(s, yx(yr), Y0 + 142, yx(yr), Y0 + 150, LINE, 1.2)
BARS = [
    ("고객사 장애 대응 · 그룹웨어 유지보수", 2019.08, 2023.83, 0, False),
    ("성능 안정화", 2023.83, 2024.5, 0, True),
    ("메일 스토어", 2024.5, 2025.5, 1, True),
    ("데이터 마이그레이션", 2025.42, 2026.5, 0, True),
    ("AI", 2026.5, 2026.92, 1, True),
]
for name, a, b, row, hot in BARS:
    y = Y0 + 20 + row * 58
    sh = rect(s, yx(a), y, yx(b) - yx(a) - 4, 46, BLUE if hot else RGBColor(0xE9, 0xEC, 0xEF),
              shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.2)
    t = sh.text_frame
    t.margin_left = t.margin_right = Pt(8)
    t.word_wrap = False
    t.vertical_anchor = MSO_ANCHOR.MIDDLE
    t.paragraphs[0].alignment = PP_ALIGN.CENTER
    runs(t.paragraphs[0], name, 20, WHITE if hot else GRAY, bold=hot)

# ═════════════════════ 2. AI ① 개요 ═════════════════════
s = slide_base("AI 에이전트 · 개요", "그룹웨어 AI 에이전트 운영", "2026. 7 ~ 현재")
section_list(s, L, 232, 800, 470, [
    "H:배경",
    "메일·결재·캘린더·메신저를 도구로 호출하는 LangGraph ReAct 에이전트",
    "외주사가 만든 POC를 **오픈 시점부터 인수해 운영과 성능 개선 담당**",
    "H:역할",
    "팀 5명 · agent 개발은 본인 + 외주 2명, **운영은 본인 담당**",
    "운영 장애 대응, 부하 테스트로 계층별 병목을 찾아 DB·메모리 문제 개선",
    "업무 자동화 서비스(ai-automation) 실행 구조 재설계·구현 (서비스 오픈 전)",
], size=24, head=28)
# 구조 그림
node(s, 960, 330, 190, 90, "Front")
node(s, 1190, 330, 190, 90, "stream", "SSE 중계")
node(s, 1420, 250, 390, 250, "agent-api", "LangGraph runtime\n체크포인터 · 업무 도구", mine=True)
hline(s, 1150, 375, 1190, 375, GRAY, 2, True)
hline(s, 1380, 375, 1420, 375, GRAY, 2, True)
node(s, 960, 540, 260, 110, "LLM", "OpenAI · Anthropic\nGemini", size=22)
node(s, 1240, 540, 260, 110, "PostgreSQL", "Redis · ES", size=22)
node(s, 1520, 540, 290, 110, "ai-file", "첨부 파싱 · 지식 색인", mine=True, size=22)
node(s, 960, 250, 420, 60, "ai-automation → step 실행 위임", mine=True, size=20)
hline(s, 1380, 280, 1420, 280, GRAY, 2, True)
for x_ in (1090, 1370, 1665):
    hline(s, min(max(x_, 1440), 1790), 500, x_, 540, GRAY, 1.6, True)
text(s, 960, 664, 850, 32, "[[파란 박스]]: 인수 후 운영하며 개선한 영역 (ai-automation 실행 구조는 재설계·구현)", 19, MUTE, align=PP_ALIGN.RIGHT)
# 주요 기여 카드
CONTRIB = [
    ("체크포인터 재설계", "부하 시 DB를 무너뜨리던 구조 해결\n(다음 장)"),
    ("요청당 DB 왕복 감축", "신규 대화 SQL 37 → 23 문장\n프로세스당 커넥션 8 → 5"),
    ("부하 테스트 병목 규명", "agent·stream·DB 계층별 병목 판정\nai-file 메모리 989MB → 280MB"),
    ("ai-automation 재설계·구현", "DB 큐 → RabbitMQ 중심 실행 구조\nDLQ·멱등 처리 구현"),
]
text(s, L, 712, 600, 40, "주요 기여", 28, BLUE, bold=True)
cw = (W - 90) / 4
for i, (h_, d) in enumerate(CONTRIB):
    x = L + i * (cw + 30)
    rect(s, x, 768, cw, 210, SOFT)
    rect(s, x, 768, 7, 210, BLUE)
    text(s, x + 30, 792, cw - 48, 44, h_, 27, INK, bold=True)
    text(s, x + 30, 846, cw - 48, 120, d, 21, GRAY, spacing=1.12)
text(s, L, 1000, W, 40,
     "Python · FastAPI · LangGraph · OpenAI / Anthropic / Gemini · PostgreSQL · Redis · RabbitMQ · Kubernetes (KEDA)",
     20, MUTE)

# ═════════════════════ 3. AI ② 문제 해결 ═════════════════════
s = slide_base("AI 에이전트 · 문제 해결", "부하 시 DB를 무너뜨리던 체크포인트 구조 재설계", "2026. 7 ~ 8")
flow_cards(s, [
    ("① 문제", ["부하 테스트 시작 약 6분 만에 PostgreSQL이 모든 파드 커넥션 절단",
               "checkpoint_blobs 27GB, 디스크가 가득 차 PG 중단",
               "DBA가 현재 구조로는 운영 불가로 반려"], None),
    ("② 원인", ["요청마다 체크포인트를 새로 쓰고, 끝나면 바로 삭제",
               "단계마다 대화 전체를 다시 저장 → 턴당 102MiB (라운드 수의 제곱으로 증가)",
               "첨부 base64까지 체크포인트에 실려 매 요청 DB에 적재"], None),
    ("③ 해결", ["1차: 종료 때 1회만 저장 (102MiB → 18.5MiB), 쓰고 지우는 구조는 남아 DB 재중단",
               "2차: 일반 run은 프로세스 메모리에만 보관 → 첨부 적재도 함께 사라짐",
               "승인 대기로 멈춘 run만 PG에 저장 → 다른 파드에서 재개",
               "파드 종료 시 graceful shutdown(최대 120초)으로 진행 중 run을 마저 처리"], None),
    ("④ 결과", ["일반 요청의 체크포인트 DB 작업 7건 → 0건 (승인 대기 run만 저장)",
               "다음 병목은 stream CPU (코어당 약 19 req/s)"], "3,000VU\nDB 오류 0"),
], h=660)
footnote(s, "7건 = 이전 상태 조회 1 + 체크포인트 3개 테이블 저장 3 + 요청 끝 삭제 3", y=922)

# ═════════════════════ 4. 이관 ① 개요 ═════════════════════
s = slide_base("데이터 마이그레이션 · 개요", "그룹웨어 3.0 → 4.0 데이터 마이그레이션", "2025. 6 ~ 2026. 6")
text(s, L, 226, W, 90,
     "VM 기반 모놀리식(3.0)의 DB·첨부·메일 데이터를 k8s 기반 차세대(4.0, DB + GCS)로 옮기는 Airflow 파이프라인\n공유형: 서비스 쿼리 작성은 담당자 약 10명, 검증은 DBA · 단독형: 서비스 담당자 없이 3명이 전 과정 진행",
     26, INK, spacing=1.1)
table(s, [
    ["", "1단계 공유형  (2025. 6 ~ 2026. 2)", "2단계 단독형  (2026. 1 ~ 2026. 6)"],
    ["대상", "공유 클러스터 9개 전체, 3차례 단계 이관 (1 → 2 → 6개)\n총 약 20만 명", "단독형 고객 2곳 → 4.0 단독형\n진행 중 요구사항 변경(공유형 통합 → 단독 유지)\n이후 희망 고객만 이관하는 정책으로 변경"],
    ["실행 구조", "Airflow 1대, 단일 메인 DAG", "master / worker 분산\n고객 VPC의 worker가 변환, master가 병합·적재"],
    ["네트워크", "사내망, 중앙 DB 직접 처리", "고객 VPC 안에서 변환, 중앙 DB는 SSH 터널 경유"],
    ["내 담당", "**전체 이관 플로우 리딩**\nAirflow 파이프라인·첨부 이관 주 개발\n결재·게시판 본문 변환 Python 구현", "**본인이 이관 주도** — master/worker 구조·이관 흐름 설계\n그룹웨어 서비스 이관 (ID 채번 변경, JSON 속 PK 변환)\n이관 정책·후속작업 자동화, 경리회계·첨부 이관"],
], L, 330, W, [250, 650, 800], row_h=118, size=24)
text(s, L, 950, W, 50, "Apache Airflow · Python · PostgreSQL · GCS (FUSE)", 22, MUTE)

# ═════════════════════ 5. 이관 ② 문제 해결 ═════════════════════
s = slide_base("데이터 마이그레이션 · 문제 해결", "중단·실패해도 다시 돌릴 수 있는 첨부 이관 파이프라인", "1단계 공유형")
flow_cards(s, [
    ("① 문제", ["클러스터마다 약 20TB, 총 약 200TB 첨부를 VM 디스크 → GCS로 이관, 오래 걸린 곳은 70시간 이상",
               "gsutil로는 클러스터 하나(20TB)에 약 2주 예상, 본이관 일정에 맞출 수 없음",
               "중간에 멈추면 어디까지 됐는지 알 수 없음"], None),
    ("② 원인", ["업로드가 상태 없는 일회성 명령",
               "업로드 성공과 메타데이터 반영 성공이 따로 놂",
               "여러 VM 디스크를 합치며 GCS 경로 충돌"], None),
    ("③ 해결", ["파일별 상태 기록 → DAG 마지막 단계에서 실행 횟수 상한 미만인 실패분만 다시 처리",
               "GCS FUSE + cp -n으로 재실행 안전, 500개 배치",
               "업로드 후 GCS API로 존재·크기 검증",
               "{회사}/{날짜}/{파일} 경로 매핑, 충돌은 자동 교정"], None),
    ("④ 결과", ["미이관 0.2%는 모두 사용하지 않는 파일이라 이관 대상에서 제외",
               "클러스터 9개 첨부 이관 완료 (1 → 2 → 6개 차수)",
               "재실행해도 이미 올린 파일은 건너뛰고 실패분만 처리"], "미이관\n0.2%"),
], h=660)
footnote(s, "선이관(본이관 1주 전 시작) → 증분 이관(운영 중 추가된 파일만) → 본이관 당일엔 [[잔여분만]] 처리", y=922)

# ═════════════════════ 8. 메일 ① 개요 ═════════════════════
s = slide_base("메일 스토어 · 개요", "메일 스토어 신규 구축 (C → Java)", "2024. 7 ~ 2025. 6")
section_list(s, L, 232, 780, 700, [
    "H:배경",
    "디스크 확장 한계 → 메일 원문 저장소를 Local → GCS로",
    "기존 C 기반 스토어를 Java로 재구축",
    "H:역할 — 외주와 협업, Java 구조는 본인",
    "외주(C 개발 경험)가 메일 API 요구사항·전체 아키텍처 설계",
    "**C 중심 설계를 Spring 구조에 맞게 함께 재설계** (Apache James 참고)",
    "**사용자별 SQLite 커넥션·트랜잭션을 Spring tx 방식(AOP + ThreadLocal)으로 직접 구현, 메일 append 수신 개발**",
    "개발을 마친 뒤 더 급한 3.0 → 4.0 이관에 차출, 운영은 다른 담당자가 이어받음",
], size=25, head=28)
node(s, 960, 300, 230, 110, "MTA / IMAP", "Webmail")
node(s, 1250, 250, 560, 210, "store-d  (Netty TCP)", "클러스터마다 2대 · 증설 가능\n사용자 생성 시 담당 store 지정 (한 사용자는 한 store만)\n길이 prefix 프레이밍 · 본문은 파일로 스트리밍", mine=True)
hline(s, 1190, 355, 1250, 355, GRAY, 2, True)
node(s, 1250, 520, 560, 210, "mailbox", "커넥션 컨텍스트 · 다중 DB 트랜잭션\nMIME 파싱 → 저장", mine=True)
hline(s, 1530, 460, 1530, 520, GRAY, 2, True)
node(s, 960, 520, 230, 100, "GCS", "메일 원문")
node(s, 960, 640, 230, 100, "사용자별 SQLite", "목록·메타")
hline(s, 1250, 570, 1190, 570, GRAY, 2, True)
hline(s, 1250, 690, 1190, 690, GRAY, 2, True)
node(s, 1250, 790, 560, 130, "indexer", "비동기 · 원문은 로컬 큐 파일로 전달 → FTS5 검색 DB")
hline(s, 1530, 730, 1530, 790, GRAY, 2, True)
text(s, L, 1000, W, 40, "Java · Spring · Netty · MyBatis · SQLite (FTS5) · GCS", 20, MUTE)

# ═════════════════════ 9. 메일 ② 문제 해결 ═════════════════════
s = slide_base("메일 스토어 · 문제 해결", "사용자별 SQLite를 안전하게 다루는 커넥션 구조와 append 수신")
flow_cards(s, [
    ("① 문제", ["사용자마다 개인 SQLite 4종(메일 mindex·대용량 첨부·MDN·웹폴더)",
               "TCP 채널마다 대상 사용자가 다름",
               "대용량 메일을 받을 때 메모리 부담"], None),
    ("② 고려할 점", ["DB를 매번 열고 닫는 비용",
                  "'나에게 쓰기'처럼 한 사용자 mindex에 쓰기가 동시에 들어오면 → busy lock",
                  "여러 DB에 걸친 쓰기 중 실패하면 함께 되돌려야 함",
                  "수신 실패 시 받던 파일 정리"], None),
    ("③ 해결", ["커넥션 컨텍스트가 DB 종류별로 필요할 때만 열고, 없으면 스키마 생성",
               "Netty 채널에 묶어 재사용, 다른 사용자 요청은 차단",
               "Spring tx 방식을 AOP + ThreadLocal로 직접 구현 → mindex·MDN을 함께 begin·rollback",
               "append: 헤더 → continuation → 본문을 파일로 스트리밍"], None),
    ("④ 결과", ["C 스토어를 대체하는 4.0 메일 스토어로 도입 (클러스터마다 2대, 처음부터 증설 가능한 구조)",
               "쓰기는 시작부터 EXCLUSIVE 락으로 순서를 세우고, 3초 넘으면 MTA가 재전송"], "Java 스토어\n4.0 전환"),
], h=660)
footnote(s, "한계: 커밋 단계 원자성은 미보장 (mindex 커밋 후 MDN 커밋 실패 시 불일치) — 기존 C와 같은 구조, 수신 확인(MDN)에 한정돼 수용", y=922)

# ═════════════════════ 10. 성능 ① 개요 ═════════════════════
s = slide_base("성능 안정화 · 개요", "1만 명 대형 고객사 서비스 성능 안정화", "2023. 11 ~ 2024. 6")
section_list(s, L, 232, 900, 700, [
    "H:배경",
    "10,000명 고객사 서비스 오픈 전 안정성 확보 (부문 KPI 과제)",
    "1차 서버 개선 10건(조직도·대화방·알림 등) → 2차 개선, **영향 큰 순서로 처리하고 목표 달성 후 종료**",
    "출발점: 2023년 약 3,400명 고객사 장애 때 쿼리로 개선한 조직도 API도 1만 명 부하는 감당 못 함 → **변경분 대신 전체 조직도를 캐시로** 내려주는 방향 (부록)",
    "H:역할 — 부하 테스트·개선·장애 대응 단독 진행",
    "테스트 장비 구축, 고객사 환경 재현 (유저 12,000 · 부서 3,000)",
    "JMeter 출근 시나리오 작성, Scouter로 병목 분석",
    "쿼리·캐시·구조 개선 → 테스트 장비 → 사내 그룹웨어 → 클라우드 8개 반영",
    "기능 테스트는 품질관리팀과 협업",
], size=24, head=28)
rect(s, 1110, 232, 700, 250, SOFT)
rect(s, 1110, 232, 7, 250, BLUE)
text(s, 1150, 252, 640, 40, "목표", 24, MUTE, bold=True)
text(s, 1150, 296, 640, 110, "1만 명 고객사 정상 서비스\n[[출근 피크 기준 8,000명 / 10분]]", 27, INK, bold=True, spacing=1.15)
text(s, 1150, 404, 640, 70, "9시 출근 약 6,500명 + 여유 약 20% (분당 800명)\n기존 최대 피크(분당 60명)의 약 13배 · 출근 1회에 API 44개", 21, GRAY, spacing=1.1)
rect(s, 1110, 500, 700, 182, SOFT)
rect(s, 1110, 500, 7, 182, BLUE)
text(s, 1150, 520, 640, 40, "고객 환경", 24, MUTE, bold=True)
text(s, 1150, 562, 640, 110, "등록 9,724명(테스트는 12,000명) · 530개 조직 9단계 · 부서 최대 400명\n9시 출근 약 6,500명 · GPS 기반 모바일 출근\n개선 전: 근태 표시 ON 시 8,000명 부하에서 장애 (CPU 85%)", 21, GRAY, spacing=1.15)
# 출근 피크를 막던 나머지 문제 (근태 표시는 다음 장)
OTHERS = [
    ("조직도", "40~50초 → 5초", "부서·부서원 전체 조직도 캐시\n+ 조직 변경 이벤트로 해당 회사만 evict"),
    ("대화방 API", "1,022ms → 134ms", "요청당 쿼리 수백 개(N+1)\n→ 필요한 컬럼만 Native Query"),
    ("캐시 엔트리 상한", "모든 고객사 반영", "장비를 키워도 그대로인 원인 규명\n→ 사용자 수 구간별 캐시·힙 가이드"),
]
text(s, L, 712, 1500, 40, "출근 피크를 막던 나머지 문제  ·  다음 장은 가장 오래 붙잡은 근태 표시", 26, BLUE, bold=True)
pg, pw, ph = 30, (W - 30 * 2) / 3, 200
for i, (h_, num, d) in enumerate(OTHERS):
    px, py = L + i * (pw + pg), 768
    rect(s, px, py, pw, ph, SOFT)
    rect(s, px, py, 7, ph, BLUE)
    text(s, px + 30, py + 20, pw - 48, 40, h_, 24, INK, bold=True)
    text(s, px + 30, py + 58, pw - 48, 44, num, 30, BLUE, bold=True)
    text(s, px + 30, py + 112, pw - 48, 80, d, 20, GRAY, spacing=1.1)
text(s, L, 1000, W, 40, "Java · Spring · JPA · MyBatis · Ehcache (Terracotta) · JMeter · Scouter", 20, MUTE)

# ═════════════════════ 11. 성능 ② 문제 해결 ═════════════════════
s = slide_base("성능 안정화 · 문제 해결", "출근 피크에 서버를 무너뜨리던 근태 표시 재설계", "2023. 11 1차 → 2024. 4 2차")
flow_cards(s, [
    ("① 문제", ["근태 표시(메신저 출근 상태) ON 시 8,000명 / 600초 출근 부하에서 장애 (CPU 85%)",
               "근태 동기화 API 28초, 첫 로그인 때 전 사원 근태를 XMPP로 받는 데 최대 20분",
               "원인을 몰라 고객사에 근태 표시 OFF로 안내한 상태"], None),
    ("② 원인", ["출근 1건마다 쓰기 트랜잭션 + 전 사원 엔티티 로딩 (dirty checking)",
               "출퇴근·휴가 상태만 필요한데 근무그룹·연장근무·휴가 상세까지 계산",
               "**출근 1건 = 회사 전원에게 XMPP 발송**"], None),
    ("③ 해결", ["1차: 근태 데이터 캐시로 API 30초 → 1초, **그래도 장애 그대로** → 문제는 발송 쪽",
               "2차: 읽기 전용 + ID 집합 연산, 상태만 조회",
               "화면 진입은 API 응답(pull), 이후 변화는 1분마다 회사별 1건으로 묶어 발송",
               "응답 방식만 81%, 묶음 발송만 82% → 둘 다 적용해 71%"], None),
    ("④ 결과", ["8,000명 / 600초 장애 → 정상",
               "동기화 API 28초 → 0.6초, 첫 로그인 전 사원 근태 수신 최대 20분 → 10초 이내 (API 응답으로)",
               "대가: 최대 1분 지연 → 옵션으로 제공 (기본은 즉시 발송)"], "CPU\n85% → 71%"),
], h=660, size=25)
footnote(s, "실서비스(1만 명 고객사) 오픈 후 출근 피크 정상 운영 · 18시 퇴근 시간 장애는 별도 원인으로 패치 (부록)", y=922)

# ═════════════════════ 12. 보유 기술 ═════════════════════
s = slide_base(None, "보유 기술")
SKILLS = [
    ("Language · Framework", ["Java", "Spring", "Python", "FastAPI"]),
    ("Persistence · Cache", ["JPA", "MyBatis", "Ehcache (Terracotta)", "Redis"]),
    ("Data · Pipeline", ["PostgreSQL", "SQLite (FTS5)", "Apache Airflow"]),
    ("Messaging · Network", ["RabbitMQ", "Netty (TCP)"]),
    ("AI", ["LangGraph", "LangChain", "OpenAI / Anthropic / Gemini API"]),
    ("Infra · 관측 · 테스트", ["Kubernetes", "KEDA", "GCP (GCS)", "JMeter", "Scouter"]),
]
for i, (cat, items) in enumerate(SKILLS):
    y = 250 + i * 122
    text(s, L, y, 460, 60, cat, 27, BLUE, bold=True, anchor=MSO_ANCHOR.MIDDLE)
    cx = L + 480
    for it in items:
        cw = 34 + len(it) * 16.5
        sh = rect(s, cx, y + 4, cw, 52, WHITE, LINE, 1.3, MSO_SHAPE.ROUNDED_RECTANGLE, 0.5)
        t = sh.text_frame
        t.margin_top = t.margin_bottom = Pt(0)
        t.vertical_anchor = MSO_ANCHOR.MIDDLE
        t.paragraphs[0].alignment = PP_ALIGN.CENTER
        runs(t.paragraphs[0], it, 23, INK)
        cx += cw + 14
    if i < len(SKILLS) - 1:
        hline(s, L, y + 92, R, y + 92, RGBColor(0xF1, 0xF3, 0xF5), 1)

# ═════════════════════ 13. 감사합니다 ═════════════════════
s = prs.slides.add_slide(BLANK)
text(s, L, 440, W, 100, "감사합니다", 60, INK, font=FONT_MED, align=PP_ALIGN.CENTER)
text(s, L, 560, W, 50, "변재혁", 24, MUTE, align=PP_ALIGN.CENTER)
text(s, L, 960, W, 40,
     "구성·디자인은 AI 도구(Claude Code)를 활용했으며, 모든 사례·수치는 코드·커밋·테스트 기록으로 본인이 검증했습니다.",
     19, MUTE, align=PP_ALIGN.CENTER)

# ═════════════════════ 부록 ═════════════════════
s = prs.slides.add_slide(BLANK)
text(s, L, 400, W, 60, "APPENDIX", 26, BLUE, bold=True, align=PP_ALIGN.CENTER)
text(s, L, 450, W, 100, "부록 · 기술 상세", 56, INK, font=FONT_MED, align=PP_ALIGN.CENTER)
text(s, L, 570, W, 50, "프로젝트별 기술 상세", 24, MUTE, align=PP_ALIGN.CENTER)

s = slide_base("부록 · AI 에이전트", "성능·안정성 상세")
section_list(s, L, 232, W, 780, [
    "H:부하 테스트로 병목 계층 규명",
    "agent만 보다가 진입점 stream을 계측 → 게이트웨이(2파드) 포화 확인",
    "게이트웨이를 빼고 stream → agent 직접 연결: 응답 헤더 3.2초 → 22ms, 5xx 14.1% → 0%",
    "H:요청당 DB 왕복 감축",
    "요청 1건의 SQL 전수 조사 → PK는 컬럼 DEFAULT가 생성, 넣은 행은 INSERT … RETURNING으로 같은 문장에서 받아 재조회 제거",
    "체크포인트 외 일반 SQL: 신규 대화 37 → 23 문장, 프로세스당 커넥션 8 → 5",
    "H:ai-file 부하 테스트 · 메모리",
    "OOM 원인(glibc mmap 임계값 + MuPDF store) 규명 → 메모리 989MB → 280MB, 요청당 증가 79배 감소",
    "PPTX 읽기 요청 1.8~3.5초 → 중앙값 약 1초 (지연의 89%였던 불필요한 재압축 제거)",
], size=29, head=32, space=12)

s = slide_base("부록 · AI 에이전트", "DB가 큐 노릇을 하던 자동화 실행 구조를 메시지 큐 중심으로", "ai-automation · 2026. 10 · 서비스 오픈 전")
flow_cards(s, [
    ("① 문제", ["대기열이 DB 테이블 — 신규 100건이 와도 큐에는 전역 동시 실행 한도인 8건만, 나머지는 DB 대기 → 대기량을 알 수 없음",
               "지연 재시도를 Worker 메모리에 둠 → 파드가 재시작되면 재시도 예약 유실",
               "발행이 리더 파드 1개에 몰리고, 매번 전역 lock + 활성 실행 전체 COUNT"], None),
    ("② 원인", ["AI Home(에이전트 실행 서버)에 MQ 연결이 없음 → 완료가 DB 행 변경이 되어 PG NOTIFY·발행 리더가 필요",
               "동시 실행 한도를 DB에서 엄격히 지킴 → 대기열이 DB로 감",
               "결국 큐의 기본 기능(지연 재시도·TTL·DLQ)을 앱 코드로 다시 만듦"], None),
    ("③ 해결", ["대기는 RabbitMQ: start / start.interactive / continue + 지연 큐·DLQ, DB 커밋 후 발행",
               "동시 실행은 Redis 슬롯 한 곳, 상한 = AI Home 파드 수 × K(파드 하나가 동시에 맡는 step 수)",
               "AI Home 완료는 콜백 → continue 큐, Worker는 step을 붙잡지 않음",
               "발행 실패는 1분 주기 안전망이 발행 기록을 보고 재발행 (기존 NOTIFY·발행 리더·advisory lock 제거)"], None),
    ("④ 결과", ["Worker를 4개 시점에 강제 종료하고 응답을 유실시켜도 각 step 1회 실행, 슬롯 누수 없음",
               "테스트 518개 통과"], "장애 주입\n5종 통과"),
], h=660, size=23)
footnote(s, "역할: 외주가 만든 기존 구조를 점검해 원인 2가지를 진단하고, ai-automation · AI Home 양쪽 실행 구조를 재설계·구현", y=922)

s = slide_base("부록 · AI 에이전트", "ai-automation — 이런 일이 생기면")
CASES = [
    ("9시에 예약이 몰리면", [
        "실패시키지 않고 큐에서 대기",
        "AI Home 부하 지표에 자동화 실행 수를 합산해 자동 증설 (큐 길이 기준·출근 시간대 미리 증설은 설계까지)",
        "사람이 누른 작업(지금 실행·승인 재개)은 전용 자리 10% → 예약 뒤에 줄 서지 않음"]),
    ("AI Home 파드가 중간에 내려가면", [
        "조회·LLM 판단만 한 단계는 다른 파드에서 다시 실행",
        "승인 후 메일 발송처럼 쓰기 도중이었다면 다시 돌리지 않고 \"결과 확인 필요\"로 남김 → [[메일 두 번 발송 방지]]",
        "근거: 쓰기 도구는 항상 사람 승인 뒤에만 실행"]),
    ("같은 메시지가 계속 실패하면", [
        "10회 실패하면 DLQ로 보내고, 60초 뒤 다시 시도",
        "3번 돌아도 안 되면 격리 큐(parked)로 옮겨 사람이 확인",
        "60분 넘게 기다린 실행은 다시 넣지 않고 실패 처리 (장애가 풀리는 순간 한꺼번에 몰리는 것 방지)"]),
]
cg = 40
cw = (W - cg * 2) / 3
for i, (h_, lines) in enumerate(CASES):
    x = L + i * (cw + cg)
    rect(s, x, 232, cw, 660, SOFT)
    rect(s, x, 232, cw, 7, BLUE)
    text(s, x + 30, 262, cw - 60, 50, h_, 30, INK, bold=True)
    t = tb(s, x + 30, 342, cw - 60, 530)
    for j, line in enumerate(lines):
        p = t.paragraphs[0] if j == 0 else t.add_paragraph()
        bullet(p, marl=24, indent=-22)
        runs(p, line, 25, INK)
        p.space_before = Pt(0 if j == 0 else 22)
        p.line_spacing = 1.1
footnote(s, "원칙: 재시도는 실패 종류마다 한 곳에서만 → 여러 곳이 동시에 재시도해 호출이 불어나는 것 방지", y=922)

s = slide_base("부록 · 데이터 마이그레이션", "기술 포인트 — 공유형")
section_list(s, L, 232, W, 780, [
    "H:SQL 병렬 실행",
    "SQL을 쿼리 단위로 쪼개 쿼리 1개 = Airflow 태스크 1개 (dynamic task mapping + pool)",
    "결재 본문: Python 파싱 방식으로 구현 → DBA가 이를 바탕으로 id 범위(5만 단위) SQL 방식으로 전환",
    "H:첨부 실패 / 재시도",
    "파일별 상태(업로드·메타데이터 성공, 실행 횟수) 기록",
    "DAG 마지막 단계에서 실행 횟수 상한 미만인 실패분만 다시 처리, 이미 올라간 파일은 메타데이터만 재시도",
    "H:gsutil → GCS FUSE",
    "파티션 1개 실측으로 클러스터마다 약 2주 예상 → FUSE 경로로 cp -n(재실행 안전), 500개 배치",
    "H:경로 변환",
    "로컬 → {회사}/{날짜}/{파일} GCS 경로 매핑, 디스크 병합 시 경로 충돌 자동 교정",
    "결재 본문 HTML의 서명·이미지 경로(암호화 토큰 복호화) 치환, 원래 값 보존 + 태그 검증 DAG",
    "H:본이관 당일",
    "차수별 14시간 컷오버(00시 차단 → 14시 오픈)에서 데이터 변환·운영 4.0 이관 DAG 직접 실행, 변환 실패 시 서비스 담당자에게 공유 후 재실행",
], size=25, head=28, space=8)

s = slide_base("부록 · 데이터 마이그레이션", "단독형 이관 전체 설계 (직접 설계)", "2026. 1 ~ 6 · 단독형 고객 2곳")
text(s, L, 222, 1040, 36, "고객사 VPC · worker 장비  ·  선이관(D-10)과 본이관이 같은 경로", 22, MUTE, bold=True)
text(s, 1196, 222, 614, 36, "중앙 Airflow 장비  ·  본이관 병합", 22, MUTE, bold=True)
hline(s, 1170, 222, 1170, 480, LINE, 1.2)
STEPS = [
    ("고객사 복제 VM", "DB 물리 복제\nmindex·mdata·첨부 마운트", False),
    ("worker 장비", "3.0 → 4.0 구조(pre_)\n변환 · FK 검증", True),
    ("중앙 Airflow 장비", "pg_dump → scp\n→ restore", False),
    ("merge_", "FK 제거 후\n고객사 데이터 병합", True),
    ("post_", "운영 + 단독형 병합\nFK 검증", True),
]
nw, ng = 300, 50
for i, (t_, sub, mine) in enumerate(STEPS):
    x = L + i * (nw + ng)
    node(s, x, 280, nw, 170, t_, sub, mine=mine, size=24)
    if i < len(STEPS) - 1:
        hline(s, x + nw + 4, 365, x + nw + ng - 4, 365, GRAY, 2, True)
rect(s, L, 486, W, 70, SOFT)
text(s, L + 24, 486, W - 48, 70,
     "[[운영 병합]]: 원래 목표가 50~100개 고객사 → 서비스를 내리기 전에 merge_에서 검증을 끝내고, 서비스 중단 후 운영 DB와 병합만  (검토한 안: 테이블 단위 로드, 논리 복제)",
     22, INK, anchor=MSO_ANCHOR.MIDDLE)
text(s, L, 566, W, 36, "첨부·mdata는 GCS로 업로드, 본이관 당일 잔여분은 DB 병합과 동시에 처리", 20, MUTE)
section_list(s, L, 630, W, 380, [
    "H:PK 처리가 필요한 이유",
    "여러 고객사 DB와 운영 데이터를 한 DB로 합치면 PK가 겹침 → 고객사별 PK offset 적용 (테이블군 분류는 동료 작업)",
    "내 몫: Works/Applet JSON 설정 안에 숨은 멤버·부서·조건값 id를 Python으로 파싱·변환, 원본을 정규화해 결과와 비교하는 검증 태스크",
    "H:결과",
    "단독형 고객 2곳 4.0 이관 완료",
], size=25, head=28, space=8)

s = slide_base("부록 · 데이터 마이그레이션", "k8s 전환 후 모바일 캘린더·연락처 동기화 장애", "2025. 11 (3주)")
flow_cards(s, [
    ("① 문제", ["VM에서 되던 모바일 캘린더·연락처 동기화가 k8s 전환 후 미동작",
               "클러스터 1~9 확인 결과 해당 기능 사용자 약 2%",
               "이관 3주 전 맡아 원인 추적"], None),
    ("② 원인", ["Ingress rewrite로 클라이언트 요청 URL과 CalDAV 응답 href가 달라져 오류", "rewrite 때문에 일부 요청은 서버까지 도달하지 못함"], None),
    ("③ 해결", ["계층별 요청 경로를 추적해 불일치 지점을 특정하고 모바일·인프라·IAM 담당자와 공유",
               "본인은 CalDAV 응답 수정, IAM·모바일은 각 담당자가 수정"], None),
    ("④ 결과", ["캘린더·연락처 동기화 정상화",
               "이관 전에 사용자 약 2%의 동기화 장애 해소"], "동기화\n정상화"),
], h=660)

s = slide_base("부록 · 메일 스토어", "사용자별 SQLite 구조와 수신 단계 분리")
section_list(s, L, 232, W, 780, [
    "H:Spring 트랜잭션을 그대로 쓰지 못한 이유",
    "Spring tx는 DataSource가 고정된 구조가 전제 — 여기는 요청한 사용자와 DB 종류에 따라 DataSource가 그때그때 정해지고, 사용자당 SQLite가 4개",
    "→ Spring tx의 AOP + ThreadLocal 방식을 본떠 직접 구현, mindex·MDN을 함께 begin·rollback",
    "H:사용자와 store 배정",
    "사용자 생성 시 담당 store를 DB에 지정 → 한 사용자는 한 store만 접근, 파드끼리 같은 SQLite를 동시에 열지 않음",
    "H:busy lock",
    "같은 사용자가 Outlook(IMAP)과 웹메일을 동시에 쓰면 mindex 쓰기가 겹침 ('나에게 쓰기' 동시 append도 같은 경우)",
    "쓰기는 시작부터 EXCLUSIVE + 3초 timeout, 중복 수신·append 실패 잔존 파일 처리",
    "H:수신 → 저장 → 색인 3단계",
    "Netty가 본문을 파일로 받고, 저장은 동기, 색인은 비동기 (indexer는 GCS 대신 로컬 큐 파일로 원문을 받음)",
    "색인이 느려도 메일 수신 응답에 영향 없음, 색인 큐는 received / indexing 디렉터리로 분리",
], size=26, head=29, space=9)

s = slide_base("부록 · 성능 안정화", "개선 전후 측정")
table(s, [
    ["개선 항목", "개선 전", "개선 후", "측정"],
    ["메신저·모바일 조직도 표시", "40~50초 (사용 불가)", "5초 이내", "테스트 장비"],
    ["조직도 API 응답 (캐시)", "215ms", "22ms  (-90%)", "사내 그룹웨어,\nScouter"],
    ["조직도 API 요청당 CPU / 메모리", "182ms / 78MB", "9ms / 1MB", "사내 그룹웨어,\nScouter"],
    ["대화방 API (Native Query)", "사내 1,022ms, 에러 88건\n클라우드 평균 150ms", "134ms, 에러 0건\n44ms  (-65%)", "사내 그룹웨어,\n클라우드 8개"],
    ["대화·알림 API (Slice)", "-", "평균 -41%, 알림 -76%", "사내 그룹웨어\naccess log"],
    ["근태 동기화 API /\n첫 로그인 전 사원 근태 수신", "28초 / 최대 20분 (XMPP)", "0.6초 / 10초 이내 (API 응답)", "테스트 장비"],
    ["근태 표시 ON 출근 부하 (600초, 목표 8,000명)", "5,000명 정상 (CPU 56%)\n8,000명 장애 (CPU 85%)", "8,000명 정상 (CPU 71%)", "같은 장비 64GB·8코어"],
], L, 232, W, [500, 470, 420, 310], row_h=86, size=23)
footnote(s, "사내 그룹웨어: 회사가 직접 VM에 구축해 전 직원이 쓰는 자사 그룹웨어 (실사용 환경)", y=950, size=21)

s = slide_base("부록 · 성능 안정화", "기술 포인트")
section_list(s, L, 232, W, 780, [
    "H:N+1 → Native Query",
    "조직도 응답 하나에 사용자·프로필·직위/직급·사진·다국어·겸직 매핑이 필요",
    "→ 필요한 컬럼만 native 쿼리로 읽고 메모리에서 조립 (조직도: 쿼리 2번 + groupingBy), 증분 조회·Slice 페이징 (대가: DB 종속성)",
    "H:조직도는 통째로, 메뉴 권한은 잘게",
    "조직도: 회사 단위 트리 전체를 캐시 1건에 — 클라이언트가 트리 전체를 요청, 변경은 드물고 조회는 잦음",
    "메뉴 권한: 사용자 1건 캐시 → (사용자, 메뉴) 단위로 세분화, 바뀐 메뉴 키만 evict",
    "무효화: 조직 변경 이벤트 14종(기존 8종에 evict 연결 + 없던 6종 신규)으로 해당 회사 키만 evict, TTL 안전망 + 기동 시 워밍업, Terracotta eventual consistency",
    "H:사이즈 가이드",
    "캐시 영역별 엔트리 크기를 실측해 사용자 수 구간별(300 ~ 10,000명) 엔트리·힙 설정표 작성, 모든 고객사 반영",
], size=27, head=30, space=10)

s = slide_base("부록 · 성능 안정화", "오픈 직후 매일 18시에 반복된 퇴근 시간 장애", "2024. 6. 7 접수 → 6. 18 패치")
flow_cards(s, [
    ("① 문제", ["오픈 직후 18시 퇴근 시간마다 장애 (6/3~6/12 중 7일)",
               "notifier CPU 급증 → 커넥션 풀 Max 도달, 고객 접속 불가",
               "유저 11,530명(active 7,672명), 1분에 API 9,116건"], None),
    ("② 원인", ["notifier GC가 CPU를 과점유 → Web이 쓸 CPU 부족",
               "모바일 접속마다 주소록(roster) 요청 → 1만 명 정보 반환",
               "아이폰 요청에 JID 리소스(ios) 누락 → routing table 탐색 중 메모리 과점유",
               "힙 덤프·iOS/Android 패킷 비교로 특정"], None),
    ("③ 해결", ["**notifier 인터셉터 패치**: roster 요청 차단, presence는 PC 세션만 통과(블랙리스트 → 화이트리스트)",
               "먼저 시도: presence 패킷 차단(효과 없음), CPU 12 → 36 vCPU, heap 8G → 16G",
               "아이폰 리소스 누락 근본 수정은 모바일팀에 전달"], None),
    ("④ 결과", ["증설(6/14) 이후 패치 전날·다음 날 비교: 18:00~18:10 openfire CPU 평균 36.6% → 7.5%, 최대 82% → 14%",
               "18시 반복 장애 해소"], "GC 1분\n180회 → 6회"),
], h=660)

s = slide_base("부록 · 고객사 장애 대응", "약 3,400명 고객사 출근 시간 장애 — 조직도 API", "2023. 3 ~ 9")
flow_cards(s, [
    ("① 문제", ["출근 시간 조직도 API 응답 08:00 10초 → 08:20 30초 → 08:30 장애",
               "3월 초·4월 초 반복 발생",
               "스레드 덤프로 원인 후보 정리, Tika·ImageMagick 등은 배제"], None),
    ("② 원인", ["조직도 변경 조회: 기준 시각이 없으면 전체 유저 조회 + 엔티티 변환 중 추가 쿼리",
               "부서 조회: 큰 limit로 풀스캔, 부서원 테이블 인덱스 없음",
               "근태 동기화: 전 사원 IN 쿼리, 쓰기 트랜잭션"], None),
    ("③ 해결", ["메신저 전용 유저 컨버터, 연관관계 Lazy, 불필요 조인 제거",
               "부서원 테이블 인덱스 추가 (DBA 검토)",
               "근태: 전 사원 IN → company_id 조건, 조회 트랜잭션 분리"], None),
    ("④ 결과", ["nGrinder: 부서 API TPS 0.7 → 8",
               "유저 API 평균 3.16초 → 1.34초 (80 vuser)",
               "이 쿼리 개선판으로 1만 명 부하 테스트 → 감당 못 함 → 이후 전체 조직도 캐시 방식으로 전환"], "TPS\n0.7 → 8"),
], h=660)

prs.save(OUT)
print("slides:", len(prs.slides))
