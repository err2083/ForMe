# 내 작업 코드 워크스루

- 작성: 2026-11-05 (진행 중 — 기억과 다른 점은 사용자 확인 후 보정)
- 목적: 면접에서 "내가 한 일이 코드로 어떻게 짜여 있는지" 설명하기 위한 복습 자료. 기여마다 범위(본인/타인) · 코드 지도 · 호출 흐름 · 핵심 코드 발췌 · 설정 · 설계 이유 · 이력 · 30초 설명
- 짝 문서: `2026-11-05-interview-study-guide.md` (예상 질문·답변, 포트폴리오 불일치 표)
- 기준: 각 저장소 develop/master HEAD (2026-11-03~05), 라인 번호는 그 시점. 저장소는 읽기만 함
- 비밀값: 마이그레이션 저장소의 평문 비밀번호는 제거된 사본만 참조, 문서에 값 없음

## 목차
1. AI 에이전트 (ai-home-poc) — 체크포인터 재설계 · DB 왕복 감축 · MCP 연동 · 재인터럽트 · 루프 상한
2. ai-file / ai-automation — 메모리 대응 · PPTX · claim-check / MQ 실행 구조(tick → DLQ)
3. 데이터 마이그레이션 (domig-airflow-dev / do-vpc-mig) — 메인 DAG · 첨부 이관 · 본문 변환 · master/worker · 숨은 PK · chat · sudo/exit code · 실물 파일 확인
4. 메일 스토어 (dop-mail-store) — SQLite 커넥션·AOP 트랜잭션 · Netty 채널 바인딩 · 길이 prefix · append · 색인 · busy lock/reserv
5. 성능 안정화 (daouoffice) — 조직도 전체 트리 캐시 · 근태 표시 · 대화방 · notifier · 2023 조직도 API · 2차 개선

## 워크스루에서 새로 확인된 사실 (기억·덱과 다른 점, 확인 필요)
| 프로젝트 | 내용 |
|---|---|
| AI | graceful_timeout 45→120, timeout 60→150, terminationGracePeriodSeconds 30→150 (4f410bb7 entrypoint → 6987c415 gunicorn_conf) |
| AI | thread 락(acquire_lock)은 dskim 원형, 승인 판정 원형은 jueon — 본인은 fail-closed 4줄(86192291) |
| AI | Redis 저장소는 단위 테스트로만 확인, dev/stg/prod 모두 backend "pg" |
| ai-automation | admission fence·`__ready__` 마커·EXECUTION_ENABLED 게이트·AI Home accept() 멱등은 springfefe. 본인: 큐 구조·커밋 후 publish·Lua 슬롯 원형(c7b295b)·handoff·generation·reserve() 429·완료 콜백·파드 등록부 |
| ai-file | PPTX 슬라이드 창 개념은 pbs-7818(8f328f2), 본인은 창 생성 방식 변경. knowledge 색인은 세대(uuid) 방식(pbs-7818 d113818). process_job 본문은 대부분 타인, 본인은 풀 컨슈머·claim SQL |
| 이관 | 쿼리 단위 mapping은 GW만. fast/slow 분리(b018def7)와 GW 건수 검증 태스크는 heesu, 본인은 DAG 연결(18c434bc) |
| 이관 | 경로 충돌 rename은 bd264dbd(2025-08-26)부터, 46461c47은 업로드 쪽 개별 복사 추가 |
| 이관 | 단독형 sensor·폴링은 대부분 hwgyun, 본인은 trigger_worker_api. chat 규모 주석이 15만 행 / 15K rooms / 약 81만으로 엇갈림 (덱 "40만 행" 확인 필요) |
| 메일 | reserv는 init~2025-01-21 expunge `{MINDEX, MDN, RESERVE}`에 묶여 있었음 → 8063570c에서 `{MINDEX, MDN}`, b2cf97b3에서 삭제. reserv = 공용 `reserve/_Reserve.db`, HikariCP 5, busy_timeout 500. 제거 이유는 본인 확인 필요 |
| 메일 | 트랜잭션은 Spring tx 아닌 자체 AOP(SqlSessionAspect)+ThreadLocal. 롤백 범위 init: 모든 MailBoxException → d82a07e0: DB 계열. Repository 밖 예외(파싱·GCS)는 rollback 안 됨 → EXCLUSIVE가 채널에 남을 위험 |
| 메일 | 채널 바인딩·rollbackQFile·@Async 색인 리스너는 init부터 존재. 본인 변경: QFileProcessType·xattr(e1ca1187), 예외별 정리(c4c2d104), 프레이밍(d3fd195e→54020b8f 바이너리 int) |
| 성능 | ⚠ 근태 relay 쿼리 `TO_DATE(...)`가 PG에서 시각을 버려 1분 구간이 빌 수 있음(db6419cc2c2 → 13580e920cc) — 운영 PG에서 확인 권장 |
| 성능 | evict는 2단계: Aware 8종(8e4f319344e, `// starlight240116` 표시) → 이벤트 발행(40b831f1361). 첫 캐시 커밋 40ee97ec354엔 evict 없음 |
| 성능 | 대화방 "쿼리 1개"는 과장 — 조립 단계에 행마다 userService.get(2차 캐시)·멤버·공지 조회 남음 |
| 성능 | notifier: 713ec09e414는 리소스 없는 presence 전부 폐기 → 32110e63e42에서 PC 세션 재전송 복구. 근태 개선 전은 공개 그룹별 최대 3건을 회사 전원에게 발송 |
| 성능 | 게시판·커뮤니티 슬로우 쿼리는 본인 커밋에서 못 찾음. 2023-08 c7aed5f0a9a 주석에 "변경 여부 확인 → 전체 조직도 호출" 구상 → 2024 캐시 전환의 근거 |


---

## AI 에이전트 (ai-home-poc) — 코드 워크스루

> 기준: `/Users/daou-8691/Documents/git/ai-home-poc` 현재 체크아웃(`develop`, HEAD `708e0cd9`, 2026-11-03). 라인 번호는 이 시점 기준이다.
> 근거 순서: 코드 → 커밋 메시지 → 당시 문서(`/Users/daou-8691/Documents/claude_md/ai-home-poc/done/`). 셋 다에서 확인 안 되면 "확인 필요".
> 개념·예상질문은 `study-ai-agent.md`에 있다. 이 문서는 "내 코드가 어디서 어떻게 불리는가"만 다룬다.

---

### 전체 코드 지도

```
app/
├─ startup/containers/infra.py        ★ create_checkpointer / build_checkpoint_store / _checkpoint_pool_factory
├─ infra/
│   ├─ checkpoint/                    ★ 전부 본인 (4809e574 신규)
│   │   ├─ buffered_saver.py            BufferedCheckpointSaver (InMemorySaver 래퍼)
│   │   ├─ snapshot_store.py            CheckpointRecord / PostgresCheckpointStore / RedisCheckpointStore
│   │   └─ settings.py                  backend 선택 (yml + env 우선)
│   └─ rdb/engine.py                  ★ pool_pre_ping=False, pool_recycle (b39a0bf0)
└─ modules/domain/ai_home/
    ├─ api/do_router.py                 POST /agent/v1/chat/stream  (진입점, dskim·외주 원형)
    ├─ services/do_agent_service.py     요청 오케스트레이션 (prepare TX → 락 → 런타임 스트림 → 결과 저장 → 락 해제)
    │                                   ★ _discard_run_checkpoint_buffer / _start_run_checkpoint_cleanup
    │                                   ★ 제목 사전판정 fast path / _summary_compaction_possible
    ├─ repositories/
    │   ├─ do_chat.py                   ★ INSERT ... RETURNING (43252a87). 락(acquire_lock)은 dskim 원형
    │   └─ sequences.py                 ★ AI_HOME_PK_SEQUENCE_NAMES 에서 6개 시퀀스 제외
    ├─ runtime/
    │   ├─ react_runtime.py             LangGraph 그래프 (8노드) — 줄 기여 1위가 본인
    │   │                               ★ durability="exit", _aflush_if_interrupted, afind_pending_interrupt,
    │   │                                 _execute_tool_step (같은 노드 재인터럽트 수정), _loop_budget_decision
    │   └─ loop_budget.py               ★ 루프 상한 설정 (fa1a1e6f)
    ├─ tools/
    │   ├─ executor.py                  도구 디스패치 (외주 원형, 결재 카드·비밀번호 재시도 분기는 ★)
    │   ├─ catalog.py                   도구 스펙·승인 판정 (원형 jueon/pbs, fail-closed 4줄 ★)
    │   ├─ mcp_client.py                MCP HTTP 클라이언트 (dskim·외주, 본인 2커밋)
    │   ├─ approval_document_card.py    ★ 100% 본인
    │   ├─ approval_bulk_result.py      ★ 100% 본인
    │   └─ secret_inputs.py             ★ 100% 본인 (간편 비밀번호 원문 격리)
    └─ messenger/                       ★ 63커밋 전부 본인 (메신저 대화 요약·조달)
scripts/gunicorn_conf.py              ★ timeout 150 / graceful_timeout 120
deploy/k8s/deployment.yaml            ★ terminationGracePeriodSeconds 150, preStop sleep 5
```

**요청 1건의 흐름 (신규 메시지)**

```
1) api/do_router.py:447  stream_chat()
      → EventSourceResponse(service.stream_chat(...))          # SSE 응답
2) services/do_agent_service.py:942  stream_chat()
      → :1058 _stream_chat_events()
         ├ content.interaction 있으면 → _stream_chat_interaction() (재개 경로, 아래 3번 참조)
         └ 없으면
            :1127 _prepare_chat_stream()   # TX1: get_or_create_thread → acquire_lock(DB 리스) → create_run ...
            :1240 self._runtime.astream(runtime_request)
3) runtime/react_runtime.py:884  astream()
      → :983 _astream_graph()  — 그래프를 별도 task 로 돌리고 asyncio.Queue 로 이벤트를 받아 yield
          :1026 self._graph.ainvoke(..., durability="exit")
              START → receive_input → load_thread_context → select_tools → prepare_model_input
                    → agent_model ⇄ tools (ReAct) → finalize → persist_result → END
              (tools 노드에서 승인/입력 필요 시 interrupt())
          :1033 "__interrupt__" in state → _aflush_if_interrupted() → "interrupted" 이벤트
                아니면 "done" 이벤트
4) do_agent_service.py
      "done"        → 결과 저장(TX5) → :1452 _start_run_checkpoint_cleanup → :1464 _release_chat_lock
      "interrupted" → :1311 afind_pending_interrupt → UI 컴포넌트 저장 → awaiting_user 표시
                      → :1332 _discard_run_checkpoint_buffer → :1333 _release_chat_lock → SSE done
```

**재개 요청(승인 버튼·폼 제출)**: 같은 `/agent/v1/chat/stream` 에 `content.interaction` 이 실려 온다 → `_stream_chat_interaction` → `:1775 afind_pending_interrupt`(여기서 prefetch) → 비밀번호 마스킹 → `:1838 astream_resume` → `Command(resume=...)` 로 그래프 재진입.

**체크포인트 키 구조 (모든 기여의 전제)** — `react_runtime.py:548-561`
```python
"configurable": {
    "thread_id": self.run_id,            # LangGraph thread = run(요청) 1개
    "ai_home_thread_id": self.thread_id, # 대화방 id 는 별도 키
    ...
}
```
대화 이력은 앱 테이블이 들고, 체크포인트는 "run 하나의 실행 중 상태"다. 재개는 interrupt 이후뿐이다.

---

### 1. 체크포인터 재설계 — 메모리 버퍼 + 인터럽트 때만 원격 저장  (2026-07-27 ~ 08-07 · 대표 `4809e574`, 머지 `b81178ca`)

**내가 한 범위**
- 본인: `app/infra/checkpoint/` 3파일 신규 전체, `infra.py` 조립부(`create_checkpointer`, `build_checkpoint_store`), 런타임 훅(`_aprefetch_run_checkpoint`, `_aflush_if_interrupted`, `afind_pending_interrupt` 의 prefetch, `adelete_run_checkpoints`/`apurge_run_checkpoints`/`adiscard_run_checkpoints`), 서비스 훅(`_discard_run_checkpoint_buffer`, `_start_run_checkpoint_cleanup` 재정의), `durability="exit"`, gunicorn/K8s 종료 예산.
- 남이 한 것: 그래프 8노드 원형·`interrupt()` HITL 원형(외주/dskim), "run 종료 시 체크포인트 삭제" 훅 원형(dskim `fa4f3bea`, 07-23), DB 리스 thread 락 `acquire_lock`(dskim 06-16), 체크포인터 풀 `autocommit`·`prepare_threshold=None` 설정(JaypTook `045d2f5e`, 07-02).

**코드 지도**
| 파일 | 클래스/함수 | 역할 |
|---|---|---|
| `app/infra/checkpoint/buffered_saver.py` | `BufferedCheckpointSaver` | `BaseCheckpointSaver` 상속, 내부에 `InMemorySaver` 하나. 장부 6개로 상태 판단 |
| 〃 | `aget_tuple` / `alist` / `aput` / `aput_writes` | LangGraph가 부르는 표준 API. 메모리 우선, `_read_through` thread만 원격 폴백 |
| 〃 | `aflush_thread` | 인터럽트 run의 메모리 체크포인트를 `alist`로 읽어 원격에 씀 |
| 〃 | `aprefetch_thread` | 재개 진입점 전용. Redis는 레코드 복원, PG는 read-through 표시만 |
| 〃 | `discard_thread` / `adelete_run_thread` / `adelete_thread` | 메모리만 파기 / 원격에 쓴 적 있을 때만 삭제 / 무조건 삭제 |
| 〃 | `sweep_stale_buffers`, `_sweep_forever` | 고아 버퍼 TTL 회수(300초 주기, 1800초 방치) |
| 〃 | `with_allowlist` | msgpack allowlist를 내부 세이버·저장소까지 적용 |
| `app/infra/checkpoint/snapshot_store.py` | `CheckpointRecord` | 체크포인트 1개 재기록에 필요한 것(put_config/writes_config/checkpoint/metadata/pending_writes) |
| 〃 | `areplay_record` | 레코드를 어떤 세이버에든 `aput`+`aput_writes`로 다시 씀 |
| 〃 | `PostgresCheckpointStore` | `AsyncPostgresSaver`로 기존 3테이블에 append(워터마크 이후만) |
| 〃 | `RedisCheckpointStore` | 레코드 목록 전체를 직렬화 → `aihome:cp:{run_id}` 키 1개 + TTL |
| `app/infra/checkpoint/settings.py` | `resolve_checkpoint_settings` | yml `ai_home.checkpoint` + env 우선 |
| `app/startup/containers/infra.py` | `create_checkpointer`(255) | 세이버 조립 → 스위퍼 시작 → `awarmup()`(실패해도 degraded 기동) |
| `react_runtime.py` | `_aflush_if_interrupted`(857) | `__interrupt__` 있으면 flush, False면 RuntimeError |
| 〃 | `afind_pending_interrupt`(761) | prefetch 먼저 → `aget_state` → `interrupts[0]` |
| 〃 | `adelete_run_checkpoints`(789) / `apurge_run_checkpoints`(808) / `adiscard_run_checkpoints`(824) | 터미널 회수 / 대화 삭제 API용 / 메모리만 |
| `do_agent_service.py` | `_start_run_checkpoint_cleanup`(5097) | 터미널 run: 백그라운드 태스크로 회수 |
| 〃 | `_discard_run_checkpoint_buffer`(5118) | awaiting_user run: 락 풀기 전 동기로 메모리만 파기 |

**흐름**

A. 일반 run (인터럽트 없음) — 저장소 접근 0
1) `_astream_graph` → `graph.ainvoke(durability="exit")` → 그래프 종료 시 LangGraph가 `BufferedCheckpointSaver.aput`/`aput_writes` 호출 → `InMemorySaver`에만 씀, `_threads`·`_touched_at` 갱신
2) `"done"` → 서비스 `_start_run_checkpoint_cleanup` → 백그라운드 `_delete_run_checkpoints_best_effort` → `runtime.adelete_run_checkpoints` → `saver.adelete_run_thread`
3) `_remote_state` 에 없음 → `_forget_locally` 만 하고 끝 (원격 DELETE 없음)

B. 인터럽트 run
1) tools 노드에서 `interrupt()` → `ainvoke` 가 `__interrupt__` 를 담아 반환 (exit 이므로 이 순간 체크포인트가 메모리에 기록)
2) `react_runtime._run_graph`(1033) → `_aflush_if_interrupted` → `saver.aflush_thread(run_id)` → `_acollect_records`(alist 역순) → `store.aflush(records, already_flushed=_flushed[...])` → `_remote_state.add`
3) flush 성공한 뒤에만 `"interrupted"` 이벤트를 큐에 넣음
4) 서비스 `:1311 afind_pending_interrupt`(메모리에 있으므로 원격 안 탐) → UI 컴포넌트 저장 → `_mark_chat_awaiting_user`
5) `:1332 _discard_run_checkpoint_buffer` → `saver.discard_thread` (메모리만 비움, `_remote_state`는 유지) → `:1333 _release_chat_lock`

C. 재개 (임의 파드)
1) 서비스 `_stream_chat_interaction` `:1775 afind_pending_interrupt` → `_aprefetch_run_checkpoint` → `saver.aprefetch_thread`
   - PG: `aload_records` 가 None → `_read_through.add` (실제 SELECT 는 다음 `aget_tuple` 때 1회)
   - Redis: GET → `areplay_record` 로 `InMemorySaver` 에 재생 → `_flushed[...] = len(records)`
2) `aget_state` → `saver.aget_tuple` → 메모리 미스 + `_read_through` → `PostgresCheckpointStore.aget_tuple`(AsyncPostgresSaver 위임)
3) `astream_resume` → `Command(resume=...)` 로 그래프 재진입 → 끝나면 A-2 경로. 이번엔 `_remote_state` 에 있으므로 원격 DELETE 실행
4) 재개 중 또 인터럽트되면 B-2 를 다시 타고, PG 는 워터마크 이후만 append

**핵심 코드**

```python
# app/infra/checkpoint/buffered_saver.py:362-372
async def aget_tuple(self, config: RunnableConfig) -> CheckpointTuple | None:
    # 원격 조회를 여기서 먼저 하지 않는다 — 신규 run 까지 원격을 타면 "접근 0"이 깨진다
    thread_id = self._thread_id_of(config)
    if thread_id is not None and thread_id in self._threads:
        self._touch(thread_id)                       # 스위퍼용 마지막 접근 시각
    found = await self._inner.aget_tuple(config)     # 1순위: InMemorySaver
    if found is not None or thread_id is None or thread_id not in self._read_through:
        return found                                 # 일반 run 은 여기서 끝 (미스여도 None)
    # 재개 경로(prefetch 가 표시한 thread)에서 메모리에 없을 때만 원격으로 넘어간다
    self._touch(thread_id)
    return await self._required_store().aget_tuple(config)
```

```python
# app/infra/checkpoint/buffered_saver.py:315-347
async def aflush_thread(self, thread_id: str) -> bool:
    key_id = str(thread_id).strip()
    ...
    if key_id not in self._threads:                  # 메모리에 이 run 이 없음 → 재개 불가 상태
        logger.warning(...); return False
    records = await self._acollect_records(key_id)   # self._inner.alist() 를 뒤집어 오래된 것부터
    if not records:
        logger.warning(...); return False
    store = self._required_store()
    self._guard_checkpoint_count(key_id, records)    # max_checkpoint_count(200) 초과 시 예외
    self._flushed[key_id] = await store.aflush(      # 반환값 = 새 워터마크(보낸 개수)
        key_id, records,
        already_flushed=self._flushed.get(key_id, 0),# PG 는 이 뒤쪽만 쓴다
        ttl_seconds=self._ttl_seconds,               # Redis 만 사용
    )
    self._remote_state.add(key_id)                   # "원격에 남겼다" → 나중에 삭제 대상
    self._touch(key_id)
    return True
```

```python
# app/modules/domain/ai_home/runtime/react_runtime.py:1023-1040  (_astream_graph 내부)
async def _run_graph() -> None:
    token = _STREAM_SINK.set(_put_event)
    try:
        state = await self._graph.ainvoke(
            graph_input, config=graph_config,
            durability=AI_HOME_RUNTIME_CHECKPOINT_DURABILITY,   # "exit" (366행)
        )
        if "__interrupt__" in state:
            # 재개 상태를 원격에 확정한 뒤에만 인터럽트를 알린다
            await self._aflush_if_interrupted(state, graph_config)
            await _queue_put(AiHomeRuntimeStreamEvent(kind="interrupted", state=state))
        else:
            await _queue_put(AiHomeRuntimeStreamEvent(kind="done", state=state))
    except BaseException as exc:
        await _queue_put(exc)                         # flush 실패도 여기로 → run 실패
```

```python
# app/infra/checkpoint/buffered_saver.py:437-458
async def adelete_run_thread(self, thread_id: str) -> bool:
    key_id = str(thread_id).strip()
    if key_id not in self._remote_state or self._store is None:
        self._forget_locally(key_id)   # 원격에 쓴 적 없음 → 메모리만 비우고 DELETE 안 함
        return False
    await self.adelete_thread(key_id)  # 메모리 파기 + store.adelete(3테이블 DELETE 또는 Redis DEL)
    return True
```

```python
# app/infra/checkpoint/snapshot_store.py:363-385  (PostgresCheckpointStore)
async def aflush(self, run_id, records, *, already_flushed, ttl_seconds) -> int:
    pending = list(records)[already_flushed:]   # append 방식: 이미 보낸 앞쪽은 건너뜀
    if not pending:
        return already_flushed
    saver = await self._asaver()                # 기동 워밍업 실패했으면 여기서 다시 open + setup
    for record in pending:
        await areplay_record(saver, record)     # AsyncPostgresSaver.aput + aput_writes (native 형식)
    return len(records)
```

```python
# app/infra/checkpoint/snapshot_store.py:90-99  (CheckpointRecord.new_versions)
@property
def new_versions(self) -> dict[str, Any]:
    # aput 의 new_versions 는 "이번에 바뀐 채널"인데 읽기 API 로 복원 불가 → 누적 channel_versions 사용.
    # 비우면 aput 이 blob 을 안 써서 messages 채널이 통째로 유실된다.
    return dict(self["checkpoint"].get("channel_versions") or {})
```

**데이터·설정**
- PG 테이블: 기존 `checkpoints` / `checkpoint_blobs` / `checkpoint_writes` (LangGraph 기본 스키마, 신규 테이블 없음)
- Redis 키: `aihome:cp:{run_id}`, 값 `"{payload_type}:{base64}"` (운영 Redis 클라이언트가 `decode_responses=True` 라 base64로 감쌈), `SET ... ex=redis_ttl_seconds`
- yml `ai_home.checkpoint` (dev/stg/prod 동일): `backend: "pg"`, `redis_ttl_seconds: 86400`, `max_checkpoint_count: 200`, `max_payload_bytes: 67108864`(64 MiB, redis만), `buffer_ttl_seconds: 1800`, `sweep_interval_seconds: 300`
- env 우선: `AI_HOME_CHECKPOINT_BACKEND`(pg|redis, `postgres`/`postgresql` 별칭 허용, 오타면 yml 값으로 폴백), `AI_HOME_CHECKPOINT_REDIS_TTL_SECONDS`
- 체크포인터 psycopg 풀(`infra.py:146-161`): `min_size=0, max_size=2, timeout=10, max_lifetime=1800, max_idle=300, autocommit=True, prepare_threshold=None`
- durability: `react_runtime.py:366` `AI_HOME_RUNTIME_CHECKPOINT_DURABILITY: Durability = "exit"`, `ainvoke`/`ainvoke_resume`/`_run_graph` 세 곳에서 넘김
- 보안: `LANGGRAPH_STRICT_MSGPACK`(Deployment env), 기동 로그 `strict_msgpack=on|off|unknown` (`_log_checkpoint_serde_mode`, `e3e4a43d`)
- 종료 예산: `scripts/gunicorn_conf.py:103-106` `max_requests=20000, max_requests_jitter=5000, timeout=150, graceful_timeout=120` / `deploy/k8s/deployment.yaml:42` `terminationGracePeriodSeconds: 150`, `:162` preStop `sleep 5`

**왜 이렇게 짰나**
- 출발점: thread_id = run_id 라 체크포인트는 HITL 재개에만 쓰인다. 그런데 매 run이 `SELECT 1 + UPSERT 3계열 + DELETE 3` 을 냈다(`4809e574` 본문). "쓰자마자 지우는" 패턴이 07-31 부하에서 PG를 무너뜨린 원인 구조.
- 버린 대안(설계 문서 §3): ① 체크포인터 풀 autocommit 끄기 — 세이버가 프로세스당 1개에 인스턴스 락이라 run별 TX 경계가 없음 ② 종료 시 삭제만 끄기 — INSERT는 그대로, 테이블 무한 증가 ③ `langgraph-checkpoint-redis` — RediSearch/RedisJSON 모듈 필요. 결론: 쓰는 양 자체를 없앤다.
- op 로그를 따로 두지 않음: 상태 사본이 2개가 되면 메모리 2배·정합성 문제. 인터럽트 순간 `alist` 로 읽으면 충분(`buffered_saver.py:16-19`).
- `InMemorySaver` 내부(storage/blobs/writes)를 안 건드림: 라이브러리 업그레이드 대비. 공개 API만(`buffered_saver.py:16`).
- 지연 초기화 → 기동 워밍업: 인터럽트가 run의 약 1/3이라 "인터럽트 없는 파드" 전제가 성립 안 함. 다만 07-31에 `cp.setup()` 실패가 lifespan 예외로 파드를 죽였기 때문에 실패해도 degraded 기동(`infra.py:283-292`).
- flush 실패 = run 실패: 저장 못 한 채 "인터럽트됨"을 알리면 그 run은 영영 재개 불가.
- awaiting_user 메모리 파기 위치: flush 직후는 안 됨(같은 요청 안에서 `afind_pending_interrupt` 가 다시 읽음), 백그라운드도 안 됨(재개 요청과 경쟁). 그래서 락 풀기 직전 동기(`61d28422`).
- 바이트 상한은 Redis만: PG에서 재려면 serde를 미리 돌려야 하고 그 사본이 곧 18.5 MiB급 메모리 회귀(`snapshot_store.py:241-245`).
- `_remote_state` 는 `_forget_locally` 로 안 지움: 인터럽트 직후 메모리를 비워도 원격엔 남아 있으므로, 같이 잊으면 재개 완료 후 PG 행이 영구 잔존(`buffered_saver.py:95-100`).
- 대화 삭제 API는 아무 파드에서나 돌아 장부가 비어 있는 게 정상 → 무조건 지우는 `apurge_run_checkpoints` 로 분리(`1deac2e8`).
- durability `exit`: 기본 `async` 는 superstep마다 기록 → ReAct 스텝 수만큼 write. interrupt도 exit에 포함되므로 HITL 유지(`react_runtime.py:361-366` 주석).
- graceful: `timeout > graceful_timeout` 인 이유 — UvicornWorker가 max_requests 드레인 중 heartbeat가 멈춰 실제 한도가 timeout이 되고, 초과 시 arbiter SIGABRT로 열린 SSE가 전멸(`gunicorn_conf.py:88-92`). `graceful_timeout < TGPS - preStop` 이어야 유효.

**바뀌어 온 이력**
1. `2ccc308e` (07-27) `durability="exit"` 도입. 커밋 메시지는 `[20260727]` 뿐, 근거는 코드 주석.
2. `4f410bb7` (07-29) 종료 예산: TGPS 30→150, `--graceful-timeout` 45→120, `--timeout` 60→150, `--max-requests` 4000→20000 (당시엔 `scripts/entrypoint.sh` CLI 인자)
3. `bf3efc8b` (07-31) 체크포인터 풀 min 1→0, max 3→2 (2번 기여와 공유)
4. `7fdf2801` (07-31) 첫 구현 "메모리 버퍼 + Redis 스냅샷". **develop에는 없다**(`refs/backup/pre-rebase-*` 에만 있음). 같은 브랜치에서 저장소 인터페이스로 빼고 PG 기본으로 재작성되어 아래 커밋으로 대체.
5. `3f0a691a` (08-04) 파드 간 재개 버그 수정: prefetch가 서비스 pre-check(`afind_pending_interrupt`)보다 뒤에 있어 처음 보는 파드에서 "no pending interrupt". → `afind_pending_interrupt` 가 먼저 prefetch. (리베이스 전 해시 `78b5d5a6`)
6. `6987c415` (08-04) gunicorn CLI 인자를 `gunicorn_conf.py` 로 흡수
7. `4809e574` (08-05) 메모리 버퍼 + 원격 저장소 추상화(PG 기본/Redis), 기동 워밍업, 스위퍼
8. `61d28422` (08-05) awaiting_user 메모리 즉시 파기, Redis `max_payload_bytes` 64 MiB 부활
9. `b81178ca` (08-07) develop 머지 (`feature/redis-buffered-checkpointer`)
10. `1deac2e8` (08-07) 빈 DELETE 제거(`_remote_state`, `apurge_run_checkpoints` 분리) + `with_allowlist` 오버라이드
11. `e3e4a43d` (10-12) strict msgpack 기동 로그
12. `d84719b1` (10-08, 머지 `df535f83` 10-12) flush 결과 False면 run 실패 추가 — 4-A 참조
13. `90eed503` (10-29) 자동화 drain을 SIGTERM 시점에 시작 (gunicorn_conf 주석에 120초 분해식 추가)

**면접 30초 설명**
"LangGraph 체크포인트 키가 run_id라서 체크포인트는 승인 대기 후 재개할 때만 쓰이는데, 매 요청이 PG 3테이블에 쓰고 끝나면 지우고 있었습니다. 그래서 `InMemorySaver`를 감싼 `BufferedCheckpointSaver`를 만들어 평소엔 메모리에만 쓰고, 그래프가 `__interrupt__`로 멈췄을 때만 `_aflush_if_interrupted`가 `aflush_thread`를 불러 그 run의 체크포인트를 PG에 다시 씁니다. 재개 요청은 어느 파드로 가든 `afind_pending_interrupt`가 먼저 `aprefetch_thread`로 read-through 표시를 해서 PG에서 읽습니다. 원격 저장소는 인터페이스로 빼서 Redis 구현도 있지만 운영은 PG이고, env 하나로 바꿀 수 있습니다. 결과적으로 인터럽트 없는 run은 체크포인트 DB 접근이 0이 됐습니다."

**헷갈리기 쉬운 점**
- "인터럽트 시 PG flush"는 **그래프가 끝난 뒤 런타임이** 한다. LangGraph의 `aput` 이 PG로 가는 게 아니다. `aput` 은 언제나 메모리.
- PG 재개 경로에서 prefetch는 **SELECT를 하지 않는다**. 표시(`_read_through`)만 하고 실제 SELECT는 `aget_tuple` 위임 때 1회. Redis는 prefetch에서 GET 1회 + 메모리 재생.
- `_flushed` 워터마크는 **PG(append)에서만 의미**. Redis는 매번 전체를 다시 SET.
- `adelete_thread`(무조건) vs `adelete_run_thread`(장부 보고) vs `discard_thread`(메모리만) — 세 개를 구분해서 말할 것.
- "요청당 0"은 **인터럽트 없는 run 기준**. 4809e574 직후에도 빈 DELETE 3건이 남아 있었고 1deac2e8에서 0이 됨.
- 체크포인터 풀 `autocommit=True` 는 지금도 그대로다(인터럽트 flush 경로만 쓰므로 둠).
- graceful 수치 원본: 120/150은 07-29 `entrypoint.sh` 에서 시작, 지금은 `gunicorn_conf.py`. "graceful_timeout 45→120"이 정확(30은 TGPS 이전 값).
- Redis 구현은 **dev에서도 기본은 pg**다(yml 3개 모두 `"pg"`). Redis 경로는 단위 테스트(`probe` fixture로 pg/redis 양쪽)로 검증. 실제 환경에서 redis로 돌린 기록은 확인 필요.
- 7fdf2801(Redis 스냅샷 첫 버전)은 develop 히스토리에 없다. 면접에서 해시를 말할 일은 없겠지만 "처음엔 Redis로 설계했다가 같은 브랜치에서 PG 기본으로 바꿨다"가 정확.

---

### 2. 요청당 DB 왕복 감축 — SQL 37→23, 커넥션 8→5  (2026-07-31 ~ 08-06 · `bf3efc8b`, `43252a87`, 머지 `add1b0c4`)

**내가 한 범위**
- 본인: 커넥션 예산 축소(`bf3efc8b`), nextval 제거 + RETURNING(`43252a87`), 제목 사전판정 TX 제거(`063a0865`)와 그 정정(`25f56c0f`), 요약 백그라운드 TX 조건부(`5dd47a76`), `pool_pre_ping` 제거(`b39a0bf0`). SQL 전수 인벤토리 문서(`2026-08-06-chatstream-요청당-SQL-문장-인벤토리-및-감축안.md`).
- 남이 한 것: 리포지토리 원형(`do_chat.py`, dskim/pbs), `ai_thread_run_context_item_seq` 제외(07-30, 작성자 확인 필요), thread 락(dskim).

**코드 지도**
| 파일 | 클래스/함수 | 역할 |
|---|---|---|
| `repositories/sequences.py` | `AI_HOME_PK_SEQUENCE_NAMES`, `next_sequence_id` | 앱이 nextval 뽑아도 되는 시퀀스 화이트리스트. 빠진 6개는 뽑으려 하면 RuntimeError |
| `repositories/do_chat.py` | `get_or_create_thread`(565), `create_context_message`(604), `create_run`(630) | `insert(...).returning(table)` 로 id+행을 한 번에 |
| `services/do_agent_service.py` | `_generate_thread_title_for_stream` 내 fast path(5044) | prepare가 읽은 `thread_title_snapshot` 이 "제목 있음"이면 TX 생략 |
| 〃 | `_summary_compaction_possible`(5204), `_update_thread_summary_background`(5221) | 압축이 걸릴 수 없으면 요약 TX 자체를 안 엶 |
| 〃 | `PreparedDoChatStream.thread_title_snapshot`(408), `.uncovered_turn_count`(412) | prepare TX에서 읽은 값을 뒤 단계로 운반 |
| `app/infra/rdb/engine.py` | 엔진 생성(62-73) | `pool_pre_ping=False`, `pool_recycle=1800` |
| `app/startup/containers/infra.py` | `_checkpoint_pool_factory`(131) | 체크포인터 풀 min 0 / max 2 |

**흐름 (요청 1건의 TX 지도 — 인벤토리 문서 §2 기준, 신규 방)**
1) TX1 prepare `_prepare_chat_stream` → `get_or_create_thread`(INSERT…RETURNING) → `acquire_lock` → `create_context_message`/`create_run`(RETURNING) … 17→11문장
2) TX2 제목 사전판정 → 신규 방은 그대로 1, 기존 방(제목 있음)은 **TX 소멸**
3) TX3 usage 로그(LLM 호출마다) 2→1
4) TX4 제목 반영 5→4 (미제목일 때만)
5) TX5 정답 확정 `_persist_chat_success` 8→5
6) TX7 락 해제 1
7) TX8 요약 백그라운드 3→0 (압축 불가 시 UoW 안 엶)
- 합계: 신규 방 37문장/7TX → 23/6, 기존 방 31/6 → 19/4. LLM 스트림 구간엔 DB 커넥션을 잡지 않는 구조(TX1 UoW가 `_finish_prepare_chat_stream` 전에 닫힘)는 원래부터였고 유지.

**핵심 코드**

```python
# app/modules/domain/ai_home/repositories/do_chat.py:575-595  (get_or_create_thread)
result = await self._session.execute(select(threads).where(threads.c.chat_room_uuid == chat_room_uuid))
row = result.mappings().one_or_none()
if row is None:
    # 전: thread_id = await self.next_id("ai_thread_seq")  → INSERT(id=thread_id) → flush → SELECT WHERE id
    #     = 왕복 3회
    # 후: id 는 컬럼 DEFAULT nextval 이 채우고 RETURNING 으로 행 전체를 받음 = 왕복 1회
    result = await self._session.execute(
        insert(threads)
        .values(chat_room_uuid=chat_room_uuid, company_uuid=company_uuid, user_id=user_id,
                agent_id=agent_id, chat_mode=chat_mode, status="ACTIVE",
                created_at=now, updated_at=now)          # id 를 넘기지 않음
        .returning(threads)
    )
    row = result.mappings().one()
return dict(row)                                          # 반환 모양은 전과 동일 → 호출부 무변경
```

```python
# app/modules/domain/ai_home/repositories/sequences.py:7-42
AI_HOME_PK_SEQUENCE_NAMES = frozenset({ "ai_agent_seq", ..., "ai_thread_generated_file_seq" })
# ai_thread_seq / ai_thread_context_message_seq / ai_thread_run_seq / ai_thread_turn_seq /
# ai_llm_call_log_seq / ai_tool_call_log_seq 는 의도적으로 빠져 있다 (2026-08-06)
async def next_sequence_id(session, sequence_name):
    if sequence_name not in AI_HOME_PK_SEQUENCE_NAMES:      # 회귀 가드: 다시 nextval 뽑으려 하면 즉시 실패
        raise RuntimeError(f"AI Home DO contract sequence is not allowed: {sequence_name}")
    result = await session.execute(text(f"SELECT nextval('public.\"{sequence_name}\"'::regclass)"))
    return int(result.scalar_one())
```

```python
# app/modules/domain/ai_home/services/do_agent_service.py:5204-5224
@staticmethod
def _summary_compaction_possible(uncovered_turn_count_at_prepare: int | None) -> bool:
    if uncovered_turn_count_at_prepare is None:   # 모르면(재개 경로) 기존대로 DB 확인
        return True
    # 백그라운드 시점 미압축 턴 = prepare 시점 + 이번 턴 1개. 10 미만이면 압축 계획이 반드시 없음
    return uncovered_turn_count_at_prepare + 1 >= _RECENT_RAW_TURN_LIMIT   # 10

async def _update_thread_summary_background(self, *, prepared):
    if not self._summary_compaction_possible(prepared.uncovered_turn_count):
        return                                    # UoW(=커넥션 체크아웃·3문장) 자체를 안 엶
    uow = await self._new_uow()
```

```python
# app/modules/domain/ai_home/services/do_agent_service.py:5044-5049  (제목 사전판정)
if not self._is_untitled_thread_title(prepared.thread_title_snapshot):
    return None        # 스냅샷이 "제목 있음"이면 DB 도 반드시 제목 있음(단조) → 조회 생략
uow = await self._new_uow()   # 스냅샷이 "미제목"이면 낡았을 수 있으므로 기존대로 DB 확인
async with uow:
    repo = DoChatRepository(uow.get_session())
    if not await self._should_generate_thread_title(repo=repo, prepared=prepared):
        return None
```

**데이터·설정**
- 테이블(PK가 DEFAULT nextval로 바뀐 대상): `ai_thread`, `ai_thread_context_message`, `ai_thread_run`, `ai_thread_turn`, `ai_llm_call_log`, `ai_tool_call_log` (+07-30 `ai_thread_run_context_item`). DDL 근거 `alembic/versions/init.sql` 의 `id bigint DEFAULT nextval(...)`.
- 엔진 풀(yml `database`, dev/stg/prod): `pool_size: 3`, `max_overflow: 0`, `pool_recycle: 1800`, 코드에서 `pool_pre_ping=False` 고정
- 체크포인터 풀: `min_size=0`, `max_size=2`
- 커넥션 산식: 워커당 (엔진 5 + 체크포인터 3) = 8 → (3 + 2) = 5. 워커 2 × 파드 100 기준 상한 1,600 → 1,000 (`bf3efc8b` 본문)

**왜 이렇게 짰나**
- 커넥션: 4개 서비스 상한 합 약 2,950이 PG `max_connections` 초과. 엔진 커넥션은 짧은 쿼리 블록에서만 잡히고(LLM 스트림 동안 미점유) 실측 필요 동시성 0.3 수준이라 3도 10배 여유. 체크포인터는 `AsyncPostgresSaver` 가 인스턴스 `asyncio.Lock` 으로 직렬화해 동시 사용이 구조적으로 1개(`infra.py:132-145` docstring).
- `min_size=0`: 프로세스 200개 × 상주 1 = 200 커넥션을 놀리게 됨.
- nextval/RETURNING: "DB가 어차피 채울 값을 앱이 미리 물어보는" 왕복. 반환 dict 모양이 같아 호출부 무변경.
- 제목 판정: 처음엔 "thread 락이 막으니 값이 같다"고 전제했는데 prepare가 **락 잡기 전에** thread를 읽어서 틀림 → 단조성(제목은 비었다가 채워질 뿐 되돌아가지 않음)을 이용해 "제목 있음" 방향만 생략(`25f56c0f`). 단조성 전제는 "title_snapshot writer가 하나뿐"을 검사하는 테스트로 고정.
- 요약 TX: 로컬 PG 12턴 실측 36문장/12TX → 9문장/3TX, 첫 압축 필요 시점(10턴)과 첫 조회 시점 일치(`5dd47a76`).
- pre_ping: asyncpg 다이얼렉트가 ping을 BEGIN→빈 쿼리→ROLLBACK으로 감싸 rollback 비율이 구조적으로 ~50%. 끄고 `pool_recycle` 1800(같은 네임스페이스 Java HikariCP maxLifetime 실측 근거). 로컬 48.8% → 1.9%. "더 낮추지 말 것": 재접속이 UoW당 +17.4ms.

**바뀌어 온 이력**
1. `bf3efc8b` (07-31) 커넥션 8→5
2. `43252a87` (08-06) nextval 6개 시퀀스 제거 + RETURNING (prepare 17→11, 정답 확정 8→5, usage 2→1)
3. `063a0865` (08-06) 제목 사전판정 TX 제거 — 전제 오류
4. `25f56c0f` (08-06) "제목 있음" 방향으로만 생략하도록 정정
5. `5dd47a76` (08-06) 요약 백그라운드 조건부
6. `b39a0bf0` (08-06) pool_pre_ping 제거, recycle 3600→1800
7. `add1b0c4` (08-06) develop 머지 (`feature/chat-stream-sql-roundtrip-reduction`)

**면접 30초 설명**
"chat/stream 1건이 내는 SQL을 트랜잭션별로 전부 표로 만들었더니 신규 방 37문장·7트랜잭션이었습니다. PK마다 `SELECT nextval` 을 따로 뽑고, INSERT 후 다시 SELECT로 되읽는 관용구가 반복돼서, 컬럼 DEFAULT nextval에 맡기고 `insert().returning()` 으로 바꿨습니다. `sequences.py` 화이트리스트에서 그 시퀀스를 빼서 누가 다시 뽑으면 바로 실패하게 막았고요. 그리고 prepare에서 이미 읽은 값(`thread_title_snapshot`, `uncovered_turn_count`)을 뒤로 실어 날라 쓸데없는 트랜잭션을 열지 않게 해서 23문장·6트랜잭션이 됐습니다. 커넥션은 엔진 5→3, 체크포인터 3→2로 워커당 8에서 5로 줄였습니다."

**헷갈리기 쉬운 점**
- 37→23은 **신규 방** 기준. 기존 방은 31→19. "요청당"이라고만 말하면 어느 쪽인지 물을 수 있음.
- 37→23은 리포지토리 호출을 실제 순서로 **재생해 센** 값(문서 §7). 운영 계측이 아님.
- 제목 판정 절감은 **신규 방(부하테스트)에선 안 나타난다**. 기존 방 운영 트래픽에서만.
- 커넥션 8→5는 **상한(풀 크기)** 이야기다. 실제 동시 사용 수 측정과 혼동하지 말 것.
- `pool_pre_ping` 제거는 감축 머지(`add1b0c4`)와 같은 날이지만 별도 커밋(`b39a0bf0`)이다.
- 체크포인터 쪽 "요청당 7건 → 0"(1번)과 앱 테이블 "37 → 23"(2번)은 다른 숫자다. 섞지 말 것.

---

### 3. MCP 도구 연동 — 전자결재 카드·간편결재 재시도, 메신저 조달  (2026-08-18 ~ 10-26 · `cb280664`, `18a36066`, `d60a5a53` 등)

**내가 한 범위**
- 본인
  - 전자결재: 결재 문서 카드 변환기 `approval_document_card.py`(100%), 카드 버튼 → 결재 도구 승인 폼 위임(`cb280664`), 간편 비밀번호 원문 격리 `secret_inputs.py`(100%), 비밀번호 불일치 시 재시도 폼(`18a36066`), 일괄 결재 비밀번호·재시도(`fd9781d6`), 일괄 부분 성공 결과 카드 `approval_bulk_result.py`(`4349882e`), 승인 판정 fail-closed(`86192291`, catalog 4줄)
  - 메신저: `messenger/` 패키지 전체(63커밋 전부 본인) — 대화 요약 조달·조립, 이후 MCP 툴(`get_chat_room_messages_bulk` 등)로 조달 전환
- 남이 한 것: MCP HTTP 클라이언트 `mcp_client.py`(dskim·외주), `run_tool`/`get_tool_schema` 메타 도구와 승인 폼 원형(외주 pbs·jueon), `_mcp_schema_requires_approval` 원형(jueon `8f45e017`, 08-19), MCP 서버 자체(dop-ai-mcp, 다른 팀원)

**코드 지도**
| 파일 | 클래스/함수 | 역할 |
|---|---|---|
| `tools/executor.py` | 디스패치(1442-1524) | 도구 이름으로 분기. `SHOW_APPROVAL_DOCUMENT_CARD_TOOL_NAME`, `MESSENGER_FETCH_TOOL_NAME`, 메신저 MCP 2종, 나머지 다이나믹 MCP |
| 〃 | `_execute_show_approval_document_card`(3778) | 상세 응답 → 카드. 재개면 `_approval_card_run_tool` 로 위임 |
| 〃 | `_is_approval_card_resume`(3984) | 이 tool_call의 카드 버튼 클릭/폼 제출 재개인지 판정(componentId 해시 대조) |
| 〃 | `_approval_card_run_tool`(4102) | 버튼 → 해당 결재 도구의 `_run_tool` 승인 단계. 인자·폼 문구를 서버가 조립 |
| 〃 | `_approval_doc_tool_to_card`(4177) | 모델이 결재 처리 도구를 직접 부르면 카드 경로로 돌림 |
| 〃 | `_run_tool` 내 비밀번호 재시도(2763-2795) | MCP 400 + 간편 비밀번호 문구면 새 승인 폼 반환(3회까지) |
| 〃 | `_password_retry_attempt`(5249), `_mcp_password_retry_form_observation`(5259) | 회차 읽기, 비밀번호만 비운 재시도 폼 생성 |
| `tools/approval_document_card.py` | `build_approval_document_card`(165), `approval_document_card_component_id`(129), `approval_action_arguments`(151), `approval_action_presentation`(134) | 순수 함수. LLM이 카드 내용을 쓰지 않음 |
| `tools/secret_inputs.py` | `mask_password_interaction_value`, `activate_secret_inputs`, `with_secret_inputs` | 원문은 ContextVar에만, 그래프·DB엔 `********` |
| `tools/catalog.py` | `_mcp_schema_requires_approval`(2327), `MCP_PASSWORD_MAX_ATTEMPTS = 3`(253) | 승인 대상 판정 |
| `runtime/react_runtime.py` | `_await_tool_interaction`(4337) | interrupt 페이로드 생성, 재개값 → `mcp_action_approval` 컨텍스트(비밀번호 회차 등 운반) |
| `messenger/summary_runner.py` | `MessengerSummaryRunner.run_with_mcp`(535), `search_with_mcp`(390) | MCP 1왕복으로 방 정보+원문 조달 → 경계·예산·익명 라벨·인용 조립 |
| `messenger/mcp_source.py` | `parse_messenger_fetch_payload`(140), 툴 이름 상수(200-209) | MCP 응답 → 내부 모델 파서. I/O 없음 |
| `services/do_agent_service.py` | `_stream_chat_interaction` 내(1775-1790) | 재개 시 비밀번호 마스킹 → 원문 보관소 활성화 |

**흐름**

A. 결재 카드 → 버튼 → 승인 폼 → 실행
1) 모델이 `get_approval_doc_detail`(MCP) 후 `show_approval_document_card` 호출 → `executor._execute_show_approval_document_card` → `build_approval_document_card(detail, component_id=sha256(run_id\0tool_call_id))` → `ui_component` 관측치 → 런타임이 interrupt (카드에 actions 가 있을 때)
2) 사용자가 [승인] 클릭 → `/chat/stream` + interaction → `afind_pending_interrupt` → `astream_resume` → 같은 tools 노드 재실행, `runtime_context.ui_component_interaction` 세팅
3) 같은 tool_call_id로 `_execute_show_approval_document_card` 재진입 → `_is_approval_card_resume` True → `_approval_card_run_tool` → 결재 도구 스키마 조회 → `approval_action_arguments`(docId·버전값) + `approval_action_presentation`(서버 고정 문구) → `_run_tool(approval_card_delegated=True)` → 승인 폼(`human_approval_required`) 반환 → 다시 interrupt
4) 폼 제출(간편 비밀번호 포함) → 서비스 `mask_password_interaction_value` 로 원문 분리 → `activate_secret_inputs` → 재개 → `_await_tool_interaction` 이 `mcp_action_approval` 생성 → 같은 tool_call_id → `_run_tool` 이 MCP 호출 직전 `with_secret_inputs` 로 원문 합침
5) MCP가 400 + 간편 비밀번호 거절 → `_is_simple_code_rejection` → 회차 < 3 이면 `_mcp_password_retry_form_observation`(다른 칸은 직전 값, 비밀번호만 빈칸, 회차별 새 componentId) → 다시 interrupt. 3회째면 일반 실패 카드.

B. 메신저 요약(MCP 조달)
1) 모델/나노 선택이 `messenger_fetch` 또는 MCP 이름 `get_chat_room_messages_bulk` 호출 → executor 디스패치(1497-1515: MCP 이름이어도 다이나믹 MCP 경로로 보내지 않음)
2) `_messenger_fetch`(1720) → `MessengerSummaryPlan` → `runner.run_with_mcp(plan)`
3) `client.run_tool(name="get_chat_room_messages_bulk", arguments=build_transcript_arguments(...))` → `parse_messenger_fetch_payload` → 경계·clamp·예산·익명 라벨·인용 번호 조립 → 관측치
4) 실패는 `AiHomeApiException` 으로 바꿔 **툴 실패**로 처리(run은 살림)

**핵심 코드**

```python
# app/modules/domain/ai_home/tools/approval_document_card.py:129-131
def approval_document_card_component_id(*, run_id: str, tool_call_id: str) -> str:
    # 결정적 id: 버튼 클릭 재개 때 같은 값을 다시 계산해 "이 카드의 재개"인지 판정한다
    digest = hashlib.sha256(f"{run_id}\0{tool_call_id}".encode("utf-8")).hexdigest()
    return f"{APPROVAL_CARD_COMPONENT_ID_PREFIX}{digest}"
```

```python
# app/modules/domain/ai_home/tools/executor.py:3984-3997
def _is_approval_card_resume(self, runtime_context, *, tool_call_id: str) -> bool:
    approval = runtime_context.get("mcp_action_approval")
    if isinstance(approval, Mapping) and approval.get("tool_call_id") == tool_call_id:
        return True                         # 승인 폼(또는 비밀번호 재시도 폼) 제출 재개
    interaction = runtime_context.get("ui_component_interaction")
    if not isinstance(interaction, Mapping) or not interaction.get("component_id"):
        return False
    run_id = runtime_context.get("run_id")
    ...
    return interaction.get("component_id") == approval_document_card_component_id(
        run_id=run_id, tool_call_id=tool_call_id)   # 카드 버튼 클릭 재개
```

```python
# app/modules/domain/ai_home/tools/executor.py:2763-2795  (_run_tool 안)
if (
    inject_secret_inputs
    and approval_form_presentation is not None
    and password_property_keys(original_schema)           # 스키마에 format=password 칸이 있는 도구
    and observation.observation.get("status") == "failed"
    and self._is_simple_code_rejection(result.response)   # 400 + simpleCode/간편 비밀번호 문구
    and self._password_target_doc_ids(tool_arguments)     # docId 있는 도구만(초안 생성 도구는 제외)
    and password_attempt < MCP_PASSWORD_MAX_ATTEMPTS      # 3
):
    return AiHomeToolObservationResult(
        observation=self._mcp_password_retry_form_observation(
            name=name, tool_arguments=tool_arguments, ...,
            tool_call_id=tool_call_id,
            attempt=password_attempt + 1,                 # 회차별 새 componentId
        )
    )                                                     # LLM 재호출 없이 같은 실행 안에서 폼 반환
return observation
```

```python
# app/modules/domain/ai_home/tools/secret_inputs.py:56-96 (발췌)
def mask_password_interaction_value(*, component, value):
    masked = dict(value); keys = _password_keys(component)     # inputType=password 칸
    ...
    for key in keys:
        raw = values.get(key)
        if raw is not None and raw != "":
            secrets[key] = str(raw)              # 원문은 따로
            masked_values[key] = PASSWORD_MASK   # 그래프·체크포인트·DB 엔 "********"
    ...
_SECRET_INPUTS: ContextVar[dict[str, str] | None] = ContextVar("ai_home_secret_inputs", default=None)
def with_secret_inputs(arguments, keys):        # MCP 호출 직전에만
    secrets = current_secret_inputs(); executed = dict(arguments)
    for key in keys:
        secret = secrets.get(key)
        if secret: executed[key] = secret
        else: executed.pop(key, None)            # 원문 없으면 키를 빼서 MCP 가 400 으로 알려 주게
    return executed
```

```python
# app/modules/domain/ai_home/tools/catalog.py:2327-2340
def _mcp_schema_requires_approval(schema_payload, *, name) -> bool:
    # 실행기 _mcp_tool_safety_policy 와 같은 규칙이어야 한다(어긋나면 회복 오류)
    ...
    supports_dry_run = isinstance(properties, Mapping) and "dry_run" in properties
    destructive = annotation_map.get("destructiveHint") is True
    # readOnlyHint 를 명시하지 않은 도구는 승인 대상 (fail-closed, 보안 감사 2026-10-07 [4]) ← 본인
    read_only = annotation_map.get("readOnlyHint") is True
    return supports_dry_run or destructive or name in MCP_USER_APPROVAL_REQUIRED_TOOL_NAMES or not read_only
```

**데이터·설정**
- UI 컴포넌트 타입: `approval-document-card`(appCode `approval`), 승인 폼 `inline-input-form`(필드 `inputType: "password"`)
- componentId 접두사 `cmp_approval_doc_` + sha256(run_id, tool_call_id)
- 카드 actions: MCP 상세의 `approvalAction.availableActions`(action/label/tool) 중 이번 run에 노출된 결재 도구만 + [취소]
- 버전 인자: `activityId`, `docVersionId`, `apprFlowVersionId` (상세에 없으면 카드 버튼 비활성)
- `MCP_PASSWORD_MAX_ATTEMPTS = 3`, 마스크 `"********"`, 스키마 마커 `format: "password"`
- 런타임 컨텍스트 키: `mcp_action_approval`(component_id, tool_call_id, action_id, target_name, arguments, submitted_values, password_required, password_attempt …), `ui_component_interaction`
- 메신저 MCP 툴 이름: `get_chat_room_messages_bulk`, `search_chat_room_messages_with_context`, `search_chat_messages`, `list_chat_messages`. 내부 툴 `messenger_fetch`

**왜 이렇게 짰나**
- 카드 내용은 LLM이 쓰지 않는다: 상세 응답을 서버가 그대로 옮김(`approval_document_card.py:3-5`). 결재 문서 정보가 환각되면 안 됨.
- 버튼 → 승인 폼은 LLM 없이: 버튼 클릭과 폼 제출을 **같은 tool_call_id** 로 처리해 폼 id·인자 다이제스트가 재개 시에도 같게 나옴(`cb280664`).
- 비밀번호 재시도를 LLM에 맡기지 않음: 같은 실행 안에서 새 폼을 돌려주면 다른 칸 값이 유지되고 모델이 결재를 엉뚱하게 재구성할 여지가 없음(`18a36066`).
- 비밀번호 원문은 그래프 상태·체크포인트·DB·로그 어디에도 안 둔다 → 체크포인트가 PG에 flush 되는 구조(1번)와 직결. ContextVar로 요청 범위에만.
- fail-closed: annotation이 빠진 쓰기 도구가 승인 없이 실행되는 걸 막음. 조회 도구 98개는 전부 `readOnlyHint: true` 라 영향 없음.
- 메신저 MCP 응답을 다이나믹 MCP 경로로 그대로 보내지 않음: 원본 봉투가 관측치가 되면 절단·익명화·인용이 빠짐(`executor.py:1499-1506`).
- 파서를 `mcp_source.py` 한 곳에 가둠: MCP 계약이 바뀌면 이 파일만 고치도록.

**바뀌어 온 이력**
- 메신저: `440b4399`(08-18) 메신저 대화 요약을 chat/stream에 태움(OpenSearch pre-fetch) → `bc448434`·`c8825ca7`(09-08) 조달을 `messenger_fetch` 툴로 → `cc80e839`(09-15) pre-fetch 경로·토글 제거 → `5a54f10d`(09-15) MCP 응답 파서 → `5f3c6e7a`·`24a118ac`(09-16) 조달을 MCP로(R7-b) → `d60a5a53`(09-17) 대화 턴 조달 창구를 나노가 고르는 MCP 툴로 → `dbe44f56`(10-08) 메신저 툴을 앱 첨부 읽기 대상에 추가
- 전자결재: `b27ccfa3`·`d556afe2`·`d5fdcd29`(10-15) 비밀번호 password 입력·원문 격리 → `86192291`(10-12) fail-closed → `4db82207`(10-16) 상세 → 카드 변환기 → `cb280664`(10-16) 카드 버튼 → 승인 폼 → `18a36066`(10-21) 간편 비밀번호 재시도 → `fd9781d6`(10-21) 일괄 결재에도 → `4349882e`(10-21) 일괄 부분 성공 카드 → `ddfb7c3f`·`6a377bcf`(10-26) 결재선 노드 표시 보강

**면접 30초 설명**
"MCP 서버는 다른 팀원이 만들었고, 저는 에이전트 쪽에서 그 도구들을 사용자 흐름으로 묶었습니다. 결재 문서를 조회하면 `build_approval_document_card` 가 MCP 상세 응답을 그대로 카드로 바꾸고, 카드의 [승인] 버튼을 누르면 LLM을 거치지 않고 `_approval_card_run_tool` 이 같은 tool_call_id로 해당 결재 도구의 승인 폼을 띄웁니다. 간편 비밀번호는 `secret_inputs` 에서 원문을 ContextVar에만 두고 체크포인트·DB엔 마스크만 흘려서, MCP 호출 직전에만 합칩니다. 비밀번호가 틀리면 같은 실행 안에서 다른 칸 값은 유지한 새 폼을 3회까지 다시 띄웁니다. 메신저는 대화 요약 조달을 OpenSearch 직조회에서 MCP 툴로 옮기고, 응답 파싱은 `mcp_source` 한 파일에 가뒀습니다."

**헷갈리기 쉬운 점**
- MCP 클라이언트(`mcp_client.py`)와 `run_tool` 메타 도구·승인 폼 원형은 **외주가 만든 것**. 본인 것은 그 위의 결재 카드·재시도·비밀번호 격리·fail-closed·메신저 조달.
- 승인 판정 함수 자체는 jueon 작성, 본인은 `not read_only` fail-closed 4줄.
- 비밀번호 재시도는 **docId가 있는 도구만**. 초안 생성(`draft_approval_doc` 등)은 실패마다 임시 초안이 남아 일반 실패 경로로 보냄.
- "3회"는 총 시도 횟수(1회차 + 재시도 2회). 3회째도 틀리면 실패 카드.
- `messenger/__init__.py` docstring에 남은 `AI_HOME_MESSENGER_FETCH_TOOL` 토글·`tool_settings.py` 설명은 **낡았다**. 토글과 pre-fetch는 `cc80e839`(09-15)에서 걷어냈고 `tool_settings.py` 파일은 현재 없다. 코드 기준으로 말할 것.
- 메신저 요약의 OpenSearch 경로(`opensearch_source.py`, `run()`)는 아직 코드에 남아 있다. MCP 경로가 `run_with_mcp`.

---

### 4. 그 밖의 설계상 의미가 큰 것

#### 4-A. 같은 노드 재인터럽트 버그 수정 — interrupt를 다음 tools 노드로 미루기  (2026-10-08 · `d84719b1`, 머지 `df535f83` 10-12)

**내가 한 범위**: `_execute_tool_step`, `_pending_tool_interaction_from_result`, `interaction_protocol=2` 표식과 옛 경로 `_execute_tools_with_interrupts` 분리, `_aflush_if_interrupted` 의 False → 실패, 파드 간 재개 테스트 2종. 원래의 "한 노드 안에서 실행·interrupt 반복" 루프는 외주 원형.

**코드 지도**
| 파일 | 함수 | 역할 |
|---|---|---|
| `react_runtime.py` | `_tools`(3813) | `interaction_protocol == 2` 이면 새 방식, 아니면 옛 방식 |
| 〃 | `_execute_tool_step`(4515) | 노드 1회 = (pending 있으면 묻기 → 실행) 또는 (실행 → 입력 필요하면 pending 반환) |
| 〃 | `_route_after_tools`(5617) | `runtime_meta.pending_tool_interaction` 있으면 다시 `tools` |
| 〃 | `_receive_input`(1212) | 새 run에 `interaction_protocol: 2` 기록 |

**흐름**: tools 노드 실행 → `_execute_tool_step(pending=None)` → 도구 실행 → 결과가 승인/입력 필요 → `{"runtime_meta": {"pending_tool_interaction": ...}}` 만 반환하고 노드 종료(3926-3937) → 라우터가 `tools` 로 되돌림 → 다음 tools 노드 실행 맨 앞에서 `_await_tool_interaction` → `interrupt()`(이 노드의 첫 동작) → 재개 시 노드가 처음부터 다시 돌아도 interrupt 앞에 도구 실행이 없음.

**핵심 코드**
```python
# app/modules/domain/ai_home/runtime/react_runtime.py:3925-3943
if deferred_interaction:                                   # interaction_protocol == 2 (새 run)
    result, next_pending = await self._execute_tool_step(
        tool_calls=tool_calls, runtime_context=tool_runtime_context,
        pending=pending_interaction,                       # 지난 노드가 남긴 "물어볼 것"
        before_resumed_execution=_emit_tool_execution_running,
    )
    if next_pending is not None:
        if next_pending["tool_call_id"] != selected_tool.get("toolCallId"):
            raise RuntimeError("AI Home pending tool interaction does not match the selected tool call")
        # 커서·messages·tool_trace 는 그대로 두고 노드를 끝낸다 → 새 체크포인트가 생긴다
        return {"runtime_meta": {_PENDING_TOOL_INTERACTION_KEY: next_pending}}
else:
    result = await self._execute_tools_with_interrupts(...)   # 배포 전 interrupt 된 옛 run 전용
```

**왜**: LangGraph는 같은 노드의 두 번째 interrupt를 **새 체크포인트 없이** 기존 체크포인트에 write만 붙인다. 재개한 파드에서는 그 체크포인트가 PG에만 있고 메모리엔 없어 `aflush_thread` 가 빈 채로 넘어갔다 → 다음 조회가 PG의 옛 승인 폼을 읽음 → 화면의 실패 카드 클릭마다 404(AI-7701, 운영 09-29). 또 재개 시 노드가 처음부터 다시 돌아 승인된 쓰기 도구가 한 번 더 실행됐다. 체크포인트 코드는 안 바꾸고 "노드 1회 = interrupt 최대 1회, 그 앞에 도구 실행 없음" 불변식으로 해결. 옛 run 호환을 위해 프로토콜 번호로 분기.

**면접 30초**: "승인 후 실행이 실패해서 같은 노드에서 실패 카드로 다시 interrupt하면, LangGraph가 새 체크포인트를 안 만들고 write만 붙여서 메모리 버퍼 flush에서 빠지는 버그가 운영에서 났습니다. 체크포인터를 고치는 대신 `_execute_tool_step` 으로 '입력이 필요하면 `pending_tool_interaction` 에 담아 노드를 끝내고 다음 노드 맨 앞에서 묻는다'로 바꿔, 노드 하나에 interrupt가 최대 한 번이고 그 앞에 도구 실행이 없게 했습니다. 재개 때 쓰기 도구가 두 번 실행되던 문제도 같이 없어졌습니다."

**헷갈리기 쉬운 점**: 이 수정은 **체크포인터 코드를 바꾸지 않았다**(커밋 본문 명시). 바뀐 건 그래프 노드 구조와 `_aflush_if_interrupted` 의 False 처리뿐. 테스트: `tests/unit/ai_home/test_react_runtime.py:6930` `..._keeps_a_failure_card_raised_after_a_cross_pod_approval`, `:7126` `..._retries_a_failed_approved_action_once_across_pods`.

#### 4-B. 에이전트 루프 상한 — 모델 호출 N회째에 도구를 멈추고 모은 결과로 답하기  (2026-09-29 · `fa1a1e6f`, 10-27 `80cf84f3`)

**내가 한 범위**: `runtime/loop_budget.py` 전체, `_loop_budget_decision`, `recursion_limit` 명시(최초·재개 `graph_config` 양쪽).

**코드 지도**: `loop_budget.py` `resolve_ai_home_loop_budget`, `recursion_limit_floor` / `react_runtime.py:3491` `_loop_budget_decision` / `_route_after_agent_model`(5595)의 `loop_budget_repair_pending` 분기 / `graph_config()`(548, 579)의 `"recursion_limit"`.

**핵심 코드**
```python
# app/modules/domain/ai_home/runtime/react_runtime.py:3516-3530
business_tool_calls = sum(1 for call in response.tool_calls
                          if call["name"] != RESPOND_WITH_SUGGESTED_ACTIONS_TOOL_NAME)
has_business_tool_calls = business_tool_calls > 0
if runtime_meta.get("loop_budget_reached") is True:       # 이미 마지막 기회를 줬는데
    if has_business_tool_calls or empty_response:
        return "loop_budget_finalized"                    # 또 도구 호출/빈 응답 → 고정 문구로 정상 종료
    return None
if has_business_tool_calls and (
    loop_index >= self._loop_budget_max_model_calls_value()            # 모델 호출 수 상한(기본 10)
    or executed_tool_calls + business_tool_calls > resolve_ai_home_loop_budget().max_tool_calls  # 도구 실행 수(기본 100)
):
    return "loop_budget_repair"   # 도구 실행 안 하고 "# Loop Budget Reached" 지시로 1회 더 호출
return None
```

**데이터·설정**: yml `ai_home.loop_budget` — 기본 `max_model_calls=10`, `recursion_limit=500`, `max_tool_calls=100`. env `AI_HOME_LOOP_BUDGET_MAX_MODEL_CALLS`, `AI_HOME_RECURSION_LIMIT`, `AI_HOME_LOOP_BUDGET_MAX_TOOL_CALLS` 우선. `recursion_limit_floor = 5 + 2×(N+1) + N` 보다 작으면 끌어올림.

**왜**: `recursion_limit` 을 지정한 적이 없어 langgraph 업그레이드(08-04) 뒤 기본 10007을 탔고, 모델 호출 수를 세는 장치가 없었다. `model_call_count` 는 `runtime_meta` 에 실려 **인터럽트 재개를 넘어** 이어지므로(재개마다 0부터 세는 recursion_limit과 다름) 비용 상한으로 쓴다. 버린 응답은 state에 넣지 않음(빈 AIMessage가 Anthropic prefill로 나감). 도구 실행 수 상한은 한 응답이 도구를 수백 개 부르는 경우 대비(보안 감사 10-21 #25).

**면접 30초**: "ReAct 루프에 상한이 없어서 `loop_budget.py` 로 모델 호출 수 상한을 뒀습니다. N번째 응답이 또 도구를 부르면 실행하지 않고 '지금까지 모은 결과로 답하라'는 지시로 한 번 더 부르고, 그래도 도구를 부르면 고정 문구로 정상 종료합니다. 카운트는 `runtime_meta` 에 실려 승인 재개를 넘어서도 이어지고, `recursion_limit` 은 그 코드가 고장 났을 때의 안전망으로 따로 둡니다."

**헷갈리기 쉬운 점**: 상한 도달 시 **예외로 끊는 게 아니다**. 1회 추가 호출 후 정상 종료. recursion_limit은 노드 실행 수 기준이고 invoke마다 0부터 센다.

---

### 부록: 이전 조사(`study-ai-agent.md`)와 달라진/보강된 사실
- graceful 수치: `graceful_timeout` 은 **45→120**, `timeout` 60→150, TGPS 30→150. 최초 반영 위치는 `scripts/entrypoint.sh` CLI 인자(`4f410bb7`)였고 `6987c415`(08-04)에 `gunicorn_conf.py` 로 옮겨졌다.
- Redis 첫 구현 `7fdf2801`(07-31)은 **develop 히스토리에 없다**(backup ref에만 존재). 리베이스로 `4809e574` 계열에 흡수.
- 파드 간 재개 수정 커밋의 develop 해시는 `3f0a691a`(리베이스 전 `78b5d5a6`).
- `ai_thread_run_lock`/`acquire_lock` 은 dskim(06-16) 원형 — 본인 코드 아님.
- `messenger/` 패키지는 63커밋 전부 본인. MCP 연동에서 본인 몫이 가장 큰 덩어리 중 하나라 3번에 포함.
- `messenger/__init__.py` docstring의 토글 설명은 코드와 불일치(낡음).

---

# 코드 워크스루 — ai-file / ai-automation (면접용, 본인 기여 중심)

- 작성 2026-11-05. 기준 코드: `ai-file` develop `4e3b962`, `ai-automation` develop `eeafc03`, `ai-home-poc` 머지 `fcfc0ff9`.
- 경로는 저장소 루트 기준. 라인 번호는 위 커밋 기준.
- 이전 조사(`study-ai-file-automation.md`)의 수치·Q&A는 반복하지 않는다. 여기서는 "코드가 어떻게 생겼고 무엇이 무엇을 부르는지"만.
- 표기: **[내 코드]** 내가 쓴 커밋, **[타인]** 다른 사람(pbs-7818, dskim, springfefe) 코드, **확인 필요** = 코드로 확인 못 함.

---

## ai-file — 코드 워크스루

### 전체 코드 지도

```
app/
  main.py                      # FastAPI 앱 + lifespan: SERVICE(file|knowledge)·dispatch_mode 로 컨슈머 기동 결정
  messaging/
    envelope.py                # 요청 봉투 모델, envelope_reject_reason (reply 키 형식 검증)        [내 코드]
    attachment_consumers.py    # read/metadata 큐 핸들러 _make_handler (+ 잡 끝 maybe_trim)         [내 코드]
    redis_publisher.py         # claim-check: SETEX 결과 → PUBLISH 알림                            [내 코드]
    knowledge_consumers.py     # knowledge 풀 컨슈머 (검증→claim→commit→ack→process_job)            [내 코드]
    dead_letter_consumers.py   # DLQ 마킹(소유권 검사)
  domain/
    shared/
      runtime.py               # 프로세스 전역 limiter 들 (anyio.CapacityLimiter)
      scratch.py               # 스크래치 디스크 staged path, 기동 시 sweep                        [내 코드]
      memprobe.py              # 요청별 메모리 샘플 + 회수 프로브 (진단 전용)                       [내 코드]
      memtrim.py               # 잡 경계 malloc_trim (운영 스위치)                                  [내 코드]
      perf.py / perf_flags.py  # 기동 시 install_perf_overrides 로 위 스위치 주입
    attachments/
      service.py               # perform_read / perform_metadata (원장 조회→다운로드→파싱)
      parser.py                # AttachmentParser: 확장자 분기, PDF 렌더, _shrink_mupdf_store
      document_extractors/pptx/extractor.py  # 슬라이드 창(window) 패키지 생성                     [창 생성 최적화만 내 코드]
    agent_knowledge/
      repository.py            # claim_queued_job (INSERT…SELECT…ON CONFLICT 락 + 소유권)
      service.py               # process_job: 다운로드→파싱→청크→임베딩→ES 색인              [대부분 타인]
      parser.py / es.py        # 지식 파서, ES 클라이언트(generation 기반 교체)               [타인]
  core/config/envs/env_model.py  # 설정 모델 (memtrim, pdf_store_shrink_after_render 등)
resources/yml/config_*.yml     # 환경별 프로파일 (값은 ${ENV:-기본값} 형태)
```

**요청 흐름 A — 채팅 첨부 read (메모리 작업이 걸려 있는 경로)**

```
AI Home ──publish──▶ RabbitMQ  ai-file.req.read  (quorum, DLX)
   │                    │
   │                    ▼
   │   attachment_consumers._make_handler.handler(body)          # :117
   │     1) RequestEnvelope 파싱 / envelope_reject_reason        # reply 키가 ai-file:result:<correlationId> 형식인지
   │     2) deadlineAt 경과면 처리 없이 return(ack)
   │     3) async with response_limiter:                          # attachment_response_inflight_count=1 [타인]
   │          perform_read(request, session)                      # service.py:366  @memory_probe("read")
   │            repository.get_attachment → storage.stat → note_target(ext,size)
   │            PDF면 artifact 캐시/singleflight, 그 외 DB 청크 캐시 조회
   │            miss → download_and_parse()                       # :381
   │                 async with runtime.attachment_inflight_limiter   # 다운로드+파싱 전체를 묶음
   │                   scratch.new_staged_path → storage.download_to_path (RAM 아닌 디스크)
   │                   parser.read(...) → 확장자 분기
   │                       pdf  → _pdf_artifact → run_attachment_read(_render_pdf_artifact)
   │                                   finally: _shrink_mupdf_store()        # MuPDF store 비우기
   │                       pptx → _read_pptx → run_attachment_parse(_extract_pptx_range_from_path)
   │                                   → extract_document_from_path → _create_slide_window
   │                   finally: file_path.unlink()
   │          RedisResultPublisher.publish: SETEX ai-file:result:<cid> → PUBLISH ai-file:reply:<host>
   │     4) maybe_trim(op)                                        # 잡 완전 종료 후 malloc_trim
   ◀──Redis SUBSCRIBE 알림 + GET 결과── (claim-check)
```

**요청 흐름 B — 사전지식 1건 (진입 → 파싱 → 색인)**

```
AI Home ──publish──▶ ai-file.req.knowledge
   knowledge_consumers.make_knowledge_pull_handler.handler(message)   # :55  [내 코드]
     1) 봉투/페이로드 검증 실패 → ack(discard)
     2) AgentKnowledgeRepository.claim_queued_job(...)                 # repository.py:267
          INSERT ai_agent_knowledge_indexing_job … SELECT FROM ai_agent_knowledge JOIN ai_agent
          WHERE 소유권(agent/company/user) 일치 AND 미삭제
          ON CONFLICT DO UPDATE … WHERE locked_until IS NULL OR locked_until < now()
        session.commit()
        False(락 보유자 있음/삭제/소유권 불일치) → ack 후 skip
     3) message.ack()            ← 여기서 ack. 이후 처리 시간은 브로커와 무관
     4) AgentKnowledgeService.process_job(...)                         # service.py:246  [본문은 타인]
          _start_lock_heartbeat (TTL/3 주기 locked_until 연장)          # [dskim 119d7e0]
          mark_progress(downloading,10)
          async with agent_knowledge_inflight_limiter:
            staged path 로 download_to_path → mark_progress(parsing,25)
            AgentKnowledgeParser.parse(..., on_chunk_batch=…)          # 스트리밍: 배치마다
                on_chunk_batch → _embed_chunk_documents(Gemini) → es.index_chunk_documents
          es.index_attachment_document(active_generation=새 uuid)      # 새 세대 활성화
          es.delete_previous_chunk_generation(이전 세대)               # [pbs-7818 d113818]
          repository.mark_indexed + commit
          예외 → 미활성 세대 청크 삭제 + _mark_job_failed
```

**내 코드가 있는 곳 (ai-file)**
| 영역 | 파일 | 대표 커밋 |
|---|---|---|
| 메모리 계측/회수 | `memprobe.py`, `memtrim.py`, `parser.py:_shrink_mupdf_store`, `env_model.py` 해당 필드 | `cf06655` `b148f14` `2f063f7` `a4cc709` `1a8c044` `2830d7f` |
| OOM 구조(디스크 스테이징·전역 limiter) | `scratch.py`, `runtime.attachment_inflight_limiter`, `service.download_and_parse` | `f388648` `b22b285` `4624755` `9276157` `ddc0fe8` `90d0441` `2e034db` |
| PPTX 창 패키지 | `pptx/extractor.py:_create_slide_window`, `_warn_if_window_not_applied` | `ff37385` → `48ed080` |
| 메시징 (봉투·claim-check·quorum) | `envelope.py`, `attachment_consumers.py`, `redis_publisher.py` | `1d2aeba` `4ed6b35` `42c3b7f` `3302e31` |
| knowledge 풀 컨슈머 + 소유권 | `knowledge_consumers.py`, `repository.claim_queued_job` | `1ebcb72` `ca7c737` `b00c75a` `07b18e6` |
| 디스패치 모드 fail-fast | `main.py:_validate_dispatch` | `4f90241` |

**타인 코드(내 성과로 말하지 말 것)**: PPTX 슬라이드 창 개념 자체(`8f328f2`, pbs-7818), response limiter(`0098839`, pbs-7818), knowledge 스트리밍 청크 배치·임베딩(`a4ffa6d` `421d99b`, pbs-7818), PDF 페이지 병렬 VLM·진행률 스로틀(`29f624b`, dskim), 락 하트비트 분리(`119d7e0`, dskim), ES generation 교체(`d113818` `031e948`, pbs-7818), PDF artifact 캐시(`0e7f047`, pbs-7818).

---

### 1. 메모리 문제 대응 코드 — MuPDF store 비우기 · 잡 경계 malloc_trim · 메모리 프로브 (2026-07-28 ~ 07-30 · `cf06655` `2f063f7` `a4cc709` `1a8c044` `2830d7f`)

**내가 한 범위**: 진단 계측(memprobe), MuPDF store 회수, malloc_trim 스위치, 관련 설정 필드·yml 전부 내 커밋. `MALLOC_MMAP_THRESHOLD_=131072` 는 **코드가 아니라 k8s Deployment env** 로 넣는 값이라 이 저장소에 없다(주석에만 언급). 실제 stg/prod Deployment 반영 여부는 **확인 필요**(이전 조사와 동일).

**코드 지도**
| 파일 | 클래스/함수 | 역할 |
|---|---|---|
| `app/domain/shared/memprobe.py` | `memory_probe(op)` 데코레이터(:108), `_sample`(:126), `_reclaim_probe`(:171), `note_target`(:70) | 잡 끝마다 RSS·`sys.getallocatedblocks()`·cgroup anon/file 한 줄 로그. N번째마다 gc→trim→store_shrink→trim 단계별 회수량 측정 |
| `app/domain/attachments/service.py` | `perform_read` 에 `@memory_probe("read")`(:366), `note_target(ext,size)` | 계측 부착 지점, 확장자 라벨 |
| `app/domain/attachments/parser.py` | `_shrink_mupdf_store()`(:136), `_render_pdf_artifact`(:1215) | PDF 렌더 끝난 뒤 `fitz.TOOLS.store_shrink(100)` |
| `app/domain/shared/memtrim.py` | `set_memory_trim`(:101), `maybe_trim(op)`(:116), `_memory_limit_bytes`(:171), `_cgroup_anon_bytes`(:203), `_malloc_trim`(:233) | 잡 경계에서 비율 게이트→쿨다운→`malloc_trim(0)` |
| `app/messaging/attachment_consumers.py` | `handler` 끝의 `maybe_trim(op)`(:220) | 응답 발행·limiter 해제 **후** 트림 |
| `app/domain/shared/perf.py` | `install_perf_overrides`(:116) | 기동 시 env-or-config 로 memprobe/memtrim on/off 주입 (`main.py:273`) |
| `app/core/config/envs/env_model.py` | `memprobe`(:227), `memprobe_reclaim_every`(:231), `memtrim`(:245), `memtrim_threshold_ratio`(:261), `memtrim_cooldown_seconds`(:264), `pdf_store_shrink_after_render`(:277) | 스위치·근거 주석 |

**흐름** (PDF read 1건 기준)
1. `attachment_consumers.handler` → `perform_read` (데코레이터 `memory_probe("read")` 가 감쌈)
2. `perform_read` → `note_target("pdf", size)` (ContextVar 에 라벨 저장)
3. → `download_and_parse` → `parser.read` → `_pdf_artifact` → `runtime.run_attachment_read(_render_pdf_artifact)` (스레드 풀)
4. `_render_pdf_artifact`: `try: _render_pdf_pages(...)` `finally: if cfg.pdf_store_shrink_after_render: _shrink_mupdf_store()` — 페이지 루프 안이 아니라 **렌더 전체가 끝난 뒤 한 번**
5. `perform_read` 반환 시 데코레이터가 `_sample("read")` → 켜져 있으면 `MEMPROBE ...` 로그, `seq % reclaim_every == 0` 이면 `_reclaim_probe` → `MEMPROBE-RECLAIM ... reclaimed_trim_mb / reclaimed_store_mb`
6. `handler` 가 Redis 발행까지 마치고 response limiter 를 놓은 뒤 `maybe_trim("read")` → 게이트(anon/limit ≥ 0.01) → 쿨다운 60초 → `malloc_trim(0)` → `MEMTRIM ... reclaimed_mb` 로그

**핵심 코드**

`app/domain/attachments/parser.py:1215-1232`
```python
def _render_pdf_artifact(self, attachment, file_path, locator) -> PdfReadArtifact:
    try:
        return self._render_pdf_pages(attachment, file_path, locator)
    finally:
        # 렌더 '전체'가 끝난 뒤 한 번만 비운다. 페이지마다 비우면 같은 문서의
        # 폰트·이미지 리소스를 다시 파싱하게 된다. 실패 경로에서도 비운다.
        if getattr(self._cfg, "pdf_store_shrink_after_render", False):
            _shrink_mupdf_store()
```
`app/domain/attachments/parser.py:136-160` (요지)
```python
def _shrink_mupdf_store() -> None:
    # TOOLS.store_maxsize 대입은 PyMuPDF 1.27에서 no-op(staticmethod 를 정수로 덮을 뿐).
    # 실제로 듣는 건 store_shrink 뿐. store 는 프로세스 전역 → 동시성 올리면 재측정 필요.
    try:
        fitz.TOOLS.store_shrink(100)      # 100% = 전부 비움 (fz_empty_store)
    except Exception:                     # 회수는 부가 작업, 요청을 깨면 안 됨
        logger.debug("MuPDF store shrink failed", exc_info=True)
```
`app/domain/shared/memtrim.py:116-150` (요지)
```python
def maybe_trim(op: str) -> None:
    if not _enabled:
        return
    try:
        limit = _memory_limit_bytes()          # /sys/fs/cgroup/memory.max (v1 폴백), 1회 캐시
        anon = _cgroup_anon_bytes()            # memory.stat 의 "anon " — 페이지 캐시는 트림 대상 아님
        if not limit or anon is None: return
        if anon / limit < _threshold_ratio:    # 기본 0.01 → 사실상 항상 통과(탈출구용 게이트)
            return
        now = time.monotonic()
        with _lock:
            if _last_trim_at is not None and now - _last_trim_at < _cooldown_seconds:
                return                         # 쿨다운 60초가 실질 주기
            _last_trim_at = now
        before = _read_rss_bytes(); trimmed = _malloc_trim(); after = _read_rss_bytes()
        logger.info("MEMTRIM op=%s ... reclaimed_mb=%s", ...)
    except Exception:                          # 운영 경로를 절대 깨지 않게
        logger.debug("MEMTRIM failed", exc_info=True)
```
`_malloc_trim` 은 `ctypes.CDLL(None).malloc_trim` 을 한 번 resolve 해 `(0)` 호출 (`memtrim.py:233-254`, memprobe 쪽도 같은 방식 `:266-278`).

**데이터·설정**
- 설정 키(`ai_file.*`): `memprobe`(기본 False), `memprobe_reclaim_every`(0), `memtrim`(True), `memtrim_threshold_ratio`(0.01), `memtrim_cooldown_seconds`(60), `pdf_store_shrink_after_render`(True)
- env 오버라이드: `AI_FILE_MEMPROBE`, `AI_FILE_MEMPROBE_RECLAIM_EVERY`, `AI_FILE_MEMTRIM`, `AI_FILE_MEMTRIM_THRESHOLD_RATIO`, `AI_FILE_MEMTRIM_COOLDOWN_SECONDS`, `AI_FILE_PDF_STORE_SHRINK_AFTER_RENDER`
- yml: dev/stg/prod/aws-* 모두 `memtrim: ${AI_FILE_MEMTRIM:-true}`, `pdf_store_shrink_after_render: ${…:-true}`
- 저장소 밖: `MALLOC_MMAP_THRESHOLD_=131072` (Deployment env)
- 읽는 커널 파일: `/sys/fs/cgroup/memory.max`, `/sys/fs/cgroup/memory.stat`, `/proc/self/statm`
- 로그 키워드: `MEMPROBE`, `MEMPROBE-RECLAIM`, `MEMTRIM`

**왜 이렇게 짰나**
- memprobe: 파드 20개라 특정 파드에 디버그 엔드포인트를 찌를 수 없음 → **잡이 스스로 한 줄씩 로그**. RSS↑ + blocks 평평 = 파이썬 누수 아님(모듈 docstring). store 크기 조회 API(`TOOLS.store_size()`)가 1.27에서 `None` 이라 "비운 뒤 RSS 차이로 역산".
- store 비우기 위치: `/read` 는 요청마다 `mkstemp` 새 경로로 받아 새로 열어서 **요청 간 store 재사용이 없음** → 비워도 손실 0 (parser.py docstring). `store_maxsize` 는 no-op 이라 버림.
- malloc_trim 위치: 응답 발행 **뒤**. 발행 전에 트림하면 직렬화가 방금 반납한 페이지를 다시 폴트(docstring).
- 임계값→주기 전환(`2830d7f`): 첫 구현 `1a8c044` 는 0.60 비율 게이트였는데 pptx 최대 45.3%, xlsx 22.4% 라 한 번도 안 불림 + 로그가 침묵해 "문제없음"으로 오독. 트림 비용(재폴트 20~40ms)은 방어할 값이 아님 → 0.01 + 쿨다운 60초. dev/stg/prod 동일 값 원칙.
- malloc_trim 은 "주인 없는 free 페이지만 반납"(재파싱·데이터 손실 없음) vs store_shrink 는 "쓸 수 있는 캐시를 버림" — 성격 다른 두 장치.
- 범위 한정: memtrim 훅은 첨부 컨슈머에만 있음 → knowledge 파드에서는 안 돎(측정 안 했으므로, docstring "스코프").

**바뀌어 온 이력**
`cf06655`(07-28 memprobe) → `2f063f7`(07-28 store drop, dev opt-in) → `a4cc709`(07-28 stg/prod 승격, 커밋 메시지에 B-2 측정값) → `b148f14`(07-29 확장자 라벨) → `1a8c044`(07-29 잡 경계 trim, 비율 0.60) → `2830d7f`(07-30 주기 기반, 전 환경) → `1470b54`(나, env_model 기본값을 운영값 True 로 정렬)

**면접 30초 설명**
"부하테스트에서 RSS가 계단처럼 오르다 OOMKill 됐는데 파드가 20개라 디버거를 붙일 수 없어서, `perform_read`에 `memory_probe` 데코레이터를 달아 잡마다 RSS와 `getallocatedblocks`, cgroup anon을 남겼습니다. 블록 수가 평평해서 파이썬 누수가 아니었고, `_reclaim_probe`로 gc→`malloc_trim`→`store_shrink` 순서로 회수량을 쪼개 glibc 미반환과 MuPDF store 두 원인으로 나눴습니다. 처방은 `_render_pdf_artifact`의 finally에서 `fitz.TOOLS.store_shrink(100)`, Deployment에 `MALLOC_MMAP_THRESHOLD_` 고정, 그리고 첨부 컨슈머 잡 끝에 `maybe_trim`으로 60초 주기 `malloc_trim`을 넣었습니다."

**헷갈리기 쉬운 점**
- `MALLOC_MMAP_THRESHOLD_` 는 코드/yml에 **값으로 없다**. 파이썬 시작 전에 glibc가 읽으므로 config yml로 못 넣는다. 끝 언더스코어 필수.
- store_shrink 는 렌더 **이후 매번**(설정 on), malloc_trim 은 **60초마다 첫 잡 경계**. 둘은 다른 함수·다른 파일.
- memprobe 는 진단(기본 off), memtrim 은 운영 스위치(기본 on). 회수 프로브는 "관찰이 아니라 개입"이라 관찰 런과 검증 런을 나눠야 함.
- `maybe_trim` 은 `/read` 뿐 아니라 metadata·source_read 핸들러에도 걸림(같은 `_make_handler`). knowledge 경로에는 없음.

---

### 2. PPTX 창(window) 패키지 재압축 제거 (2026-07-29 · `ff37385` → `48ed080`)

**내가 한 범위**: `_create_slide_window` 내부 구현 교체 + `_warn_if_window_not_applied` + 테스트 `tests/test_pptx_window_compression.py`. **"요청 슬라이드만 담은 임시 pptx를 만든다"는 창 개념 자체는 pbs-7818의 `8f328f2`(07-16)**. 나는 그 창을 만드는 방식을 바꿨다.

**코드 지도**
| 파일 | 함수 | 역할 |
|---|---|---|
| `app/domain/attachments/parser.py` | `_read_pptx`(:1358), `_extract_pptx_range_from_path`(:298) | 슬라이드 범위 정규화, DB 청크 캐시, miss 시 스레드 풀에서 추출 |
| `app/domain/attachments/document_extractors/pptx/extractor.py` | `extract_document_from_path`(:414) | 창 생성 → python-pptx 추출 → 창 파일 삭제 |
| 같은 파일 | `_slide_window_parts`(:165) | `ppt/presentation.xml` 의 `sldIdLst`, `ppt/_rels/presentation.xml.rels` 에서 범위 밖 슬라이드 제거한 XML 2개 생성 |
| 같은 파일 | `_create_slide_window`(:203) | 원본 `shutil.copyfile` → `ZipFile(mode="a")` 로 XML 2개 append |
| 같은 파일 | `_warn_if_window_not_applied`(:52) | 리더가 실제로 뒤 엔트리를 고르는지 확인, 어긋나면 경고만 |

**흐름**
1) `parser._read_pptx` → `_normalize_range(slides, max_count=pptx_slide_window_size)` → `repository.get_cached_chunk(chunk_type="SLIDES", range_key="slides:a-b")`
2) miss → `runtime.run_attachment_parse(_extract_pptx_range_from_path, file_path, start, end, pptx_read_max_bytes)`
3) → `extractor.extract_document_from_path(start_slide, end_slide)` → `_create_slide_window`
4) `_create_slide_window`: `NamedTemporaryFile(dir=원본과 같은 스크래치 디렉터리, delete=False)` → `ZipFile(원본)` 으로 `_slide_window_parts` (XML 2개 bytes) → `shutil.copyfile(원본, 창)` → `ZipFile(창, mode="a", ZIP_DEFLATED, compresslevel=1).writestr(XML 2개)` → `_warn_if_window_not_applied`
5) `_extract_document(window_path, start_slide=1, end_slide=n, slide_number_offset=start-1)` (python-pptx 가 창만 로드)
6) `finally: window_path.unlink()` → `repository.upsert_chunk(...)` 로 캐시

**핵심 코드** — 수정 전(`ff37385` 시점, 루프 구조는 원래 pbs-7818 코드)
```python
with ZipFile(file_path) as source, ZipFile(window_path, mode="w") as target:
    replacements = _slide_window_parts(source, ...)
    for info in source.infolist():
        target_info = copy(info)                       # ← 원본 compress_type(DEFLATED)까지 복사
        _apply_window_compression(target_info, info)   # ← ff37385 에서 추가한 1차 수정(멤버별 판정)
        ...
        with source.open(info) as reader, target.open(target_info, mode="w", force_zip64=True) as writer:
            shutil.copyfileobj(reader, writer, length=1024 * 1024)   # 멤버마다 inflate → deflate
```
수정 후 `app/domain/attachments/document_extractors/pptx/extractor.py:231-253`
```python
    try:
        with ZipFile(file_path) as source:
            replacements = _slide_window_parts(source, start_slide=start_slide, end_slide=end_slide)

        shutil.copyfile(file_path, window_path)   # 바이트 그대로 복사 (리눅스: sendfile/copy_file_range)

        with warnings.catch_warnings():
            # 같은 이름 멤버를 덧붙이는 게 핵심 → zipfile 의 "Duplicate name" 경고만 이 구간에서 억제
            warnings.filterwarnings("ignore", message="Duplicate name", category=UserWarning)
            with ZipFile(window_path, mode="a", compression=ZIP_DEFLATED,
                         compresslevel=_WINDOW_COMPRESSLEVEL) as target:   # = 1
                for name, data in replacements.items():   # presentation.xml, presentation.xml.rels 2개뿐
                    target.writestr(name, data)           # 중앙 디렉터리의 '뒤 엔트리'가 이김

        _warn_if_window_not_applied(window_path, replacements)   # 앞 엔트리 리더면 전체 슬라이드 로드 위험
        return window_path
    except Exception:
        window_path.unlink(missing_ok=True)
        raise
```

**데이터·설정**: `pptx_slide_window_size`, `pptx_read_max_bytes`(설정), DB 캐시 청크 `chunk_type="SLIDES"`, `range_key="slides:<a-b>"`, 상수 `_WINDOW_COMPRESSLEVEL = 1`, 창 파일명 `.<stem>-slides-<a>-<b>-*.pptx`(스크래치 디렉터리).

**왜 이렇게 짰나**
- 1차(`ff37385`): 원인을 "`copy(info)`가 압축 방식을 들고 와서 재압축"으로 보고, 원본 zip 헤더의 `compress_size/file_size > 0.9` 면 STORED, 아니면 DEFLATED level 1 (`_apply_window_compression`, `ZipInfo._compresslevel` 비공개 슬롯 사용). 전면 STORED 는 XML 많은 덱이 3배 커져서(1.01→3.16MB) 버림. 합성 픽스처 336멤버에선 6.6배.
- 2차(`48ed080`): 실파일은 5,697멤버·89%가 16KB 미만 → 비용이 바이트가 아니라 **zlib 스트림당 고정비**(128KB `head` 테이블 0 채우기 등, 요청당 스트림 11,394개). 압축 설정으로는 스트림 수가 안 줄어듦 → "틀린 레버". zip 은 끝의 중앙 디렉터리로 찾고 같은 이름이면 뒤가 이김 → 원본 복사 + 2개 append. 원본 멤버의 압축·CRC·zip64 를 안 건드리는 부수 이점.
- 버린 대안: 멤버별 압축 판정(1차), 전면 STORED.
- 트레이드오프: zip 은 멤버 삭제가 안 돼 원본 매니페스트가 파일에 남음 → 앞 엔트리를 읽는 리더라면 창이 무시되고 **전 슬라이드 로드(메모리 사고)**. python-pptx 는 뒤 엔트리를 읽음을 테스트로 고정, 운영은 경고만(`_warn_if_window_not_applied`).

**바뀌어 온 이력**: `8f328f2`(07-16, pbs-7818, 창 도입·전 멤버 스트림 복사) → `0098839`/`6ae580c`(07-22, pbs-7818, 응답 바이트 상한) → `ff37385`(07-29, 나, 멤버별 압축) → `48ed080`(07-29, 나, append 방식)

**면접 30초 설명**
"pptx read가 PDF보다 몇 배 느렸는데 89%가 `_create_slide_window`였습니다. 요청 슬라이드만 담은 임시 패키지를 만들면서 `copy(info)`로 압축 방식까지 복사해 모든 멤버를 풀었다 다시 압축하고 있었죠. 처음엔 멤버별로 압축 여부를 고르게 고쳤는데 실파일에선 1.6배뿐이었고, 원인이 5,700개 작은 XML의 zlib 스트림 고정비라는 걸 찾았습니다. 그래서 원본을 `shutil.copyfile`로 그대로 복사하고 `ZipFile(mode='a')`로 `presentation.xml`과 rels 두 개만 덧붙였습니다. zip은 뒤 엔트리가 이기니까요. 함수 기준 0.88초에서 0.024초가 됐고, 앞 엔트리를 읽는 리더 위험은 `_warn_if_window_not_applied`와 테스트로 막았습니다."

**헷갈리기 쉬운 점**
- 0.880s → 0.024s 는 **창 생성 함수 단위, macOS, 실파일 모양 픽스처** 측정. 요청 단위 수치와 섞지 말 것.
- "창(window)"을 만든 사람은 내가 아니다. 나는 "창을 만드는 방법"을 바꿨다.
- `compresslevel=1` 은 덧붙이는 XML 2개에만 적용. 원본 멤버는 원래 압축 그대로.
- `_warn_if_window_not_applied` 는 예외를 던지지 않는다(운영 경고만). 테스트는 hard assert.

---

### 3. 첨부 OOM 구조 — 디스크 스테이징 + 프로세스 전역 in-flight limiter (2026-07-14 · `f388648` `b22b285` `4624755` `9276157` `ddc0fe8` `90d0441` `2e034db`)

**내가 한 범위**: 위 커밋 전부 내 것(설계 문서 `ai-file/done/2026-07-13-attachment-oom-stability-design.md`). knowledge 쪽 `agent_knowledge_inflight_limiter` 사용 위치(`process_job`)는 같은 패턴인데 그 본문 작성자는 **확인 필요**.

**코드 지도**
| 파일 | 함수 | 역할 |
|---|---|---|
| `app/domain/shared/scratch.py` | `attachment_scratch_dir`, `agent_knowledge_scratch_dir`, `new_staged_path`(mkstemp), `sweep_stale` | `<file_scratch_dir>/attachments`, `/agent_knowledge` 아래 임시 경로, 기동 시 잔존 파일 삭제 |
| `app/domain/shared/runtime.py` | `AiFileRuntime.__init__` 의 `attachment_inflight_limiter`(:64) 등 | 파드 전역 `anyio.CapacityLimiter`. 파싱은 `_run_sync`→`anyio.to_thread.run_sync(limiter=…)` |
| `app/domain/attachments/service.py` | `perform_read.download_and_parse`(:381), `perform_metadata` 내부(:149, :199) | limiter 안에서 staged path 생성→다운로드→파싱→finally unlink (caller-owned) |
| `app/main.py` | `lifespan`(:267): `install_perf_overrides()`, `sweep_stale()`(:278) | 기동 시 정리 |

**흐름**: `perform_read` → (캐시 miss) `download_and_parse` → `async with runtime.attachment_inflight_limiter` → `scratch.new_staged_path(dir, suffix=".pdf")` → `storage.download_to_path(bucket, path, dest, max_bytes=max_file_size_bytes)` → `parser.read(attachment, file_path, locator)` → `finally: file_path.unlink(missing_ok=True)`

**핵심 코드** `app/domain/attachments/service.py:381-420` (요지)
```python
async def download_and_parse(current_attachment):
    scratch_dir = attachment_scratch_dir()
    async with runtime.attachment_inflight_limiter:      # 다운로드+파싱 '전체'를 묶는다(전엔 파싱만)
        file_path = scratch.new_staged_path(dir=scratch_dir, suffix=f".{current_attachment.extension}")
        try:
            downloaded_identity = await storage.download_to_path(   # bytes 를 RAM 에 안 올리고 디스크로 스트림
                bucket=current_attachment.bucket, path=current_attachment.storage_path,
                dest=file_path, max_bytes=cfg.max_file_size_bytes)
            ...
            return await parser.read(current_attachment, file_path, request.locator)
        finally:
            file_path.unlink(missing_ok=True)            # 경로를 만든 호출자가 지운다 → 취소돼도 정리(ddc0fe8)
```

**데이터·설정**: `file_scratch_dir`, `attachment_inflight_count`(dev/stg/prod yml 기본 1, local 4), `attachment_response_inflight_count`(1, pbs-7818), `max_file_size_bytes`, `image_max_pixels`(24M), `pdf_max_render_pixels`(36M).

**왜 이렇게 짰나**: 원래 `download_as_bytes()` 로 원본 전체를 RAM에 올리고 limiter 는 파싱만 막아 "동시 요청 수 × 원본 크기"가 상주. 원본은 디스크로, 상한은 다운로드부터 걸고, 픽셀 수는 디코딩 전에 검사(`2e034db` 이미지 후보 지연 생성). 경로 생성·삭제를 같은 함수(호출자)가 소유해 취소 안전.

**면접 30초 설명**: "첨부 원본을 `download_as_bytes`로 통째로 메모리에 올리던 걸 `scratch.new_staged_path`로 만든 디스크 경로에 스트리밍하게 바꾸고, `attachment_inflight_limiter`를 다운로드부터 파싱 끝까지 감싸게 옮겼습니다. 경로는 만든 쪽이 finally에서 지우고, 크래시로 남은 파일은 기동 시 `sweep_stale`이 지웁니다."

**헷갈리기 쉬운 점**: limiter 가 여러 개다 — `attachment_inflight_limiter`(내 것, 다운로드+파싱), `attachment_parse_limiter`/`attachment_read_limiter`(스레드 풀 크기), `attachment_response_limiter`(pbs-7818, 직렬화까지). 메모리 상한의 핵심은 inflight.

---

### 4. 메시징: 첨부 claim-check + knowledge 풀 컨슈머(처리 전 ack) (2026-07-16 ~ 10-21 · `1d2aeba` `4ed6b35` `42c3b7f` `1ebcb72` `ca7c737` `b00c75a`)

**내가 한 범위**: 봉투 모델·검증, Redis claim-check 발행, 요청 큐 quorum 선언, knowledge 풀 핸들러와 ack 순서, claim SQL 의 소유권 조건. `process_job` 본문(파싱·임베딩·색인)은 타인.

**코드 지도**
| 파일 | 함수 | 역할 |
|---|---|---|
| `app/messaging/envelope.py` | `RequestEnvelope`, `ReplyNames`(:33), `envelope_reject_reason` | reply.resultKey 가 `ai-file:result:<correlationId>`, channel 이 `ai-file:reply:` 접두인지 — 임의 Redis 키 덮어쓰기 방지 |
| `app/messaging/attachment_consumers.py` | `_make_handler`(:107), `make_read_handler`(:225), `make_metadata_handler`(:250) | op 표: read→`perform_read`, source_read→`perform_source_read`, metadata→`perform_metadata` |
| `app/messaging/redis_publisher.py` | `RedisResultPublisher.publish`(:40) | `SETEX resultKey ttl body`(1회 재시도) → `PUBLISH reply_channel 알림` |
| `app/messaging/knowledge_consumers.py` | `make_knowledge_pull_handler`(:35) | 검증→claim→commit→**ack**→process_job |
| `app/domain/agent_knowledge/repository.py` | `claim_queued_job`(:267) | 한 문장 upsert+락+소유권 |
| `app/main.py` | `build_attachment_consumers`(:104), `build_knowledge_consumers`(:154), `_validate_dispatch`(:218) | SERVICE·dispatch_mode 게이트, queue 모드인데 rabbitmq/redis 미설정이면 기동 실패 |

**핵심 코드** `app/messaging/knowledge_consumers.py:101-153` (요지)
```python
async with session_factory() as session:
    try:
        acquired = await AgentKnowledgeRepository(session).claim_queued_job(
            knowledge_id=..., worker_id=worker_id, lock_ttl_seconds=lock_ttl_seconds,
            agent_id=..., company_uuid=..., user_id=...)      # 소유권까지 한 문장에서
        await session.commit()                                # ① 먼저 DB 에 '내가 잡았다'를 남기고
    except Exception:
        await message.nack(requeue=True)                      # claim 실패 → 즉시 재배달(상한은 delivery-limit)
        raise
    if not acquired:
        await message.ack(); return                           # 락 보유자 있음/삭제/소유권 불일치 → 버림
    await message.ack()                                       # ② 그 다음 ack. 이후 처리 시간은 브로커와 무관
    await AgentKnowledgeService(...).process_job(...)         # ③ 긴 처리(크래시 시 locked_until 만료→AI Home sweep)
```
claim SQL 핵심(`repository.py:299-350`): `INSERT INTO ai_agent_knowledge_indexing_job … SELECT … FROM ai_agent_knowledge k JOIN ai_agent a WHERE k.id=:knowledge_id AND k.agent_id=:agent_id AND a.company_uuid=:company_uuid AND a.user_id=:user_id AND a.status!='DELETED' AND k.deleted_at IS NULL … ON CONFLICT (knowledge_id) DO UPDATE SET locked_by=:worker_id, locked_until=now()+ttl … WHERE locked_until IS NULL OR locked_until < now()`

**데이터·설정**: 큐 `ai-file.req.read`, `ai-file.req.metadata`, `ai-file.req.knowledge`, DLQ `ai-file.req.dead`(DLX `ai-file.dlx`, 큐 선언 인자 소유는 AI Home), Redis 키 `ai-file:result:<correlationId>`(TTL `result_ttl_seconds`=180), 채널 `ai-file:reply:<host>-<8hex>`, 테이블 `ai_agent_knowledge_indexing_job`(locked_by/locked_until), 설정 `agent_knowledge_queue_lock_ttl_seconds`(300), `agent_knowledge_queue_poll_interval_seconds`(1.0), `dispatch_mode`(queue|local).

**왜 이렇게 짰나**: 처리 후 ack 이면 처리 시간이 브로커 `consumer_timeout`(30분)에 묶여 초과 시 채널 끊김→requeue→같은 knowledgeId 동시 실행. commit 전 ack 이면 DB·큐 어디에도 없는 유실. 그래서 "commit → ack" 순서가 계약. 소유권 검사를 claim 문장에 넣은 건 10-14 감사 #3(knowledgeId 만 맞춘 메시지로 타 테넌트 지식이 FAILED 로 바뀜). late 모드는 `ca7c737` 에서 삭제.

**면접 30초 설명**: "knowledge 컨슈머는 `queue.get`으로 슬롯이 빌 때만 한 건 꺼내는 풀 모델이고, `claim_queued_job` 한 문장으로 잡 행 upsert·락·소유권 검사를 한 뒤 commit하고 나서야 ack합니다. 그래서 긴 인덱싱이 브로커 타임아웃에 걸려 중복 실행되는 일이 없고, ack 후 죽으면 `locked_until` 만료를 보고 AI Home이 재발행합니다."

**헷갈리기 쉬운 점**: 첨부(read/metadata)는 **처리 후 ack + 결과를 Redis에**, knowledge 는 **처리 전 ack + 결과를 DB 상태로**. 재시도 오케스트레이션은 AI Home 소유(`a01bc5b` 로 ai-file 쪽 스케줄러 제거).

---

## ai-automation — 코드 워크스루

### 시퀀스 다이어그램 (예약 1건, tick → … → DLQ)

```
Java Batch     automation API                 Postgres            RabbitMQ                 Worker                         Redis                  AI Home
    │ POST /internal/schedules/tick (X-Internal-Secret)                                                                                            
    │──────────▶ internal_ticks.schedules_tick                                                                                                    
    │           authenticate→require_execution()                                                                                                    
    │           run_tick('schedule')→run_schedule_batches                                                                                           
    │           scheduler_service.create_due                                                                                                        
    │             select_due: row_number() over(partition by company_uuid) … FOR UPDATE SKIP LOCKED                                               
    │             INSERT ai_automation_execution(status=QUEUED, request_key=schedule:<sid>:<slot>) ON CONFLICT DO NOTHING                         
    │             UPDATE schedule.next_run_at ──────────▶ COMMIT                                                                                  
    │           (커밋 후, 회사 RR 순서로) start_publication.publish_start_outcome                                                                   
    │             load → start_kind=START → start_queue=automation.start                                                                         
    │             MqPublisher.publish (confirm) ─────────────────────▶ automation.start {v,execution_id,kind:START,generation}                  
    │             UPDATE start_published_gen=generation WHERE generation=…                                                                        
    │◀── 200 TickResult{processed,published,mayHaveMore,…}                                                                                       
    │                                                      │                     │ worker_runtime._work → start_consumer.handle_start            
    │                                                      │                     │ _Start.run: load, generation 비교                               
    │                                                      │                     │ _Start.admit: Slots.acquire(member="<id>:<gen>",SCHEDULED) ─▶ Lua _ACQUIRE
    │                                                      │                     │      FULL/RECONCILING → 3s±1 대기 반복 (ACK 안 함)       ◀─ NEW/EXISTING
    │                                                      │◀── transitions.start_running: UPDATE QUEUED→RUNNING WHERE generation=… ; insert_step(PENDING, requestId=auto-<id>-<step>-a1)
    │                                                      │                     │ consumer_common.hand_off: Slots.ensure ──────────────────▶ _ENSURE
    │                                                      │                     │ handoff.ensure_handoff: POST /internal/automation/v1/step-runs ─────────────────▶ accept()
    │                                                      │                     │                                                     (같은 requestId면 기존 결과, PENDING→RUNNING 커밋 후 task spawn)
    │                                                      │                     │ ◀────────────────────────────────────────────────────────────────── 202
    │                                                      │                     │ message.ack()                                                       
    │                                                      │                     │                                                     execute → commit_result(step SUCCEEDED)
    │           callbacks.complete_step ◀──────────────────────────────────────────────────────────── POST /internal/automation/v1/executions/{id}/steps/{stepId}/complete
    │           notifications.notify_step_result: step 상태·current_request_id 확인                                                                 
    │             publish ─────────────────────────────────────────────▶ automation.continue {kind:RESULT, request_id, generation}            
    │             UPDATE step.notified_gen=generation                                                                                             
    │                                                      │                     │ continue_consumer.handle_continue → process                    
    │                                                      │                     │  generation·current_request_id 확인 → on_succeeded              
    │                                                      │◀── advance(다음 step PENDING)          │ → hand_off_current → ensure_handoff … (반복)          
    │                                                      │◀── 마지막 step: finish(SUCCEEDED) → finish_and_release → Slots.release(ZREM) ─▶            
    │
    │  실패 경로:
    │   step-runs 5xx/429/네트워크 → handoff.schedule_retry: dispatch_attempts CAS +1 → publish_delayed ─▶ automation.retry.{2,10,30,60}s
    │        (TTL 만료) ─▶ DLX automation.direct, 원래 routing key ─▶ automation.continue {kind:CALL_RETRY} ─▶ 다시 ensure_handoff
    │   핸들러 예외(인프라 외) → message.reject(requeue=True) … x-delivery-limit 10 초과 ─▶ automation.dlx ─▶ automation.dlq
    │   dead_letters.handle_dead_letter: x-death[0].queue 로 원래 큐 찾기 → 60s 지연 재발행(x-automation-dlq-cycles+1)
    │        3회 초과/파싱 불가/원 큐 없음 ─▶ automation.parked (운영자)
    │   안전망: POST /internal/executions/recover-tick → recovery h→e→f→a→b→d→g
    │        (a) start_published_gen≠generation 재발행, (b) notified_gen≠generation 재통지, (f) Redis↔DB 슬롯 대조/재구성 …
```

### 전체 코드 지도

```
src/automation/
  entrypoints/{api,worker,scheduler}.py   # 프로세스 3종 진입
  api.py                 # 사용자 API: POST /automation/v1/workflows/{id}/executions (수동 실행), /executions/{id}/resume
  internal_ticks.py      # POST /internal/schedules/tick, /internal/executions/recover-tick, GET …/ticks/status   [내 재작성]
  scheduler_service.py   # select_due(회사 RR), create_due(커밋 후 발행), 로컬 Scheduler 루프                   [RR·발행 내 코드]
  start_publication.py   # publish_start_outcome: 커밋된 실행의 start 발행 + start_published_gen 기록           [내 코드]
  mq.py                  # 큐 토폴로지 declare_topology, MqPublisher(confirm, mandatory)                       [내 코드]
  messages.py            # StartMessage / ContinueMessage (v, execution_id, generation …)                     [내 코드]
  slots.py               # Redis 슬롯 Lua (_LIMIT/_ACQUIRE/_ENSURE/_RECONCILE)                                 [내 코드, __ready__ 는 타인]
  start_consumer.py      # _Start.run/admit/hand_off/drop_new_member                                          [내 코드, admission fence 는 타인]
  continue_consumer.py   # process / on_succeeded / validate_step_output                                      [내 코드]
  consumer_common.py     # run_retrying, hand_off, finish_and_release, INFRA_ERRORS                           [내 코드]
  handoff.py             # ensure_handoff, classify, schedule_retry, exhausted_outcome                        [내 코드]
  transitions.py         # 조건부 UPDATE 전이: start_running, insert_step, advance, finish …                  [11093bf 로 추출]
  step_requests.py       # build_step_request: requestId = auto-<executionId>-<stepId>-a<attempt>
  callbacks.py           # POST /internal/automation/v1/executions/{id}/steps/{stepId}/complete               [내 코드]
  notifications.py       # notify_step_result (콜백·tick(b) 공용)                                             [내 코드]
  dead_letters.py        # DLQ: 60초 후 원 큐로 / parked                                                      [내 코드]
  worker_runtime.py      # 컨슈머 연결·채널·prefetch, ACK/PARK/RELEASE 처리, 셧다운                           [내 코드]
  recovery.py            # recover-tick 항목 a,b,d,e,f,g,h                                                   [내 재작성]
  availability.py        # EXECUTION_ENABLED 게이트 execution_capability/require_execution                    [타인, springfefe]
  admission_fence.py     # PG advisory lock 접수(공유)/재구성(배타)                                           [타인, 20a11cd]
  fault.py               # fault_point(name) — local 에서만 env 로 주입                                        [내 코드]
```
AI Home 쪽 (`ai-home-poc/app/modules/domain/ai_home/automation/`): `api.py`(step-runs 라우터, 429/503 헤더), `step_run_service.py`(`accept`, `reserve`, `commit_result`→`callback.schedule`), `completion_callback.py`, `pod_registry.py`, `task_lifecycle.py`.

**프로세스별 역할**: API(사용자 API + 내부 tick + 콜백 수신, 자체 `MqPublisher`·`Slots`), Worker(4개 컨슈머: start 4·interactive 4·continue 60·dlq 10), Scheduler(로컬 전용 `database_loop`; 운영은 Java Batch 가 tick API 호출).

---

### 1. 큐 토폴로지와 커밋 후 발행 (2026-10-29 · `7c43f9d` `d428b91` `4c773d4` `cacc787` `2e0f39b`)

**내가 한 범위**: 큐 선언·퍼블리셔·메시지 모델·커밋 후 발행·회사 RR 정렬 전부. 기존 tick 인증/배치 골격(`50f94ad`)과 `create_due` 의 초기 형태는 springfefe. 머지 후 springfefe 가 `create_due` 에 승인 만료 처리(`expire_waiting`, deferred)를 추가(`021d59b`).

**코드 지도**
| 파일 | 함수 | 역할 |
|---|---|---|
| `mq.py` | `names()`(:54), `declare_topology`(:68), `MqPublisher._channel/_send/publish/publish_delayed`(:105~) | 큐·익스체인지 선언, confirm 발행 |
| `scheduler_service.py` | `select_due`(:20), `create_due`(:39) | 회사 RR 선택 → INSERT → 커밋 → 순서대로 발행 |
| `start_publication.py` | `start_kind`, `start_queue`, `publish_start_outcome`(:47) | DB 다시 읽어 큐 결정, 발행, `start_published_gen` 기록 |
| `api.py` | `execute`(:319) | 수동 실행: `repo.run_manual` 커밋 → `publish_start` (실패해도 202) |
| `internal_ticks.py` | `schedules_tick`, `run_schedule_batches`(:61) | 최대 `internal_tick_max_batches` 배치, 발행 실패 시 즉시 종료 |

**핵심 코드** `mq.py:68-91`
```python
async def declare_topology(channel) -> None:
    ns = settings.mq_namespace                                   # 기본 'automation'
    direct = await channel.declare_exchange(ns + '.direct', DIRECT, durable=True)
    dlx    = await channel.declare_exchange(ns + '.dlx', DIRECT, durable=True)
    work = {"x-queue-type": "quorum", "x-delivery-limit": DELIVERY_LIMIT,     # 10회 재전달 후 DLX
            "x-dead-letter-exchange": ns + '.dlx', "x-dead-letter-strategy": "at-least-once",
            "x-overflow": "reject-publish"}                        # 꽉 차면 발행 거절(조용히 버리지 않음)
    ...
    for name, extra in ((n.start, {"x-consumer-timeout": CONSUMER_TIMEOUT_MS}),      # 슬롯 대기 동안 unacked 로 쥠
                        (n.interactive, {"x-consumer-timeout": CONSUMER_TIMEOUT_MS}), (n.continue_, {})):
        queue = await channel.declare_queue(name, durable=True, arguments={**work, **extra})
        await queue.bind(direct, name); await dlq.bind(dlx, name)
    for tier, name in n.retry.items():                            # 2,10,30,60초 지연 큐
        fanout = await channel.declare_exchange(f'{ns}.retry.{tier}', FANOUT, durable=True)
        queue = await channel.declare_queue(name, durable=True, arguments={
            "x-queue-type": "quorum", "x-message-ttl": tier * 1000,
            "x-dead-letter-exchange": ns + '.direct', ...})       # TTL 지나면 direct 로, 원래 routing key 유지
        await queue.bind(fanout)
```
`start_publication.py:47-72`
```python
async def publish_start_outcome(publisher, execution_id) -> StartOutcome:
    try:
        async with asyncio.timeout(settings.publish_timeout_seconds):        # 기본 2초
            execution, step = await load(execution_id)                       # 호출자 말고 DB 상태로 결정
            kind = start_kind(execution, step)                               # QUEUED→START, 승인재개 대기→RESUME
            generation = execution['generation']
            if kind is None or execution['start_published_gen'] == generation:
                return 'SKIPPED'                                             # 이미 이 세대 발행됨
            await publisher.publish(start_queue(execution, kind),            # 예약 첫 시작만 start, 나머지 interactive
                StartMessage(v=1, execution_id=execution['id'], kind=kind, generation=generation))
        async with sessions.begin() as db:                                   # confirm 받은 뒤 기록
            recorded = await db.execute(update(E).where(E.c.id == execution['id'], E.c.generation == generation)
                                        .values(start_published_gen=generation))
        return 'PUBLISHED' if recorded.rowcount == 1 else 'UNRECORDED'
    except Exception:
        log.exception('start publication deferred to tick id=%s', execution_id)
        return 'FAILED'                                                      # 절대 raise 안 함 → tick(a)가 회수
```
회사 RR `scheduler_service.py:26`: `row_number().over(partition_by=W.c.company_uuid, order_by=(S.c.next_run_at, S.c.id))` → 바깥 `ORDER BY rn, next_run_at, id LIMIT batch` → `FOR UPDATE OF workflow SKIP LOCKED`. INSERT 의 `RETURNING request_key, id` 를 dict 로 받아 **선택 순서대로** 발행(`order = [created[e['request_key']] …]`).

**데이터·설정**
- 익스체인지: `automation.direct`, `automation.dlx`, `automation.retry.{2,10,30,60}`(fanout)
- 큐: `automation.start`, `automation.start.interactive`, `automation.continue`, `automation.retry.{2,10,30,60}s`, `automation.dlq`, `automation.parked`
- 컬럼: `ai_automation_execution.generation`, `start_published_gen`, `queued_at`, `request_key`(`schedule:<scheduleId>:<slotISO>`, unique)
- 설정(`AUTOMATION_` 접두): `MQ_NAMESPACE`, `PUBLISH_TIMEOUT_SECONDS`(2), `SCHEDULE_BATCH_SIZE`(100), `INTERNAL_TICK_MAX_BATCHES`(100), `INTERNAL_TICK_BUDGET_SECONDS`(10), `UNPUBLISHED_GRACE_SECONDS`(30)
- 상수: `START_CONSUMER_TIMEOUT_MS = 5400000`(90분), `DELIVERY_LIMIT = 10`, `RETRY_TIERS = (2,10,30,60)`

**왜 이렇게 짰나**: 커밋 전 발행 → Worker 가 없는 행/롤백된 행을 읽음. 별도 outbox 테이블 대신 실행 행의 `start_published_gen` 하나가 "미발행" 표시(이전 구조의 outbox+리더 publisher 제거, `b25097a`). 발행 실패 시 그 tick 은 바로 멈춤(`2e0f39b`) — 과부하 브로커에 재시도 증폭 금지, 나머지는 tick(a). 회사/사용자 동시 실행 한도(DB COUNT)는 없애고(D8) 예약 발행 순서로만 공정성(D13). 사람이 누른 작업은 interactive 큐로 분리(D17).

**바뀌어 온 이력**: `7c43f9d`(컬럼·설정) → `d428b91`(토폴로지·confirm 퍼블리셔) → `4c773d4`(커밋 후 발행) → `cacc787`(회사 RR) → `2e0f39b`(발행 실패 후 즉시 재스캔 금지) → `b25097a`(DB 디스패치 경로·마이그레이션 010 제거) → `dec9a6f`(start 발행 결과 정확히 보고: UNRECORDED 등)

**면접 30초 설명**: "실행은 먼저 DB에 QUEUED로 커밋하고, 커밋이 끝난 다음 `publish_start_outcome`이 DB를 다시 읽어 `automation.start` 또는 `start.interactive`에 confirm 발행한 뒤 `start_published_gen`을 기록합니다. 발행이 실패해도 사용자에겐 202를 주고, recover-tick (a)가 `start_published_gen`이 `generation`보다 뒤처진 행을 다시 발행합니다. 예약은 `row_number() over (partition by company_uuid)`로 회사별로 번갈아 뽑아 그 순서대로 발행합니다."

**헷갈리기 쉬운 점**
- 지연 재시도 큐는 **fanout 익스체인지 + TTL + DLX=direct**. routing key 를 원래 큐 이름으로 보내 두면 TTL 만료 후 direct 가 원래 큐로 돌려준다.
- `x-consumer-timeout` 은 start 두 큐에만(90분). `queue_timeout_seconds`(60분)가 그보다 600초 이상 작아야 기동(`config.validate_profile`).
- 회사 RR 은 **예약 tick 배치 안에서만**. 발행 후엔 FIFO, 수동 실행 폭주는 못 막음.

---

### 2. Worker 의 start 처리와 Redis 전역 슬롯 (2026-10-29 · `566b698` `b816e96` `9106149`)

**내가 한 범위**: Lua 스크립트 4개, `Slots` 클래스, `_Start` 상태기계(획득·전이·소유자 반납), epoch 키. **머지 후 springfefe(`20a11cd`, 11-02)가 바꾼 것**: `__ready__` 마커 추가(epoch 키만으론 부분 재구성 감지 불가), `ZCARD - 1`(마커 보정), `admit()` 에 admission fence(PG advisory lock) 안에서 재획득+전이를 같은 트랜잭션으로, `reconcile_slots` 를 fence 아래로.

**코드 지도**
| 파일 | 함수 | 역할 |
|---|---|---|
| `slots.py` | `_LIMIT`, `_ACQUIRE`, `_ENSURE`, `_RECONCILE`, `_CAPACITY`, `keys()`, `slot_member()`, `Slots.acquire/ensure/release/reconcile/epoch_present` | 전역 세마포어 |
| `start_consumer.py` | `handle_start`(:141), `_Start.run`(:55), `admit`(:85), `drop_new_member`(:50), `on_stop`(:134) | 세대 검사 → 슬롯 대기 → 조건부 전이 → handoff |
| `transitions.py` | `start_running`(:65~), `insert_step`(:55) | `UPDATE … WHERE id AND generation AND status=QUEUED` + 첫 step PENDING INSERT + `slot_expires_at` 고정 |
| `consumer_common.py` | `run_retrying`(:75), `provisional_expiry`(:96), `release_quietly`(:103) | 인프라 오류만 5초 후 처음부터 재시도 |
| AI Home `pod_registry.py` | `PodRegistry.beat` | `{ns}:aihome:pods` ZSET 에 파드명, score=now+30s, 10초마다 |

**흐름**: `worker_runtime._work` → `handle_start(body, queue_kind)` → `parse_start`(실패 시 PARK) → `run_retrying(_Start.run)` → `load` → 터미널/구세대면 ACK → `RUNNING` 이면 바로 `hand_off` → 아니면 `admit`: 기한 확인(`queued_at + queue_timeout_seconds`, 넘으면 `expire_queued`) → `Slots.acquire` → FULL/RECONCILING 이면 `_slot_wait()`(3초±1) → NEW/EXISTING 이면 `start_running` → STARTED/ALREADY_RUNNING 이면 다시 `run` 루프 → `hand_off`.

**핵심 코드** `slots.py:14-35` (Lua)
```lua
-- _LIMIT: 살아있는 AI Home 파드 수 × K 를 [MIN, MAX] 로 자른다
local now = tonumber(ARGV[1])
redis.call('ZREMRANGEBYSCORE', KEYS[2], '-inf', now)           -- 만료된 파드 제거 ({ns}:aihome:pods)
local limit = redis.call('ZCARD', KEYS[2]) * tonumber(ARGV[2])
if limit < lo then limit = lo end ; if limit > hi then limit = hi end

-- _ACQUIRE
if redis.call('EXISTS', KEYS[3]) == 0 or not redis.call('ZSCORE', KEYS[1], '__ready__')
  then return 'RECONCILING' end                                 -- epoch 키/마커 없음 = Redis 유실 → DB 로 재구성 전까지 거절
redis.call('ZREMRANGEBYSCORE', KEYS[1], '-inf', ARGV[1])        -- 만료 슬롯 회수(Worker 가 죽어도 자동 반환)
if redis.call('ZSCORE', KEYS[1], ARGV[5]) then return 'EXISTING' end   -- 같은 실행:세대 이미 있음(재전달 등)
local cap = limit
if ARGV[7] == 'SCHEDULED' then cap = math.floor(limit * tonumber(ARGV[8]) + 1e-9) end   -- 예약은 90%까지
if redis.call('ZCARD', KEYS[1]) - 1 < cap then                  -- -1 = __ready__ 마커 (머지 후 보정)
  redis.call('ZADD', KEYS[1], ARGV[6], ARGV[5]) ; return 'NEW'  -- score = 만료 시각(deadline+120s)
end
return 'FULL'
```
`start_consumer.py:41-53, 117-127` (소유자만 반납)
```python
class _Start:
    """One delivery. `acquired` survives retries so a NEW member is released only by its owner."""
    def __init__(self, message, deps, stop, queue_kind):
        self.member = slot_member(message.execution_id, message.generation)   # "<executionId>:<generation>"
        self.acquired: str | None = None        # 이 처리에서 처음 받은 결과(NEW/EXISTING)를 재시도 동안 유지
        self.transitioned = False

    async def drop_new_member(self) -> None:
        if self.acquired == 'NEW':              # 내가 ZADD 한 경우만 ZREM
            await _release_quietly(self.deps.slots, self.member)
            self.acquired = None
    ...
        # (admit 끝) FAILED/NOT_RUNNABLE: 전이 못 함
        # EXISTING 은 다른 처리자(이미 RUNNING 시킨 동료)의 멤버일 수 있으니 건드리지 않음 → tick(f) 대조에 맡김
        await self.drop_new_member()
        return 'ACK'
```
내가 머지한 시점의 `admit`(c7b295b)은 "슬롯 루프 → `start_running`" 두 단계였고, 현재 코드는 springfefe 가 `async with sessions.begin() as db: await admission(db); acquire 재확인; start_running(db=db)` 로 바꿈.

**데이터·설정**
- Redis 키(전부 `{ns}` 해시태그 → Cluster 단일 슬롯에서 Lua 실행): `{automation}:slots`(ZSET, 멤버 `executionId:generation`, score 만료 epoch초), `{automation}:aihome:pods`(ZSET, AI Home 이 갱신), `{automation}:epoch`(STRING)
- DB: `execution.slot_expires_at`(= run_deadline + `lease_grace_seconds` 120s, `start_running` 에서 1회 고정), `queued_at`
- 설정: `SLOT_K`=8, `SLOT_MIN`=4, `SLOT_MAX`=300(측정 전 보수값), `SCHEDULED_SLOT_RATIO`=0.9, `SLOT_RETRY_SECONDS`=3, `QUEUE_TIMEOUT_SECONDS`=3600, `REDIS_CLUSTER`, `START_PREFETCH`=4

**왜 이렇게 짰나**
- 실제 병목은 AI Home → 상한을 AI Home 파드 수에 비례(D11). 파드는 AI Home 이 직접 등록(만료 score) → Prometheus 지표는 제어 경로에 안 넣음(D4).
- 슬롯 없을 때 "쥐고 대기"(D12): ACK 하지 않고 Redis 만 3초 간격으로 다시 봄(DB 잠금 쿼리 반복 금지). 그래서 start 큐 `x-consumer-timeout` 과 설정 검증이 필요.
- 소유자만 반납: EXISTING 은 재전달·중복 메시지에서 나온다 → 그 멤버는 이미 RUNNING 실행 것일 수 있다.
- epoch: Redis 가 비워지면(재시작·failover) 실행 중인 슬롯을 모르고 새로 내줄 위험 → epoch 없으면 RECONCILING 으로 막고 tick(f) 가 DB 의 RUNNING 으로 재구성(`_RECONCILE` 은 `ZADD NX` 로 기존 score 보존, `b816e96`).
- K < AI Home 프로세스별 상한 C (초기 K≈C/1.5) — 슬롯 통과 후 AI Home 429 를 줄임.

**바뀌어 온 이력**: `566b698`(슬롯·Lua) → `b816e96`(ensure/reconcile 가 기존 score 덮지 않게 NX) → `9106149`(start 핸들러) → `ecea2ce`(Cluster failover 오류도 인프라 재시도) → [머지 후 타인] `20a11cd`(`__ready__`, admission fence)

**면접 30초 설명**: "Worker는 start 메시지를 받으면 `_Start.admit`에서 Redis Lua `_ACQUIRE`로 `실행ID:세대` 멤버를 ZSET에 넣습니다. Lua 안에서 만료 슬롯을 먼저 지우고, AI Home이 등록한 살아있는 파드 수 × K를 MIN~MAX로 잘라 상한으로 쓰고, 예약은 그 90%까지만 받습니다. 꽉 차면 ACK하지 않고 3초 간격으로 다시 보고, 전이가 실패하면 이번 처리에서 NEW로 직접 넣은 멤버만 지웁니다. epoch 키가 없으면 RECONCILING을 돌려 DB 기준 재구성 전엔 슬롯을 안 내줍니다."

**헷갈리기 쉬운 점**
- `__ready__` 마커·admission fence 는 **내 코드 아님**(이전 조사에서 내 것처럼 적혀 있었음).
- 슬롯 만료 score 는 획득 시 "임시값"(`provisional_expiry`) → 전이 후 DB `slot_expires_at` 이 정본. `hand_off` 에서 `Slots.ensure` 로 다시 넣는다(실패해도 진행, tick(f) 가 채움).
- EXISTING 이 반드시 "내 것"은 아니다. "소유자만 반납" = 정확히는 "이 delivery 가 NEW 로 넣은 경우만 ZREM".

---

### 3. 멱등 handoff (requestId) 와 재시도 분류 (2026-10-29 · `11093bf` `198155f` `ada3581` `9bbbdff` `d971316`)

**내가 한 범위**: `handoff.py` 전체, `transitions.py` 추출. **멱등의 근거인 AI Home `accept()`(같은 requestId → 기존 결과 반환, 본문 다르면 409)는 springfefe 의 `f28ee0a0`(10-14)**. 나는 AI Home 에 프로세스별 상한(`reserve()`→429, `1feec7af`)과 완료 콜백(`c51ac38e`)을 추가.

**코드 지도**
| 파일 | 함수 | 역할 |
|---|---|---|
| `step_requests.py` | `build_step_request`(:54) | `requestId = f"auto-{executionId}-{stepId}-a{attempt}"`, 본문을 step 행에 저장 |
| `transitions.py` | `insert_step` | step 행 `status='PENDING'`, `request_hash`, `request_payload` 저장 + `current_request_id` 포인터 이동 |
| `handoff.py` | `ensure_handoff`(:84), `classify`(:69), `schedule_retry`(:123), `exhausted_outcome`(:171) | PENDING 일 때만 POST 1회, 결과 Accepted/Retry/Rejected |
| `consumer_common.py` | `hand_off`(:126) | ensure 슬롯 → ensure_handoff → 결과별 ACK/실패/지연 재시도 |
| AI Home `step_run_service.py` | `accept`(:207), `reserve`(:167), `accepted`(:112) | 행 잠금 → 해시 비교 → PENDING 아니면 기존 결과 → 슬롯 예약 → RUNNING 커밋 → spawn |

**핵심 코드** `handoff.py:84-120`
```python
async def ensure_handoff(execution, step, agent) -> HandoffResult:
    if step is None:
        return Rejected('INCONSISTENT_AGENT_STATE')
    if step['status'] != 'PENDING' and step['resume_status'] != 'PENDING':
        return Accepted()                     # AI Home 이 이미 받음(접수와 같은 트랜잭션에서 RUNNING) → HTTP 불필요
    remaining = (execution['run_deadline_at'] - now()).total_seconds()
    if remaining <= 0:
        return Rejected('DEADLINE_EXCEEDED')  # 미접수 확정이라 실패 처리해도 AI Home 에서 도는 것 없음(D21)
    headers = execution_headers(execution)    # 인증 제공자 없으면 RuntimeError → Rejected
    if step['status'] == 'PENDING':
        path, body = STEP_RUNS, step['request_payload']          # 항상 '저장된' 본문 = 같은 requestId 재호출
    else:
        path, body = f"{STEP_RUNS}/{step['request_id']}/resume", resume_body(execution, step)
    budget = min(CALL_SECONDS, remaining)                        # 15초 or 남은 기한
    try:
        async with asyncio.timeout(budget):
            data = await agent.call('POST', path, headers, body, httpx.Timeout(budget, connect=...))
        fault_point('after_http_response')
        agent.step_result(data, step['request_payload'])         # 응답 identity 검증
    except httpx.HTTPStatusError as exc:
        return classify(exc.response, step)   # 429 CAPACITY_FULL/503 DRAINING = 횟수 미포함, 5xx/429 = 횟수 포함, 404 = 불일치
    except (httpx.RequestError, TimeoutError):
        return Retry(counted_delay(step), counted=True)
    return Accepted()
```
`schedule_retry`(:140-156): counted 면 `UPDATE step SET dispatch_attempts=n+1 WHERE id AND dispatch_attempts=n`(CAS, 0행이면 `DUPLICATE`), n≥4 면 `EXHAUSTED` → `ContinueMessage(kind='CALL_RETRY')` 를 `publish_delayed(automation.continue, delay≤60)`.

AI Home `step_run_service.accept` 요지(:216-247): `row(…, lock=True)` → `digest(request) != row.request_hash` 면 `409 REQUEST_PAYLOAD_CONFLICT` → `row.status != 'PENDING'` 면 `return self.accepted(row)`(멱등, 용량 검사 안 함) → `reserve()`(가득 차면 DB 안 건드리고 `429 AUTOMATION_CAPACITY_FULL`, `Retry-After: 2`, `Connection: close`) → thread/run 생성, `UPDATE step SET status='RUNNING', agent_claim_token, agent_lease_expires_at=now+60s` → 커밋 후 `slot.spawn(self.execute(...))`.

**데이터·설정**: 엔드포인트 `POST /internal/automation/v1/step-runs`, `POST …/step-runs/{requestId}/resume`; step 행 컬럼 `request_id`, `request_hash`, `request_payload`, `status`, `resume_status`, `dispatch_attempts`, `agent_lease_expires_at`; 상수 `R4_DELAYS=(2,10,30,60)`, `CALL_SECONDS=15`, `CONNECT_SECONDS=3`, `UNCOUNTED={(429,'AUTOMATION_CAPACITY_FULL'),(503,'AUTOMATION_DRAINING')}`.

**왜 이렇게 짰나**: "상태 저장 시점"과 "다음 서비스에 넘긴 시점"을 분리 — step 행 `PENDING` = AI Home 미접수가 보장(AI Home 이 접수와 같은 트랜잭션에서 RUNNING 으로 바꾼 뒤에만 task 를 띄움, D21). 그래서 모든 메시지 처리의 마지막을 `ensure_handoff` 로 통일하면 Worker 가 어느 지점에서 죽어도 재전달 시 "남은 넘김만" 한다. 재시도 횟수는 메시지 헤더가 아니라 행의 `dispatch_attempts`(재전달돼도 일관). AI Home 용량 거절은 횟수에서 빼고 `Connection: close` 로 다른 파드에 붙게. Retry-After 가 길어도 60초로 자름 — tick(g) 의 정체 판정(180초)을 넘으면 두 번째 재시도 체인이 생김(`d971316`).

**면접 30초 설명**: "step을 넘기기 전에 requestId와 요청 본문을 step 행에 PENDING으로 먼저 저장하고, 넘김은 `ensure_handoff`가 항상 저장된 본문으로 같은 requestId를 POST합니다. AI Home `accept()`는 같은 requestId면 기존 결과를 돌려주고 본문이 다르면 409라서, Worker가 여러 번 재호출해도 한 번만 실행됩니다. 실패는 `classify`가 횟수 포함/미포함으로 나누고, `dispatch_attempts`를 CAS로 올린 뒤 지연 큐로 CALL_RETRY를 보냅니다."

**헷갈리기 쉬운 점**: 멱등성 자체(accept 의 dedupe)는 AI Home 쪽 기존 코드. 내 기여는 "그걸 근거로 Worker 쪽을 PENDING 판정 + 저장 본문 재호출 구조로 짠 것". 새 attempt(`-a2`)는 handoff 가 만들지 않는다 — 정상 종료로 선점된 step(`STEP_PREEMPTED`)만 `on_preempted` 에서.

---

### 4. 완료 콜백 → continue → 다음 step, generation 검사 (2026-10-29 · `72f559c` `36b7206` `7c43f9d` / AI Home `c51ac38e`)

**내가 한 범위**: 콜백 수신 API, `notify_step_result`, continue 컨슈머, generation 컬럼과 모든 비교. AI Home 쪽 `CompletionCallback` 과 `commit_result` 의 호출부.

**코드 지도**
| 파일 | 함수 | 역할 |
|---|---|---|
| AI Home `step_run_service.py` | `commit_result`(:638) → `self.callback.schedule(...)`(:681) | 결과 커밋 **후**, 기다리지 않고 콜백 예약 |
| AI Home `completion_callback.py` | `CompletionCallback.send`(:56) | `X-Internal-Secret` 헤더, 지연 (1,3,10)초 재시도, 401 은 재시도 안 함 |
| `callbacks.py` | `complete_step`(:31), `authenticate_callback`(:16) | 비밀값 hmac 비교 → `notify_step_result` → 200/404/409/503 |
| `notifications.py` | `notify_step_result`(:33), `record_notified`(:27) | DB 에서 결과 상태 읽고 continue 발행, `notified_gen` 기록 |
| `continue_consumer.py` | `handle_continue`(:124), `process`(:94), `on_succeeded`(:71) | 세대·requestId 확인 → 상태별 분기 → 다음 step |
| `consumer_common.py` | `finish_and_release`(:110), `hand_off_current`(:153) | 종료 전이 + 슬롯 반납, 남은 handoff |

**핵심 코드** `continue_consumer.py:94-121`
```python
async def process(message: ContinueMessage, deps: Deps) -> Outcome:
    execution, step = await load(message.execution_id)           # 매 시도마다 DB 재조회
    if execution is None:
        return 'ACK'
    if execution['status'] != 'RUNNING' or execution['generation'] != message.generation:
        return 'ACK'                     # 끝났거나 승인대기거나 '다른 세대'의 늦은 메시지 → 버림
    if execution['current_request_id'] != message.request_id:
        return await hand_off(deps, execution, step)   # 옛 step 의 결과는 반영 안 하고 현재 step 넘김만
    if execution['run_deadline_at'] <= now():
        await finish_and_release(deps, execution, step, 'FAILED', 'DEADLINE_EXCEEDED')
    elif step is None or step['status'] == 'PENDING' or step['resume_status'] == 'PENDING':
        return await hand_off(deps, execution, step)
    elif step['status'] == 'RUNNING':
        if holds_live_agent(step, now()):
            return await hand_off(deps, execution, step)   # 결과는 콜백으로 옴
        await on_lease_expired(deps, execution, step)
    elif step['status'] in ('SUCCEEDED', 'SKIPPED'):      # SKIPPED 는 머지 후 static step 지원으로 추가(타인)
        await on_succeeded(deps, execution, step)          # 출력 검증 → advance(다음 step PENDING) 또는 SUCCEEDED
    elif step['status'] == 'WAITING_APPROVAL':
        await finish_and_release(deps, execution, step, 'WAITING_APPROVAL')
    elif step['status'] == 'FAILED' and step['error_code'] == 'STEP_PREEMPTED':
        return await on_preempted(deps, execution, step)
    elif step['status'] == 'FAILED':
        await finish_and_release(deps, execution, step, 'FAILED', ...)
    return await hand_off_current(deps, execution['id'], execution['generation'])   # 마지막은 항상 handoff 보장
```
`notifications.py:46-62` 요지: `execution.status != RUNNING or current_request_id != request_id` → `STALE` / `step.notified_gen == generation` → `ALREADY` / 아니면 `publish(automation.continue, kind='RESULT', generation)` (timeout 2s) → `record_notified`(실패해도 PUBLISHED; 중복 continue 1번은 Worker 가 흡수).

`consumer_common.finish_and_release`(:110-123): `finish(id, generation, request_id, status)` 조건부 UPDATE 가 0행이면 False(다른 처리자가 전이 → 반납 결정도 그쪽) → 다시 읽어 `holds_live_agent` 가 아니면 `release_quietly(slot_member(id, generation))`.

**데이터·설정**: 엔드포인트 `POST /internal/automation/v1/executions/{execution_id}/steps/{step_id}/complete`(body `requestId`), 헤더 `X-Internal-Secret`(Java tick 키와 **다른** 비밀값, Secret `ai-automation-callback`), 설정 `AUTOMATION_CALLBACK_ENABLED`(기본 false), `NOTIFY_GRACE_SECONDS`(30), `CONTINUE_PREFETCH`(60); 컬럼 `execution.generation`, `current_request_id`, `run_deadline_at`, step `notified_gen`; 메시지 `ContinueMessage{v, execution_id, step_id, request_id, generation, kind: RESULT|CALL_RETRY|LEASE_EXPIRED}`.

**왜 이렇게 짰나**: AI Home 은 MQ 연결이 없음 → 큐를 몰라도 되게 HTTP 콜백(D2), 결과는 DB 에 있고 콜백은 "깨우기 신호"일 뿐(D3) → 콜백 유실은 tick(b)(`notified_gen ≠ generation`, 30초 경과)가 회수. generation 이 필요한 이유: 승인 재개는 **같은 step 행·같은 requestId** 를 재사용하므로 requestId 만으론 이전 실행분의 늦은 메시지와 구분 불가(D20). 그래서 start/continue 메시지·슬롯 멤버·`start_published_gen`·`notified_gen` 모두 세대를 가진다.

**면접 30초 설명**: "AI Home은 step 결과를 커밋한 다음 기다리지 않고 completion 콜백을 보냅니다. automation API는 결과를 콜백 본문이 아니라 DB에서 읽어 `automation.continue`에 발행하고 `notified_gen`을 기록합니다. continue 컨슈머는 메시지 세대가 현재 세대와 다르면 바로 ACK, requestId가 현재 step이 아니면 결과는 반영하지 않고 현재 step 넘김만 하고, 성공이면 `advance`로 다음 step을 PENDING으로 만든 뒤 마지막에 항상 `hand_off_current`로 넘깁니다."

**헷갈리기 쉬운 점**: 콜백 API 는 **발행만** 하고 상태를 바꾸지 않는다(상태 전이는 Worker). 콜백 실패(503 NOTIFICATION_DEFERRED)는 AI Home 재시도 + tick(b) 이중 안전망. 늦은 continue 가 다른 step 을 가리켜도 버리지 않고 "현재 step handoff" 를 한다.

---

### 5. DLQ / parked 와 Worker 런타임 (2026-10-29 · `6d2fca4` `60f66bc`)

**코드 지도**
| 파일 | 함수 | 역할 |
|---|---|---|
| `worker_runtime.py` | `_consumers`(:133), `_work`(:97), `_guarded`(:80), `_dead_letters`(:112) | 큐별 채널·prefetch, outcome → ack/park/release, 비인프라 예외 → `reject(requeue=True)` |
| `dead_letters.py` | `handle_dead_letter`(:62), `_original_queue`(:45), `park`(:29) | `x-death[0].queue` 로 원 큐 확인 → 60초 지연 재발행 / parked |

**핵심 코드** `worker_runtime.py:80-109` 요지
```python
async def _guarded(queue_name, message, step):
    try:
        await step()
    except Exception as exc:
        if _retryable(exc):          # 연결 계열 → unacked 로 두고 채널 복구에 맡김
            return
        await message.reject(requeue=True)   # 버그·포이즌 → requeue. quorum delivery-limit(10) 넘으면 DLX → DLQ

def _work(queue_name, deps, handle):
    async def process(message, stop):
        async def step():
            outcome = await handle(message.body, stop)          # 'ACK' | 'PARK' | 'RELEASE'
            if outcome == 'PARK':
                await _retrying(lambda: park(deps.publisher, message), ...)   # confirm 복사 후
            if outcome in ('ACK', 'PARK'):
                await message.ack()
            # RELEASE: ack도 nack도 안 함 → 셧다운 시 채널 닫히며 브로커가 재전달
        await _guarded(queue_name, message, step)
    return process
```
`dead_letters.py:71-84`: reason = `unparseable` / `no origin` / `bad cycles` / `cycles exhausted`(≥ `dlq_max_cycles`=3) → parked(헤더 `x-automation-park-reason`, `x-automation-original-queue`), 아니면 `publish_delayed_raw(origin, body, 60, headers={…, 'x-automation-dlq-cycles': n+1})`. `x-death` 는 브로커 헤더라 재발행에서 뺀다. confirm 후에만 ack.

**왜**: 즉시 재큐잉 루프 대신 고정 TTL 지연 큐. DLQ 컨슈머는 "판단하지 않는다" — 되돌리거나 격리만. DLQ 자체엔 delivery-limit/DLX 가 없어 reject 하면 핫루프/유실이므로 처리 실패는 parked 로.

**헷갈리기 쉬운 점**: 로컬 RabbitMQ 4.x 에서 nack 은 delivery-limit 에 안 잡히고 reject 만 잡히는 걸 관찰 → 그래서 `reject(requeue=True)`. 운영 3.13 동작은 **확인 필요**(docstring "verify on the production 3.13 broker").

---

### 6. recover-tick 안전망 (2026-10-29 · `920f173` `d971316` `bd52f45` `5a38e5d`)

**코드 지도**: `internal_ticks.run_recovery_items`(:81) 가 순서 `h → e → f → a → b → d → g` 로 `recovery.py` 함수를 부름. 항목마다 `internal_tick_budget_seconds / 7` 타임아웃, 한 항목 실패가 다른 항목을 막지 않음.

| 항목 | 함수 | 하는 일 |
|---|---|---|
| h | `expire_queued` | `queue_timeout_seconds` 지난 QUEUED → QUEUE_TIMEOUT 실패 |
| e | `expire_approvals` | 승인 기한 만료 (머지 후 `approval_expiry.expire_waiting` 로 이동, 타인) |
| f | `reconcile_slots`(:211) | epoch 없으면 DB RUNNING(`should_hold`)으로 `Slots.reconcile`, 있으면 양방향 대조(남는 멤버 ZREM, 빠진 멤버 ensure) |
| a | `recover_unpublished`(:48) | `start_published_gen IS DISTINCT FROM generation` + 30초 → `publish_start` |
| b | `recover_unnotified`(:61) | 결과 준비됐는데 `notified_gen ≠ generation` + 30초 → `notify_step_result` |
| d | `recover_lease_expired` | AI Home 리스 만료 step → LEASE_EXPIRED continue |
| g | `recover_stalled_handoffs` | PENDING 이 `handoff_stall_seconds`(180) 넘게 정체 → CALL_RETRY |

공통 원칙(`recovery.py` docstring): 후보는 `FOR UPDATE SKIP LOCKED` 로 집고 **트랜잭션 종료 후** MQ/Redis 호출(L4, 브로커 대기 중 행 잠금 금지), 모든 쓰기는 조건부라 다른 Worker·두 번째 tick 레플리카와 동시에 돌아도 안전.

**면접 30초 설명**: "MQ 경로의 모든 '발행 누락'은 DB 컬럼 하나로 표시돼 있어서, recover-tick이 `start_published_gen`·`notified_gen`이 세대보다 뒤처진 행을 SKIP LOCKED로 집고, 트랜잭션을 끝낸 다음 다시 발행합니다. Redis 슬롯은 (f)가 DB와 양방향으로 맞추고, epoch가 없으면 통째로 재구성합니다."

---

### 7. EXECUTION_ENABLED 플래그 (게이트) — **타인 코드, 나는 사용만**

- 정의: `availability.py:6-15` `execution_capability()` = `settings.execution_enabled and effective_auth_mode != 'disabled'`, `require_execution()` 은 아니면 `503 EXECUTION_NOT_READY`. 작성 **springfefe**(`c49efac` 10-14, `50f94ad` 10-20).
- 호출 지점: 사용자 API `execute`/`resume`/`patch_workflow`(api.py:310,322,350), 내부 tick `authenticate`(internal_ticks.py:39), 예약 `create_due` 첫 줄(scheduler_service.py:49, 꺼져 있으면 `0, False`), Worker 기동(`worker_runtime.py:258`).
- `config.validate_profile`: `deployment_environment == 'server'` 면 `execution_enabled` 가 True 일 수 없다(기동 실패). 즉 **서버 프로필에선 env 만 바꿔서 켤 수 없다**(deploy/README.md:25).
- 배포 템플릿: `deploy/automation.yaml:15` `AUTOMATION_EXECUTION_ENABLED: "false"`, Worker `replicas: 0`(:111).
- 면접: "운영 실행은 아직 꺼져 있다. 서버 프로필 검증이 실행 활성화를 거부하므로 인증 어댑터 구현·검수 후 켠다."

---

### ai-automation 전체 — 내가 한 범위 / 바뀌어 온 이력 / 30초

**내가 한 범위**: 10-26·10-28 진단 문서 → 10-28 설계 1판, 10-29 설계 2판(`ai-automation/done/2026-10-29-ai-automation-mq-centric-design-v2.md`, D1~D22) → `feature/mq-centric-execution` 29커밋(`7c43f9d..c7b295b`, 10-29~11-02) → develop 머지 `52ad1e1`. AI Home `feature/automation-mq-callback` 16커밋(`c51ac38e`~`8caf30f7`), 머지 `fcfc0ff9`. 이전 DB 중심 구조와 POC 기반, tick 인증·EXECUTION_ENABLED 게이트, AI Home `accept()` 멱등은 springfefe. 머지 후 static step·admission fence·`__ready__`·승인 만료 이동도 springfefe(`20a11cd`, `021d59b`).

**커밋 순서**: `7c43f9d` 컬럼·설정 → `d428b91` 토폴로지·퍼블리셔 → `566b698` 슬롯 → `b816e96` NX → `11093bf` 전이 추출 → `198155f` START 원자 실패 → `ada3581` 멱등 handoff → `9bbbdff` 404 분류 → `9106149` start 컨슈머 → `36b7206` continue·선점 재시도 → `ecea2ce` Cluster failover → `6d2fca4` 컨슈머 런타임 → `60f66bc` DLQ 핸들러 park → `4c773d4` 커밋 후 발행 → `72f559c` 콜백 수신 → `cacc787` 회사 RR → `2e0f39b` → `920f173` recover-tick 재작성 → `d971316` → `b25097a` DB 디스패치 제거 → `bd52f45` → `c243867` 지표 → `d8333e3` → `e46ef63`/`a563c30` 장애 주입 검증 → `dec9a6f` → `5a38e5d` → `4c122c3` → `c7b295b`

**면접 30초 설명 (전체)**
"예약 tick이 `create_due`에서 회사별 라운드로빈으로 실행을 QUEUED로 커밋한 뒤 `automation.start`에 발행합니다. Worker는 Redis Lua로 `실행ID:세대` 슬롯을 잡고, `start_running`으로 조건부 RUNNING 전이와 첫 step 행을 PENDING으로 저장한 다음, `ensure_handoff`가 저장된 requestId로 AI Home step-runs를 호출하고 202를 받으면 ACK합니다. AI Home은 결과를 커밋하고 콜백을 보내고, API가 `automation.continue`로 넘기면 Worker가 세대와 requestId를 확인해 다음 step을 넘기거나 끝내며 슬롯을 반납합니다. 실패는 2·10·30·60초 지연 큐, 반복 크래시는 delivery-limit 10 후 DLQ에서 60초 뒤 원래 큐로, 3회면 parked입니다. 발행 누락은 recover-tick이 DB의 세대 컬럼을 보고 다시 발행합니다."

**헷갈리기 쉬운 점 (전체)**
- 큐 이름의 `automation` 은 `AUTOMATION_MQ_NAMESPACE` 기본값. Redis 키도 `{automation}:…`.
- tick 비밀값(`X-Internal-Secret`, `INTERNAL_TICK_SECRET`)과 콜백 비밀값(`CALLBACK_SECRET`)은 **다른 값**. 둘 다 32바이트 미만이면 거부.
- start 컨슈머의 outcome 은 3종(ACK/PARK/RELEASE). nack 은 쓰지 않고, 비인프라 예외만 `reject(requeue=True)`.
- 운영 미활성(EXECUTION_ENABLED=false, Worker 0). K 측정, 큐 길이 KEDA 트리거, RabbitMQ 3.13 delivery-limit 동작, Redis Cluster 는 미확인/설계만.
- `fault_point` 4곳: `after_transition`, `after_http_response`, `after_202`, `after_step_saved` (local 에서만 env 로 발동).

---

## 데이터 마이그레이션 — 코드 워크스루

> 표기: `[공유]` = /Users/daou-8691/PycharmProjects/domig-airflow-dev (branch master), `[단독]` = /Users/daou-8691/PycharmProjects/do-vpc-mig (branch master, 일부는 feature 브랜치).
> 본인 = author `starlight2083` / `변재혁` (email starlight2083@daou.co.kr). "본인 vs 타인"은 `git blame`·`git log --author`로 확인함.
> `[공유] dags/storage/tasks/do/storage_tasks.py` 발췌는 비밀번호를 지운 사본 기준 줄 번호이고, sudo 암호 인자는 발췌에서 뺐다. 상수 `AES_KEY`, `WORKER_API_PASSWORD` 같은 값은 이름만 적는다.

---

### 전체 코드 지도

#### 공유형 `[공유]` domig-airflow-dev

**디렉터리 요약**
| 경로 | 내용 |
|---|---|
| `dags/main.py` | DB 축 메인 DAG `본이관-메인` (본인 144줄 / 곽면순 42 / mskw 23) |
| `dags/main_multi_until_pre.py`, `dags/main_multi_pre_to_post.py` | 메인 DAG를 pre까지 / pre→post 두 개로 나눈 버전 (`본이관-멀티이관-메인-until-pre` 등, d524d740 2025-11-18 본인) |
| `dags/dop/{webmail,gw,attend,chat,iam,acc,...}/*_tasks.py` | 서비스별 `@task_group` 정의. 메인 DAG가 import해서 조립함 |
| `dags/dop/gw/gw_tasks.py` | GW 서비스 태스크 그룹 + **쿼리 단위 dynamic task mapping** (`gw_get_query`) |
| `dags/dop/gw/editor/*` | 결재·게시판 등 HTML 본문 변환 (Python), 결재 본문 SQL 변환 호출, 태그 검증 |
| `sql/gw/pre/transfer/{fast,slow}/` | GW v3→pre_v4 변환 SQL (fast 41개 파일, slow 8개 파일) |
| `sql/gw/pre/editor/` | 결재 본문 SQL 변환: range 테이블·변환 함수·range worker·복호화 함수 |
| `dags/storage/*_dag*.py` | 첨부 이관 DAG들 |
| `dags/storage/tasks/do/` | 첨부(다우오피스) 태스크: `mapping_tasks.py`, `storage_tasks.py`, `storage_correct_tasks.py`, `storage_check_mount_tasks.py` |
| `sql/storage/` | `storage_mapping` 스키마, 전체/기간 sync SQL |

**DAG 목록과 실행 순서**
- DAG 사이를 잇는 `TriggerDagRunOperator`는 없다(`dags/` 전체 검색, 0건). 전부 `schedule=None`이고 **사람이 순서대로 수동 실행**한다.
- 첨부: `사전준비-파일_마이그레이션_다우오피스`(본이관 전에 여러 번 실행) → 필요하면 `사전준비-파일_마이그레이션_GCS_PATH_보정`, `사전준비-실물_파일_확인`.
- DB: `본이관-메인` 하나 (또는 `본이관-멀티이관-메인-until-pre` → `...pre-to-post`).
- `본이관-메인` 내부 순서 (`dags/main.py:65-211`):
  `본이관_시작 → add_variable_log_seq → v3 마스킹 → [db_v3_to_pre_v4: 서비스 5개 병렬] → db_pre_v4_validation → db_pre_v4_fk → db_pre_v4_to_post_v4 → db_post_v4_fk → (iam만 data_mask_post_v4) → db_to_cluster_v4 → DOP_DB_로드 → 재인덱싱(echo) → 본이관_종료`
  - 서비스(webmail/gw/attend/chat/iam)는 단계마다 `TaskGroup` 안에 나란히 있고, 의존성은 **같은 서비스끼리만** 걸려 있다(예: `gw_db_v3_to_pre_v4_group >> gw_db_pre_v4_validate_group`, `main.py:82-86`). 그래서 GW가 느려도 chat은 다음 단계로 넘어간다.

**본인 코드 위치**: `dags/main.py`, `dags/dop/gw/gw_tasks.py`(225/483줄, 나머지는 heesu), `dags/dop/gw/editor/*`(전부 본인), `dags/storage/storage_transfer_file_dag_for_do.py`·`tasks/do/*`(전부 본인), `sql/storage/sync_all_mapping.sql`(전부 본인), `sql/storage/create_mapping_schema.sql`(본인 19 / mjpark 24), `sql/gw/pre/editor/*`(커밋 계정은 본인).

#### 단독형 `[단독]` do-vpc-mig

**디렉터리 요약**
| 경로 | 내용 |
|---|---|
| `dags/dop/main_manager.py` | master 메인 DAG `310_data_main` (본인 177줄 / hwgyun 114 / jsb568 20) |
| `dags/dop/main_worker.py` | worker DAG `Main_worker` (hwgyun 182 / 본인 48) |
| `dags/dop/common/common_tasks.py` | master→worker REST 제어(trigger, Variable/Connection upsert, sensor) |
| `dags/dop/common/master_db_access.py`, `worker_dump_to_master.py` | worker→master SSH 터널 DB 접근, pre dump scp (hwgyun / jsb568) |
| `dags/dop/common/master_callback.py` | worker→master REST 콜백 — **`feature/company-insert-master-decoupling` 브랜치에만 있음** |
| `dags/dop/gw/applet/_common.py`, `dags/dop/gw/validate/common.py` | GW JSON 속 PK 변환·검증 (전부 본인) |
| `sql/chat/pre/10_chat_room.sql`, `14_chat_message.sql` | chat 변환 SQL |
| `dags/storage/tasks/{do,acc}/` | 첨부(DO)·경리회계(ACC) 첨부 업로드 |
| `tests/storage/`, `tests/gw/`, `tests/dop/` | pytest 회귀 테스트 |

**DAG 목록과 실행 순서** (DAG id 앞 번호가 실행 순서. 근거: `docs/overview/master-worker-dag-runbook.md`)
`010_precheck_env`(사전 점검) → `100_setup_master_config_to_worker`(worker에 Connection·Variable 팬아웃) → `120_setup_db_restore` → `130_setup_company_insert` → **`310_data_main`** → `410_reset_post` → `420_merge_to_post` → `430_switchover_to_remote`.
- `310_data_main` 안에서 master가 worker마다 `Main_worker` 등을 REST로 trigger하고 sensor로 기다린 뒤 서비스별 merge를 돈다.

**본인 코드 위치**: `main_manager.py`, `common_tasks.py`의 `trigger_worker_api`(25/28줄 본인), `gw/applet/_common.py`, `gw/validate/common.py`, `sql/chat/pre/*`(2ad58b92), `storage/tasks/acc/storage_tasks.py`(21a552ba), `storage/tasks/do/storage_check_mount_tasks.py`, feature 브랜치의 `master_callback.py`.

---

### 1. 메인 DAG 구조 — 쿼리 실행 태스크(dynamic task mapping + pool, slow/fast)  (2025-06 ~ 2026-01 · e0176366/fc828f2a, 18c434bc)

**내가 한 범위**
- 본인: `본이관-메인` DAG 골격(단계 TaskGroup, 서비스별 병렬, cluster 반영 skip 분기), GW의 `gw_get_query()` + `.partial().expand(query=...)` + `pool='gw_pool'`, fast/slow 폴더를 DAG에 연결(18c434bc).
- 타인: SQL 파일을 fast/slow 폴더로 나눈 건 heesu(`b018def7` 2025-09-23 "그룹웨어 이관 쿼리 최적화 (#DOP-9552)"). GW 검증 태스크 `gw_generate_migration_validation`(gw_tasks.py 228-453)도 heesu. 다른 서비스 SQL은 각 담당자.
- **쿼리 단위 mapping은 GW에만 있다.** webmail·attend·chat·iam은 `SQLExecuteQueryOperator`로 파일 단위 실행(`expand(query` 검색: gw_tasks.py 3건, 다른 서비스 0건).

**코드 지도**
| 파일 | DAG/태스크/함수 | 역할 |
|---|---|---|
| `dags/main.py` | `본이관-메인` | 단계 TaskGroup × 서비스 5개 조립, 서비스별 의존성 연결 |
| `dags/dop/gw/gw_tasks.py:24-91` | `gw_db_v3_to_pre_v4_group` | fast/slow 쿼리 목록 → mapped task, 이후 본문 변환 분기 |
| `dags/dop/gw/gw_tasks.py:204-226` | `gw_db_v3_to_pre_v4` 등 3개 `@task(pool='gw_pool')` | 쿼리 1개를 `hook.run`으로 실행 |
| `dags/dop/gw/gw_tasks.py:454-475` | `gw_get_query()` | 폴더 읽기 → Jinja 렌더 → 파일 통째 또는 `;` split |
| `dags/dop/gw/gw_tasks.py:93-101` | `get_type_gw_transfer_doc_body_editor_task_branch` | Variable로 결재 본문 변환 방식(script/sql) 선택 |
| `dags/dop/common/constants.py:23-24` | `APPR_POOL_SLOT`, `APPR_EDITOR_WORKER` | 본문 변환 분할 수 (Variable, 기본 8 / 4) |

**흐름**
1) DAG 파싱 시 `gw_db_v3_to_pre_v4_group()`이 실행되면서 `gw_get_query()`가 `/opt/domig-airflow-dev/sql/gw/pre/transfer/{fast,slow}` 폴더를 읽는다.
2) 각 파일을 Jinja로 렌더(`add_value`, `cluster`, `iam_max_log_seq` 등 주입).
3) `run_files`에 든 파일은 통째로 1개 쿼리, 나머지는 `;`로 쪼갠다. fast는 `run_files = os.listdir(fast)`라 **전 파일이 파일 단위**, slow는 `gw_create_table.sql`·`gw_action_logs.sql`만 파일 단위이고 나머지는 **쿼리 단위**.
4) `slow + fast` 리스트를 `gw_db_v3_to_pre_v4.partial().expand(query=query_list)`로 넘겨 리스트 길이만큼 mapped task instance를 만든다. 실행 동시성은 `gw_pool` 슬롯 수로 제한된다.
5) mapped task 전체가 끝나면 `noti_event → applet_bfs → 01/02_new_table_data_insert → invalid_data_update`가 순서대로 돈다(`gw_tasks.py:62`).
6) 별도 줄기로 본문 변환 분기(→ 3번 기여)와 기타 에디터(공문·게시판·클립보드 등) mapped task가 돈다(`gw_tasks.py:64-91`).
7) 같은 패턴이 FK 단계(`sql/gw/pre/constraint/{fast,slow}`)와 cluster 반영 단계에도 쓰인다(`gw_tasks.py:132-192`).

**핵심 코드**
```python
# [공유] dags/dop/gw/gw_tasks.py:24-39
@task_group(group_id="gw_db_v3_to_pre_v4_group")
def gw_db_v3_to_pre_v4_group():
    # fast: 빨리 끝나는 SQL → 파일 통째로 태스크 1개
    fast_folder_path = '/opt/domig-airflow-dev/sql/gw/pre/transfer/fast'
    fast_exclude_files = []
    fast_run_files = os.listdir(fast_folder_path)          # 전부 파일 단위
    fast_query_list = gw_get_query(fast_folder_path, fast_exclude_files, fast_run_files)

    # slow: 오래 걸리는 SQL → 쿼리(;) 단위로 쪼개 병렬화
    slow_folder_path = '/opt/domig-airflow-dev/sql/gw/pre/transfer/slow'
    slow_exclude_files = []
    slow_run_files = ['gw_create_table.sql', 'gw_action_logs.sql']  # 쪼개면 안 되는 파일만 예외
    slow_query_list = gw_get_query(slow_folder_path, slow_exclude_files, slow_run_files)

    query_list = slow_query_list + fast_query_list
    gw_db_v3_to_pre_v4_task = gw_db_v3_to_pre_v4.partial().expand(query=query_list)  # 쿼리 수만큼 mapped task

# [공유] dags/dop/gw/gw_tasks.py:204-210
@task(task_id='gw_db_v3_to_pre_v4_task', pool='gw_pool')   # 동시 실행 수 = gw_pool 슬롯
def gw_db_v3_to_pre_v4(query):
    try:
        hook.run(query)
    except Exception as e:
        logging.log(logging.ERROR, f"[ERROR] Failed to execute query: {query}. Error: {e}")
        raise e                                             # 실패한 쿼리만 이 map_index가 빨갛게 남음

# [공유] dags/dop/gw/gw_tasks.py:461-473 (gw_get_query 본문)
    for filename in os.listdir(folder_path):
        if filename in exclude_files:
            continue
        ...
                query_content = Template(content).render({'params': {...}, 'var': {'value': {...}}})  # Jinja 렌더
                if filename in run_files:
                    query_list.append(query_content)                      # 파일 통째
                else:
                    query_list.extend([x.strip() + ';' for x in query_content.split(';') if x.strip()])  # ; 단위
```

**데이터·설정**
- 스키마: 원본 `asisgw.*` → 변환 `pre_dopgw.*`(pre_v4) → `post_v4` → cluster.
- Pool: `gw_pool`(GW 쿼리·에디터·검증 태스크 전부), 슬롯 수는 코드에 없음(Airflow UI 설정) → **확인 필요**.
- Variable: `iam_max_log_seq`(Jinja 주입), `auto_cluster_remote`(false면 cluster 반영 단계를 `EmptyOperator`로 바꿔치기, `main.py:143-156`), `type_gw_transfer_doc_body`(script|sql, 기본 sql), `appr_pool_slot`(기본 8), `appr_editor_worker`(기본 4).
- Connection: `POSTGRES_DB_CONNECTION_ID`(값은 constants).

**왜 이렇게 짰나**
- 쿼리 1개 = mapped task 1개라서 실패한 쿼리만 Airflow UI에서 그 map_index만 재실행할 수 있고, 어떤 쿼리가 느린지 태스크 시간으로 바로 보인다.
- `;` split은 단순 문자열 분리라서 함수 정의(`$$...;...$$`)나 순서 의존이 있는 파일은 쪼개면 깨진다. 그래서 `run_files` 예외 목록을 뒀다.
- heesu가 SQL을 "빠른 것/느린 것"으로 나눈 뒤(b018def7), 빠른 쪽은 쪼갤 이득보다 태스크 수(스케줄링 오버헤드)가 더 크니 파일 단위로 돌리고, 느린 쪽만 쿼리 단위로 쪼갰다(18c434bc). 처음 버전(18c434bc)은 `fast + slow` 순서였는데 지금은 `slow + fast`. 의도는 커밋에 없음 → 확인 필요(느린 것을 먼저 큐에 넣으려는 것으로 보이나 추정).
- 버린 방식: 18c434bc 이전엔 한 폴더(`sql/gw/pre/transfer`) 전체를 쿼리 단위로 쪼개고, 쪼개면 안 되는 파일(`33_1/33_2_gw_org_id_mapping.sql`)만 `run_files`로 뺐다.
- 트레이드오프: mapped task끼리는 순서가 보장되지 않는다. 같은 폴더 안에서 A 쿼리 결과를 B 쿼리가 쓰면 깨진다 → 의존 있는 쿼리는 같은 파일(run_files)로 묶거나 뒤 단계(`01/02_new_table_data_insert`)로 뺐다. 또 쿼리 목록은 **DAG 파싱 시점**에 만들어져서 SQL 파일을 바꾸면 DAG 재파싱 후 반영된다.

**바뀌어 온 이력**
- 2025-06-04 ~ 06-09 `58cffe16`, `0613273a` 등: "emptyOp test" — EmptyOperator로 메인 DAG 골격부터 세움.
- 2025-08-21 `e0176366`, `fc828f2a`: `gw_get_query` + `.partial().expand(query=...)` 도입(FK·cluster 단계 포함). 처음엔 Jinja 렌더를 태스크 안에서 했음.
- 2025-08-22 `ae979daa`: `pool='gw_pool'` 추가. `58f93fe3`: `gw_get_query` 현재 형태.
- 2025-09-15 `2a2942ab`: Jinja 렌더 인자 확장.
- 2025-09-23 `b018def7`(heesu): SQL을 fast/slow 폴더로 분리. 2025-09-24 `18c434bc`(본인): DAG를 fast/slow 구조로 연결.
- 2025-11-18 `d524d740`: 멀티 이관용 메인 DAG 2개 추가.
- 2026-01-08 `1536944d`, 2026-01-09 `25c32978`: slow `run_files`를 지금의 2개로 조정.
- 2026-01-15 `4b205b9a`/`13bda883`: 본문 변환 script/sql 분기(`type_gw_transfer_doc_body`) 추가.

**면접 30초 설명**
"메인 DAG는 단계를 TaskGroup으로 고정하고, 그 안에 서비스 5개를 나란히 두되 의존성은 같은 서비스끼리만 걸었습니다. 그래서 한 서비스가 느려도 다른 서비스는 다음 단계로 갑니다. GW는 SQL 양이 가장 많아서 폴더의 SQL을 Jinja로 렌더링한 뒤 세미콜론으로 쪼개 dynamic task mapping으로 쿼리마다 태스크를 만들었고, `gw_pool`로 DB 동시 부하를 묶었습니다. 실패한 쿼리만 다시 돌릴 수 있게 하려는 것이었고, 빨리 끝나는 SQL은 태스크 수만 늘어나니 파일 단위로 돌리고 느린 SQL만 쿼리 단위로 쪼갰습니다."

**헷갈리기 쉬운 점**
- "쿼리 1개 = 태스크 1개"는 **GW slow 폴더에만** 맞다. fast는 파일 단위, 다른 서비스는 `SQLExecuteQueryOperator` 파일 단위.
- fast/slow로 SQL을 나눈 사람은 heesu, 나는 DAG 연결. GW 이관률 검증 태스크(`gw_generate_migration_validation`)도 heesu 코드.
- `;` split은 문자열 안의 `;`를 구분하지 않는다(따옴표를 따지는 split은 heesu의 검증 코드 `extract_queries_from_sql`에만 있음).
- pool 슬롯 수, 서비스별 처리 시간은 코드에 없다.
- `db_pre_v4_to_post_v4`, `db_post_v4_fk`, `DOP_DB_로드`의 GW 태스크는 지금 `EmptyOperator`/`echo hello` placeholder다(`gw_tasks.py:159-202`).

---

### 2. 첨부 이관 파이프라인  (2025-07 ~ 2026-02 · 83327553, 01a9fa35, de2a7fe9, 9cc4529d, 46461c47, 2ba7aad2)

**내가 한 범위**
- 본인: DAG `사전준비-파일_마이그레이션_다우오피스`(87줄 전부), `mapping_tasks.py`·`storage_correct_tasks.py`(전부), `storage_tasks.py`(DO, 본인 93커밋), `sync_all_mapping.sql`(전부).
- 타인: `storage_mapping` 테이블 최초 생성은 mjpark(`76ec0fac` 2025-03-05 "mapping table 생성"), 이후 본인이 컬럼·인덱스 추가(blame 24 : 19). 처음 `gsutil -m cp` 배치 호출 코드도 mjpark. 경리회계(ACC)는 MariaDB 원본이라 별도 DAG.

**코드 지도**
| 파일 | DAG/태스크/함수 | 역할 |
|---|---|---|
| `dags/storage/storage_transfer_file_dag_for_do.py` | `사전준비-파일_마이그레이션_다우오피스` | 전체 흐름 조립 |
| `dags/storage/tasks/do/mapping_tasks.py:52-68` | `is_sync_all_attach_for_do`(branch), `get_period_info` | 최초 1회 전체 sync / 이후 `max(upload_at)` 이후만 |
| `sql/storage/sync_all_mapping.sql`, `sync_period_mapping.sql` | `sync_*_attach_for_do_task` | 원본 첨부 → `storage_mapping` INSERT (`ON CONFLICT (attach_id) DO NOTHING`) |
| `dags/storage/tasks/do/mapping_tasks.py:7-50` | `validate_sync_*_mapping_table_for_do` | 원본 건수 vs 매핑 건수 비교(로그만) |
| `dags/storage/tasks/do/storage_correct_tasks.py` | `is_correct_all_...`(branch), `correct_all_...`, `correct_period_...` | 경로 충돌 그룹을 찾아 `gcs_path` rename |
| `storage_tasks.py:20-48` | `get_company_uuid_list_for_do` | 회사별 파일 수 내림차순 → 라운드로빈 청크 |
| `storage_tasks.py:81-93` | `upload_attach_for_do` (mapped, `pool='storage_pool'`) | 회사 → dest_bucket_path → 업로드 |
| `storage_tasks.py:249-293` | `_run_gsutil` | FUSE 마운트 경로로 `cp -n` 500개 배치 |
| `storage_tasks.py:295-330` | `run_gsutil_correct_file` | 이름이 바뀐(충돌 교정) 파일만 1건씩 새 이름으로 복사 |
| `storage_tasks.py:349-399` | `_validate_gcs_upload`, `_patch_metadata` | GCS API로 존재·크기 확인 후 메타데이터 patch |
| `storage_tasks.py:401-467` | `_record_upload_result` | 결과 4분류를 `storage_mapping`에 UPDATE |
| `storage_tasks.py:51-79, 95-107, 240-247` | `*_retry` | 같은 DAG 안의 재시도 단계, 메타데이터만 재시도 분기 |

**흐름** (`storage_transfer_file_dag_for_do.py:57-84`)
1) `is_sync_all_attach_for_do_task`(branch): Variable `sync_mapping_table_sync_first_run`이 "true"면 "false"로 바꾸고 전체 sync로, 아니면 `get_period_info_task`(= `select max(upload_at) from storage_mapping`)로.
2) `sync_all_attach_for_do_task` 또는 `sync_period_attach_for_do_task`: `asisgw.go_attach_files` 등을 조인해 파일마다 `app_code`, `gcs_path`, `dest_bucket_path`를 계산해 INSERT.
3) `validate_sync_*`: 원본(`deleted_at is null`) 건수와 매핑 건수를 출력하고, 다르면 매핑에 없는 원본 건수를 출력. **실패시키지 않는다.**
4) `sync_mapping_join_task`(NONE_FAILED_MIN_ONE_SUCCESS)로 두 갈래 합류.
5) `is_correct_all_app_code_and_gcs_path_branch`: Variable `correct_mapping_table_first_run` 기준으로 전체/기간 경로 충돌 보정.
6) `get_company_uuid_list_for_do`: `execute_flag=false`인 회사를 파일 수 내림차순 정렬 → `idx % chunk_size`로 최대 1000개 리스트에 분배 → `upload_attach_for_do.expand(company_uuid_list=...)`.
7) 각 mapped task: 회사 → 그 회사의 `dest_bucket_path`(= `{app_code}/{uuid}/{YYYYMMDD}`)마다 `_get_file_records` → `_run_gsutil`(FUSE `cp -n`) → `_validate_gcs_upload` → `_record_upload_result`.
8) `get_company_uuid_list_for_do_retry`(`trigger_rule='all_done'`): 앞 업로드가 일부 실패해도 실행. 대상 `execute_flag=TRUE AND execute_count<12 AND metadata_success_flag=FALSE`.
9) `upload_attach_for_do_retry`: `success_flag=FALSE`면 파일부터 다시 복사, `success_flag=TRUE`(파일은 있음)면 **복사 없이 바로 검증+메타데이터 patch**.

**핵심 코드**
```python
# [공유] storage_tasks.py:264-287 (_run_gsutil 본문, sudo 암호 인자 생략)
        # gcs_path 파일명 != 원본 파일명 → 충돌 교정으로 이름이 바뀐 레코드
        correct_file_records = [row for row in file_records if row[5].split('/')[-1] != row[1].split('/')[-1]]
        if correct_file_records:
            success_correct_records, fail_correct_records = run_gsutil_correct_file(dest_bucket, correct_file_records)
            success.extend(success_correct_records)
            fail.extend(fail_correct_records)

        # 교정 대상으로 처리한 src 파일은 일반 배치 cp 대상에서 제외
        correct_src_set = {row[1] for row in correct_file_records}
        file_paths = [row[1] for row in file_records if row[1] not in correct_src_set]

        # cp 호출을 배치로 나눠 실행하여 argv 길이 제한 회피
        batch_size = 500
        for i in range(0, len(file_paths), batch_size):
            batch = file_paths[i:i + batch_size]
            command = ["sudo", "-S", "cp", "-n"] + batch + [dest_bucket]   # dest_bucket = FUSE 마운트 경로
            output = subprocess.run(command, ..., check=False, ...)
            success_paths.extend(batch)      # exit code는 보지 않음 → 진짜 판정은 아래 GCS 검증

# [공유] storage_tasks.py:355-373 (_validate_gcs_upload)
    for record in success_records:
        file_id, file_path, file_size, file_name, upload_at, gcs_path = record[0], ..., record[5]
        try:
            blob = bucket.get_blob(gcs_path)                    # GCS API로 존재 확인
            if blob is None:
                validate_fail.append({'id': file_id, 'message': "...파일을 찾을 수 없습니다..."})
            elif file_size != 0 and blob.size != int(file_size):  # DB 크기 0이면 비교 생략
                if os.path.getsize(file_path) == int(blob.size): # DB 값이 틀린 경우: 실물 크기와 같으면 성공
                    _patch_metadata(blob, file_name, upload_at, app_code)
                    validate_success.append(file_id)
                    continue
                validate_fail.append({'id': file_id, 'message': "...사이즈가 다릅니다..."})
            else:
                _patch_metadata(blob, file_name, upload_at, app_code)  # content_type, disposition, custom_time, metadata
                validate_success.append(file_id)
        except GoogleAPIError as e:
            validate_meta_fail.append(...)                      # 파일은 있는데 patch 실패

# [공유] storage_tasks.py:240-247 (재시도: 메타데이터만 다시)
def _upload_gcs_retry(file_records, dest_bucket):
    execute_at = datetime.now()
    retry_file_records = [record for record in file_records if not record[6] and not record[7]]   # 파일부터 실패
    retry_metadata_records = [record for record in file_records if record[6] and not record[7]]   # 파일 OK, 메타 실패
    result = _run_gsutil(retry_file_records, execute_at, dest_bucket)
    return {'success_records': result['success_records'] + retry_metadata_records,  # 복사 없이 검증·patch로 직행
            'fail_records': result['fail_records'], 'execute_at': execute_at}
```
```python
# [공유] dags/storage/tasks/do/storage_correct_tasks.py:46-74 (경로 충돌 교정)
    sql_groupby_gcs_path = """
                SELECT app_code_and_gcs_path FROM public.storage_mapping sm
                WHERE app_code_and_gcs_path IS NOT NULL AND sm.upload_at > %s
                GROUP BY app_code_and_gcs_path
                HAVING COUNT(*) > 1                       -- 같은 버킷·같은 경로가 2건 이상
            """
...
def update_gcs_path(app_code_and_gcs_path):
    records = get_storage_mapping_records(app_code_and_gcs_path)   # 그 경로를 가진 레코드 전부
    if len(records) <= 1:
        return
    now = datetime.now()
    for idx, record in enumerate(records):
        new_gcs_path = f"{record[1]}_{now}_{idx}"                   # 모든 레코드 이름 뒤에 _{시각}_{순번}
        update_storage_mapping_gcs_path(record[0], new_gcs_path)
```
```sql
-- [공유] sql/storage/sync_all_mapping.sql:28-53 (경로 계산)
    CASE -- gcs_path  (버킷 안 object 이름)
        WHEN t3.destination_directory_path != '' THEN t3.destination_directory_path || '/' || t3.random_name
        WHEN t3.app_path = 'banner' THEN 'banner' || '/' || t3.uuid || '/' || TO_CHAR(t3.upload_at, 'YYYYMMDD') || '/' || t3.random_name
        when t3.app_code = 'NONE' then ''
        ELSE t3.uuid || '/' || TO_CHAR(t3.upload_at, 'YYYYMMDD') || '/' || t3.random_name   -- {회사}/{날짜}/{파일}
    end as gcs_path,
    ...
    CASE -- dest_bucket_path  (업로드 묶음 단위 = {앱}/{회사}/{날짜})
        ...
        when t3.app_code = 'NONE' then null                 -- 어느 서비스에도 안 붙은 파일은 업로드 대상 아님
        ELSE t3.app_code || '/' || t3.uuid || '/' || TO_CHAR(t3.upload_at, 'YYYYMMDD')
    end as dest_bucket_path
-- 마지막 줄(270): ON CONFLICT (attach_id) DO NOTHING;
```

**데이터·설정**
- 상태 테이블 `public.storage_mapping` (`sql/storage/create_mapping_schema.sql`): `attach_id`(UNIQUE), `app_code`, `company_uuid`, `path`(원본 경로), `file_size`, `file_name`, `upload_at`, `gcs_path`, `dest_bucket_path`, `app_code_and_gcs_path`, `execute_flag`, `execute_at`, `execute_count`, `success_flag`, `metadata_success_flag`, `result_message`, `thumbnail_flag`, `preview_flag`.
- 인덱스: `(execute_flag, company_uuid, dest_bucket_path)`, `(execute_flag, execute_count, dest_bucket_path)`, `gcs_path`, `app_code_and_gcs_path`, `dest_bucket_path`, `attach_id`.
- 상태 전이 (`_record_upload_result`):
  | 결과 | execute_flag | success_flag | metadata_success_flag | execute_count | result_message |
  |---|---|---|---|---|---|
  | ① 검증+메타 성공 | TRUE | TRUE | TRUE | 그대로 | - |
  | ② 파일 OK·메타 patch 실패 | TRUE | TRUE | (FALSE 유지) | +1 | 에러 메시지 |
  | ③ 검증 실패(없음/크기 다름) | TRUE | (FALSE 유지) | (FALSE 유지) | +1 | 에러 메시지 |
  | ④ 복사 단계 실패 | TRUE | (FALSE 유지) | (FALSE 유지) | +1 | 'gsutil fail' |
- 버킷: `get_bucket_name(app_code)`(앱별 버킷, 예외 `portal-public-repo`). FUSE 경로: `FUSE_PATH`(Variable `fuse_path`, 기본 `/fuse_data/mnt/`) + `APP_CODE_MAP[app_code]` + `/{uuid}/{날짜}/`.
- Variable: `sync_mapping_table_sync_first_run`, `correct_mapping_table_first_run`, `chunk_size_company_uuid`(기본 1000), `pcwook_test_mode`.
- Pool: `storage_pool`(업로드·보정 태스크). 슬롯 수 → 확인 필요.

**왜 이렇게 짰나**
- 파일 1건 = 1행 상태 테이블: 대상 선정·재시도·검증이 전부 이 테이블 조건 조회라서 DAG를 몇 번 다시 돌려도 안전하다. `ON CONFLICT DO NOTHING`(매핑), `cp -n`(복사), `execute_flag`(선정) 세 겹 멱등.
- 최초 1회 전체 sync 후엔 `max(upload_at)` 이후만 sync: 본이관 전에 여러 번 돌려 증분만 따라잡게 하려는 구조.
- 회사별 파일 수 내림차순 + 라운드로빈: 큰 회사가 한 mapped task에 몰리지 않게. 단 개수 기준이지 용량 기준은 아니다.
- `gsutil -m` → FUSE + `cp -n`: 단일 파일 `-m` 무한 로딩(83327553) 등 gsutil 문제 이후, 버킷을 로컬 디렉터리로 마운트해 일반 `cp`로 복사. 500개씩 끊은 건 주석대로 argv 길이 제한 때문.
- cp exit code를 버리고 GCS 검증을 진실로 삼음(2ba7aad2): 판정을 한 곳(GCS API 조회)으로 모았다. 이유는 커밋 메시지에 없음 → 확인 필요.
- 메타데이터만 재시도: 파일은 이미 올라갔는데 patch만 실패한 경우 수 GB 파일을 다시 복사하지 않으려고.
- 재시도를 별도 DAG가 아니라 같은 DAG 뒤 단계에 `trigger_rule='all_done'`으로 둠: 본 업로드 mapped task 일부가 실패해도 이어서 재시도 대상만 다시 뽑는다.
- 경로 충돌 교정: 디스크 여러 개를 한 버킷으로 합치면 `{회사}/{날짜}/{랜덤파일명}`이 겹칠 수 있다. 겹친 그룹은 전원 rename하고, 업로드 때 "gcs_path 파일명 ≠ 원본 파일명"인 레코드만 배치에서 빼서 1건씩 새 이름으로 복사(46461c47). 본문 변환이 `storage_mapping.gcs_path`를 조회해 치환하므로 rename이 본문 링크에도 그대로 반영된다.
- 버린 대안: 체크섬(MD5/CRC32C) 비교는 코드에 없다. Storage Transfer Service 검토 흔적도 없다.

**바뀌어 온 이력**
- 2025-03-05 `76ec0fac`(mjpark): mapping 테이블 생성.
- 2025-07-22 `6dca6632`: ACC 추가. 2025-07-29 `83327553`: 단일 파일이면 `-m` 제거.
- 2025-08-05 `ef2eb405`, `01a9fa35`: "fuse test" — FUSE 경로 도입.
- 2025-08-26 `bd264dbd` ~ 2025-12-04 `8671b4d5`: `storage_correct_tasks.py` 신설·수정(경로 충돌 rename 쪽).
- 2025-09-02 `a9ff2b4b`: 전송 DAG 파일 생성. 2025-09-04 `de2a7fe9`: `cp` → `cp -n`.
- 2026-01-12 `9cc4529d`: 500개 배치. 같은 날 `46461c47`: 업로드 쪽 충돌 파일 개별 복사(`run_gsutil_correct_file`) + 연습용 `tests/storage/test_storage_1_tasks.py`.
- 2026-01-13 `3f8885b0`: DB 크기 불일치 시 실물 크기로 재비교.
- 2026-01-26 `2ba7aad2`: 배치 returncode 판정 제거.
- 2026-02-10 `1a5d5311`: 재시도 상한 10 → 12.

**면접 30초 설명**
"첨부는 파일 하나당 한 행인 storage_mapping 테이블로 상태를 관리했습니다. 원본 첨부를 매핑 테이블에 넣을 때 `{회사}/{날짜}/{파일}` 경로를 미리 계산하고, 업로드는 회사별로 쪼갠 mapped task가 FUSE로 마운트한 버킷에 `cp -n`으로 500개씩 복사합니다. 성공 판정은 cp 결과가 아니라 GCS API로 객체 존재와 크기를 다시 확인해서 하고, 결과를 네 가지로 기록합니다. 같은 DAG 뒤에 all_done 재시도 단계를 둬서, 파일은 올라갔는데 메타데이터만 실패한 건은 다시 복사하지 않고 메타데이터만 붙입니다."

**헷갈리기 쉬운 점**
- 재시도는 "재시도 DAG"가 아니라 같은 DAG의 뒤 단계다.
- 검증은 **존재 + 크기만**. DB 크기 0이면 크기 비교도 안 한다. 체크섬 없음.
- `run_gsutil_correct_file`은 로컬 원본이 없으면 일단 success로 넘긴다(`storage_tasks.py:312-314`) → 최종 판정은 GCS 검증에서 "파일 없음"으로 난다.
- 충돌 교정은 `gcs_path`만 바꾸고 `app_code_and_gcs_path` 컬럼은 갱신하지 않는다(`storage_correct_tasks.py:83-89`).
- 기간 보정은 `upload_at > start` **안에서만** 중복을 센다. 그래서 신규 1건이 기존 1건과 겹치는 경우는 이 쿼리로 안 잡히고(코드상 그렇게 읽힘), 반대로 신규끼리 겹친 그룹이 잡히면 `get_storage_mapping_records`가 날짜 조건 없이 조회해 **이미 올라간 기존 레코드까지 rename**한다. 지적받으면 인정할 부분.
- 4분류는 "성공 포함 4분류"(docstring)다. 실패만 세면 복사 실패 / 객체 없음 / 크기 불일치 / 메타 patch 실패.
- 건수 비교 태스크는 불일치여도 실패시키지 않는다(로그만).
- 공유형 업로드 코드는 `sudo -S`로 비밀번호를 stdin에 넘긴다(하드코딩). 단독형 ACC만 21a552ba에서 제거됨.

---

### 3. 결재·게시판 본문 변환  (2025-08 ~ 2026-01 · 8bc0125a, bc99999e, c1293e4d, 4b205b9a)

**내가 한 범위**
- 본인: `dags/dop/gw/editor/*` 전부(Python 변환, SQL 변환 호출 태스크, 태그 검증), `sql/gw/pre/editor/*`(커밋 계정 본인, c1293e4d).
- 포트폴리오에는 "DBA가 SQL로 전환"이라고 적었음. 커밋은 본인 계정이라 실제 작성자 분담은 **확인 필요**.

**코드 지도**
| 파일 | DAG/태스크/함수 | 역할 |
|---|---|---|
| `dags/dop/gw/gw_tasks.py:64-91` | branch + 에디터 mapped task들 | 결재 본문 script/sql 분기, 기타 에디터 `divide` 분할 |
| `dags/dop/gw/editor/gw_appr_doc_body_editor_tasks.py:15-89` | `gw_transfer_doc_body_editor`(`divide` mapped) | 결재 본문 Python 변환 |
| 같은 파일 `:222` | `gw_transfer_post_editor` | 게시판(post) 본문 변환, 같은 구조 |
| 같은 파일 `:352-382` | `insert_contents` | named cursor 스트리밍 → 변환 → `execute_values` |
| 같은 파일 `:384-503` | `replace_content` | BeautifulSoup으로 `img/table/td`의 `src` 치환 |
| 같은 파일 `:505-508` | `get_do_decrypt_hex` | 암호화 토큰 → `java -jar DoDecryptHex.jar` |
| `dags/dop/gw/editor/gw_appr_doc_body_editor_sql_task.py` | `gw_transfer_sql_doc_body_editor_task_group`, `run_doc_bodies_range`(mapped) | SQL 방식: 함수 설치 후 range worker 호출 |
| `sql/gw/pre/editor/dobBody/01_initNreset.sql` | - | `mig_doc_bodies_ranges` 생성, 5만 단위 range 적재 |
| `sql/gw/pre/editor/02_transform_function.sql` | `gw_mig_transform_contents()` | PL/pgSQL HTML 치환 |
| `sql/gw/pre/editor/03_dbrangeworker.sql` | `gw_mig_process_one_doc_bodies_range()` | range 1개 claim(SKIP LOCKED) → 변환 INSERT → done |
| `sql/gw/pre/editor/04_decryptfunction.sql` | `extract_random_key_aes_cbc()` | pgcrypto AES-CBC 복호화 |
| `dags/dop/gw/editor/gw_editor_tag_validation.py` | `*_tag_validation`(mapped) | `src` 가진 비정상 태그를 로그로 수집 |

**흐름**
- 분기: `get_type_gw_transfer_doc_body_editor_task_branch`가 Variable `type_gw_transfer_doc_body`(기본 `sql`)로 `editor_script_task` 또는 `editor_sql_task`를 고른다.
- Python(script) 경로:
  1) `gw_transfer_doc_body_editor.partial(slots=8).expand(divide=0..7)` → 각 태스크가 `id % slots = divide`인 행만 맡는다.
  2) `insert_contents`: 읽기 커넥션의 **named(server-side) cursor**로 `PAGE_SIZE`씩 `fetchmany`.
  3) `generate_soup_and_gcs_map_fn`: 페이지 안 모든 본문을 BeautifulSoup으로 파싱해 서명(`/thumb/user/stamp/{id}-..`)·`data-id` attach_id를 모은 뒤 `storage_mapping`을 **한 번** IN 조회해 `attach_id → gcs_path` 맵을 만든다.
  4) `replace_content`: 태그마다 원래 `src`를 `mig-src`에 보관하고 `src`를 `/api/thumb/.../{bucket}/{gcs_path}`로 바꾼다. 암호화 토큰 URL은 `get_do_decrypt_hex`(jar subprocess)로 attach_id를 얻고 1건씩 `storage_mapping` 조회.
  5) 쓰기 커넥션에서 `execute_values`로 `pre_dopgw.go_appr_doc_bodies`에 배치 INSERT 후 commit.
- SQL 경로 (`gw_appr_doc_body_editor_sql_task.py:55-59`):
  1) `01_initNreset.sql`(본문·이력 두 개): range 테이블 TRUNCATE 후 `generate_series(min_id, max_id, 50000)`로 range 적재, 문서별 최신 `created_at` 캐시 테이블 준비.
  2) `02_transform_function.sql` → `03_dbrangeworker.sql` → `04_decryptfunction.sql`: 함수 설치.
  3) `run_doc_bodies_range.expand(worker_id=0..APPR_EDITOR_WORKER-1)`: 각 태스크가 세션 변수 `gw_mig.aes_key`를 설정하고 `SELECT gw_mig_process_one_doc_bodies_range()`를 `false`가 나올 때까지 반복, 매 호출마다 commit.
- 태그 검증 DAG(`gw_editor_tag_validation_dag.py` 등): 원본 본문을 `LIMIT/OFFSET`으로 읽어 `img/script/iframe/source`가 아닌데 `src`를 가진 태그를 `logging.info`로 남긴다. 실패 판정은 없다.

**핵심 코드**
```sql
-- [공유] sql/gw/pre/editor/03_dbrangeworker.sql:27-75 (range worker 1회 호출)
  WITH picked AS (
    SELECT range_id, start_id, end_id
    FROM public.mig_doc_bodies_ranges
    WHERE done_at IS NULL
    ORDER BY range_id
    FOR UPDATE SKIP LOCKED          -- 다른 워커가 잡은 range는 기다리지 않고 건너뜀
    LIMIT 1
  ),
  claimed AS (
    UPDATE public.mig_doc_bodies_ranges r
    SET claimed_at = now(), claimed_by = pg_backend_pid()
    FROM picked p WHERE r.range_id = p.range_id
    RETURNING p.range_id, p.start_id, p.end_id
  )
  SELECT range_id, start_id, end_id INTO v_range_id, v_start_id, v_end_id FROM claimed;

  IF v_range_id IS NULL THEN
    RETURN false;                   -- 남은 range 없음 → Airflow 루프 종료
  END IF;

  INSERT INTO pre_dopgw.go_appr_doc_bodies (id, contents, user_id, created_at, updated_at)
  SELECT s.id,
         public.gw_mig_transform_contents(s.contents, v_fixed_bucket, v_aes_key, v_encoding),  -- HTML 치환
         s.user_id, COALESCE(c.created_at, now()), COALESCE(c.created_at, now())
  FROM asisgw.go_appr_doc_bodies s
  LEFT JOIN public.mig_doc_body_latest_created_at c ON c.doc_body_id = s.id   -- 미리 만든 캐시
  WHERE s.id BETWEEN v_start_id AND v_end_id;                                 -- PK range scan

  UPDATE public.mig_doc_bodies_ranges SET done_at = now() WHERE range_id = v_range_id;
  RETURN true;
```
```python
# [공유] dags/dop/gw/editor/gw_appr_doc_body_editor_sql_task.py:61-78 (Airflow 쪽 루프)
@task(task_id='run_doc_bodies_range_task', pool='gw_pool')
def run_doc_bodies_range(worker_id: int):
    from dop.common.constants import AES_KEY
    conn = hook.get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SET gw_mig.aes_key = %s", (AES_KEY,))   # 키는 세션 변수로만 전달
            while True:
                cur.execute("SELECT public.gw_mig_process_one_doc_bodies_range();")
                got = cur.fetchone()[0]
                conn.commit()                                  # range 1개 = 트랜잭션 1개
                if got is True:
                    continue
                break
    finally:
        conn.close()
```
```python
# [공유] gw_appr_doc_body_editor_tasks.py:404-430 (Python 경로의 치환 규칙 일부)
            elif data_src and data_src.startswith("/thumb/user/stamp/"):      # 결재 서명 이미지
                img["mig-src"] = data_src                                      # 원본 경로 보존
                attach_id = data_src.split("/")[-1].split("-")[0]
                img["src"] = f"/api/thumb/user/small/{bucket_name}/{gcs_path_map.get(attach_id)}"
            elif data_src and data_src.startswith("/thumb/temp"):
                continue                                                       # 임시파일은 손대지 않음
            elif data_src and (data_src.startswith("/go/thumb/attach/original") or data_src.startswith("/thumb/attach/original")):
                decrypt_attach_id = get_do_decrypt_hex(data_src)               # java -jar DoDecryptHex.jar <token>
                decrypt_gcs_path = get_do_gcs_path(cursor, decrypt_attach_id)  # storage_mapping 1건 조회
                img["mig-src"] = data_src
                img["src"] = f"/api/thumb/attach/original/{bucket_name}/{decrypt_gcs_path}"
```

**데이터·설정**
- 테이블: 원본 `asisgw.go_appr_doc_bodies`(+ 이력 `_h`), 대상 `pre_dopgw.go_appr_doc_bodies`, 작업 큐 `public.mig_doc_bodies_ranges(range_id, start_id, end_id, claimed_at, claimed_by, done_at)`, 캐시 `public.mig_doc_body_latest_created_at(doc_body_id PK, created_at)`, 경로 조회 `public.storage_mapping`.
- 상태값: `done_at IS NULL` = 미처리. range 크기 `50000`(`01_initNreset.sql:45`).
- Variable: `type_gw_transfer_doc_body`(script|sql), `appr_pool_slot`(Python `divide` 수, 기본 8), `appr_editor_worker`(SQL worker 수, 기본 4). 상수 `AES_KEY`(값 비공개), `CHUNK_SIZE_DOC_BODY_CONTENT`.
- 버킷: 결재는 `dop-employee-approval` 고정, 게시판 등은 `storage_mapping.app_code`로 찾고 없으면 `dop-employee-board`.

**왜 이렇게 짰나**
- Python 경로의 비용: 본문을 DB → Airflow로 끌어와 파싱하고 다시 INSERT. 암호화 토큰은 이미지마다 JVM을 띄우고(`subprocess java -jar`), 토큰마다 `storage_mapping`을 1건씩 조회한다.
- Python 경로 개선(8bc0125a, bc99999e): `id < last_id LIMIT n` 반복 조회 → named cursor 스트리밍, 1:N 조인 후 GROUP BY → `DISTINCT ON (doc_body_id)` 서브쿼리, 페이지 안 attach_id를 모아 IN 1회 조회, 읽기/쓰기 커넥션 분리. chunk 200 → 800(bc99999e, 이전 조사 기준).
- SQL 경로: 데이터가 DB 밖으로 나가지 않고, 복호화도 pgcrypto(`decrypt_iv(..., 'aes-cbc/pad:none')` + 수동 PKCS#7 제거)로 DB 안에서 끝난다. 변환 함수도 "attach_id를 먼저 다 모으고 storage_mapping은 1회만 조회해 jsonb 맵으로 캐시"(`02_transform_function.sql` 머리 주석).
- range + `SKIP LOCKED`: 워커끼리 같은 range를 안 잡고 대기 없이 다음 range로 간다. 호출 1번 = range 1개 = 트랜잭션 1개라 중간에 죽어도 그 range는 rollback되어 `done_at`이 NULL로 남고 다시 잡힌다. 워커 수는 Airflow mapped task 수로만 조절.
- `id % slots` 샤딩(Python)과 달리 range는 PK 구간 스캔이라 인덱스 range scan 한 번으로 끝난다.
- range 크기 트레이드오프는 SQL 주석에 있다: "너무 크면 워커 1개가 오래 잡고, 너무 작으면 claim/commit 오버헤드가 커짐".
- 두 방식을 Variable 분기로 남겨 둔 이유: 문제가 생기면 Python으로 돌아갈 수 있게. (의도 기록은 없음 → 확인 필요)

**바뀌어 온 이력**
- 2025-08 ~ 09: `gw_editor_tasks.py`, `gw_appr_doc_body_editor_tasks.py` Python 변환, `divide` 분할 수를 `Pool.get_pool('gw_pool').slots`로 계산하던 시기도 있음(18c434bc diff).
- 2026-01-02~05 `8bc0125a`, `bc99999e`: "mig editor 성능 개선".
- 2026-01-15 `c1293e4d`: SQL 변환(`sql/gw/pre/editor/*`) 추가. 같은 날 `4b205b9a`/`13bda883`: script/sql 분기 Variable.
- (단독형) 2026-04-23 `491e5faf`/`cb39f3b6`: range worker priority_weight 85, `94f19475`(2026-06-23) `APPR_POOL_SLOT = cpu_count//4` — 이전 조사 기준.

**면접 30초 설명**
"결재 본문 HTML 안에 서명 이미지, 첨부 이미지 경로가 3.0 주소로 박혀 있어서, 첨부 이관 때 만든 storage_mapping의 새 경로로 바꿔야 했습니다. 처음엔 Python에서 BeautifulSoup으로 파싱하고 암호화 토큰은 Java jar로 복호화했는데, 데이터를 DB 밖으로 꺼냈다 넣는 비용이 컸습니다. 그래서 PK를 5만 단위 range로 나눈 작업 테이블을 만들고, 워커들이 `FOR UPDATE SKIP LOCKED`로 range를 하나씩 가져가 DB 함수 안에서 치환과 복호화까지 끝내게 바꿨습니다. Airflow는 워커 수만큼 태스크를 띄워서 남은 range가 없을 때까지 함수를 부르기만 합니다."

**헷갈리기 쉬운 점**
- 태그 검증은 "검증 통과/실패"가 아니라 **로그 수집**이다.
- 원래 `src`를 `mig-src` 속성에 남긴다(되돌리기·추적용). 매핑을 못 찾으면 Python은 `src`를 `.../None` 또는 빈 경로로 만들 수 있고(로그만 남김), SQL은 원본을 유지한다(`02_transform_function.sql` "매핑이 없으면 원본 유지"). 두 방식의 결과가 완전히 같지는 않다.
- Python 경로에서 `table`/`td`도 `src`를 가질 수 있어서 함께 본다.
- 변환 함수 기본 세션 변수명은 `gw.aes_key`이지만 range worker는 `gw_mig.aes_key`를 읽어 인자로 넘긴다(동작에는 문제 없음).
- `03_dbrangeworker.sql` 한국어 주석이 인코딩이 깨져 있다.
- 작성 주체(DBA 협업 여부)는 git으로 확인 안 됨.

---

### 4. master/worker 구조와 데이터 이동  (2026-01 ~ 2026-08 · 356e6cc8, de61556c, 7c39173a, 78c4fe04, 8650791d)

**내가 한 범위**
- 본인: master 메인 DAG `310_data_main`(최다 기여), `trigger_worker_api`(REST로 worker DAG trigger), `_upsert_worker_variable` 일부, feature 브랜치의 worker→master REST 콜백 전체.
- 동료: worker DAG `Main_worker` 대부분(hwgyun), sensor/폴링 코드 `_create_task_sensor`·`_poll_worker_state` 대부분(hwgyun 58 / 본인 20줄), **SSH 터널 master DB 접근 `master_db_access.py`(hwgyun 218줄 전부)**, **pre dump scp `worker_dump_to_master.py`(hwgyun 384 / jsb568 80)**.
- **REST 콜백은 `feature/company-insert-master-decoupling` 브랜치(2026-08-14, 커밋 7개)에만 있고 master에 머지되지 않았다.** 범위는 `Company_insert_worker` 하나.

**코드 지도**
| 파일 | DAG/태스크/함수 | 역할 |
|---|---|---|
| `dags/dop/main_manager.py` | `310_data_main` | worker 목록 루프 → worker별 trigger/sensor → 서비스별 merge |
| `dags/dop/main_worker.py` | `Main_worker` | 원본 DB restore → 서비스 변환(pre_dop*) → pre dump |
| `dags/dop/common/common_tasks.py:253-279` | `trigger_worker_api` | `POST http://{worker}:8080/api/v1/dags/{id}/dagRuns`, `dag_run_id` 고정 |
| `common_tasks.py:297-319` | `_upsert_worker_variable` | PATCH → 404면 POST |
| `common_tasks.py:361` | `upsert_worker_connection` | worker Connection upsert |
| `common_tasks.py:645-723` | `_create_task_sensor`, `_poll_worker_state`, `_check_dag_state`, `_create_dag_sensor` | `PythonSensor(mode='reschedule', poke 30s)`로 worker 상태 폴링 |
| `dags/dop/common/master_db_access.py` | (hwgyun) | worker → master DB, SSH local port-forward |
| `dags/dop/common/worker_dump_to_master.py` | `create_worker_pre_dump_groups` (hwgyun/jsb568) | pre 스키마 dump를 master로 scp |
| (feature) `dags/dop/common/master_callback.py` | `trigger_master_dag` | worker → master REST 콜백, 409=성공 |
| (feature) `dags/dop/common/uuid/company_apply_master.py` | `Company_apply_master` | worker payload를 master DB에 반영 |
| (feature) `dags/dop/common/uuid/company_insert_worker.py` | `Company_insert_worker` | 로컬 조회 → payload → master 콜백 |

**흐름** (`310_data_main`, `main_manager.py:138-311`)
1) `init_cluster_number_master` → `validate_membership_ids` → `init_variable_master` → [merge 스키마 생성 분기 / acc 스키마 / worker 대상 검증].
2) worker 대상마다 cluster 번호 전파 → `trigger_init_variable_worker`(worker Variable seed) → `ready_mig_join_task`.
3) worker마다(`for index, worker in enumerate(worker_targets)`, `:196`): `trigger_uuid_generate` → `trigger_join_date_worker` → `trigger_storage_mapping` → `trigger_main_manager_group`. 각 그룹은 "REST trigger 태스크 → 서비스별 sensor 그룹" 구조.
4) worker 쪽 `Main_worker`: source DB dump/restore → 초기화·인덱스 생성 → 서비스별 `v3_to_pre_v4 → validate (→ fk)` → `pre_dump_groups[서비스]`(dump를 master로 scp).
5) master sensor가 `/dagRuns/{run_id}/taskInstances/{task}` 상태를 30초마다 확인, 성공이면 `service_merge_group`의 서비스별 `service_merge_pipeline`(pre → merge 스키마).
6) post 병합은 별도 DAG `420_merge_to_post`(Variable `skip_merge_to_post`를 False로 바꾸고 수동 실행).
- feature 브랜치의 상향 콜백 흐름: master `130_setup_company_insert`가 `trigger_worker_api(..., apply_run_id_prefix=...)`로 worker를 trigger하면서 `conf.apply_run_id`를 내려줌 → worker `Company_insert_worker`가 로컬 asisgw를 조회해 payload를 만들고 `trigger_master_dag("Company_apply_master", apply_run_id, conf)` → master `Company_apply_master`가 master DB에 반영 → master는 `_poll_local_dag_run_state`(로컬 메타DB `DagRun.find`)로 완료 대기.

**핵심 코드**
```python
# [단독] dags/dop/common/common_tasks.py:262-279 (master → worker DAG trigger, 본인)
    if data is None:
        data = {}
    # Airflow run_id 기반으로 고정 (재실행해도 같은 DAG 실행 내에서는 동일)
    run_id = context['run_id'].replace(':', '').replace('+', '')
    data.setdefault('dag_run_id', f"master_triggered_{run_id}")
    _ensure_worker_dag_unpaused(url)                 # paused면 먼저 unpause
    response = requests.post(url, auth=(WORKER_API_USER, WORKER_API_PASSWORD),
                             headers={'Content-Type': 'application/json'}, json=data)
    response.raise_for_status()
    return data['dag_run_id']                        # XCom → sensor가 이 run_id로 폴링

# [단독] common_tasks.py:671-676 (_check_dag_state, 폴링 판정)
    state = body.get('state') if isinstance(body, dict) else None
    if state in ('failed', 'upstream_failed'):
        raise AirflowFailException(f"Worker DAG 실행 실패: state={state}")   # 재시도 없이 즉시 실패
    if state == 'skipped':
        raise AirflowFailException(f"Worker DAG 실행 스킵: state={state}")
    return state == 'success'                        # False면 reschedule 후 30초 뒤 다시
```
```python
# [단독] feature/company-insert-master-decoupling: dags/dop/common/master_callback.py:49-82
def trigger_master_dag(dag_id, dag_run_id, conf):
    if not dag_run_id:
        raise AirflowFailException("dag_run_id 는 필수입니다. master 가 conf.apply_run_id 로 내려준 값을 쓰세요.")
    conn = _require_master_api_connection()          # Connection 'master_api' (100_setup_worker_state가 팬아웃)
    url = build_master_dag_runs_url(conn.host, conn.port, dag_id)
    response = requests.post(url, auth=(conn.login, conn.password), headers={...},
                             json={"dag_run_id": dag_run_id, "conf": conf or {}}, timeout=30)
    if response.status_code == 409:                  # 같은 run_id가 이미 있음 = worker retry → 성공 취급
        return dag_run_id
    if response.status_code >= 400:
        raise AirflowFailException(f"master DAG trigger 실패: ... status={response.status_code} ...")
    return dag_run_id
```

**데이터·설정**
- 스키마 흐름: worker `asisgw`(고객 원본 restore) → worker `pre_dop{iam,gw,mail,chat,attend,hr,ai,drive,doas,linkplus}` → (dump/scp) → master `merge_dop*` → post.
- master 메타: worker 대상 목록(`worker_targets`, `worker_ip`, `worker_id`), Variable `skip_merge_to_post`, Param `Init_merge_schemas`.
- worker REST 인증: `WORKER_API_USER`/`WORKER_API_PASSWORD`(constants, 값 비공개). feature 브랜치: Connection `master_api`(login/password 필수 검사), conf 키 `apply_run_id`, XCom 키 `apply_run_id`.
- sensor: `poke_interval=30`, task sensor `timeout=30분`, DAG sensor `timeout=30시간`, master 로컬 sensor `timeout=3시간`.

**왜 이렇게 짰나**
- 고객 데이터가 고객 VPC 안에 있어서 변환(worker)과 병합(master)을 나눔(`docs/overview/system-architecture.md`).
- master→worker를 REST로 한 이유: worker DB·파일에 직접 붙지 않고 worker Airflow가 자기 DAG를 돌게 함. `dag_run_id`를 master run_id로 고정해서 master 태스크를 다시 돌려도 같은 worker run을 가리키게 함.
- sensor `mode='reschedule'`: 최대 30시간 대기라 poke 모드면 worker 슬롯을 계속 잡음.
- feature 브랜치(상향 콜백): docstring 기준 "worker → master DB(5432) 직결과 master_ssh(22) 포트포워딩이 모두 금지". 큰 데이터는 dump scp, 작은 결과는 REST `conf`. `apply_run_id`를 worker가 아니라 **master가 worker별로 만들어 내려주는** 이유도 docstring에 있다: manager가 worker N대에 팬아웃할 때 worker `dag_run_id`가 전부 같아서, worker가 파생하면 apply run_id가 충돌한다.
- 409=성공: worker 태스크 retry 때 같은 반영이 두 번 일어나지 않게 하는 멱등 장치.
- 트레이드오프: `conf`는 master 메타DB에 JSON으로 저장되므로 큰 payload에는 맞지 않음(구체 한도 확인 필요).

**바뀌어 온 이력**
- 2026-01-28 `f8d6e89a`: 공유형 복제로 단독형 시작. 2026-02-19 `21f8c808`: 공유형 이관 종료 후 최신화.
- 2026-03-03 `356e6cc8`: `trigger_worker_api`(본인, 이전 조사 기준).
- hwgyun `0957ec5d`, `f3176c3c`: SSH 터널 master DB 접근(DOVPCMIG-125/145).
- 2026-08-14 feature 브랜치: `3b8320b0` cluster_id 결정 순수 함수 분리 → `de61556c` master_callback → `78c4fe04` apply run_id 주입 + 로컬 DagRun sensor(+ 테스트 308줄) → `69e0de67` sensor 테스트 → `7c39173a` Company_apply_master → `8650791d` Company_insert_worker에서 master DB 접근 제거 → `d632dd81` master_api Connection 팬아웃.

**면접 30초 설명**
"단독형은 고객 VPC 안의 worker Airflow가 원본 DB를 복원·변환해 pre 스키마를 만들고, 중앙 master가 그것들을 merge해 post에 반영합니다. 저는 master 메인 DAG를 맡았고, master가 worker Airflow REST API로 Variable을 심고 DAG를 trigger한 뒤 reschedule 모드 sensor로 기다리는 구조를 짰습니다. 이후 worker에서 master DB로 붙는 경로가 정책상 막히는 상황에 대비해, worker가 계산 결과를 master DAG의 conf로 올리고 master가 자기 DB에 반영하는 REST 콜백을 feature 브랜치로 만들었습니다. master가 run_id를 내려주고 409를 성공으로 처리해 재시도해도 중복 반영이 없게 했습니다."

**헷갈리기 쉬운 점**
- SSH 터널(`master_db_access.py`), dump scp(`worker_dump_to_master.py`)는 **동료 코드**.
- REST 콜백은 **미머지 feature 브랜치**, 범위는 `Company_insert_worker` 하나. master HEAD의 worker는 여전히 SSH 터널로 master DB에 접근한다.
- 폴링 sensor 코드도 대부분 hwgyun. 내 코드는 trigger 쪽.
- runbook에 `master_db`/`master_ssh` Connection 팬아웃이 아직 적혀 있다(정책 변경이 master에 다 반영된 것은 아님).

---

### 5. JSON 속 숨은 PK 변환·검증  (2026-05-21 ~ 06-16 · 6a2e5442, a53c85e9, 32421893, 19fea3b7)

**내가 한 범위**
- 본인: `dags/dop/gw/applet/_common.py`(649줄 전부), `dags/dop/gw/validate/common.py`(207줄 전부), 이를 쓰는 applet/works 변환 태스크·검증 태스크, `tests/gw/test_gw_applet_*`.
- 동료: 테이블군별 PK offset 분류(`add_value` vs `gw_pk_add_value`) 정리 `docs/overview/gw-pk-offset-classification.md`(hwgyun, DOVPCMIG-48).

**코드 지도**
| 파일 | DAG/태스크/함수 | 역할 |
|---|---|---|
| `dags/dop/gw/applet/_common.py:22-32` | `_shift_id` | 양수 숫자만 offset 가산, 타입 유지 |
| `_common.py:46-98` | `_convert_members`, `_convert_depts` | 조직도 멤버(list/dict 두 포맷)·부서 |
| `_common.py:137-236` | `_convert_rule_values*`, `_convert_rule_in_props` | `rule.values`의 USER/USERS/DEPTS 등 |
| `_common.py:237-276` | `_convert_query_string` | `key:(v1 v2)` / `key:123` 정규식 치환 |
| `_common.py:332, 485` | `_convert_report_item_data`, `_convert_component` | 리포트 아이템·works 템플릿 컴포넌트 |
| `_common.py:584-649` | `convert_applet_field_properties` | `go_applet_fields.properties_as_json` 진입점 |
| `dags/dop/gw/applet/gw_applet_fields_tasks.py` | `gw_transfer_applet_fields_89_task` | 원본 조회 → 변환 → `pre_dopgw` INSERT |
| `dags/dop/gw/validate/common.py` | `normalize_numeric`, `normalize_json`, `compare_jsons`, `diff_json` | 원본에 같은 offset을 적용·정렬한 뒤 결과와 비교 |
| `dags/dop/gw/validate/gw_applet_*_tasks.py` 등 | 검증 태스크 | 테이블별 비교 실행 |

**흐름** (`gw_applet_fields_tasks.py:27-71` 예)
1) `go_applet_fields` 전체에서 `cid → (value_type, field_type)` lookup 딕셔너리를 먼저 만든다(queryString·rule에서 "이 cid가 조직도 필드인가"를 판단하려고).
2) 원본을 `ORDER BY id DESC LIMIT n OFFSET m`으로 페이지 조회.
3) 행마다 PK 컬럼은 `_shift_col(row_id, gw_pk_add_value)`, JSON 컬럼은 `convert_applet_field_properties(...)`.
4) `execute_values`로 `pre_dopgw.go_applet_fields`에 INSERT, 페이지마다 commit.
5) 검증 DAG: 같은 행의 원본 JSON을 `normalize_json(asis, is_source=True)`(offset 가산 + 리스트 정렬), 결과 JSON을 `normalize_json(dop, False)`로 정규화해 `==` 비교, 다르면 `diff_json`으로 경로별 차이를 로그.

**핵심 코드**
```python
# [단독] dags/dop/gw/applet/_common.py:22-32
def _shift_id(value, offset):
    """양수 숫자형 또는 양수 숫자 문자열이면 offset 을 더해 반환. 입력 타입(int/str) 유지.
    음수/0 은 sentinel 또는 오류값으로 간주하여 원본 반환."""
    if isinstance(value, bool):          # bool은 int의 하위 타입 → 먼저 걸러야 True+offset 사고가 안 남
        return value
    if isinstance(value, int):
        return value + offset if value > 0 else value
    if isinstance(value, str) and value.lstrip('-').isdigit():
        v = int(value)
        return str(v + offset) if v > 0 else value   # "123" → "1000123" (문자열 유지)
    return value

# [단독] _common.py:249-276 (_convert_query_string 내부)
    def _replace(match):
        key = match.group(1)
        paren_values = match.group(2)    # status:(1 2 3)
        single_value = match.group(3)    # status:3
        if key == 'status':
            offset = gw_pk_add_value                       # go_applet_statuses.id
        elif key in field_lookup:
            value_type, field_type = field_lookup[key]
            if field_type in ('org', 'org_dept') and value_type in _ORG_VALUE_TYPES:
                offset = add_value                         # 조직도(사용자/부서) id
            else:
                return match.group(0)                      # 그 외 필드는 손대지 않음
        else:
            return match.group(0)
        if single_value is not None:
            v = int(single_value)
            return f"{key}:{v + offset}" if v > 0 else match.group(0)
        parts = paren_values.split()
        new_parts = [str(int(p) + offset) if p.lstrip('-').isdigit() and int(p) > 0 else p for p in parts]
        return f"{key}:({' '.join(new_parts)})"
    return _QUERY_PART_RE.sub(_replace, query_str)   # r'([\w_-]+):(?:\(([^)]*)\)|(-?\d+)(?!\d))'

# [단독] _common.py:647-649 (convert_applet_field_properties 끝)
    if not dirty:
        return props_str                 # 바꾼 게 없으면 원본 문자열 그대로 (공백·키 순서 보존)
    return json.dumps(props, ensure_ascii=False)
```

**데이터·설정**
- offset 두 종류: `ADD_VALUE`(조직: user/dept id), `GW_PK_ADD_VALUE`(GW 테이블 PK: applet id, status id, companyId 등). 상수는 `dop.common.constants`, 값은 Variable 기반(회사별).
- 대상 컬럼 예: `go_applet_fields.properties_as_json`, works 템플릿, applet forms/filter conditions/bf conditions/report items, `appr_classify_rules`, `appr_integration_outputs`, outbounds (validate 디렉터리 파일 목록 기준).
- `_ORG_VALUE_TYPES = {'USER','USERS','DEPTS'}`.

**왜 이렇게 짰나**
- 여러 고객 DB를 하나로 합치면 PK에 offset을 더해야 하는데, 이 값들은 JSON 문자열 안에 있어서 SQL `+ add_value`로는 못 바꾼다.
- 순수 함수(`Airflow 의존성 없음`, 파일 머리 주석)로 분리해 pytest로 포맷별 케이스를 고정했다(`tests/gw/test_gw_applet_*`).
- 0·음수는 "미지정" 같은 sentinel로 보고 유지, 타입(int/str)은 원본 유지: 애플리케이션이 문자열 id를 기대하는 곳이 있어서. 단 `19fea3b7`(2026-06-16)에서 `rule.values.id`는 변환 케이스에 한해 문자열로 저장하도록 바꿈(`str_id=True`).
- 검증을 "원본에 같은 규칙을 적용한 기대값 vs 결과" 비교로 한 이유: 키 순서·리스트 순서 차이를 정렬로 지우고 진짜 값 차이만 남기려고. 다르면 경로별 diff를 남긴다.
- 트레이드오프: 페이지 조회가 `LIMIT/OFFSET`이라 뒤로 갈수록 느려질 수 있음. 검증 정규화 로직이 변환 로직과 비슷하게 짜여 있어서, 같은 오해가 양쪽에 있으면 검증이 못 잡는다.

**바뀌어 온 이력**
- 2026-05-21 `6a2e5442` "validate json" → 05-27 `a53c85e9` "works json pk - applet_form" → 05-29 `1376c840` report_items, `3cfe8ec1` "value도 확인하는 케이스" → 06-01 `32421893` "json add value", `b4857d5d`/`876f4c2e` works_templates → 06-02 `7f050c0f` report item → 06-04 `fe0aa5f0` applet field → 06-15 `346a921d` works add_value, `16ed2f1f` "타입 변환으로 인한 이슈 수정", `2db7e6ed` works pk → 06-16 `19fea3b7` "rule.values.id str로 저장하도록 변경".

**면접 30초 설명**
"여러 고객 데이터를 한 DB로 합치려면 PK에 offset을 더해야 하는데, Works·Applet 설정은 멤버·부서·조건값 ID가 JSON 문자열 안에 들어 있어서 SQL로는 놓칩니다. 그래서 포맷별 변환 함수를 Airflow와 분리된 순수 함수로 만들었습니다. 양수 숫자만 offset을 더하고 원래 타입을 유지하며, queryString은 정규식으로 파싱하고 필드 정의를 미리 읽어 조직도 필드인 경우에만 바꿨습니다. 검증은 원본에 같은 offset을 적용·정렬한 결과와 변환 결과를 비교하는 DAG로 했습니다."

**헷갈리기 쉬운 점**
- offset 분류 기준(어떤 테이블이 어떤 offset인지) 정리는 동료 작업. 내 기여는 JSON 쪽.
- `bool` 제외는 의도된 처리(파이썬에서 `isinstance(True, int)`가 True).
- 바뀐 게 없으면 원본 문자열을 그대로 돌려준다 → 결과 JSON의 공백·키 순서가 행마다 다를 수 있다.

---

### 6. chat 변환 pre-join + 부분 인덱스  (2026-04-17 · 2ad58b92)

**내가 한 범위**: 본인 커밋 1건(`2ad58b92` "[20260416] chat query 수정"). chat 변환 SQL 원본 작성자는 서비스 담당자(이전 조사).

**코드 지도**
| 파일 | DAG/태스크/함수 | 역할 |
|---|---|---|
| `sql/chat/pre/10_chat_room.sql` | chat v3→pre 변환 | `pre_dopchat.dop_chat_room` INSERT |
| `sql/chat/pre/14_chat_message.sql` | chat v3→pre 변환 | `pre_dopchat.dop_chat_message_temp` CTAS |
| `dags/dop/common/index/pg_index_tasks.py` | `index_create` (worker `index_create_task`) | 원본 asisgw에 변환용 인덱스 생성 |

**흐름**: worker `Main_worker`의 setup 체인에서 `index_create_task`가 먼저 인덱스를 만들고(`main_worker.py:151`), 이후 chat 변환 태스크가 위 SQL을 실행한다.

**핵심 코드** (2ad58b92 diff 기준)
```sql
-- [단독] sql/chat/pre/10_chat_room.sql (변경 후)
    -- 원본: 방마다 상관 서브쿼리 (select id ... where gcm.chat_room_id = gcr.id order by created_at desc limit 1)
    coalesce(last_msg.id + {{ var.value.add_value }}, 0) as last_sent_message_id,
    ...
    buddy_agg.user_id_set,
from asisgw.go_chat_rooms gcr
    left join (
        select distinct on (chat_room_id) chat_room_id, id      -- 방별 최신 메시지 1건을 한 번에
        from asisgw.go_chat_messages
        where message_type not in ('ROOMLEAVE', 'ROOMINVITE', 'ROOMJOIN', 'ROOMKICKOUT')
           or message_type is null
        order by chat_room_id, created_at desc                  -- idx7_go_chat_messages(chat_room_id, created_at desc)
    ) last_msg on last_msg.chat_room_id = gcr.id
    left join (
        select chat_room_id, to_jsonb(array_agg(user_id + {{ var.value.add_value }})) as user_id_set
        from asisgw.go_chat_buddies
        where join_room = true                                  -- 부분 인덱스 조건과 동일
        group by chat_room_id
    ) buddy_agg on buddy_agg.chat_room_id = gcr.id

-- [단독] dags/dop/common/index/pg_index_tasks.py (추가된 1줄)
"CREATE INDEX IF NOT EXISTS idx_gcb_chat_room_join on asisgw.go_chat_buddies using btree (chat_room_id, user_id) where join_room = true;",

-- [단독] sql/chat/pre/14_chat_message.sql (변경 후 일부)
        when el.target_message is not null then 'EMOTICON'     -- 원본: when exists (select 1 from emoticon_list ...)
    gcr.company_id + {{ var.value.add_value }} as company_id,  -- 원본: (select company_id from go_chat_rooms where id = gcm.chat_room_id)
from asisgw.go_chat_messages gcm
    left join asisgw.go_chat_rooms gcr on gcr.id = gcm.chat_room_id
    left join emoticon_list el on el.target_message = gcm.message   -- emoticon_list는 select distinct unnest(...)로 중복 제거
```

**데이터·설정**: `asisgw.go_chat_rooms`, `go_chat_messages`, `go_chat_buddies` → `pre_dopchat.dop_chat_room`, `dop_chat_message_temp`. 인덱스 `idx7_go_chat_messages(chat_room_id, created_at desc)`(기존), `idx_gcb_chat_room_join(chat_room_id, user_id) WHERE join_room = true`(추가). `{{ var.value.add_value }}`로 PK offset.

**왜 이렇게 짰나**
- 상관 서브쿼리는 바깥 행 수만큼 실행된다. 방별 최신 메시지·참여자를 미리 한 번 집계해 LEFT JOIN하면 테이블을 한 번씩만 읽는다.
- `chat_message`도 행마다 하던 방 조회·이모티콘 EXISTS를 hash join으로 바꿈. 이모티콘 목록에 `distinct`를 넣은 건 LEFT JOIN 시 메시지 행이 중복되지 않게 하려는 것(코드 주석).
- 부분 인덱스: `join_room = true`인 참여자만 쓰므로 조건을 인덱스에 넣어 크기를 줄임.
- 의미 보존: 서브쿼리와 pre-join 둘 다 같은 필터·같은 정렬(`created_at desc`)이라 결과는 같아야 한다. 단 `created_at`이 같은 메시지가 여러 개면 어느 것이 뽑히는지는 두 방식 모두 보장이 없다.
- 전후 실행 시간은 코드·커밋에 없음 → 확인 필요.

**바뀌어 온 이력**: 2026-04-17 `2ad58b92` 1회.

**면접 30초 설명**
"chat 방 변환 쿼리가 방마다 최신 메시지와 참여자 목록을 상관 서브쿼리로 구하고 있어서 방 수만큼 서브쿼리가 돌았습니다. 최신 메시지는 `DISTINCT ON`, 참여자는 `GROUP BY`로 한 번에 집계해 조인하도록 바꾸고, 실제로 쓰는 `join_room = true` 조건으로 부분 인덱스를 추가했습니다. 메시지 테이블도 행마다 하던 방 조회와 이모티콘 EXISTS를 조인으로 바꿨습니다."

**헷갈리기 쉬운 점**
- 규모 수치가 주석끼리도 다르다: chat_room은 "15만 행 × N번", chat_message 주석에는 "15K rooms", 같은 파일의 예전 주석에는 "mid null 개수: 729694, not null 개수: 80135"(합 약 81만). 포트폴리오의 "40만 행"과도 다름 → 면접 전 실제 건수 확인 필요.
- 전체 방을 다 집계하는 쿼리라 플래너가 인덱스 대신 seq scan + hash aggregate를 고를 수도 있다. "인덱스 덕분에 빨라졌다"보다 "N번 실행 → 1번 스캔"이 핵심.

---

### 7. sudo / exit code 판정 수정과 회귀 테스트  (2026-08-22 · 21a552ba)

**내가 한 범위**: 본인 커밋. 대상은 **경리회계(ACC) 첨부 업로드**(`dags/storage/tasks/acc/storage_tasks.py`), 같이 `storage_symlink_tasks.py` 멱등화. 커밋에 `Co-Authored-By: Claude` 줄이 있다.

**코드 지도**
| 파일 | DAG/태스크/함수 | 역할 |
|---|---|---|
| `dags/storage/tasks/acc/storage_tasks.py:274-276` | `_is_no_clobber_skip_only` | stderr에 `ERROR:`가 없으면 "이미 있어서 건너뜀"으로 봄 |
| `storage_tasks.py:278-327` | `_run_gsutil` | `gcloud storage cp --no-clobber` 500건 배치, exit code 판정, 실패 배치 1회 재시도 |
| `dags/storage/tasks/acc/storage_symlink_tasks.py` | `_create_fixed_symlink` | 이미 맞는 링크면 건드리지 않음 |
| `tests/storage/test_acc_upload_gcloud.py` | 9개 테스트 | 판정 회귀 테스트 |
| `tests/storage/test_acc_symlink_tasks.py` | 6개 테스트 | symlink 회귀 테스트 |

**흐름** (`_run_gsutil`)
1) 파일 경로를 500건씩 자름.
2) `gcloud storage cp --no-clobber <files...> <dest>`를 sudo 없이 실행.
3) exit 0 → 배치 전체 success. exit 1 + stderr에 `ERROR:` 없음 → no-clobber skip으로 보고 success.
4) 그 외 → stderr를 `logging.error`로 남기고, 로컬에 파일이 없는 레코드는 바로 fail, 있는 레코드만 모아 1회 재시도.
5) 결과는 공유형과 같은 `_validate_gcs_upload` → `_record_upload_result`로 넘어가 GCS에서 한 번 더 검증.

**핵심 코드**
```python
# [단독] dags/storage/tasks/acc/storage_tasks.py:296-325
    for i in range(0, len(file_paths), batch_size):          # batch_size = 500
        batch_paths = file_paths[i:i + batch_size]
        batch_records = file_records[i:i + batch_size]
        # sudo 로 감싸면 secure_path 에 gcloud 가 없거나 root 에 인증이 없어 즉시 실패한다.
        command = ["gcloud", "storage", "cp", "--no-clobber"] + batch_paths + [dest_bucket]
        output = subprocess.run(command, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=os.environ)

        if output.returncode == 0:
            success.extend(batch_records)
        elif output.returncode == 1 and _is_no_clobber_skip_only(output.stderr):
            # --no-clobber로 인해 이미 GCS에 존재하는 파일만 skip된 경우 → 성공 처리
            success.extend(batch_records)
        else:
            logging.error("gcloud storage cp 업로드 실패 (exit_code=%d): %s", output.returncode, output.stderr)
            existing_records = [r for r in batch_records if os.path.exists(r[1])]
            missing_records = [r for r in batch_records if not os.path.exists(r[1])]
            if missing_records:
                fail.extend(missing_records)                 # 원본이 없으면 재시도해도 소용없음
            if existing_records:
                retry_cmd = ["gcloud", "storage", "cp", "--no-clobber"] + [r[1] for r in existing_records] + [dest_bucket]
                retry_out = subprocess.run(retry_cmd, ...)
                if retry_out.returncode == 0 or _is_no_clobber_skip_only(retry_out.stderr):
                    success.extend(existing_records)
                else:
                    fail.extend(existing_records)

# [단독] tests/storage/test_acc_upload_gcloud.py:78-91 (운영에서 본 케이스를 그대로 고정)
def test_silent_nonzero_exit_is_failure(fake_run):
    """운영에서 관측된 케이스: exit != 0 인데 stderr 가 비어 있다. ..."""
    fake_run["results"].extend([(1, ""), (1, "")])          # 본 실행·재시도 모두 조용히 실패
    records = [_record(27, "/mnt/hdd0/nfs_data/doacc/a/f27")]
    result = module._run_gsutil(records, datetime.now(), DEST)
    assert result["fail_records"] == records
    assert result["success_records"] == []
```

**데이터·설정**: `storage_mapping`(ACC용 스키마 `create_mapping_schema_acc.sql`) 같은 상태 컬럼. 인증은 `GOOGLE_APPLICATION_CREDENTIALS` 환경변수(utils.py가 세팅, 값 비공개). 테스트는 `subprocess.run`과 `os.path.exists`를 monkeypatch로 가짜로 바꿔 실제 gcloud 없이 판정 로직만 검증.

**왜 이렇게 짰나** (커밋 본문 근거)
- 증상: 업로드 안 됐는데 성공으로 기록되고, 뒤 단계 blob 검증에서만 "파일을 찾을 수 없습니다"로 드러남.
- 원인 1: `sudo -S gcloud storage cp`가 sudo의 `secure_path`·root 인증 부재·`env_reset`(→ `GOOGLE_APPLICATION_CREDENTIALS` 유실)로 gcloud 부트스트랩 전에 종료.
- 원인 2: `_run_gsutil`이 exit code를 안 보고 stderr를 gsutil 시절 정규식 `ERROR:.*\[(/[^\]]+)\]`로만 판정 → gcloud 에러·빈 stderr를 못 잡아 전건 success. stderr 로깅도 없었음. `69386a34`의 gsutil → gcloud 전환 때 DO만 재작성되고 ACC는 패턴만 교체됐기 때문.
- 수정: sudo·하드코딩 암호 제거, exit code 판정 + stderr 로깅, 같은 명령 두 번 실행하던 코드 제거, 500건 배치(ARG_MAX), `--no-clobber`로 재실행 멱등, 실패 배치는 존재분만 1회 재시도. DO 축 `_run_gcloud_local` 패턴에 맞춤.
- symlink: `/mnt/hdd0/nfs_data`가 root 소유라 링크 재생성 시 PermissionError → 이미 맞는 링크면 아무것도 안 하고, 실패는 `ln -sfn` 안내와 함께 `AirflowFailException`.

**바뀌어 온 이력**: `69386a34`(2026-05-20, gsutil → gcloud 전환, 원인 제공) → `21a552ba`(2026-08-22, 수정, master 머지됨).

**면접 30초 설명**
"경리회계 첨부가 실제로는 안 올라갔는데 성공으로 기록된 적이 있습니다. sudo로 감싼 gcloud가 환경 초기화 때문에 인증 정보를 잃고 바로 죽었는데, 판정은 exit code가 아니라 gsutil 시절 stderr 정규식이라 gcloud 에러를 못 잡아 전부 성공으로 분류됐습니다. sudo를 빼고 exit code로 판정하도록 바꾸고 실패 시 stderr를 남겼습니다. 운영에서 본 '종료 코드는 실패인데 stderr가 빈' 케이스를 포함해 subprocess를 가짜로 바꾼 회귀 테스트 15개를 붙였습니다."

**헷갈리기 쉬운 점**
- 대상은 **경리회계 첨부**. DO 첨부는 이미 `_run_gcloud_local`로 exit code 판정 중이었다.
- 테스트 수: 커밋 본문은 10+5, 실제 `def test_`는 9+6 = 15.
- exit 1 + `ERROR:` 없는 stderr를 skip으로 보는 부분은 여전히 stderr 문자열에 의존한다. 그리고 재시도 쪽 조건은 `returncode == 0 or _is_no_clobber_skip_only(...)`라 exit 코드 1로 한정하지 않는다(본 실행보다 느슨). 최종 안전망은 뒤의 GCS 검증.
- 이 커밋 diff에는 지운 sudo 암호가 남아 있으니 `git show`로 띄우지 말 것.

---

### 8. 실물 파일 확인 (순차 + 10초 타임아웃, 20 스레드 시도·원복)  (2026-06-08 ~ 06-09 · 15358a84, e08eb56c, 36f28ec3)

**내가 한 범위**: 본인. `dags/storage/tasks/do/storage_check_mount_tasks.py` (DAG `storage_check_mount_file_dag_for_do`).

**코드 지도**
| 파일 | DAG/태스크/함수 | 역할 |
|---|---|---|
| `storage_check_mount_tasks.py:12-28` | `_safe_isfile` | `test -f`를 subprocess로 실행, 10초 타임아웃 → None |
| `storage_check_mount_tasks.py:31-104` | `check_mount_file_task` | 미완료 레코드를 1000건씩 읽어 순차 확인, 집계, 타임아웃 있으면 실패 |

**흐름**
1) DAG param `log_mode`(`missing` 기본 | `existing`).
2) `storage_mapping`에서 `execute_flag = true AND metadata_success_flag = false AND app_code != 'NONE' AND company_uuid IS NOT NULL`인 행을 뽑고, 경로에서 `app_path`를 정규식으로 꺼내 `lab/device/ci/user`는 제외.
3) `fetchmany(1000)`으로 돌며 행마다 `_safe_isfile(path)`.
4) `None`(타임아웃)은 따로 세고, `missing` 모드면 없는 파일, `existing` 모드면 있는데 이관 안 된 파일을 경고 로그 + `app_path`별 Counter.
5) 끝에 합계를 찍고, 타임아웃이 1건이라도 있으면 `RuntimeError("NFS 복구 후 재실행")`.

**핵심 코드**
```python
# [단독] dags/storage/tasks/do/storage_check_mount_tasks.py:9-28
FILE_CHECK_TIMEOUT = 10  # NFS hung 방지: subprocess가 이 시간 초과 시 타임아웃 처리

def _safe_isfile(path: str):
    """
    NFS hung 시 스케줄러 프로세스 블록을 막기 위해 subprocess로 격리.
    반환값: True=존재, False=없음, None=타임아웃(확인 불가)
    """
    if not path:
        return False
    try:
        result = subprocess.run(['test', '-f', path], timeout=FILE_CHECK_TIMEOUT, capture_output=True)
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        logging.warning(f"[WARN] 파일 확인 타임아웃(NFS 무응답): {path}")
        return None                          # "없음"과 "모름"을 구분

# [단독] storage_check_mount_tasks.py:84-104
                    result = _safe_isfile(path)
                    if result is None:
                        timeouts += 1
                    elif log_mode == 'existing' and result:
                        ...
                    elif log_mode == 'missing' and not result:
                        ...
    if timeouts > 0:
        raise RuntimeError(f"NFS 무응답으로 {timeouts}개 파일을 확인하지 못했습니다. NFS 복구 후 재실행하세요.")
```

**데이터·설정**: Connection `mig_db`, `CHUNK_SIZE = 1000`, `FILE_CHECK_TIMEOUT = 10`, param `log_mode`. 대상 = 재시도까지 끝났는데 아직 `metadata_success_flag = false`인 첨부.

**왜 이렇게 짰나**
- 목적: 미이관 첨부를 "원본 파일 자체가 없음"과 "있는데 안 올라감"으로 나누기.
- `15358a84`(06-08) 커밋 메시지: "파일 존재 여부 체크를 ThreadPoolExecutor(20) 병렬 처리로 변경 → **스케줄러 heartbeat 끊김 방지**", SQL도 `regexp_split_to_array` CTE를 `split_part CASE`로 단순화.
- `e08eb56c`(06-09) "첨부 예외 추가": ThreadPool 제거, 다시 순차 `os.path.isfile`. **제거 이유는 커밋에 없음 → 확인 필요**.
- `36f28ec3`(06-09) "파일 nfs": `os.path.isfile`을 `test -f` subprocess + 10초 타임아웃으로 감싸 NFS 무응답이 태스크 프로세스를 묶지 않게 하고, 타임아웃이 있으면 결과를 믿을 수 없으니 실패 처리.
- 트레이드오프: 순차라 느리다. 대신 타임아웃이 걸린 파일 수를 정확히 세고 "없음"으로 잘못 세지 않는다.

**바뀌어 온 이력**: `2b76cbb0`/`b73e3d4e`/`a0f45d8f`(06-08 첨부파일 검증) → `15358a84`(스레드 20) → `e08eb56c`(스레드 제거) → `36f28ec3`(subprocess 타임아웃) → `c6c6ba3c`/`aa86e4f4`(06-09 `log_mode`) → `f78a13b9`(2026-08-20, `app_path` 추출을 `sync_all_mapping.sql`과 같은 정규식으로; 고정 위치 `split_part`는 prefix 없는 경로에서 날짜 폴더를 뽑는 문제).

**면접 30초 설명**
"재시도 후에도 남은 미이관 첨부가 원본이 없는 건지 업로드가 안 된 건지 가르려고 NFS 마운트에서 실물 파일을 확인하는 태스크를 만들었습니다. NFS가 응답하지 않으면 파일 확인 호출이 멈춰서 태스크가 묶였는데, 스레드 20개 병렬을 넣어봤다가 하루 만에 순차로 되돌렸습니다. 대신 파일 확인을 `test -f` 하위 프로세스로 격리해 10초 타임아웃을 걸고, 타임아웃은 '없음'이 아니라 '확인 불가'로 따로 세서 하나라도 있으면 NFS 복구 후 다시 돌리도록 태스크를 실패시켰습니다."

**헷갈리기 쉬운 점**
- 최종 코드는 **순차 + subprocess 10초 타임아웃**이다. "20 스레드 + 타임아웃"이 아니다.
- 스레드 도입 이유(heartbeat 끊김 방지)는 커밋에 있고, 원복 이유는 없다.
- `15358a84`, `21a552ba` 커밋에는 AI co-author 줄이 있다.
- 일반론: hard 마운트 NFS에서 프로세스가 D state에 빠지면 타임아웃 후 kill도 바로 안 먹을 수 있다. 실제로 그런 일이 있었는지는 확인 필요.

---

### 이전 조사(study-migration.md)와 달라지거나 새로 확인된 사실
1. 쿼리 단위 dynamic task mapping은 **GW에만** 있다. webmail/attend/chat/iam은 `SQLExecuteQueryOperator` 파일 단위.
2. fast/slow로 SQL을 나눈 사람은 heesu(`b018def7`, DOP-9552), 본인은 다음 날 DAG 연결(`18c434bc`). `gw_generate_migration_validation`(GW 건수 검증)도 heesu 코드(226줄) → 이전 조사 Q22의 "만들었습니다"는 수정 필요.
3. 경로 충돌 rename(`storage_correct_tasks.py`)은 2025-08-26부터 있었고, `46461c47`(2026-01-12)은 업로드 쪽 개별 복사를 추가한 커밋이다. rename 때 `app_code_and_gcs_path`는 안 바뀌고, 기간 보정은 신규끼리의 중복만 센다.
4. 스레드 20 도입 이유는 커밋 메시지에 있다("스케줄러 heartbeat 끊김 방지"). 원복 이유는 여전히 없음.
5. chat 규모 주석이 서로 다르다(15만 / 15K / 약 81만).
6. 단독형 ACC 재시도 분기의 성공 조건이 본 실행보다 느슨하다.
7. 단독형 sensor/폴링 코드는 대부분 hwgyun. 본인은 `trigger_worker_api` 쪽.
8. pool 슬롯 수는 코드에 없다(Airflow UI 설정).

---

## 메일 스토어 (dop-mail-store) — 코드 워크스루

> 기준: `/Users/daou-8691/Documents/git/dop-mail-store` HEAD `f5b8ec23`(main), 2026-11-05 읽기 전용 조회.
> 라인 번호는 HEAD 기준. 본인 = author `starlight2083`/`변재혁`.
> **작성자 구분 원칙**: 첫 커밋 `179da848 init project`(2024-10-30)는 본인 이름이지만 그 이전 이력이 없어 init 시점 코드의 실제 작성자는 **확인 필요**. 아래에서 "본인"은 init 이후 본인 커밋으로 들어간/바뀐 부분만 가리킨다. init에 이미 있던 구조는 "init부터 있음"으로 표시.

---

### 전체 코드 지도

**모듈·패키지**

| 모듈 | 패키지/클래스 | 역할 |
|---|---|---|
| `store-d` | `stored.config.NettyServerConfig` | boss/worker `NioEventLoopGroup`, `ServerBootstrap`(SO_RCVBUF 256KB, `AdaptiveRecvByteBufAllocator(64KB,256KB,1MB)`) |
| | `stored.netty.StoreReceiverInitializer` | 채널 파이프라인 구성 |
| | `stored.netty.StoreReceiverRequestDecoder` | 길이 prefix 프레이밍, 헤더 파싱, hostname 검증, continuation, 본문 → 파일 |
| | `stored.netty.StoreReceiverInboundHandler` | Bean Validation, 채널 ↔ `ConnectionContext` 바인딩, Processor 호출 |
| | `stored.netty.StoreReceiverResponseEncoder`, `BufferUtil` | 응답 `[4바이트 길이][JSON+CRLF]` |
| | `stored.protocol.<도메인>.parser/*Parser`, `processor/*Processor`, `mapper.ParserMapper/ProcessorMapper`, `type.ProtocolType` | 명령별 JSON → RequestMessage 변환, 명령별 처리기(→ `MailboxServiceHub`) |
| `mailbox` | `domain.MailboxServiceHub` | `@UseSqlSession`이 붙은 서비스 진입점(Facade) |
| | `common.connection.*` (`ConnectionContext`, `ThreadLocalConnectionManager`, `SqlSessionAspect`, `UseSqlSession`, `TransactionStatus`, `SqlSessionTemplate`, `ConnectionType`, `mapper/ConnectionMapper.xml`) | 사용자별 SQLite 커넥션 + 직접 만든 트랜잭션 |
| | `domain.common.MailBoxAspect`, `MailBoxValidator`, `@ValidMailBox` | 메일함 검증/자동 생성(별도 트랜잭션) |
| | `domain.msg.service.MailMessageServiceImpl` | append/expunge/move/copy 비즈니스 로직 |
| | `domain.store.repository.GcsStoreRepository`(prod) / `FileStoreRepository` | 원문 저장(`StoreConfig`가 `mail.store.type`으로 선택) |
| | `indexing.service.IndexingEventListener`, `EmbeddedIndexingService`, `indexing.manager.QFileProgressManager`, `indexing.type.QFileProcessType`, `indexing.queue.HttpQueue` | 색인 이벤트 → 큐 파일 이동 → indexer에 HTTP POST |
| `indexer` | 별도 Boot 앱 | FTS5 색인(주로 외주·이승진) |

**Netty 파이프라인** (`store-d/.../netty/StoreReceiverInitializer.java:32-40`)

```
[inbound]  ReadTimeoutHandler(50초) → ChunkedWriteHandler → StoreReceiverRequestDecoder → StoreReceiverInboundHandler
[outbound] StoreReceiverResponseEncoder ← ctx.writeAndFlush(ResponseMessage)
allocator: UnpooledByteBufAllocator(false) (힙 버퍼), worker 스레드 prod 10개
```
비즈니스 처리(SQLite, GCS I/O)는 별도 `EventExecutorGroup` 없이 worker 이벤트 루프 스레드에서 그대로 실행된다.

**요청 1건 흐름 ① MSG-APPEND (쓰기, 본문 있음)**

1. 클라이언트 → `[int 길이][PROTO/ver JSON hostName MSG-APPEND {json}]`
2. `StoreReceiverRequestDecoder.decode` (`:108-147`): 4바이트 길이만큼 쌓일 때까지 `markReaderIndex/resetReaderIndex` → 공백으로 5조각 분리 → `ProtocolHeader` 생성 → `header.validate()`(hostname 비교) → `ProtocolType.MSG_APPEND.isUseLiteral()==true` → `ParserMapper` → `MsgAppendParser`(Jackson) → `MsgAppendRequest`
3. `requestMoreData` (`:203-209`): continuation `[len]{"message":"OK", "code": 200}\r\n` 전송, 채널 attribute 맵에 `REQUEST_MESSAGE`, `NEEDED_DATA(size)` 저장
4. 다음 read부터 `decode` 앞부분(`:78-106`): 본문 프레임의 4바이트 길이를 한 번 검증(`VERIFY`) → `writeToFile`로 `/opt/dop/queue/received/<uuid>_<ms>.received.emlq`에 append → size만큼 다 받으면 `FileBasedLiteral`을 붙여 `out.add(msgAppendRequest)`
5. `StoreReceiverInboundHandler.channelRead0` (`:35-66`): Bean Validation → `initConnection`(채널 attribute의 `ConnectionContext` 재사용/생성, ThreadLocal 등록) → `ProcessorMapper` → `MsgAppendProcessor.processCommand`
6. `MailboxServiceHub.appendMessage` (`@UseSqlSession`, 기본 `{MINDEX}`) → Spring AOP 프록시 → `SqlSessionAspect.transactional` → `ThreadLocalConnectionManager.beginExclusive` → `ConnectionContext.getSqlSession(MINDEX)`(없으면 파일 열기/스키마 생성) → `ConnectionMapper.beginExclusive()` = `BEGIN EXCLUSIVE;`
7. `MailMessageServiceImpl.appendMessage` (`:107-181`): 메일함 검증 → MIME 파싱(`MimeDescriptorImpl`) → `fileCompressor.compress` → `GcsStoreRepository.save`(`WriteChannel` 스트리밍) → `getUidNextAndIncrease` → `addMessage` → `saveSortingData`/`saveHeaderData` → `plusMessageStats` → 태그 → quota 파일 → `saveIndexing`(`MsgIndexingAddEvent` 발행)
   - 모든 DB 접근은 `MyBatis*Repository` → `SqlSessionTemplate.execute(callback, ConnectionType)` → ThreadLocal의 같은 SqlSession
8. Aspect: 정상 → `ConnectionContext.commit` = `COMMIT;` / DB 예외 → `ROLLBACK;` / finally `closeSingleUse()`(ThreadLocal 비우기, 채널 컨텍스트는 닫지 않음)
9. 핸들러가 `SuccessResponse` → `StoreReceiverResponseEncoder` → `[len]{json}\r\n`
10. (별도 스레드 `index-task-*`) `IndexingEventListener.handleIndexingAddEvent` → `EmbeddedIndexingService.request` → `QFileProgressManager.progressToNextState`(received → `indexing/<0~1023>/..indexing.emlq`, xattr `user:QFileMeta`) → `HttpQueue.convertAndSend`(POST indexer) / 실패 시 `moveToBackground`(backup)

**요청 1건 흐름 ② 읽기 (예: MSG-GET-LIST-UID)**
디코더(`isUseLiteral()==false`라 바로 `out.add`) → 핸들러 `initConnection` → `MsgGetListUidProcessor` → `MailboxServiceHub.getMailMessageListUid` `@UseSqlSession(readOnly = true)` → Aspect가 `beginTransaction` = `BEGIN TRANSACTION;`(DEFERRED) → 조회 → `COMMIT;`

**요청 1건 흐름 ③ 원문 조회 FILE-GET (SQLite 안 거침)**
디코더 → 핸들러 `initConnection`(채널 바인딩은 일어남) → `FileGetProcessor` → `FileService.getFile` → `GcsStoreRepository.getObject` → `FileGetResponse` → 인코더가 `BufferUtil.setHeaderLength(out, InputStream, size)`로 **원문 전체를 ByteBuf에 써서** 전송. `@UseSqlSession`이 없어서 Aspect·트랜잭션 없음.

**본인 코드 위치 요약**

| 기여 | 본인 커밋으로 바뀐 곳 |
|---|---|
| 커넥션/트랜잭션 | `SqlSessionAspect`·`ThreadLocalConnectionManager`·`ConnectionContext`·`TransactionStatus`·`ConnectionMapper.xml`(d82a07e0, 9a311ad5), `MailBoxValidator`(f1845e97), `InitTableMapper`로 DDL 이동(8f799ed2), messageStore 정규화(8e714ac4, f7198947) |
| 채널 바인딩 | 바인딩 자체는 init부터 있음. 본인: 검증 실패 시 큐 파일 삭제(1d77afef, a749e89f), hostname 검증(8d29742c, a61bab37) |
| 프레이밍 | `StoreReceiverRequestDecoder` 길이 prefix(d3fd195e~b9dab634), `BufferUtil`, `StoreReceiverResponseEncoder`(a296a8a0) |
| append 수신 | 디코더 VERIFY 단계(a296a8a0), 실패 시 파일 삭제(c132ba3f), 서비스 rollbackQFile/Mdata(f33409c2 등) |
| 색인 연결 | `QFileProcessType`·`progressToNextState` 메타(e1ca1187), received/indexing 분리(93782489, c626b60f, b6c33050, 414b2ccb) |
| busy lock | 134528c4 ~ 2b325390 전체, reserv 제거(8063570c, b2cf97b3) |

---

### 1. 사용자별 SQLite 커넥션 구조 (2024-10 init ~ 2025-02 · d82a07e0, 9a311ad5, f1845e97, 8f799ed2, 8e714ac4)

**내가 한 범위**
- init(179da848)부터 있던 것: `ConnectionContext`(Map<ConnectionType, SqlSession>), `ThreadLocalConnectionManager`, `@UseSqlSession` + `SqlSessionAspect`, `MailBoxAspect`/`@ValidMailBox`, 당시 RESERVE용 HikariCP. 이 시점 작성자는 **확인 필요**(본인 기억: 외주 설계를 Java 구조로 옮기며 본인이 구현).
- init 이후 본인 커밋: JDBC `autoCommit(false)`+`sqlSession.commit()` 방식을 **SQL `BEGIN/COMMIT/ROLLBACK` 직접 실행**으로 교체하고 `TransactionStatus`·`TransactionBeginException`·`ConnectionMapper.xml` 추가(d82a07e0), 읽기/쓰기 분리(9a311ad5), 메일함 검증 트랜잭션을 finally에서 COMMIT(f1845e97), DDL을 Java 문자열에서 `InitTableMapper`로 이동(8f799ed2, 70e9a1b5), messageStore를 요청이 아니라 `ConnectionContext`에서 꺼내 쓰도록 변경(8e714ac4), RESERVE 제거(b2cf97b3).
- 타인: `getSqlSessionOnly`/`beginOnlyExclusive`/`executeQueryOnly`(스키마 생성 없이 여는 경로)는 이승진 `96404871`(2025-07 MBOX-INIT). append 시 `@ValidMailBox` 대신 서비스에서 검증하도록 바꾼 것도 이승진 `24e5226a`(2025-08). Aspect의 `TransactionBeginException` 시 큐 파일 삭제는 이승진 `7cda0011`, `f85a4cd6`(2025-08).

**코드 지도**

| 파일 | 클래스/메서드 | 역할 |
|---|---|---|
| `mailbox/.../common/connection/UseSqlSession.java` | `@UseSqlSession(value = {MINDEX}, readOnly = false)` | 메서드가 쓸 DB 종류와 읽기 여부 선언 |
| `.../connection/SqlSessionAspect.java` | `transactional` (`@Around`, `@Order(2)`) | BEGIN → proceed → COMMIT / ROLLBACK, finally ThreadLocal 정리 |
| `.../connection/ThreadLocalConnectionManager.java` | `init`, `checkAndCreateSingleUse`, `beginExclusive`, `beginTransaction`, `commit`, `rollback`, `closeSingleUse`, `close` | ThreadLocal<ConnectionContext> 보관, DB 종류 배열 순서대로 BEGIN |
| `.../connection/ConnectionContext.java` | `getSqlSession`, `openSession`, `createTables`, `commit`, `rollback`, `validateMessageStore`, `generateMessageStore`, `close` | 사용자 1명의 DB 커넥션 묶음, 지연 오픈·스키마 생성 |
| `.../connection/TransactionStatus.java` | `(connectionType, transactional, rollbackOnly)` | BEGIN 결과를 DB 종류별로 기록 |
| `.../connection/SqlSessionTemplate.java` | `execute(callback, type)` | Repository가 ThreadLocal 세션을 꺼내 쓰는 통로, 모든 예외를 `MailBoxDataAccessException`으로 감쌈 |
| `mailbox/src/main/resources/.../connection/mapper/ConnectionMapper.xml` | `beginTransaction`/`beginExclusive`/`commit`/`rollback` | `BEGIN TRANSACTION;` / `BEGIN EXCLUSIVE;` / `COMMIT;` / `ROLLBACK;` |
| `.../config/DBConnectionConfig.java`, `config/model/DBConfigModel.java` | `getDBPath`, `getDirectoryPath`, `getDBFilePath` | `ConnectionType` → JDBC URL/파일 경로 |
| `.../config/MyBatisConfig.java` | `sqlSessionFactory` | 단일 `SqlSessionFactory`, `defaultStatementTimeout` |
| `.../domain/MailboxServiceHub.java` | `appendMessage`, `expunge`, … | 어노테이션이 붙는 유일한 진입점 계층 |
| `.../domain/common/MailBoxAspect.java`, `MailBoxValidator.java` | `@Order(1)`, `validate` | 메일함 검증용 별도 EXCLUSIVE 트랜잭션 |

**흐름**
1. 핸들러(또는 Netty 밖 경로면 Aspect의 `checkAndCreateSingleUse`)가 `ConnectionContext`를 ThreadLocal에 넣는다.
2. `MailboxServiceHub.xxx()` 호출 → 프록시 → (`@ValidMailBox`가 있으면 `MailBoxAspect`가 먼저) → `SqlSessionAspect.transactional`.
3. `begin(value, readOnly)` → `readOnly ? beginTransaction : beginExclusive` → 배열 순서대로 `getSqlSession(type)` → `ConnectionMapper.beginXxx()`.
4. `getSqlSession`: 맵에 있으면 재사용, 없으면 `openSession` → 디렉터리 생성 → 파일 존재 여부 확인 → `DriverManager.getConnection("jdbc:sqlite:<root>/<messageStore><suffix><fileName>")` → `autoCommit(true)` → `factory.openSession(connection)` → 새 파일이면 `createTables`.
5. BEGIN 중 하나라도 실패 → `TransactionStatus(type, false, true)` 추가 후 중단 → Aspect가 `containsRollbackOnly`면 이미 연 것 ROLLBACK 후 `TransactionBeginException`.
6. `joinPoint.proceed()` → 서비스 → Repository → `SqlSessionTemplate.execute(cb, type)` → `connectionManager.getSqlSession(type)` (같은 세션).
7. 정상 → `ConnectionContext.commit(statuses)`: `transactional==true`인 것만 순서대로 `clearCache/flushStatements` 후 `COMMIT;`.
8. `PersistenceException | SQLException | MailBoxDataAccessException` → `rollback(statuses)` 후 재던짐.
9. finally `closeSingleUse()`: 일회용이면 `close()`, 아니면(Netty 채널 소유) ThreadLocal만 `remove()`.

**핵심 코드**

```java
// mailbox/src/main/java/com/daou/dop/mailbox/common/connection/SqlSessionAspect.java:33-71
@Around("@annotation(useSqlSession) && args(requestMessage,..)")
public Object transactional(ProceedingJoinPoint joinPoint, RequestMessage requestMessage, UseSqlSession useSqlSession) throws Throwable {
    ConnectionType[] value = useSqlSession.value();          // 예: {MINDEX} 또는 {MINDEX, MDN}
    boolean readOnly = useSqlSession.readOnly();
    List<TransactionStatus> transactionStatuses = Collections.emptyList();
    try {
        transactionStatuses = begin(value, readOnly);         // BEGIN 먼저 (ThreadLocal에 컨텍스트가 있어야 실제로 실행됨)
        connectionManager.checkAndCreateSingleUse(requestMessage. getMessageStore()); // Netty 밖 경로용 일회용 컨텍스트
        Object proceed = joinPoint.proceed();
        commit(transactionStatuses);                          // DB 종류별 COMMIT; 순차 실행
        return proceed;
    } catch (PersistenceException | SQLException | MailBoxDataAccessException e) {
        if (requestMessage instanceof MsgAppendRequest) { rollbackQFile((MsgAppendRequest) requestMessage); } // (2025-08 이승진 추가)
        rollback(transactionStatuses);                        // DB 계열 예외만 ROLLBACK
        throw e;
    } catch (TransactionBeginException e) {                   // BEGIN 실패(busy 등) — 이미 begin()에서 롤백함
        ...
        throw e;
    } finally {
        connectionManager.closeSingleUse();                   // ThreadLocal 정리 (채널 소유 커넥션은 닫지 않음)
    }
}

private List<TransactionStatus> begin(ConnectionType[] value, boolean readOnly) {
    List<TransactionStatus> statuses = readOnly ? connectionManager.beginTransaction(value) : connectionManager.beginExclusive(value);
    if (containsRollbackOnly(statuses)) {                     // 하나라도 BEGIN 실패
        rollback(statuses);                                   // 앞에서 BEGIN 성공한 것만 ROLLBACK
        throw new TransactionBeginException("Transaction is marked as rollback-only");
    }
    return statuses;
}
```

```java
// mailbox/src/main/java/com/daou/dop/mailbox/common/connection/ConnectionContext.java:68-93
public SqlSession getSqlSession(SqlSessionFactory factory, ConnectionType connectionType) throws SQLException {
    if (sqlSessionMap.containsKey(connectionType)) {          // 이미 연 DB 종류면 재사용
        return sqlSessionMap.get(connectionType);
    }
    SqlSession sqlSession = openSession(factory, connectionType); // 처음 필요할 때만 연다(지연 오픈)
    sqlSessionMap.put(connectionType, sqlSession);
    return sqlSession;
}

private SqlSession openSession(SqlSessionFactory factory, ConnectionType connectionType) throws SQLException {
    DirectoryUtils.createDirectories(Path.of(dbConnectionConfig.getDirectoryPath(connectionType, messageStore)));
    boolean newSqliteFile = !Files.exists(Path.of(dbConnectionConfig.getDBFilePath(connectionType, messageStore)));
    Connection connection = DriverManager.getConnection(dbConnectionConfig.getDBPath(connectionType, messageStore)); // 풀 없음, 사용자 파일마다 직접 연결
    setBusyHandler(connection);                               // 현재 주석 처리돼 no-op
    connection.setAutoCommit(true);                           // 트랜잭션 경계는 SQL BEGIN/COMMIT으로 직접
    SqlSession sqlSession = factory.openSession(connection);
    if (newSqliteFile) {
        createTables(connectionType, sqlSession);             // MINDEX면 기본 폴더 디렉터리 + 테이블/인덱스 + 기본 mail_folder 행
    }
    return sqlSession;
}
```

```java
// mailbox/src/main/java/com/daou/dop/mailbox/common/connection/ConnectionContext.java:106-120
public void commit(List<TransactionStatus> statuses) {
    for (TransactionStatus transactionStatus : statuses) {   // {MINDEX, MDN}이면 MINDEX → MDN 순서로
        if (!transactionStatus.isTransactional()) continue;
        SqlSession sqlSession = sqlSessionMap.get(transactionStatus.getConnectionType());
        if (sqlSession != null) {
            clearSqlSession(sqlSession);                      // MyBatis 1차 캐시 비우고 배치 flush
            sqlSession.getMapper(ConnectionMapper.class).commit(); // "COMMIT;" — DB마다 따로, 2PC 없음
        }
    }
}
```

**데이터·설정**
- `ConnectionType`: `MINDEX`, `BIG_ATTACH`, `MDN`, `WEB_FOLDER` (`ConnectionType.java:3-9`)
- 경로(`mailbox/src/main/resources/config/application-prod.yml:28-49`, `DBConfigModel.getDbPath`): `jdbc:sqlite:` + `<mindexPath>/<messageStore>` + suffix + fileName
  - MINDEX `/_mcache.db`, BIG_ATTACH `/etc/BIGATTACH/_mcache.db`, MDN `/etc/MDN/_Mdn.db`, WEB_FOLDER `/etc/WEBFOLDER/_mcache.db`, 모두 `privateDB: true`(사용자별). `privateDB: false`는 공용 DB 경로를 뜻하며 과거 RESERVE가 이걸 썼다.
- MINDEX 테이블(`createMailboxTables`, `ConnectionContext.java:322-362`): mail_folder, mail_message, mail_search, mail_header, mail_tag, mail_tag_message, user_search + 인덱스. MDN: mdn_message, mdn_info. WEB_FOLDER/BIG_ATTACH: mail_folder, mail_message(+WEB_FOLDER는 mail_search).
- messageStore: `/mindex/companyGroup/company/userGroup/user`. `generateMessageStore`(`:154-174`)가 `/`로 7조각 이상이면 앞 6조각(=루트 + 5단계)까지만 잘라 사용자 루트로 정규화.
- 사용처: 대부분 `{MINDEX}`, MDN 명령은 `{MDN}`, 자료실 `{WEB_FOLDER}`, 대용량첨부 `{BIG_ATTACH}`, **여러 DB 묶음은 `expunge` 한 곳 `{MINDEX, MDN}`** (`MailboxServiceHub.java:221-225`).
- 커넥션 풀 없음(`DriverManager` 직접). `MyBatisConfig`의 `SQLiteDataSource`는 Environment 구성용이고 실제 커넥션은 `factory.openSession(connection)`으로 주입.

**롤백되는 예외 범위 (코드 기준)**
- Aspect가 ROLLBACK하는 것: `PersistenceException`, `SQLException`, `MailBoxDataAccessException`.
- `SqlSessionTemplate.execute`(`:21-27`)가 콜백 안의 `SQLException | RuntimeException`을 전부 `MailBoxDataAccessException`으로 감싸므로, **Repository 안에서 난 예외는 사실상 모두 ROLLBACK 대상**.
- Repository 밖에서 난 `MailBoxException` 계열(`MailParsingException`, `StoreException`(GCS), `FileWriteException`, 메일함 이름 검증 `MailBoxException`, `MailFolderNotFoundException` 등)은 **COMMIT도 ROLLBACK도 하지 않고** 그대로 올라간다. 채널에 묶인 커넥션이면 `BEGIN EXCLUSIVE`가 열린 채 남을 수 있다(아래 "헷갈리기 쉬운 점").
- d82a07e0 이전(init 버전)은 `catch (MailBoxException e)`로 **모든 MailBoxException에서 rollback**했다. d82a07e0에서 DB 계열로 좁혔다. 좁힌 이유는 커밋 메시지에 없음 → **확인 필요**.

**왜 이렇게 짰나**
- DataSource가 "사용자 × DB 종류"마다 다르고 요청 시점에야 정해진다. Spring `@Transactional`/`DataSourceTransactionManager`는 고정 DataSource에 묶여 있어 그대로 쓰기 어렵고, `AbstractRoutingDataSource`는 대상 DataSource를 미리 등록해야 하는데 사용자 수만큼 파일이 있다. 그래서 어노테이션 + Aspect + ThreadLocal로 직접 만들었다.
- 저장소 전체에 `@Transactional`/`PlatformTransactionManager`가 없다(이전 조사 확인).
- 지연 오픈: append는 MINDEX만, MDN 명령은 MDN만 쓰므로 4개를 다 열 필요가 없다. 신규 사용자는 미리 DB를 만들지 않고 첫 접근 때 만든다(C 스토어 데이터 포맷 `_mcache.db`, `MCACHE_VERSION=200`을 그대로 씀).
- autoCommit(false) → autoCommit(true)+SQL BEGIN: JDBC autoCommit(false)는 sqlite-jdbc가 내부적으로 `BEGIN`(DEFERRED)을 보내서 락 모드를 고를 수 없다. `BEGIN EXCLUSIVE`를 직접 쓰려고 바꿨다(6번 참조).
- 버린 대안/트레이드오프: 여러 DB를 `ATTACH DATABASE`로 한 커넥션에 붙이면 커밋이 원자적이지만 락 범위가 넓어진다. 현재 구조는 DB별 순차 COMMIT이라 커밋 단계 원자성이 없다(MINDEX COMMIT 후 MDN COMMIT 실패 시 보상 없음). ATTACH를 검토했는지는 커밋 기록에 없음 → **확인 필요**.

**바뀌어 온 이력**
1. `179da848`(2024-10-30) init: `autoCommit(false)`, `sqlSession.commit(true)/rollback(true)`, `catch (MailBoxException)` 롤백, RESERVE는 HikariCP.
2. `d391d274`(2024-11-21) 메일 기본 폴더 생성, `84dea97c`(11-26) version_no 200.
3. `d82a07e0`(2025-01-21) busy_lock 에러: `autoCommit(true)` + `ConnectionMapper.xml`(`beginTransaction`=`BEGIN EXCLUSIVE`) + `TransactionStatus` + `TransactionBeginException`, 롤백 대상 DB 예외로 축소, 당시 readOnly는 BEGIN 없이 autocommit. `defaultStatementTimeout(30)` 추가.
4. `0079b08e`(01-21) connection readOnly 추가, `8063570c`/`b2cf97b3`(01-21~22) RESERVE 제거.
5. `9a311ad5`(01-23) readOnly도 트랜잭션: `beginTransaction`=`BEGIN TRANSACTION`, 쓰기용 `beginExclusive` 추가, `MailBoxValidator`도 `beginExclusive`로. 같은 날 `474032d3`, `77c49d11`로 readOnly일 때 commit/rollback 건너뛰던 분기 제거, `f1845e97` 검증 트랜잭션 finally COMMIT.
6. `8f799ed2`(02-07) DDL → `InitTableMapper`, `70e9a1b5`(02-10) user_search 테이블.
7. `8e714ac4`, `f7198947`, `c72af3d8`(02-12) messageStore를 `ThreadLocalConnectionManager.getMessageStore()`에서 가져오도록, 정규화 로직.
8. (인수 후) 이승진 `96404871`(2025-07) `getSqlSessionOnly`, `24e5226a`(2025-08) append 검증 서비스로 이동.

**면접 30초 설명**
"메일 스토어는 사용자마다 SQLite 파일이 4종류씩 있어서 DataSource를 미리 정할 수 없었습니다. 그래서 `@UseSqlSession(DB종류, readOnly)` 어노테이션과 `SqlSessionAspect`를 만들어, ThreadLocal에 있는 사용자별 `ConnectionContext`에서 필요한 DB만 그때 열고, 파일이 없으면 스키마와 기본 폴더까지 만든 뒤 `BEGIN EXCLUSIVE`나 `BEGIN`을 SQL로 직접 실행했습니다. 정상 종료면 DB별로 COMMIT, DB 예외면 ROLLBACK하고, 메일 영구삭제처럼 MINDEX와 MDN을 같이 쓰는 경우는 어노테이션에 둘 다 적어 같은 순서로 BEGIN/COMMIT합니다. 처음엔 JDBC autoCommit(false)였는데 busy lock을 겪고 락 모드를 직접 고르려고 SQL BEGIN 방식으로 바꿨습니다."

**헷갈리기 쉬운 점**
- "Spring 트랜잭션"이 아니다. Spring AOP만 쓰고 트랜잭션 관리는 직접 SQL. `@Transactional` 없음.
- 다중 DB "트랜잭션"은 BEGIN/COMMIT을 순서대로 반복할 뿐 원자적이지 않다. 현재 묶는 곳은 `expunge {MINDEX, MDN}` 하나.
- `MailBoxAspect`가 `@Order(1)`이라 **바깥**에서 먼저 돈다. `MailBoxValidator.validate`가 자기 `BEGIN EXCLUSIVE` → 검증/폴더 생성 → finally `COMMIT`을 끝낸 뒤 `SqlSessionAspect`(`@Order(2)`)가 본 트랜잭션을 연다. 즉 트랜잭션 2개.
- 현재 append는 `@ValidMailBox`가 주석이고 `mailBoxService.validate`가 본 트랜잭션 **안**에서 돈다. 이건 인수 후 이승진 변경(24e5226a, 2025-08). 본인 마지막 커밋 `1e319418`(2025-06-25) 시점에는 `@UseSqlSession` + `@ValidMailBox(needToCreate = true)`였다(확인함). 면접에서는 이 버전(검증 트랜잭션 → 본 트랜잭션 2단계)으로 설명할 것.
- 열린 트랜잭션이 남을 수 있는 경로(코드상 추론, 운영 영향은 **확인 필요**): Repository 밖 `MailBoxException`이면 COMMIT/ROLLBACK 없이 빠져나가고, 채널 소유 커넥션은 닫히지 않는다. 다음 요청의 `BEGIN EXCLUSIVE`는 "트랜잭션 안에서 트랜잭션 시작" 오류로 `rollbackOnly` 상태가 되는데, 이 상태는 `transactional=false`라 `rollback()`이 건너뛴다. 결국 채널이 닫힐 때(`channelInactive` → `close`)까지 락이 남을 수 있다.
- `begin()`이 `checkAndCreateSingleUse()`보다 **먼저** 호출된다. Netty 밖 경로(ThreadLocal이 비어 있음)에서는 `beginExclusive`가 컨텍스트가 없어 빈 리스트를 돌려주고, 이후 일회용 컨텍스트가 만들어져 autocommit으로 실행된다(d82a07e0부터 이 순서). 그런 경로가 운영에서 실제로 쓰이는지는 **확인 필요**.
- 스키마 생성 실패는 로그만 남기고 삼킨다(`createMailboxTables`의 catch). 스키마 버전 관리 없음.

---

### 2. Netty 채널 바인딩 (init부터 · 본인 변경 1d77afef, a749e89f, 8e714ac4, 8d29742c, a61bab37)

**내가 한 범위**
- 채널 attribute에 `ConnectionContext`를 붙여 재사용하고, 다른 messageStore면 `InvalidMessageStoreException`, `channelInactive`에서 닫는 구조는 **init(179da848)에 이미 있음**. init 이전 작성자 **확인 필요**.
- 본인 커밋: Bean Validation 실패·messageStore 불일치 시 받아 둔 큐 파일 삭제(1d77afef, a749e89f: `LiteralRequestMessage.close()` default 메서드 추가), messageStore 비교를 핸들러에서 `ConnectionContext.validateMessageStore`(정규화 포함)로 이동(8e714ac4 계열), 헤더에 hostname 필드 추가·검증(8d29742c → a61bab37), 에러 로그 보완(b8f2ea9a). MDC 로그 관련은 황규연(hwgyun) 커밋.

**코드 지도**

| 파일 | 클래스/메서드 | 역할 |
|---|---|---|
| `store-d/.../netty/StoreReceiverInboundHandler.java` | `channelRead0`, `initConnection`, `initializeAndSetSqlSession`, `channelInactive`, `deleteQFile` | 채널 ↔ 컨텍스트 바인딩, Processor 호출, 정리 |
| `mailbox/.../connection/ConnectionContext.java` | `validateMessageStore`, `generateMessageStore` | 같은 채널의 다른 사용자 요청 차단 |
| `mailbox/.../connection/ThreadLocalConnectionManager.java` | `init(ConnectionContext)`, `init(String)`, `close(ConnectionContext)` | ThreadLocal 등록/정리 |
| `store-d/.../protocol/common/ProtocolHeader.java` | `validate()` | 헤더 hostName == 내 hostname |
| `mailbox/.../common/loader/SystemConfigLoader.java` | `getHostName()` | 기동 시 `InetAddress.getLocalHost().getHostName()` |
| `store-d/.../netty/StoreReceiverRequestDecoder.java` | `decode` `:131-136` | hostname 불일치 → code 500 |

**흐름**
1. 연결 수립: 디코더 `channelActive`가 로그용 UUID와 디코더 상태 맵(`FrameDecoderMap`)을 채널 attribute에 넣음.
2. 첫 요청: 디코더가 `ProtocolHeader.validate()`로 hostname 확인 → 핸들러 `initConnection` → attribute `SqlSessionContext`가 비어 있으면 `connectionManager.init(messageStore)`로 생성 후 attribute에 저장(ThreadLocal에도 set).
3. 같은 채널의 다음 요청: attribute에서 꺼냄 → `validateMessageStore`(정규화 후 다르면 예외) → `connectionManager.init(context)`로 ThreadLocal에 다시 set. 이미 열린 SqlSession(SQLite 커넥션)을 그대로 씀.
4. 요청 끝: Aspect finally `closeSingleUse()` → 채널 소유라 `close()`하지 않고 ThreadLocal만 `remove()`.
5. 연결 종료(클라이언트 close, `ReadTimeoutHandler` 50초): 핸들러 `channelInactive` → `connectionManager.close(context)` → 모든 SqlSession close → attribute null. 디코더 `channelInactive`는 받던 큐 파일 삭제.

**핵심 코드**

```java
// store-d/src/main/java/com/daou/dop/stored/netty/StoreReceiverInboundHandler.java:49-102
ResponseMessage responseMessage;
try {
    initConnection(ctx, request);                                   // 채널 컨텍스트를 ThreadLocal에 올림
    responseMessage = processorMapper.getProcessorWithCommand(request).processCommand(request);
} catch (InvalidMessageStoreException e) {                          // 같은 채널로 다른 사용자 요청
    deleteQFile(request);                                           // 본문 받아 둔 .received.emlq 삭제 (a749e89f)
    exceptionCaught(ctx, e);
    responseMessage = new ErrorResponse(e.getMessage());
} catch (MailBoxException e) { ... } catch (Exception e) { ... }
ctx.writeAndFlush(responseMessage);
...
private void initConnection(ChannelHandlerContext ctx, RequestMessage request) {
    ConnectionContext connectionContext = getSqlSessionContext(ctx); // channel.attr("SqlSessionContext")
    if (connectionContext != null) {
        validateMessageStore(connectionContext, request);           // 다르면 InvalidMessageStoreException
        connectionManager.init(connectionContext);                  // 재사용: ThreadLocal.set
    } else {
        initializeAndSetSqlSession(ctx, request.getMessageStore());  // 새로 만들어 채널에 붙임
    }
}
...
@Override
public void channelInactive(ChannelHandlerContext ctx) throws Exception {
    ConnectionContext connectionContext = ctx.channel().attr(ATTRIBUTE_SQL_SESSION_CONTEXT_KEY).get();
    connectionManager.close(connectionContext);                     // 열린 SQLite 커넥션 전부 close
    ctx.channel().attr(ATTRIBUTE_SQL_SESSION_CONTEXT_KEY).set(null);
    super.channelInactive(ctx);
}
```

```java
// mailbox/src/main/java/com/daou/dop/mailbox/common/connection/ConnectionContext.java:146-152
public void validateMessageStore(String target) {
    String targetMessageStore = generateMessageStore(target);       // 요청 경로를 사용자 루트까지로 정규화
    if (StringUtils.hasText(targetMessageStore) && !messageStore.equals(targetMessageStore)) {
        throw new InvalidMessageStoreException("messageStore not match " + messageStore + " != " + targetMessageStore);
    }
}
```

```java
// store-d/src/main/java/com/daou/dop/stored/protocol/common/ProtocolHeader.java:46-48  (8d29742c → a61bab37)
public boolean validate() {
    return hostName.equals(SystemConfigLoader.getHostName());       // 헤더 3번째 토큰 == 이 서버 hostname
}
// StoreReceiverRequestDecoder.java:133-136
if (!header.validate()) {
    handleDecodeException(ctx, in, new StoreDException("Invalid hostId"), MailBoxStatusCode.RETURN.getCode()); // code 500
    return;
}
```

**데이터·설정**
- 채널 attribute 키: `SqlSessionContext`(ConnectionContext), `FrameDecoderMap`(디코더 상태), 로그 키 `FRAME_DECODE_LOG_ATTRIBUTE_KEY`.
- `mail.store.timeout: 50`(store-d `application-prod.yml:6`) → `ReadTimeoutHandler(50)`초.
- 상태 코드 `MailBoxStatusCode`: OK 200, RETRY 400, RETURN 500. 디코더의 매핑/파싱 오류는 400(RETRY), hostname 불일치·본문 크기 부족은 500(RETURN).

**왜 이렇게 짰나**
- 한 연결은 한 사용자의 명령을 연달아 보낸다는 전제(IMAP 세션 등)라 요청마다 SQLite 파일을 열고 닫는 비용(파일 open, 스키마 확인)을 연결 단위로 줄였다.
- 전제가 깨지면(다른 사용자 요청) 잘못된 사용자 DB에 쓰게 되므로 막는다.
- hostname 검증: 사용자 데이터가 특정 store 서버의 디렉터리(NFS)에 있으므로 다른 서버로 잘못 라우팅된 요청을 거부. 처음엔 `/opt/dop/config/global.config`의 `hostId`(8d29742c)였다가 다음 날 OS hostname(a61bab37)으로 바꿈 — 설정 파일 배포 없이 쓰려던 것으로 보이나 이유는 커밋에 없음 → **확인 필요**.
- 트레이드오프: 연결이 오래 유지되면 SQLite 커넥션(파일 핸들)도 유지된다. 열린 트랜잭션이 남으면 연결이 닫힐 때까지 락도 남는다.

**바뀌어 온 이력**
`179da848` 바인딩 구조(init) → `c4c2d104`(2024-11-15) append 에러 공통 처리 → `1d77afef`(2025-02-06) message valid → `a749e89f`(02-07) 검증 실패/다른 사용자 시 큐 파일 삭제 → `8e714ac4`·`f7198947`(02-12) messageStore 정규화를 `ConnectionContext`로 → `b8f2ea9a`(03-26) append 에러 로그 → `8d29742c`(05-12) 헤더 hostId 필드·검증, "GET " 매직 넘버 처리 제거 → `a61bab37`(05-13) hostname 기반으로 변경.

**면접 30초 설명**
"`StoreReceiverInboundHandler`가 첫 요청에서 사용자별 `ConnectionContext`를 만들어 Netty 채널 attribute에 붙이고, 같은 채널의 다음 요청에서는 그걸 꺼내 ThreadLocal에 올려 SQLite 커넥션을 재사용합니다. 같은 채널로 다른 사용자의 messageStore가 오면 `InvalidMessageStoreException`으로 막고 받아 둔 본문 파일도 지웁니다. 채널이 닫히면 `channelInactive`에서 열린 DB를 모두 닫습니다. 그리고 사용자 데이터가 특정 store 서버에 있기 때문에, 디코더에서 헤더의 hostname이 자기 hostname과 다르면 500으로 돌려보내게 했습니다."

**헷갈리기 쉬운 점**
- 채널 바인딩 구조 자체는 init 커밋에 있었다. 본인 변경분은 정리(파일 삭제), 정규화, hostname 검증. "처음부터 내가 설계"라고 말하려면 init 이전 경위를 본인 기억으로 보강해야 함.
- hostname 검증은 핸들러가 아니라 **디코더**에서 한다(본문 받기 전에 거부).
- ThreadLocal과 이벤트 루프: 핸들러가 worker 스레드에서 동기로 끝까지 실행되므로 ThreadLocal이 유효하다. `@Async` 색인 스레드에는 ThreadLocal이 없어서 `saveIndexing`이 이벤트 객체에 messageStore를 미리 담아 보낸다.
- 커넥션 "풀"이 아니다. 채널 수만큼 사용자 DB 커넥션이 열린다. 같은 사용자가 여러 채널(IMAP + 웹메일)로 붙으면 같은 파일에 커넥션이 여러 개 → 여기서 busy lock이 난다(6번).
- 에러 메시지 문자열은 hostname으로 바뀐 뒤에도 `"Invalid hostId"` 그대로다.

---

### 3. 프로토콜/프레이밍 (2024-11 ~ 2024-12 · d3fd195e, 54020b8f, a296a8a0)

**내가 한 범위**
- 본인: 패킷 오류 조사(60f9abca, c4973a3c, 0be5cbbf, 804883ae, 2024-11-08), 4바이트 길이 prefix 도입(d3fd195e, c3b325de, a4883622, 54020b8f, 2024-12-04), 응답에도 길이 prefix(4f783b4d), 본문(리터럴) 프레임 길이 검증·`BufferUtil` 추출(a296a8a0, b9dab634), CRLF 더미 제거(d5dfb308, 2025-04-02). 디코더 파일의 이력은 MDC 로그(황규연) 외 전부 본인.
- 클라이언트(MTA/IMAP/웹메일 측 C 코드) 쪽 변경은 이 저장소에 없음 → 상대 측 작업자는 **확인 필요**.

**코드 지도**

| 파일 | 클래스/메서드 | 역할 |
|---|---|---|
| `store-d/.../netty/StoreReceiverRequestDecoder.java` | `decode` `:108-147` | 헤더 프레임: 길이 대기 → 읽기 → 파싱 |
| 〃 | `handleDecodeException` `:211-226` | 버퍼 버리고, 큐 파일 삭제, 길이 prefix 붙은 에러 응답 |
| `store-d/.../netty/BufferUtil.java` | `MESSAGE_LEN=4`, `setHeaderLength`, `createBuffer` | `[int 길이][본문+CRLF]` 쓰기 |
| `store-d/.../netty/StoreReceiverResponseEncoder.java` | `encode` | `ResponseMessage` → JSON → 길이 prefix |
| `store-d/.../protocol/common/ProtocolHeader.java` | 생성자, `getParserKey`, `isUseLiteral` | `PROTO/ver`, dataType, hostName, command |

**흐름 (헤더 프레임)**
1. `readableBytes < 4`면 return (더 받기).
2. `markReaderIndex()` → `readInt()`로 길이.
3. `readableBytes < messageLength`면 `resetReaderIndex()` 후 return → `ByteToMessageDecoder`가 다음 read에서 누적 버퍼로 다시 호출.
4. 길이만큼 `readBytes` → UTF-8 문자열 → `split("\\s+", 5)` → `[PROTO/ver, dataType, hostName, COMMAND, json]`.
5. 남은 바이트는 버퍼에 그대로 남아 다음 `decode` 호출에서 다음 프레임으로 처리된다(ByteToMessageDecoder가 읽은 만큼만 소비).

**핵심 코드**

```java
// store-d/src/main/java/com/daou/dop/stored/netty/StoreReceiverRequestDecoder.java:108-131 (현재)
int readableBytes = in.readableBytes();
if (readableBytes < BufferUtil.MESSAGE_LEN) {      // 길이 필드(4바이트)도 아직 안 옴
    return;
}
in.markReaderIndex();                              // 되돌릴 지점 표시
int messageLength = in.readInt();                  // big-endian int 길이
if (in.readableBytes() < messageLength) {          // 헤더가 TCP 세그먼트 여러 개로 나뉘어 옴
    in.resetReaderIndex();                         // 길이 필드까지 되돌리고 다음 read 대기
    return;
}
byte[] bytes = new byte[messageLength];
in.readBytes(bytes);                               // 정확히 한 프레임만 소비
String message = new String(bytes, StandardCharsets.UTF_8);
String[] parts = message.split(DELIMITER, 5);
ProtocolHeader header = new ProtocolHeader(parts[0], parts[1], parts[2], parts[3]);
```

```java
// 이전 방식 (179da848 init) — 경계 개념이 없음
String bufferString = in.toString(StandardCharsets.UTF_8); // 지금 버퍼에 있는 것 전부를 한 요청으로 간주
in.clear();                                                // 나머지(다음 요청 일부)도 버림
String[] parts = bufferString.split(DELIMITER, 4);

// 0be5cbbf (2024-11-08) 임시 대응 — 버퍼가 꽉 찼으면 '나뉘어 온 것'으로 추정
if (in.maxFastWritableBytes() == 0) {
    // 버퍼 쓰기 공간이 없으면 데이터가 분할되어서 온다.
    return;
}
```

```java
// store-d/src/main/java/com/daou/dop/stored/netty/BufferUtil.java:16-21  (응답도 같은 프레이밍)
public static void setHeaderLength(ByteBuf buffer, String message) {
    String eol = message + EOL;                            // JSON + "\r\n"
    byte[] bytes = eol.getBytes(StandardCharsets.UTF_8);
    buffer.writeInt(bytes.length);                         // 길이(바이트 수, CRLF 포함)
    buffer.writeBytes(bytes);
}
```

**데이터·설정**
- 요청 헤더: `[int32 BE 길이][UTF-8 "PROTO/ver JSON hostName COMMAND {json}"]`
- 리터럴 명령의 본문: `[int32 길이][원문 바이트]`
- 응답: `[int32 길이][JSON + CRLF]`, 파일 응답은 `[len][메타 JSON+CRLF][len][원문+CRLF]` 두 프레임
- 명령: `ProtocolType` 97종, 리터럴(본문 있음)은 `FILE-ADD`, `MSG-APPEND`, `WEBFOLDER-UPLOAD`, `BIGATTACH-APPEND` 4개(`ProtocolType.java:17,50,153,182`).
- 수신 버퍼: `SO_RCVBUF` 256KB, `AdaptiveRecvByteBufAllocator(64KB, 256KB, 1MB)`(e0a0619e).

**왜 이렇게 짰나**
- 원인: TCP는 메시지 경계가 없다. init 코드는 "한 번의 read = 한 요청"으로 가정해 `in.toString()` 후 `in.clear()`했다. 헤더가 두 세그먼트로 나뉘면 앞 조각만 파싱해 깨지고, 두 요청이 붙어 오면 뒤 요청을 버렸다. 버퍼가 가득 찼는지(`maxFastWritableBytes()==0`)로 추정하는 0be5cbbf 방식은 "버퍼가 덜 찼는데 아직 다 안 온 경우"를 못 잡는 휴리스틱이었다.
- 해결: 길이 prefix(length-field framing). 구분자(CRLF) 방식은 JSON/본문 안에 구분자가 들어갈 수 있고, 길이 prefix는 필요한 바이트 수를 정확히 안다.
- 진행: d3fd195e는 4자리 ASCII 숫자 문자열(`Integer.parseInt`) → c3b325de `readInt` → a4883622 다시 문자열 → 54020b8f `readInt` 확정(모두 2024-12-04 하루). 클라이언트와 맞추며 오간 것으로 보이나 상대 측 사정은 **확인 필요**. 4자리 문자열이면 9999바이트 상한이라 바이너리 int가 맞다.
- `LengthFieldBasedFrameDecoder`를 안 쓴 이유(설계 해석): 같은 디코더가 리터럴 본문을 프레임 단위로 메모리에 모으지 않고 파일로 흘려야 해서, 헤더/본문 상태(NEEDED_DATA/VERIFY/SINK)를 직접 관리했다. 당시 검토 기록은 없음 → **확인 필요**.

**바뀌어 온 이력**
`179da848` 경계 없음 → `60f9abca`·`c4973a3c`·`0be5cbbf`·`804883ae`(2024-11-08) 로그, 문자셋 비교, `maxFastWritableBytes` 휴리스틱 → `9414e2c6`(11-15) 디코더/인코더 에러 공통 처리 → `d3fd195e`(12-04) 4바이트 길이 + mark/reset → `c3b325de`/`a4883622`/`54020b8f`(12-04) 문자열↔int, int 확정 → `4f783b4d`(12-04) 응답 길이 prefix → `a296a8a0`(12-05) 본문 프레임 길이 검증, `BufferUtil` → `b9dab634`(12-05) 리팩터링 → `d5dfb308`(2025-04-02) 본문 끝 CRLF 2바이트 기대 제거 → `8d29742c`(05-12) 헤더 5토큰(hostName 추가), "GET " 매직 넘버(1195725856) 분기 제거.

**면접 30초 설명**
"초기 디코더는 한 번 읽은 버퍼를 한 요청으로 보고 통째로 비웠는데, 큰 요청이 TCP에서 나뉘어 오거나 두 요청이 붙어 오면 파싱이 깨졌습니다. 로그로 확인한 뒤 클라이언트와 프로토콜을 맞춰 4바이트 길이 prefix를 붙였고, `StoreReceiverRequestDecoder`에서 `markReaderIndex`로 표시해 두고 길이만큼 안 쌓였으면 `resetReaderIndex`로 되돌려 다음 read를 기다리게 했습니다. 응답도 `BufferUtil`로 같은 형식으로 맞췄고, 본문 프레임은 헤더에 선언한 크기보다 작으면 거부합니다."

**헷갈리기 쉬운 점**
- 길이 필드는 **바이너리 int**(4바이트 BE). "4자리 문자열"은 하루 사이 중간 버전.
- 헤더 길이 상한(maxFrameLength) 검사가 없다. 잘못된 길이가 오면 `new byte[messageLength]`로 큰 배열을 시도하거나 무한 대기할 수 있다(코드상 추론).
- `in.clear()`가 에러 처리(`handleDecodeException`)에 남아 있다. 에러 시 버퍼에 있던 뒤 요청도 버린다.
- `ByteToMessageDecoder`는 `decode`가 바이트를 소비하지 않고 out도 비어 있으면 루프를 멈추고 다음 read를 기다린다 — 그래서 `resetReaderIndex` 후 `return`이 맞다.

---

### 4. append 수신 (2024-12 ~ 2025-04 · a296a8a0, c132ba3f, 93782489, f33409c2, d5dfb308)

**내가 한 범위**
- init에 있던 것: continuation 응답 → `NEEDED_DATA`만큼 파일에 append하는 기본 골격(`obtainInputStream`), `FileBasedLiteral`, `MsgAppendParser/Processor`, `MailMessageServiceImpl.appendMessage` 골격. 작성자 **확인 필요**.
- 본인 커밋: 본문 프레임 길이 prefix와 크기 검증(`VERIFY`, a296a8a0), 파일명 `.received.emlq`와 received 디렉터리(e1ca1187, 93782489), 디코딩 실패·연결 끊김 시 파일 삭제(c132ba3f), 핸들러 검증 실패 시 삭제(a749e89f), 서비스 실패 시 정리의 예외별 catch 구성(c4c2d104)과 삭제 방식 변경(f33409c2) — `rollbackQFile`/`rollbackMdata` 메서드 자체는 init부터 있음, CRLF 더미 제거(d5dfb308), 단계별 로그(`[1]~[14]`).
- 타인: GCS 저장(`GcsStoreRepository`, 이승진 197ee0a2 등), Aspect의 busy lock 시 파일 삭제(이승진 7cda0011/f85a4cd6, 2025-08), append 검증 위치 변경(이승진 24e5226a).

**코드 지도**

| 단계 | 파일 | 클래스/메서드 | 역할 |
|---|---|---|---|
| 디코더 | `store-d/.../netty/StoreReceiverRequestDecoder.java` | `requestMoreData` `:203-209` | continuation 전송, 상태 저장 |
| | 〃 | `decode` 리터럴 분기 `:78-106` | 본문 길이 검증 → 파일 쓰기 → 완료 시 out |
| | 〃 | `needInputStream`, `writeToFile` `:159-190`, `getSink` `:192-201` | 받는 대로 파일 append |
| | 〃 | `channelInactive` `:66-71`, `handleDecodeException`, `deleteQFile` `:228-241` | 실패/끊김 시 파일 삭제 |
| 모델 | `mailbox/.../literal/FileBasedLiteral.java` | `getInputStream`, `size`, `close`(파일 삭제) | 파일 기반 본문 |
| | `mailbox/.../literal/LiteralRequestMessage.java` | `setLiteral`, `getSize`, default `close()` | 리터럴 명령 공통 인터페이스 |
| 핸들러 | `store-d/.../netty/StoreReceiverInboundHandler.java` | `channelRead0`, `deleteQFile` | 검증 실패·다른 사용자 시 삭제 |
| 처리기 | `store-d/.../protocol/msg/processor/MsgAppendProcessor.java` | `processCommand` | `hub.appendMessage` |
| 서비스 | `mailbox/.../msg/service/MailMessageServiceImpl.java` | `appendMessage` `:107-181`, `convertAndSave` `:198-237`, `rollbackQFile`, `rollbackMdata` | 파싱·GCS·DB·색인 이벤트, 실패 정리 |
| 저장 | `mailbox/.../store/repository/GcsStoreRepository.java` | `save`(`WriteChannel`) | 원문 업로드 |

**흐름**
1. 헤더 프레임 → `MsgAppendRequest`(JSON의 `size` 포함) 생성. `out`에 넣지 않고 `requestMoreData`로 continuation 전송 + `NEEDED_DATA=size`.
2. 클라이언트가 `[int 길이][원문]` 전송.
3. 다음 `decode`: `NEEDED_DATA` 있음 → `VERIFY` 전이면 4바이트 읽어 `messageLength < neededData`면 거부(500), 아니면 `VERIFY=true`.
4. `writeToFile`: 지금 버퍼에 있는 바이트를 전부 읽어 `getSink()` 파일에 append. 누적 크기 < size면 true(더 받기), 아니면 초과분을 잘라 쓰고 false.
5. 완료 → `new FileBasedLiteral(0, neededData, sink)` → `setLiteral` → `out.add` → 상태 맵 `clear()`.
6. 핸들러 → Processor → Hub(`@UseSqlSession` → `BEGIN EXCLUSIVE`) → `appendMessage`:
   `[1]` MIME 파싱 → `[2]` mdata 경로 생성 → `[3]` (gzip 옵션) GCS 저장 → `[4]` 플래그 → `[5]` `MailMessage` 빌드 → `[6]` 헤더 → `[7]` 검색 모델 → `[8]` `appendMessageToDB`(uid_next 증가 + INSERT) → `[9]` mail_search → `[10]` mail_header → `[11]` 폴더 통계 → `[12]` 태그 → `[13]` quota 파일 → `[14]` `saveIndexing`(이벤트).
7. 성공: Aspect `COMMIT` → `SuccessResponse`. 큐 파일은 색인 쪽이 이동(5번).
8. 실패: 서비스 catch에서 큐 파일 삭제(+DB/알 수 없는 예외면 GCS 원문 삭제) → 재던짐 → Aspect(DB 예외면 ROLLBACK) → 핸들러가 `ErrorResponse`.

**핵심 코드**

```java
// store-d/src/main/java/com/daou/dop/stored/netty/StoreReceiverRequestDecoder.java:78-106
Map<String, Object> attachment = ctx.channel().attr(FRAME_DECODE_ATTACHMENT_ATTRIBUTE_KEY).get();
if (attachment.containsKey(NEEDED_DATA)) {                    // continuation 이후 = 본문 수신 중
    int neededData = (Integer) attachment.get(NEEDED_DATA);   // 헤더 JSON에 선언된 size
    if (!attachment.containsKey(VERIFY)) {                    // 본문 첫 조각에서 한 번만
        if (in.readableBytes() < BufferUtil.MESSAGE_LEN) return;
        int messageLength = in.readInt();                     // 본문 프레임 길이
        if (messageLength < neededData) {                     // 선언보다 작으면 거부 (a296a8a0)
            handleDecodeException(ctx, in, new StoreDException("Invalid data size"), MailBoxStatusCode.RETURN.getCode());
            return;
        }
        attachment.put(VERIFY, true);
    }
    if (needInputStream(ctx, in, attachment)) {               // 아직 size만큼 안 모임 → 파일에 쓰고 대기
        return;
    }
    File sink = (File) attachment.get(SINK);
    LiteralRequestMessage literalRequestMessage = (LiteralRequestMessage) attachment.get(REQUEST_MESSAGE);
    FileBasedLiteral literal = new FileBasedLiteral(0, neededData, sink); // 본문은 메모리 아닌 파일 참조
    literalRequestMessage.setLiteral(literal);
    out.add(literalRequestMessage);                           // 이제야 핸들러로 전달
    attachment.clear();
    return;
}
```

```java
// 〃 :167-190
private boolean writeToFile(ByteBuf in, int size, File sink) throws IOException {
    int readableBytes = in.readableBytes();
    byte[] bytes = new byte[readableBytes];                   // 이번 read분(최대 수신 버퍼 크기)만 힙에
    in.readBytes(bytes);
    if (readableBytes + sink.length() < size) {               // 아직 모자람
        try (FileOutputStream fos = new FileOutputStream(sink, true)) { fos.write(bytes); }
        return true;
    }
    int overSize = readableBytes + (int) sink.length() - size;
    try (FileOutputStream fos = new FileOutputStream(sink, true)) {
        fos.write(bytes, 0, readableBytes - overSize);        // size 초과분은 버림
    }
    return false;
}
```

```java
// mailbox/src/main/java/com/daou/dop/mailbox/domain/msg/service/MailMessageServiceImpl.java:154-180 (실패 정리)
} catch (MailParsingException e) {             // 파싱 실패: 아직 GCS 저장 전일 수 있음
    rollbackQFile(((FileBasedLiteral) literal).getFile());   // received 큐 파일 삭제
    throw e;
} catch (StoreException e) { rollbackQFile(...); throw e;    // GCS 저장 실패
} catch (FileWriteException e) { rollbackQFile(...); throw e;
} catch (MailBoxDataAccessException e) {       // DB 실패: GCS에는 이미 올라감
    rollbackQFile(((FileBasedLiteral) literal).getFile());
    if (mailMessage != null) {
        rollbackMdata(mailMessage.getFullPath());            // 올린 원문도 삭제
    }
    throw e;                                                  // → Aspect가 ROLLBACK
} catch (Exception e) { rollbackQFile(...); if (mailMessage != null) rollbackMdata(...); throw e; }
```

**데이터·설정**
- 큐 파일: `/opt/dop/queue/received/<UUID>_<epochMs>.received.emlq` (`mail.store.receivedQDir`, mailbox `application-prod.yml:5`; 파일명 규칙 `QFileProcessType.RECEIVED.getFilePath`).
- continuation 응답: `[len]{"message":"OK", "code": 200}\r\n`.
- 원문: prod `mail.store.type: 'GCS'`, 경로는 `mdataPath/<messageStore>/yyyymmdd/...`(`FileSystemManager.generateMdataFullPath`).
- 정리 지점 4곳: 디코더(디코딩 오류·연결 끊김) / 핸들러(Validation 실패·`InvalidMessageStoreException`) / 서비스(appendMessage catch) / Aspect(BEGIN 실패, DB 예외 — 2025-08 이승진).

**왜 이렇게 짰나**
- IMAP의 literal + continuation(`+ go ahead`) 방식과 같은 구조: 서버가 헤더(메일함, 크기 등)를 먼저 확인한 뒤 본문을 받는다.
- 본문을 `ByteBuf`에 모으면 수십 MB 메일 × 동시 연결만큼 힙을 쓴다. 받는 대로 파일에 쓰면 연결당 힙은 수신 버퍼 크기 수준. 받은 파일은 이후 MIME 파싱(InputStream), GCS 업로드, 색인 큐 파일로 그대로 재사용(복사 없음).
- 실패 시 남는 파일: 큐 디렉터리에 고아 파일이 쌓이면 색인 백그라운드 처리나 디스크에 영향 → 실패 지점마다 삭제.
- 트레이드오프: 청크마다 `FileOutputStream`을 새로 연다(열린 채널 유지 안 함). 디스크 I/O를 이벤트 루프 스레드에서 한다.

**바뀌어 온 이력**
`179da848` 골격(`qDir/<uuid>.eml`, CRLF 2바이트 더 기대) → `e1ca1187`(2024-11-06) `.received.emlq` 상태 확장자 → `a296a8a0`(12-05) 본문 길이 prefix + `VERIFY` → `ca7dee19`(2025-01-24) 로그 → `93782489`(02-05) received 디렉터리 분리 → `f33409c2`(02-05) 파일 삭제 처리 방법 변경 → `c132ba3f`(02-06) 리터럴 쓰기 중 실패 시 삭제 → `a749e89f`(02-07) 핸들러 삭제 → `c2cdb835`~`e777594f`(03-26~27) 리터럴 크기 로그 → `d5dfb308`(04-02) CRLF 더미 제거 → (인수 후) `7cda0011`/`f85a4cd6`(2025-08) Aspect에서 삭제, `24e5226a` 검증 위치 변경.
(서비스 `rollbackQFile/rollbackMdata` 메서드 자체는 **init(179da848)부터 있음**. 본인 변경은 `c4c2d104`(2024-11-15, append 에러 공통 처리 — 예외별 catch 블록 구성)와 `f33409c2`(2025-02-05, `file.delete()` → `Files.deleteIfExists` + IOException 로그).)

**면접 30초 설명**
"append는 IMAP literal처럼 두 단계입니다. `StoreReceiverRequestDecoder`가 헤더를 받아 `MsgAppendRequest`를 만들고 바로 핸들러로 넘기지 않고 continuation을 보냅니다. 그다음 본문은 길이 prefix를 검증한 뒤 받는 대로 received 큐 디렉터리의 `.emlq` 파일에 append하고, 선언한 크기만큼 다 받으면 `FileBasedLiteral`을 붙여 핸들러로 넘깁니다. 서비스는 그 파일을 스트림으로 MIME 파싱하고 GCS에 올리고 SQLite에 메타를 씁니다. 디코딩 중 끊기거나, 검증에서 걸리거나, 저장 중 실패하면 각 단계에서 큐 파일과 이미 올린 원문을 지웁니다."

**헷갈리기 쉬운 점**
- "본문 전체 스트리밍"은 **수신과 GCS 업로드**까지. MIME 파싱(`MimeDescriptorImpl`)은 파트 본문을 `ByteArrayOutputStream`에 복사하고, FILE-GET 응답은 원문 전체를 ByteBuf에 쓴다(이전 조사 확인). "메모리 상한 보장"이라고 하면 안 됨.
- `writeToFile`은 초과분(`overSize`)을 **버린다**. 클라이언트가 본문 뒤에 다음 요청을 바로 붙여 보내면 그 앞부분이 사라진다 — 요청-응답을 번갈아 하는 프로토콜이라 전제상 문제가 안 되는 구조. 코드에 `// todo-star header 만큼 읽도록 변경해야함` 주석이 남아 있다.
- 본문 프레임의 길이 값(`messageLength`)은 검증에만 쓰고, 실제로 받는 양은 헤더의 `size`(`NEEDED_DATA`) 기준.
- 성공해도 받은 파일을 지우지 않는다 — 색인 큐 파일로 넘어간다(5번).

---

### 5. 저장 → 색인 연결 (2024-11 ~ 2025-02 · e1ca1187, 93782489, c626b60f, b6c33050, 414b2ccb)

**내가 한 범위**
- init에 있던 것: `IndexingEventListener`(`@Async("indexTaskExecutor")` + `@EventListener`), `EmbeddedIndexingService`, `HttpQueue`, `MsgIndexingAddEvent` 발행 구조. 작성자 **확인 필요**(이승진 `6a9bbfe9`/`6d4893c9`(2024-10-31)가 COPY 리스너 추가).
- 본인: 큐 파일 상태 확장자(`QFileProcessType` RECEIVED/INDEXING)와 `progressToNextState`(xattr `user:QFileMeta` 메타 저장 후 이동) 도입(e1ca1187, 2024-11-06), 이벤트에 msgSize 추가(7973e658), **received / indexing 디렉터리 분리 + indexing 하위 0~1023 분산**(93782489), 기동 시 received/qDir 디렉터리 생성(c626b60f, b6c33050), indexer에 넘기는 경로를 rootQDir 기준 상대경로로(414b2ccb), 스레드풀 설정 분리(754b4ee8).
- 타인: 전송 실패 시 backup 이동 `moveToBackground`(이승진 99b02379, 2025-02-10), indexer 쪽 재시도·fail 디렉터리·`BackgroundIndexer`(외주/이승진).

**코드 지도**

| 파일 | 클래스/메서드 | 역할 |
|---|---|---|
| `mailbox/.../msg/service/MailMessageServiceImpl.java` | `saveIndexing` `:691-713` | `MsgIndexingAddEvent` 생성·발행(트랜잭션 안) |
| `mailbox/.../indexing/service/IndexingEventListener.java` | `handleIndexingAddEvent` `:37-52` | 비동기로 `AddIndexRequest` 생성 |
| `mailbox/.../indexing/service/EmbeddedIndexingService.java` | `request(AddIndexRequest)` `:36-60` | 파일 이동 → HTTP 전송, 실패 시 backup |
| `mailbox/.../indexing/manager/QFileProgressManager.java` | `progressToNextState` `:35-55`, `getDirPath`, `setFilePath`, `moveToBackground` | received → indexing/<n>/ 이동, 메타 xattr |
| `mailbox/.../indexing/type/QFileProcessType.java` | `getFilePath`, `nextProcessType` | `.received.emlq` → `.indexing.emlq` |
| `mailbox/.../indexing/queue/HttpQueue.java` | `convertAndSend` | `RestTemplate` POST |
| `mailbox/.../config/AsyncConfig.java` | `indexTaskExecutor` | ThreadPoolTaskExecutor |

**흐름**
1. `appendMessage` `[14]` → `saveIndexing`: 큐 파일이 있고 searchKey가 있으면 `MsgIndexingAddEvent`(messageStore는 ThreadLocal에서, filePath=received 절대경로, searchKey, uid, email, receiveTime, baseSubject, msgSize) → `publisher.publishEvent`. **이 시점은 BEGIN EXCLUSIVE 안, COMMIT 전.**
2. `@EventListener` + `@Async("indexTaskExecutor")` → 호출 스레드는 바로 반환, `index-task-*` 스레드에서 `handleIndexingAddEvent`.
3. received 기준 상대경로로 `AddIndexRequest` → `EmbeddedIndexingService.request`.
4. `QFileProgressManager.progressToNextState`: 파일 존재 확인 → `.indexing.emlq` 이름 계산 → 요청 JSON을 xattr `user:QFileMeta`에 저장 → `indexing/<currentTimeMillis & 1023>/` 생성 → `Files.move` → 요청의 filePath를 rootQDir 기준 상대경로로 갱신.
5. `HttpQueue.convertAndSend` → indexer `/index` POST.
6. 전송 실패(`FailSendMessageException`, `RestClientException`, `IOException`, JSON 오류) → `moveToBackground` → `/opt/dop/queue/backup/...` → indexer `BackgroundIndexer`가 주기적으로 재처리(indexer 쪽, 본인 작업 아님).

**핵심 코드**

```java
// mailbox/src/main/java/com/daou/dop/mailbox/indexing/service/IndexingEventListener.java:37-52
@Async("indexTaskExecutor")            // 별도 스레드풀 — append 응답을 막지 않음
@EventListener                         // 트랜잭션 단계와 무관하게 publishEvent 즉시 디스패치
public void handleIndexingAddEvent(MsgIndexingAddEvent event) {
    AddIndexRequest indexRequest = AddIndexRequest.builder()
            .messageStore(event.getMessageStore())                 // ThreadLocal이 없으니 이벤트에 담아 옴
            .filePath(getRelativize(receivedQDir, event.getFilePath())) // received 기준 상대경로
            .searchKey(event.getSearchKey())
            .messageUid(event.getMessageUid())
            ...
            .build();
    indexingService.request(indexRequest);
}
```

```java
// mailbox/src/main/java/com/daou/dop/mailbox/indexing/manager/QFileProgressManager.java:35-59 (93782489, 414b2ccb)
public void progressToNextState(QFileSupport qFileSupport) throws IOException {
    String filePath = qFileSupport.getFilePath();
    Path source = Path.of(receivedQDir, filePath);                     // /opt/dop/queue/received/x.received.emlq
    if (!Files.exists(source)) throw new FileNotFoundException("File not found: " + source);
    String targetFilePath = QFileProcessType.nextProcessType(filePath); // x.indexing.emlq
    String writeValueAsString = objectMapper.writeValueAsString(qFileSupport);
    Files.setAttribute(source, "user:QFileMeta", writeValueAsString.getBytes()); // 메타를 파일 xattr에 (재처리 시 복원용)
    String random = getDirPath().toString();                           // currentTimeMillis & 1023
    Files.createDirectories(Path.of(indexingQDir, random));
    Path fullPath = Path.of(indexingQDir, random, targetFilePath);     // /opt/dop/queue/indexing/<0~1023>/x.indexing.emlq
    Files.move(source, fullPath);                                      // 같은 파일시스템이면 rename
    setFilePath(qFileSupport, random, targetFilePath);                 // indexer엔 rootQDir 기준 상대경로 전달
}
```

**데이터·설정**
- 디렉터리(mailbox `application-prod.yml`): `rootQDir: /opt/dop/queue`, `receivedQDir: /opt/dop/queue/received`, `qDir: /opt/dop/queue/indexing`, `indexing.background.qDir: /opt/dop/queue/backup`(`:24`). fail 디렉터리는 indexer 설정.
- 파일 상태: `<uuid>_<ms>.received.emlq` → `indexing/<n>/<uuid>_<ms>.indexing.emlq` (+ xattr `user:QFileMeta`).
- 스레드풀(prod `:53-56`): index core 2 / max 5 / queue 100, 이름 `index-task`.
- `MsgIndexingAddEvent.indexArea(7)` 고정.

**왜 이렇게 짰나**
- 색인(본문·첨부 텍스트 추출, FTS 쓰기)은 느리므로 append 응답 경로에서 분리.
- 상태를 디렉터리/확장자로 표현: 프로세스가 죽어도 파일이 어느 디렉터리에 있는지로 어디까지 갔는지 알 수 있고, 메타는 xattr에 있어 파일만으로 재처리 가능.
- received/indexing 분리(93782489): 그전엔 `qDir` 한 디렉터리에서 이름만 바꿨다. "수신 중/수신 완료·미전송" 파일과 "색인 대기" 파일이 섞이면 백그라운드 처리 대상 구분이 어렵다. indexing 아래 0~1023 하위 디렉터리는 한 디렉터리 파일 수가 너무 커지는 것을 막으려는 분산(커밋 메시지엔 이유 없음, 설계 해석).
- `@TransactionalEventListener(AFTER_COMMIT)`는 Spring 트랜잭션 동기화가 있어야 동작하는데 이 구조엔 Spring TX가 없어 쓸 수 없다.

**바뀌어 온 이력**
init 리스너/서비스 → `e1ca1187`(2024-11-06) `QFileProcessType`, xattr 메타, `progressToNextState` → `7973e658`(12-03) msgSize → `93782489`(2025-02-05) received/indexing 분리, 하위 1024 분산 → `754b4ee8`(02-05) ThreadPool config 분리 → `99b02379`(02-10, 이승진) backup 이동 → `c626b60f`(02-11) received 폴더 생성 → `b6c33050`(02-13) qDir 생성 → `414b2ccb`(02-14) indexer 전달 경로를 rootQDir 기준으로.

**면접 30초 설명**
"메일 저장 마지막 단계에서 `MsgIndexingAddEvent`를 발행하고, `IndexingEventListener`가 `@Async` 스레드풀에서 받아 처리하게 해서 저장 응답이 색인을 기다리지 않게 했습니다. 수신한 원문 파일을 그대로 색인 요청 파일로 쓰는데, 제가 상태를 디렉터리로 나눴습니다. 받는 중이거나 받기만 한 파일은 received, 색인 요청을 보낸 파일은 메타데이터를 xattr에 붙여 indexing 아래 1024개 하위 디렉터리로 옮깁니다. 전송이 실패하면 backup으로 옮겨 indexer의 백그라운드 처리기가 다시 가져갑니다."

**헷갈리기 쉬운 점**
- **"커밋 후 색인"이 아니다.** `publishEvent`는 `BEGIN EXCLUSIVE` 안에서 호출되고, `@Async`라 리스너가 COMMIT 전에 실행될 수 있다. 이후 COMMIT이 실패하거나 ROLLBACK되면 색인 요청만 남는다. 또 Aspect/서비스의 실패 정리(`rollbackQFile`)와 리스너의 `Files.move`가 경합할 수 있다(코드상 추론).
- backup·fail·재시도는 본인 작업이 아니다(이승진·외주).
- 스레드풀 큐(100)가 차면 `TaskRejectedException`이 `publishEvent` 호출 쪽(=append 트랜잭션 안)으로 올라온다 → `catch (Exception e)`에서 큐 파일·원문 삭제 후 재던짐. Aspect는 이 예외를 ROLLBACK 대상으로 보지 않는다. 운영에서 발생했는지는 **확인 필요**.
- 메타를 xattr에 쓰므로 파일시스템이 user xattr를 지원해야 한다.

---

### 6. busy lock 대응 (2025-01 ~ 2025-02 · DOPMAIL-290 · 134528c4 → d82a07e0 → 9a311ad5 → 2b325390, reserv 제거 b2cf97b3)

**내가 한 범위**
- 2025-01~02의 busy 관련 변경은 전부 본인 커밋. 인수 후 이승진이 2025-08에 BusyHandler를 다시 넣었다가 주석 처리(abf8e3f6 → eda2d7e5 → 20a55ea8 → cbd7fc2a)하고 BEGIN 실패 시 큐 파일 삭제(7cda0011, f85a4cd6)를 추가.
- RESERVE(공용 예약 DB) 구조 자체는 init에 있었음(작성자 **확인 필요**). 제거는 본인(8063570c, b2cf97b3).

**코드 지도**

| 파일 | 클래스/메서드 | 역할 |
|---|---|---|
| `mailbox/src/main/resources/.../connection/mapper/ConnectionMapper.xml` | `beginTransaction`, `beginExclusive` | `BEGIN TRANSACTION;`(DEFERRED) / `BEGIN EXCLUSIVE;` |
| `mailbox/.../connection/SqlSessionAspect.java` | `begin` `:64-71` | readOnly → DEFERRED, 쓰기 → EXCLUSIVE |
| `mailbox/.../connection/ThreadLocalConnectionManager.java` | `beginExclusive` `:110-130`, `beginTransaction` `:88-108` | 실패 시 rollbackOnly 표시 |
| `mailbox/.../config/MyBatisConfig.java` | `statementTimeout` `:17-29` | MyBatis `defaultStatementTimeout` 3초 |
| `mailbox/.../connection/ConnectionContext.java` | `busyHandler`, `setBusyHandler` `:42-56, 95-98` | BusyHandler(300ms×20) 정의만 남고 미사용 |
| `mailbox/.../msg/repository/MyBatisMailMessageRepositoryImpl.java` | `getUidNextAndIncrease` `:116-124` | 읽고-쓰는 대표 쿼리(SELECT uid_next → UPDATE) |
| (삭제됨) `config/ConnectionPoolConfig.java`, `domain/reserve/*`, `protocol/reserve/*` | `reserveDataSource`, `ReserveService` 등 | 공용 예약 DB |

**흐름 (현재)**
1. 쓰기 명령 → Aspect `begin(value, false)` → `beginExclusive` → `BEGIN EXCLUSIVE;`
2. 다른 커넥션이 같은 파일을 잡고 있으면 SQLite가 SQLITE_BUSY까지 busy timeout만큼 대기(앱에서 명시 설정 없음 → sqlite-jdbc 기본값, 값은 **확인 필요**). MyBatis statement timeout(3초)는 JDBC `Statement.setQueryTimeout`으로 걸림.
3. 실패 → `PersistenceException` → `TransactionStatus(type, false, true)` → Aspect가 `TransactionBeginException`(append면 큐 파일 삭제) → 핸들러 `ErrorResponse`.
4. 읽기 명령 → `BEGIN TRANSACTION;`(DEFERRED) → 첫 SELECT에서 SHARED 락 → COMMIT.

**핵심 코드**

```xml
<!-- mailbox/src/main/resources/com/daou/dop/mailbox/common/connection/mapper/ConnectionMapper.xml:6-20 -->
<update id="beginTransaction">  BEGIN TRANSACTION;  </update>  <!-- 읽기: DEFERRED, 첫 SELECT 때 SHARED -->
<update id="beginExclusive">    BEGIN EXCLUSIVE;    </update>  <!-- 쓰기: 시작 시점에 EXCLUSIVE 락 확보 -->
<update id="commit">            COMMIT;             </update>
<update id="rollback">          ROLLBACK;           </update>
```

```java
// mailbox/src/main/java/com/daou/dop/mailbox/domain/msg/repository/MyBatisMailMessageRepositoryImpl.java:116-124
public int getUidNextAndIncrease(long folderNo) {
    return template.execute(sqlSession -> {
        MailboxMapper mailFolderMapper = sqlSession.getMapper(MailboxMapper.class);
        Long uidNext = mailFolderMapper.getMailFolder(folderNo).getUidNext(); // 먼저 읽고 (SHARED)
        mailFolderMapper.updateUidNext(folderNo, uidNext + 1);                // 나중에 씀 (RESERVED로 승격 필요)
        return uidNext.intValue();
    });
}
// DEFERRED 트랜잭션 두 개가 동시에 여기 오면 둘 다 SHARED를 쥔 채 승격을 기다려 한쪽이 바로 SQLITE_BUSY.
// BEGIN EXCLUSIVE면 두 번째 트랜잭션은 BEGIN에서 기다리므로 이 교착이 생기지 않는다.
```

```java
// mailbox/src/main/java/com/daou/dop/mailbox/config/MyBatisConfig.java:17-29 (74a7d9db, 2b325390)
@Value("${mailbox.mybatis.statementTimeout: 3}")   // 30 → 5 → 3초
private int statementTimeout;
...
configuration.setDefaultStatementTimeout(statementTimeout); // 모든 매퍼 문장에 쿼리 타임아웃
```

```java
// 제거 전 RESERVE 구조 (b2cf97b3~1)
// config/ConnectionPoolConfig.java — 공용 DB는 사용자별이 아니라 HikariCP 풀
@Bean(destroyMethod = "close")
public HikariDataSource reserveDataSource() {
    ...
    dataSource.setJdbcUrl(dbConnectionConfig.getReserveJdbcUrl());     // jdbc:sqlite:reserve/_Reserve.db (privateDB: false)
    dataSource.setMaximumPoolSize(...);                                // min 5 / max 5
    dataSource.setConnectionInitSql(...);                              // 'PRAGMA busy_timeout = 500'
}
// ConnectionContext — 같은 Map에 RESERVE 세션을 풀에서 빌려 넣음
if (ConnectionType.RESERVE.equals(connectionType)) {
    SqlSession sqlSessionWithReserve = getSqlSessionWithReserve(factory, reserveDataSource); // autoCommit(false)
    sqlSessionMap.put(ConnectionType.RESERVE, sqlSessionWithReserve);
}
// ThreadLocalConnectionManager.closeSingleUse — 채널 소유 컨텍스트라도 RESERVE 커넥션은 요청마다 풀에 반납
} else { connectionContext.closeReserveDB(); }
// MailboxServiceHub (init ~ 2025-01-21)
@UseSqlSession(value = {ConnectionType.MINDEX, ConnectionType.MDN, ConnectionType.RESERVE})
public ExpungeResponse expunge(ExpungeRequest expungeRequest) { ... }   // 예약 메일 삭제까지 같은 Aspect 묶음
@UseSqlSession(value = {ConnectionType.RESERVE}) public void reserveAdd(...)   // RESERVE-ADD/ADD-RETRY/READ/DEL 4개 명령
```

**데이터·설정**
- 현재: JDBC URL 파라미터 없음, BusyHandler 미설정, `defaultStatementTimeout` 3초(`mailbox.mybatis.statementTimeout`), `autoCommit(true)`, journal_mode 설정 없음(SQLite 기본 rollback journal, 코드 기준).
- 제거 전 RESERVE: `reserve/_Reserve.db`(상대경로, 공용), 테이블 `reserve_mail(reserve_time, reserve_file, reserve_sender, reserve_retry)` + `idx1_reserve_mail(reserve_time, reserve_sender)`, HikariCP min/max 5, connectionTimeout 30000, init SQL `PRAGMA busy_timeout = 500`. 명령 `RESERVE-ADD`, `RESERVE-ADD-RETRY`, `RESERVE-READ`, `RESERVE-DEL`. 요청에 messageStore가 비어 있으면 `isTransaction`이 RESERVE 단독일 때만 트랜잭션 처리.
- 제거 후 `expunge`는 `isDeleteReserved`면 삭제된 msgId 목록을 `ExpungeResponse`로 돌려줌(`MailMessageServiceImpl.java` deleteMailMessages 끝부분) — 예약 정리는 호출 측 책임으로 넘어간 형태.

**왜 이렇게 짰나**
- 증상: 같은 사용자 mindex에 쓰기가 동시에 들어올 때 SQLITE_BUSY. 커밋 주석(134528c4~d82a07e0 사이 `BUSY_TIMEOUT` 주석): "나에게 쓰기시 MSS, IMAP 동시에(받은메일함, 보낸메일함) APPEND가 들어오는 경우가 발생 / 최소 1초 이상으로 설정 필요".
- 1단계(01-08, 하루에 여러 번): busy_timeout 500 → 2000ms, BusyHandler(100ms×20), 다시 timeout, `setBusyTimeout`, 2,000,000, URL `?busy_timeout=5000000`. 대기 시간만 늘리는 접근.
- 2단계(01-21, d82a07e0): 대기 시간으로 안 풀리는 경우가 있다고 보고 트랜잭션 시작 방식을 바꿈. JDBC autoCommit(false)는 드라이버가 DEFERRED `BEGIN`을 보내므로, 읽고-쓰는 트랜잭션 두 개가 SHARED를 쥔 채 승격을 기다리면 SQLite가 교착을 피하려고 한쪽에 **busy handler를 부르지 않고** 바로 BUSY를 준다. 그래서 autoCommit(true) + `BEGIN EXCLUSIVE`를 직접 실행해 쓰기 트랜잭션은 시작부터 락을 잡고 줄 서게 했다. 같은 커밋에서 URL busy_timeout 제거, BusyHandler(300ms×20)로 대체, statement timeout 30초 추가.
- 3단계(01-21 b9cdfa8e): BusyHandler 주석 처리("timeout 시간을 설정하여 동작안함, 팔요시 사용").
- 4단계(01-23, 9a311ad5): d82a07e0에서 readOnly는 BEGIN 없이 autocommit이었는데, 읽기도 `BEGIN TRANSACTION`(DEFERRED)으로 감싸고 쓰기는 `beginExclusive`로 분리. 읽기는 SHARED만 잡아 동시 읽기 허용, 여러 SELECT를 한 스냅숏으로.
- 5단계(02-18): statement timeout 30 → 5 → 3초. 오래 기다리기보다 빨리 실패를 돌려주고 클라이언트(MTA 등)가 재시도하게 하는 방향(재시도 정책은 클라이언트 쪽 → **확인 필요**).
- reserv 제거(01-21~22): 공용 DB 하나를 HikariCP 5개 커넥션으로 모든 사용자 요청이 공유 → 사용자별 DB와 달리 store 전체가 한 파일 락을 경쟁. 또 `expunge`가 MINDEX·MDN과 함께 RESERVE까지 BEGIN했다. busy lock 작업 바로 그날 제거한 것은 확인되나 **제거 이유는 커밋 메시지에 없음 → 본인 기억 확인 필요**(예: 예약 발송 기능이 다른 서비스로 이동).
- 버린 대안: WAL 모드(동시 읽기/쓰기 가능) — NFS에서는 공유 메모리 wal-index 때문에 쓸 수 없다는 판단(본인 설명 기준, 코드에 journal_mode 설정 없음). `BEGIN IMMEDIATE` — 읽기를 막지 않아 더 가벼운데 EXCLUSIVE를 고른 이유는 기록 없음 → **확인 필요**.

**바뀌어 온 이력**
`134528c4`(2025-01-08) BUSY_TIMEOUT 500→2000 + BusyHandler(100ms×20) → `292800d4` → `be448192`(BusyHandler 제거, busy_timeout 복귀) → `fdc9ddb1`(`setBusyTimeout`) → `2763ec07`(2,000,000) → `feec52d6`(URL `?busy_timeout=5000000`) → `d82a07e0`(01-21) autoCommit(true) + SQL BEGIN EXCLUSIVE + `TransactionStatus` + BusyHandler(300ms×20) + statementTimeout 30 + URL 파라미터 제거 → `0079b08e` readOnly 플래그 → `b9cdfa8e` BusyHandler 주석 → `8063570c`(01-21) expunge에서 RESERVE 제외 → `b2cf97b3`(01-22) RESERVE 전체 삭제(41파일, −937줄) → `7a3ef177`/`9a311ad5`(01-23) DEFERRED/EXCLUSIVE 분리 → `474032d3`/`77c49d11`/`f1845e97` → `74a7d9db`(02-18) statementTimeout 설정화(기본 5) → `2b325390`(02-18) 기본 3초. (인수 후 2025-08 이승진: BusyHandler 재도입 후 주석, BEGIN 실패 시 큐 파일 삭제)

**면접 30초 설명**
"같은 사용자에게 나에게 쓰기처럼 받은메일함·보낸메일함 append가 동시에 들어오면 사용자 mindex SQLite에서 busy lock이 났습니다. 처음엔 busy_timeout과 재시도 핸들러를 늘려 봤는데, uid_next를 읽고 바로 갱신하는 식의 트랜잭션은 DEFERRED로 시작하면 두 트랜잭션이 읽기 락을 쥔 채 서로 기다려서 대기 시간을 늘려도 바로 실패했습니다. 그래서 JDBC autoCommit 대신 `ConnectionMapper`로 `BEGIN EXCLUSIVE`를 직접 실행해 쓰기는 시작부터 락을 잡고 줄 서게 하고, 읽기는 `BEGIN`으로 가볍게 열었습니다. 대기 상한은 MyBatis statement timeout 3초로 두어 오래 붙잡지 않고 실패를 돌려주게 했고, 같은 시기에 모든 사용자가 공유하던 예약 메일 DB와 그 로직을 store에서 걷어냈습니다."

**헷갈리기 쉬운 점**
- **이전 조사 정정**: reserv는 expunge 트랜잭션에 **들어 있었다**. init부터 2025-01-21까지 `expunge`는 `@UseSqlSession({MINDEX, MDN, RESERVE})`였고, `8063570c`에서 `{MINDEX, MDN}`으로 바뀌었다. 다만 당시 커밋도 DB별 순차 `sqlSession.commit()`이라 원자적이진 않았다. 나머지 예약 명령 4개는 RESERVE 단독.
- RESERVE는 사용자별 `DriverManager` 연결이 아니라 **HikariCP 풀**이었고, 채널에 묶이지 않고 요청마다 `closeReserveDB()`로 반납했다.
- 현재 busy_timeout 실효값: 앱 코드에 설정 없음. sqlite-jdbc 기본 busy timeout과 statement timeout 3초가 어떻게 상호작용하는지는 **확인 필요**(드라이버 버전 3.47.2.0 기준 기본값을 직접 확인해야 함).
- `BEGIN EXCLUSIVE`는 rollback journal 모드에서 다른 커넥션의 **읽기까지** 막는다. 쓰기 하나가 길어지면(예: GCS 업로드가 트랜잭션 안에 있음 — `convertAndSave`의 `mdataRepository.save`가 Aspect의 BEGIN 이후 실행) 같은 사용자의 목록 조회도 기다린다. 트랜잭션 범위 안에 외부 I/O가 있다는 점은 개선점으로 말할 수 있다.
- "statement timeout으로 busy를 해결"이 아니라 "실패를 빨리 돌려주는 상한"이다. 근본 대응은 EXCLUSIVE/DEFERRED 분리.

---

## 성능 안정화 · 고객사 장애 대응 (daouoffice) — 코드 워크스루

> 근거: git 최상위 `/Users/daou-8691/Documents/git/do` (daouoffice · notifier · ladmin), 본인 커밋(author `starlight2083` / `변재혁`), `git log --all`.
> 경로 약어: `common/` = `daouoffice/go-common/src/main/java/com/daou/go/`, `web/` = `daouoffice/go-web/src/main/java/com/daou/go/`, `plugin/` = `notifier/plugins/openfire-goservice-plugin/src/java/org/jivesoftware/openfire/plugin/go/`
> 라인 번호는 **2026-11-05 develop 작업트리 기준**이다. 2024년 이후 다른 사람이 손댄 부분(스패로우 정적분석 대응, Oracle 호환 쿼리, Spring Data 2.x 전환)이 섞여 있으므로, 당시 코드가 중요한 곳은 `git show <hash>:<path>` 로 따로 표시했다.
> 성능 수치(28초→0.6초 등)는 저장소에 없다. 이 문서는 구조와 흐름만 다룬다.

---

### 전체 코드 지도

```
web/ (Controller, go-web)                     common/ (Service·Repository·Domain, go-common)            설정
──────────────────────────────────────        ───────────────────────────────────────────────            ───────────────
core/controller/api/DepartmentController      core/service/DeptWebServiceImpl     (권한검사·조립)          go-common/src/main/resources/
  GET /departments/relation/target     ──▶      getRelationChangedCompanyIds                                 ehcache_user.xml  (jpa-2lc-org)
  GET /departments/relation/accessible ──▶      getAllDepartmentChildren  ──┐                               ehcache_admin.xml / _development.xml
  GET /departments/relation/entire     ──▶      getEntireDeptChildren     ──┤                            ladmin/config/go/ehcache_*.xml (설치형 배포본)
                                              core/service/DeptCacheableServiceImpl  ◀┘ @Cacheable + *Aware 14종
                                              core/service/DeptServiceImpl#getDeptChildrenModel (native 2회 + 메모리 트리)
                                              core/repository/DeptMemberRepository / DepartmentRepository (native)
                                              core/event/listner/Dept*EventListener → *Aware 콜백
                                              core/component/DeptCacheableInitializer / OrgCacheInitializer (기동 워밍업)

ehr/timeline/controller/api/TimelineUserController (@RequestMapping("/ehr/timeline"))
  POST /status, /history ...  ──▶ ehr/timeline/service/web/TimelineHistoryWebServiceImpl#create
                                      └ timeline.display.relay=false 일 때만 TimelineOneDayEventPublisher (즉시 푸시)
  GET  /display               ──▶ TimelineUserWebServiceImpl#getIntegratedEmployeesDisplay (응답 pull)
  GET  /info                  ──▶ ehr/common/service/EhrWebServiceImpl (사이드 정보)
                              Quartz TimelineDisplayRelayJob (1분) → TimelineBatchManager → TimelineOneDayNotifier
                                → TimelinePushManager → TimelinePushMessageConverter → 큐 → XmppSenderImpl → notifier(openfire)

chat/controller/api/ChatHistoryController
  GET /chat/new/buddies       ──▶ chat/service/ChatHistoryServiceImpl#getChatBuddiesWithPin
                                    → ChatBuddyRepository#getDataForChatBuddyModel (native, Slice<Object[]>)
                                    → ChatBuddyMap(Object[] 래퍼) → ChatModelConverter#convertToModel(map, me)

notifier/plugins/openfire-goservice-plugin  GoServicePlugin → InterceptorManager.addInterceptor(GoCustomInterceptor)
```

본인 코드 위치 요약

| 영역 | 본인이 새로 만든 것 | 본인이 고친 기존 것 |
|---|---|---|
| 조직도 | `DeptCacheableService(Impl)`, `DeptChildrenEntireModel`, `MaxUpdatedDepartmentModel`, `DeptCacheableInitializer`, `OrgCacheInitializer`, `OrgCacheInitProperties`, 이벤트 6종(`DeptMoved/DeptMemberSaved/DeptMemberSeqMoved/DeptOrderItemChanged/DeptTempDeleted/UserPositionChanged` Event·Listener·Aware), `DeptMemberModelMap`, `DepartmentModelMapForDeptChildrenModel`, `jpa-2lc-org` 캐시 영역 | `DeptWebServiceImpl#getAllDepartmentChildren`, `DepartmentController` relation API, `DeptServiceImpl`(이벤트 발행 지점) |
| 근태 표시 | `TimelineDisplayRelayJob`, `TimelineDisplayRelayProperties`, `TimelineOneDayDisplayStatusModel/Collection`, `TimelineDisplaySettingGroup`, `getIncludeWorkingTimeMap` native 4종 | `TimelineOneDayNotifier`, `TimelinePushMessageConverter`, `TimelineOneDayEventListener`(원저자 정동교, 2021), `TimelineHistoryWebServiceImpl`, `XmppSenderImpl` |
| 대화방 | `ChatBuddyMap`, `ChatMessageMap`, `ChatMessageHistoryMap`, `SliceModel`, `getDataForChatBuddyModel(WithPin)` | `ChatHistoryServiceImpl`, `ChatModelConverter` |
| notifier | `GoCustomInterceptor`(기존 `PresenceInterceptor` 이름 변경 + IQ 분기 추가) | 기존 presence 라우팅(원저자 곽면순, 2020~2021) |

---

### 1. 조직도 전체 트리 캐시  (2023-11 ~ 2024-02 · 대표 `6c365dac1f6`, `40ee97ec354`, `8e4f319344e`, `40b831f1361`, `e124eb465d4`, `8ce6ae02ee7` · `feature/트랜스_코스모스_조직도_캐시` → `bugfix/GO-44859_조직도_개선_release3600` → release/3.6.0.0 → develop)

**내가 한 범위**: 캐시 서비스·키 설계, 조회 API 구조 전환, evict 이벤트 설계(기존 8종 연결 + 6종 신설), 캐시 값 계산을 native 프로젝션으로 교체, ehcache 영역 추가, 기동 워밍업, 리스너 버그 수정까지 전부 본인 커밋이다. 기존에 있던 것은 `*Aware` + `ApplicationListener` 이벤트 체계(`DeptCreatedAware` 등 8종), `CacheConfig`(EhCacheCacheManager), Terracotta 연결 설정이다. 2025년 이후 `DeptCacheableServiceImpl` 수정 3건은 배현중(스패로우 null 검사)이다.

**코드 지도**

| 파일 | 클래스/메서드 | 역할 |
|---|---|---|
| `web/core/controller/api/DepartmentController.java:96-127` | `getDepartmentChildrenByRevisionInCompanyGroup`, `getTargetCompanyIds`, `getDepartmentRelation` | `/relation/accessible`(전체 트리, @Deprecated), `/relation/target`(바뀐 회사 ID), `/relation/entire`(회사 1개 트리) |
| `common/core/service/DeptWebServiceImpl.java:533-561, 994-1006` | `getAllDepartmentChildren`, `getRelationChangedCompanyIds`, `getEntireDeptChildren`, `validateAccessPermission` | 관계사 권한 확인 후 회사별 캐시 결과를 이어 붙임 |
| `common/core/service/DeptCacheableServiceImpl.java:37-145` | `getEntireDeptChildren`(@Cacheable), `on*` 14개, `evict(...)` 오버로드 | 캐시 경계. 값 계산 + 무효화를 한 클래스에 모음 |
| `common/core/service/DeptServiceImpl.java:952-972` | `getCompanyIdChangedDepartmentByRevision` | 회사별 `MAX(updated_at)` 과 rdate 비교 |
| `common/core/service/DeptServiceImpl.java:1567-1631` | `getDeptChildrenModel`, `getDeptAlterationMergeModel`, `getDeptMemberAlterationMergeModel` | native 2회 → groupingBy → 정렬 → `DeptChildrenModel` 목록 |
| `common/core/repository/DeptMemberRepository.java:30-40` | `getDeptMemberModelMap` | users ⨝ dept_members ⨝ user_profiles ⨝ domain_codes(직위·직책) 1회 |
| `common/core/repository/DepartmentRepository.java:53-54, 62-67` | `findMaxUpdatedAtGroupByCompanies`, `getDepartmentModelMapForDeptAlterationMergeModel` | 변경 회사 판별 JPQL, 부서 목록 native(로케일 이름 스칼라 서브쿼리) |
| `common/core/domain/model/DeptMemberModelMap.java` | `Object[]` 인덱스 getter | native 결과 행 → 모델 변환 |
| `common/core/event/listner/DeptMovedEventListener.java:18-36` 외 5종 | `onApplicationEvent` | 이벤트를 받아 `List<XxxAware>` 전부 호출 |
| `common/core/component/DeptCacheableInitializer.java:20-27` | `afterPropertiesSet` | 기동 시 전 회사 트리 미리 계산 |
| `common/core/component/OrgCacheInitializer.java:34-54` | `afterPropertiesSet` | `org.cache.init=true` 일 때 엔티티 findAll 로 2차 캐시 적재 |
| `go-common/src/main/resources/ehcache_user.xml:107-112` | `<cache name="jpa-2lc-org">` | 트리 캐시 영역 |

**흐름**

개선 전 (`6c365dac1f6^` 기준)
```
GET /departments/relation/accessible?companies=..&rdate=..&page=..
 → DeptWebServiceImpl.getAllDepartmentChildren(userId, companies, rdate, pageable)
     companies.map(companyService::getCompanyById) + relatedCompanies.contains 로 필터
 → DeptServiceImpl.getChildrenByCompaniesAndChangedAfter(targets, rdate, pageable)
     Specification: (부서 created/updated/deleted ≥ rdate)          ← 2023-06(904d25f5c95) 이전엔 부서원 LEFT JOIN 까지 OR 조건
 → Page<Department>.map(deptConverter::convertDeptToDeptChildren)  ← 엔티티 그래프(children, deptMembers→user→profile…) lazy 탐색
 → PageModel (count 쿼리 포함)
```
사용자마다 rdate 가 달라 결과를 공유할 수 없고, 변환이 엔티티를 따라가며 쿼리를 계속 낸다.

개선 후 (develop)
```
① GET /departments/relation/target?rdate=T
   DeptWebServiceImpl.getRelationChangedCompanyIds
    → userService.get(userId).getRelatedCompanies()
    → DeptServiceImpl.getCompanyIdChangedDepartmentByRevision
        → DepartmentRepository.findMaxUpdatedAtGroupByCompanies   (JPQL: MAX(updatedAt) GROUP BY company)
        → updatedAt.after(T) 인 회사 ID만 반환 (rdate 없으면 전부)
② GET /departments/relation/accessible?companies=1,2   (또는 /relation/entire?companyId=1)
   DeptWebServiceImpl.getAllDepartmentChildren   @Transactional(readOnly)
    → validateAccessPermission (요청 회사 ⊆ 관계사, 아니면 400)
    → for companyId: deptCacheableService.getEntireDeptChildren(companyId)     ← 프록시 경유
          ├ HIT : ehcache "jpa-2lc-org" 의 "DeptChildrenEntireModel$companyId:{id}" 반환
          └ MISS: DeptServiceImpl.getDeptChildrenModel(companyId)
                    ├ DeptMemberRepository.getDeptMemberModelMap(companyId)          native 1회
                    ├ DepartmentRepository.getDepartmentModelMapForDeptAlterationMergeModel(companyId, locale)  native 1회
                    ├ 부서원 groupingBy(departmentId), 부서 groupingBy(parentId)
                    └ 부서마다 DeptChildrenModel(직속 하위부서·부서원, sortOrder→id 정렬)
                  + deptService.getOrderConfig(companyId)
                  → DeptChildrenEntireModel.of(...) 저장
    → content 이어 붙여 PageModel(PageInfo(0, n, n))  ← rdate 파라미터는 받기만 하고 쓰지 않음
```
무효화 흐름
```
관리자 부서 이동: DeptServiceImpl.moveDept(...)  (DeptServiceImpl.java:1740-1767)
 → deptRepository.save / resetDeptSeq
 → orgSyncEventPublisher.publishOrgSyncEvent(companyId)          (기존)
 → eventPublisher.publishEvent(DeptMovedEvent.builder().department(d).build())   ← 40b831f1361 추가
     → DeptMovedEventListener.onApplicationEvent  (ApplicationListener = 동기, 같은 스레드·같은 트랜잭션 안)
         → for DeptMovedAware aware : DeptCacheableServiceImpl.onDeptMoved(d)
             → cacheManager.getCache("jpa-2lc-org").evict("DeptChildrenEntireModel$companyId:" + d.getCompanyId())
```

**핵심 코드**

```java
// common/core/service/DeptCacheableServiceImpl.java:25-45
@Service
@RequiredArgsConstructor
public class DeptCacheableServiceImpl implements DeptCacheableService,
        DeptMemberMovedAware, DeptMemberAddedAware, DeptMemberDeletedAware, DeptCreatedAware, DeptDeletedAware, DeptUpdatedAware, // 기존 이벤트 8종
        UserCreatedAware, UserDeletedAware, DeptTempDeletedAware, DeptOrderItemChangedAware, DeptMovedAware,                      // 뒤 3개부터 신설
        DeptMemberSeqMovedAware, DeptMemberSavedAware, UserPositionChangedAware {                                                 // 신설 6종 (40b831f1361)

    private static final String DEPT_CACHE_KEY = "DeptChildrenEntireModel$companyId:";   // evict 용 키 접두어 — @Cacheable SpEL 과 문자열이 반드시 같아야 함
    ...
    @Override
    @Transactional(readOnly = true)
    @Cacheable(value = CacheRegion.ENTITY_ORG,                                  // "jpa-2lc-org"
               key = "'DeptChildrenEntireModel$companyId:'.concat(#p0)")       // 회사당 엔트리 1건
    public DeptChildrenEntireModel getEntireDeptChildren(Long companyId) {
        List<DeptChildrenModel> deptChildrenModels = deptService.getDeptChildrenModel(companyId); // miss 때만 실행: native 2회 + 메모리 조립
        DeptOrderConfigModel orderConfig = deptService.getOrderConfig(companyId);                 // 부서원 자동정렬 설정도 같이 캐시
        return DeptChildrenEntireModel.of(deptChildrenModels, orderConfig);
    }
```

```java
// common/core/service/DeptCacheableServiceImpl.java:109-145  — 콜백은 "엔티티에서 companyId 만 꺼내 키 1개 삭제"
    @Override
    public void onDeptMoved(Department department) { evict(department); }

    @Override
    public void onDeptOrderItemChanged(Long companyId) { evict(companyId); }   // 정렬 기준 변경은 엔티티 없이 회사 ID 로

    private void evict(Department source) {
        Cache cache = getCache();
        cache.evict(DEPT_CACHE_KEY.concat(source.getCompanyId().toString()));
    }
    private void evict(DeptMember deptMember) { evict(deptMember.getDepartment()); } // 부서원 저장 → 소속 부서의 회사
    private Cache getCache() { return cacheManager.getCache(CacheRegion.ENTITY_ORG); }
```

```java
// common/core/service/DeptServiceImpl.java:1569-1585  — miss 시 트리 조립 (쿼리 2번 이후는 전부 메모리)
    public List<DeptChildrenModel> getDeptChildrenModel(Long companyId) {
        List<DeptChildrenModel> deptChildrenModelList = new ArrayList<>();
        // 부서원 전체를 한 번에 읽어 부서 ID 로 묶는다 (native 1회)
        Map<Long, List<DeptMemberAlterationMergeModel>> deptMemberGroupMap = getDeptMemberAlterationMergeModel(companyId).stream()
                .collect(Collectors.groupingBy(DeptMemberAlterationMergeModel::getDepartmentId));
        // 부서 전체를 한 번에 읽어 부모 ID 로 묶는다 (native 1회). 루트(parentId null)는 제외
        List<DeptAlterationMergeModel> departmentModeList = getDeptAlterationMergeModel(companyId);
        Map<Long, List<DeptAlterationMergeModel>> departmentGroupMap = departmentModeList.stream()
                .filter(dept -> dept.getParentId() != null)
                .collect(Collectors.groupingBy(DeptAlterationMergeModel::getParentId));
        departmentModeList.forEach(dept -> {
            // 각 부서: 직속 부서원(sortOrder→id), 직속 하위부서(sortOrder→id) 를 Map 에서 꺼내 붙인다
            ...
```

```java
// common/core/repository/DeptMemberRepository.java:30-40
    @Query(value = "SELECT gdm.id, gdm.sort_order, gdm.type, gdm.user_id, gdm.department_id, gdm.deleted_at," +
            " gup.position_id, gdcp.en_name AS positionEnName , ... gdcp.zhtw_name AS positionZhtwName," +   // 직위 다국어 6개
            " gdm.duty_id, gdcd.en_name AS dutyEnName, ... gdcd.zhtw_name AS dutyZhtwNam" +                  // 직책 다국어 6개
            " FROM go_users gu" +
            " JOIN go_dept_members gdm ON gdm.user_id = gu.id" +
            " JOIN go_user_profiles gup ON gu.user_profile_id = gup.id" +
            " LEFT JOIN go_domain_codes gdcp ON gup.position_id = gdcp.id" +
            " LEFT JOIN go_domain_codes gdcd ON gdm.duty_id = gdcd.id" +
            " WHERE gu.company_id = :companyId AND gdm.deleted_at IS NULL", nativeQuery = true)
    List<Object[]> getDeptMemberModelMap(@Param("companyId") Long companyId);   // 행 → DeptMemberModelMap(data[0]=id, [1]=sort_order ...)
```

```xml
<!-- daouoffice/go-common/src/main/resources/ehcache_user.xml:107-112 (ladmin/config/go/ehcache_user.xml:105-110 동일) -->
<!-- 회사수 Heap 갯수로 지정 -->
<cache name="jpa-2lc-org" maxElementsInMemory="100" eternal="false" timeToIdleSeconds="86400"
       timeToLiveSeconds="432000" overflowToDisk="false" maxElementsOnDisk="220" statistics="true">
    <terracotta consistency="eventual"/>   <!-- 원문은 열고 닫는 태그 -->
</cache>
```

DeptMovedEventListener 버그 (`8ce6ae02ee7`)
```java
// git show 40b831f1361:daouoffice/go-common/.../core/event/listner/DeptMovedEventListener.java  (수정 전)
    public void onApplicationEvent(DeptMovedEvent event) {
        Department department = event.getDepartment();
        if (!department.isDeleted()) {   // ← 삭제된 부서일 때만 통과. 일반 부서 이동은 여기서 return → evict 안 됨
            return;
        }
        for (DeptMovedAware aware : deptMoveAwares) aware.onDeptMoved(department);
    }
// 8ce6ae02ee7: 위 3줄 삭제.  같은 날 151a70fef8e: 같은 가드를 DeptTempDeletedEventListener(임시 삭제) 쪽에 추가.
// → 같은 날 만든 두 리스너 중 "임시 삭제" 리스너에 있어야 할 가드가 "이동" 리스너에 들어가 있었다.
```

**데이터·설정**

| 항목 | 값 | 근거 |
|---|---|---|
| 캐시 영역 | `jpa-2lc-org` (`CacheRegion.ENTITY_ORG`) | `common/core/CacheRegion.java:7` |
| 캐시 키 | `DeptChildrenEntireModel$companyId:{companyId}` | `@Cacheable` SpEL, `DEPT_CACHE_KEY` |
| 값 | `DeptChildrenEntireModel { List<DeptChildrenModel> dept; DeptOrderConfigModel orderConfig }` (BaseModel → Serializable) | Terracotta 저장을 위해 직렬화 가능해야 함 |
| 엔트리 상한 | 힙 100(회사 수 기준), Terracotta 측 `maxElementsOnDisk=220` | `fe9df4906f0`(2024-01-25)에서 220 추가 |
| 만료 | TTI 86400s(1일), TTL 432000s(5일) | `e124eb465d4` |
| 일관성 | Terracotta `consistency="eventual"`, 서버 `127.0.0.1:30310` | `CacheConfig` → `EhCacheCacheManager` |
| 인덱스 | `idx1_go_departments(company_id, updated_at)` (`MAX(updated_at)` 판별용) | `c7aed5f0a9a`, `ladmin/autopatch/db/10.5.15.0.sql` |
| 워밍업 | `DeptCacheableInitializer` 항상, `OrgCacheInitializer` 는 `org.cache.init`(기본 false) | `OrgCacheInitProperties` |
| 이벤트 코드 | `DEPT_MOVED`, `DEPT_ORDER_ITEM_CHANGED`, `DEPT_TEMPORARY_DELETED`, `DEPT_MEMBER_SAVED`, `DEPT_MEMBER_SEQ_MOVED`, `USER_POSITION_CHANGED` | `common/core/event/EventCode.java` (`40b831f1361`) |

이벤트 14종과 발행 지점 (신설 6종만, develop 기준)

| 이벤트 | 발행 위치 | evict 대상 |
|---|---|---|
| `DeptMemberSavedEvent` | `DeptMemberManagerImpl.saveDeptMember:117-120` | 부서원의 부서 → 회사 (같은 이벤트로 `MenuCacheEvictHelper` 도 메뉴 권한 캐시를 지움) |
| `DeptMemberSeqMovedEvent` | `DeptServiceImpl:858`, `:1949` | 부서 → 회사 |
| `DeptTempDeletedEvent` | `DeptServiceImpl:1697` | 부서 → 회사 |
| `DeptMovedEvent` | `DeptServiceImpl:1766` | 부서 → 회사 |
| `DeptOrderItemChangedEvent` | `DeptWebServiceImpl:1198` | companyId |
| `UserPositionChangedEvent` | `UserServiceImpl:518` | 사용자 → 회사 |

**왜 이렇게 짰나**

- 키를 회사 단위로 둔 이유: 메신저가 그리는 단위가 회사 전체 트리이고, 그 결과는 같은 회사 사용자 모두에게 같다. 사용자별 rdate 기준 변경분은 공유가 안 된다. 2023-08 `c7aed5f0a9a` 의 `/departments/children/changed` 주석에 이미 "변경사항이 있는가? → 전체 조직도 호출 / 없다면 로컬 스토리지 데이터 사용" 이라고 적혀 있다. "바뀌었는지 판별"과 "내용 전달"을 나누는 생각을 캐시로 완성한 것이다.
- `@Cacheable` 을 별도 빈(`DeptCacheableServiceImpl`)에 둔 이유: `DeptWebServiceImpl` 안에서 자기 메서드를 부르면 프록시를 거치지 않아 캐시가 안 걸린다. 다른 빈에서 주입받아 호출해야 한다. 이 빈이 evict 콜백까지 가지므로 키 문자열이 한 클래스 안에서만 쓰인다.
- evict를 `@CacheEvict` 가 아니라 `cacheManager.getCache().evict()` 로 직접 한 이유: 콜백(`onDeptMoved` 등)은 `List<XxxAware>` 를 통해 같은 빈의 메서드로 호출되는데, 어노테이션 키 SpEL 을 콜백마다 다르게(Department/User/DeptMember/Long) 써야 해서 직접 호출이 단순하다. `evictDeptChildrenEntireModel(Long)` 은 `@CacheEvict` 로도 만들어 두었다.
- 이벤트 방식을 쓴 이유: 처음(`8e4f319344e`, 2024-01-16)에는 무효화가 필요한 곳마다 `// starlight240116` 표시만 붙여 두고 기존 8종 Aware 만 연결했다. 사흘 뒤(`40b831f1361`) 표시 지점마다 직접 evict 를 넣는 대신 도메인 이벤트 6종을 새로 만들어 `publishEvent` 로 바꿨다. 조직 서비스가 캐시를 몰라도 되고, 같은 이벤트를 메뉴 권한 캐시(`MenuCacheEvictHelper implements DeptMemberSavedAware`)도 받는다.
- 값 계산을 native 로 바꾼 이유(`e124eb465d4`): 첫 버전(`40ee97ec354`)은 `deptService.getDepartmentsByCompany(companyId).stream().map(deptConverter::convertDepartmentWithChildren)` 로 엔티티를 따라갔다. 캐시 miss 한 번이 사용자 수만큼 연관 엔티티를 로딩한다. 필요한 컬럼만 조인해 2번에 읽고 메모리에서 트리를 만들었다.
- 버린 대안: (a) 부서 단위 캐시 — 부서 이동·정렬 변경이 여러 부서의 부모·형제 관계를 동시에 바꿔 지울 키를 정확히 고르기 어렵다. (b) 엔티티 2차 캐시만 강화(`b1aaff96df2`, 2023-10, `feature/트랜스_코스모스` 에만 있음) — 결과 트리 조립 비용은 그대로다. (c) fetch join — 컬렉션 여러 개(부서원·하위부서·다국어 additions)라 카테시안 곱/`MultipleBagFetchException` 문제가 있다.
- 트레이드오프: 조직 변경 1건에도 회사 전체 트리를 다시 계산한다. 리스너가 커밋 전에 evict 하므로 짧은 순간 옛 값이 다시 들어갈 수 있다(아래 "헷갈리기 쉬운 점"). 다중 노드에서는 eventual 이라 노드 간 반영 지연이 있다.

**바뀌어 온 이력**

| 커밋 | 날짜 | 브랜치 | 내용 |
|---|---|---|---|
| `86c1e3ce598`, `904d25f5c95`, `c7aed5f0a9a` | 2023-05~08 | `bugfix/GO-43787_조직도_API_성능_분석` | 변경분 API 다듬기(2번 항목) |
| `b1aaff96df2` | 2023-10-04 | `feature/트랜스_코스모스` 만 | 엔티티 2차 캐시 영역 분리 (develop 미반영) |
| `40ee97ec354` | 2023-11-07 | → develop | `DeptCacheableServiceImpl`, `jpa-2lc-org`, `/relation/entire`, `findMaxUpdatedAtGroupByCompanies` 신설 (엔티티 탐색 버전) |
| `6c365dac1f6` | 2023-11-13 | → develop | `getAllDepartmentChildren` 을 변경분+페이징 → 회사별 캐시 합치기로 전환 |
| `040bb7cd151`, `79d483791f1` | 2023-12-21/27 | `feature/트랜스_코스모스_조직도_캐시` | `DeptCacheableInitializer`, `OrgCacheInitializer` |
| `8e4f319344e` | 2024-01-16 | GO-44859 | 기존 Aware 8종 구현 + 수정 지점 표시 주석 |
| `40b831f1361`, `5a6d8b12f0a` | 2024-01-19 | GO-44859 | 이벤트 6종 신설, 표시 주석을 publishEvent 로 교체 |
| `e124eb465d4`, `da7e70c5728` | 2024-01-24 | GO-44859 | native 프로젝션 + 메모리 트리, ehcache 영역 정의 |
| `208de50b0de`, `81353f5d866`, `fe9df4906f0` | 2024-01-25 | GO-44859 | PR 리뷰 반영, 캐시 영역(`maxElementsOnDisk=220`) |
| `151a70fef8e`, `8ce6ae02ee7` | 2024-01-31 | GO-44859 | 리스너 가드 위치 수정 |
| `7227e946ae6`, `6897fe56c1d` | 2024-02-05 | release/3.6.0.0 | ladmin 설치형 ehcache 에 영역 추가 |

**면접 30초 설명**

"조직도 API가 사용자마다 '마지막 수신 시각 이후 바뀐 것'을 계산하는 구조라 출근 시간에 같은 회사 조직도를 사람 수만큼 다시 만들고 있었습니다. 저는 '바뀌었는지'와 '내용'을 분리했습니다. `/relation/target` 은 회사별 `MAX(updated_at)` 으로 바뀐 회사 ID만 돌려주고, 내용은 `DeptCacheableServiceImpl.getEntireDeptChildren` 에 `@Cacheable` 을 걸어 회사당 엔트리 하나로 캐시했습니다. miss 때는 `DeptServiceImpl.getDeptChildrenModel` 이 native 쿼리 두 번으로 부서와 부서원을 읽어 메모리에서 트리를 만듭니다. 무효화는 기존 `*Aware` 이벤트 8종에 부서 이동·순서 변경 같은 이벤트 6종을 새로 만들어 붙였고, 콜백은 회사 키 하나만 지웁니다. TTL 5일·TTI 1일은 누락 대비 안전망이고, 기동할 때 `DeptCacheableInitializer` 가 전 회사를 미리 채웁니다."

**헷갈리기 쉬운 점**

- **evict 시점은 커밋 전이다.** `Dept*EventListener` 는 `ApplicationListener`(동기)라 `publishEvent` 를 부른 서비스 트랜잭션 안에서 evict 된다. 커밋 전 틈에 다른 요청이 miss → 옛 데이터를 읽어 다시 넣을 수 있다. 같은 코드베이스의 `CompanyCreateEventListener` 는 `@TransactionalEventListener` 를 쓴다. 개선안은 AFTER_COMMIT evict.
- **`@Cacheable(sync = true)` 없음.** evict 직후 동시 miss 는 모두 DB 를 탄다. 비용을 native 2회로 줄여 둔 것이 완화책이다.
- **`/relation/accessible` 은 rdate·page 를 무시한다.** 이름과 달리 항상 전체 트리다. `@Deprecated` 표시가 붙어 있고 신규 클라이언트는 `/relation/entire` 를 쓴다(클라이언트 실제 호출 순서는 저장소로 확인 안 됨).
- **`jpa-2lc-org` 는 이름과 달리 develop 에서는 Hibernate 2차 캐시가 아니라 Spring Cache(트리) 전용이다.** 엔티티 2차 캐시를 이 영역으로 옮긴 `b1aaff96df2` 는 고객사 브랜치에만 있다.
- **`DeptCacheableInitializer.afterPropertiesSet` 의 `@Transactional` 은 효과 없음**(초기화 콜백은 프록시 밖). 그래도 내부에서 주입받은 프록시 `deptCacheableService` 를 부르므로 `@Cacheable`·`@Transactional(readOnly)` 는 그쪽에서 정상 적용된다. `OrgCacheInitializer` 는 직접 `findAll` 하므로 트랜잭션 없이 실행된다(lazy 로딩이 되는지는 OSIV/세션 설정에 따라 다름 — 확인 필요).
- **`findMaxUpdatedAtGroupByCompanies` 는 `GROUP BY ... HAVING d.company IN (...)`** 이라 전 회사를 집계 후 거른다. `WHERE` 가 맞다.
- **`onDeptMemberMoved(user, oldDept, newDept)` 는 newDept 회사만 지운다.** 겸직·관계사 간 이동처럼 회사가 다르면 oldDept 회사 캐시가 남는다(관계사 간 부서원 이동이 가능한지는 확인 필요).
- **수정 표시 주석**: `8e4f319344e` 의 `// starlight240116` 은 "evict 필요 지점" 표시였고 `40b831f1361` 에서 전부 지워졌다. 면접에서 "이벤트 누락 지점을 어떻게 찾았냐"는 질문에 쓸 수 있는 실제 근거다.

---

### 2. 근태 표시 성능 개선  (2024-04 ~ 07 · 대표 `f143c382d99`, `a3482ae478a`, `f81be9162a9`, `95616fd95a9`, `b1628d8f484`, `13580e920cc` · `bugfix/GO-45171_프로필_표시_release3_6_2_5` 등 → develop)

**내가 한 범위**: Notifier·Converter·EventListener 의 트랜잭션/로딩 변경, `/display` 응답 API, relay 잡·프로퍼티, timeline 푸시 failover 생략, 겸직 처리, pg9 쿼리 오류 수정까지 본인. `TimelineOneDayNotifier`·`TimelinePushMessageConverter`·`TimelineOneDayEventListener` 원 구조는 정동교(2021-10, "조직도-근태 상태 실시간 표시"). openfire 쪽 근태 presence 처리는 곽면순(2021).

> 같은 내용이 해시 두 개로 develop 에 들어간 경우가 있다(예: `f143c382d99` ↔ `6fed5a2127b`, 브랜치별 cherry-pick). 파일 log 에는 뒤쪽 해시가 보일 수 있다.

**코드 지도**

| 파일 | 클래스/메서드 | 역할 |
|---|---|---|
| `common/ehr/timeline/service/web/TimelineHistoryWebServiceImpl.java:170-172` | `create` | 출퇴근 이력 저장 후 relay 꺼져 있을 때만 즉시 이벤트 |
| `common/ehr/timeline/event/TimelineOneDayEventListener.java` | `handleEvent` (@Async @TransactionalEventListener) | 커밋 후 비동기로 Aware 호출 |
| `common/ehr/timeline/component/TimelineOneDayNotifier.java:31-67` | `onUpdatedTimelineOneDayRelay`, `onUpdatedTimelineOneDay` | 요청 모델(RELAY/UPDATE/READ) 만들어 PushManager 로 |
| `common/ehr/timeline/component/TimelinePushManager.java` | `convertAndSend` | Converter 호출 → 큐(`sendQByList`) |
| `common/ehr/timeline/converter/TimelinePushMessageConverter.java:66-87, 131-172` | `createEveryoneMessageToEveryone`, `createMessageToEveryone`, `createMessageToMe` | 수신자·본문 결정 |
| `common/ehr/timeline/service/core/TimelineDisplaySettingServiceImpl.java:47-150` | `getTimelineDisplayTarget`, `getTimelineDisplayStatusTarget` | 공개 그룹별 수신자 ID 를 집합 연산으로 계산 |
| `common/ehr/timeline/service/core/TimelineOneDayServiceImpl.java:317-348` | `getEmployeesDisplayStatus`, `getDisplayStatus(companyId, before, now)`, `getDisplayVacation` | native 결과 → `TimelineOneDayDisplayStatusModel` |
| `common/ehr/timeline/repository/TimelineOneDayRepository.java:60-92` | `getIncludeWorkingTimeMap` 4종 | 사용자별 최신 상태 1건(row_number) |
| `common/ehr/timeline/job/TimelineDisplayRelayJob.java:20-40` | `executeInternal` | 1분 구간 계산 |
| `common/ehr/timeline/component/TimelineBatchManager.java:108-120` | `timelineOneDayRelayPublishTimelineEvent` | 근태·표시옵션 켜진 회사마다 relay 호출 |
| `common/config/application/QuartzAdminSerialTriggerConfig.java:123-138` | `timelineDisplayRelayJobTrigger` | cron `0 0/1 * * * ?` |
| `common/common/properties/TimelineDisplayRelayProperties.java:14` | `timeline.display.relay` (기본 false) | 대형 고객사 전용 스위치 |
| `web/ehr/timeline/controller/api/TimelineUserController.java:218-221` | `GET /ehr/timeline/display` | 화면 진입 시 회사 전체 상태 응답 |
| `common/core/component/XmppSenderImpl.java:~305` | `sendXmppMessage` | `type=timeline` 이면 APNs/FCM 후처리 생략 |

**흐름**

개선 전 (`f143c382d99^`)
```
출근 버튼 → TimelineHistoryWebServiceImpl.create → (커밋)
 → TimelineOneDayEventListener.handleEvent  @Async @TransactionalEventListener
     executeWithTransaction(TransactionTemplate REQUIRES_NEW, 읽기/쓰기)
 → TimelineOneDayNotifier.onUpdatedTimelineOneDay  @Transactional (쓰기)
     em.flush()
     userService.getOnlineAndDormantListByCompany(company)        ← 전 사원 User 엔티티 로딩 (수신자 존재 확인용일 뿐)
 → TimelinePushManager.convertAndSend → TimelinePushMessageConverter.createMessageToEveryone(userId)
     colleagues = getOnlineAndDormantListByCompany(company)        ← 또 전 사원 엔티티
     findOrCreateOneDay(from, today)                               ← 쓰기 가능 메서드
     colleagues.groupingBy(getTimelineGroupFunction)               ← 사원마다 isAllowedToCheckStatus/Vacation → Circle.isMember(user)
     그룹(최대 3개)마다 PushMessage 1건, 수신자 = 그룹 전원
 → 큐 → XmppSenderImpl → notifier REST → 모바일이면 APNs/FCM failover 까지
 커밋 시: 쓰기 트랜잭션이라 영속성 컨텍스트의 수천 개 엔티티 dirty checking
```
출근 1건마다 위 전체가 돈다. 화면 진입(READ)도 `createMessageToMe` 가 전 사원 엔티티 + `getTimelineOneDays(userIds)` IN 조회 + `TimelineOneDayModel` 전체 변환 후 XMPP 로 보냈다.

개선 후 (develop, `timeline.display.relay=true`)
```
출근 버튼 → TimelineHistoryWebServiceImpl.create
   if (!relay.isEnabled()) publisher.onUpdatedTimelineOneDay(userId)   ← relay 모드면 즉시 발송 안 함

화면 진입 → GET /ehr/timeline/display
 → TimelineUserWebServiceImpl.getIntegratedEmployeesDisplay(userId)    (겸직이면 회사별로 반복)
     getEmployeesDisplay(user): 권한(status/vacation) 확인
       userService.getRepUserIdsOnlineAndDormantByCompany(companyId)   ← 엔티티가 아니라 ID 목록
       timelineOneDayService.getEmployeesDisplayStatus → native row_number() 사용자별 최신 상태 1건
       timelineOneDayService.getDisplayVacation         → native 오늘 휴가자 user_id
       TimelineOneDayDisplayStatusCollection.of(group, status, vacation) → 응답 본문

매 1분 → Quartz(클러스터드 JobStore) TimelineDisplayRelayJob.executeInternal
   relay 꺼져 있으면 return
   before = fireTime 초 0 - 1분, now = fireTime 초 0
 → TimelineBatchManager.timelineOneDayRelayPublishTimelineEvent(before, now)
     companyService.findAllCompanyIds() → filter(근태 사용) → filter(표시 옵션 사용)
     → TimelineOneDayNotifier.onUpdatedTimelineOneDayRelay(companyId, before, now)   @Async @Transactional(readOnly, REQUIRES_NEW)
 → TimelinePushMessageConverter.createEveryoneMessageToEveryone
     수신자 = getTimelineDisplayStatusTarget(company)  (전체 공개면 대표ID 목록, 아니면 Circle 멤버 ID)
     본문   = getDisplayStatus(companyId, before, now) (직전 1분간 바뀐 사람들의 최신 상태)
     PushMessage 1건 (발신자 = 기본 시스템 관리자)
 → 큐 → XmppSenderImpl (type=timeline 이면 APNs/FCM 후처리 없이 return)
```

**핵심 코드**

```java
// git show f143c382d99^:daouoffice/go-common/.../ehr/timeline/component/TimelineOneDayNotifier.java:33-52  (개선 전)
    @Override
    @Transactional                                   // 쓰기 트랜잭션 → 커밋 때 flush + dirty checking
    public void onUpdatedTimelineOneDay(Long userId) {
        if (!isValid(userId)) return;
        em.flush();                                  // 의미 없는 강제 flush
        User user = userService.getById(userId);
        Company company = user.getCompany();
        List<User> users = userService.getOnlineAndDormantListByCompany(company);  // 전 사원 엔티티를 "비어 있나" 확인용으로 로딩
        if (CollectionUtil.isEmtpy(users)) { ...; return; }
        timelinePushManager.convertAndSend(TimelineRequestModel.builder().userId(userId).requestType(UPDATE).build());
    }
```

```java
// common/ehr/timeline/component/TimelineOneDayNotifier.java:31-67  (개선 후)
    @Override
    @Async
    @Transactional(readOnly = true, propagation = Propagation.REQUIRES_NEW)   // 회사마다 독립 읽기 전용 트랜잭션
    public void onUpdatedTimelineOneDayRelay(Long companyId, DateTime before, DateTime now) {
        ...
        TimelineRequestModel timelineRequestModel = TimelineRequestModel.builder()
                .requestType(TimelineRequestModel.RequestType.RELAY)          // 신규 타입: 회사 단위 1분 묶음
                .companyId(companyId).now(now).before(before).build();
        timelinePushManager.convertAndSend(timelineRequestModel);
    }

    @Override
    @Async
    @Transactional(readOnly = true, propagation = Propagation.REQUIRES_NEW)
    public void onUpdatedTimelineOneDay(Long userId) {
        if (!isValid(userId)) return;
        User user = userService.getById(userId);
        Company company = user.getCompany();
        int usedCount = company.getUsedCount();         // 전 사원 로딩 대신 회사 엔티티의 사용자 수 컬럼
        if (usedCount < 1) { ...; return; }
        ...
    }
```

```java
// common/ehr/timeline/converter/TimelinePushMessageConverter.java:66-87
    private List<PushMessage> createEveryoneMessageToEveryone(Long companyId, DateTime before, DateTime now) {
        List<PushMessage> result = new ArrayList<>();
        Company company = companyService.getCompany(companyId);
        ...
        List<Long> timelineDisplayStatusTarget = timelineDisplaySettingService.getTimelineDisplayStatusTarget(company); // 수신자 ID
        List<TimelineOneDayDisplayStatusModel> displayStatus = timelineOneDayService.getDisplayStatus(company.getId(), before, now); // 직전 1분 변경분
        if (CollectionUtil.isEmtpy(timelineDisplayStatusTarget) || displayStatus.isEmpty()) {
            return result;                                // 변경이 없으면 아무것도 안 보냄
        }
        User defaultSystemAdmin = userService.getDefaultSystemAdmin();   // 발신자를 시스템 관리자로
        TimelineOneDayDisplayStatusCollection collection = TimelineOneDayDisplayStatusCollection.of(displayStatus);
        PushMessage pushMessage = createPushMessage(defaultSystemAdmin, timelineDisplayStatusTarget, collection); // 메시지 1건, 수신자 N명
        ...
    }
```

```java
// common/ehr/timeline/repository/TimelineOneDayRepository.java:86-92  (relay 용, 13580e920cc 이후)
    @Query(value = "SELECT sub.include_working_time, sub.user_id FROM" +
            " ( SELECT gts.include_working_time, gtod.user_id," +
            "   row_number() over (partition BY gtod.user_id ORDER BY gth.created_at DESC) rn" +   // 사용자별 최신 이력 1건
            "   FROM go_timeline_one_days gtod" +
            "   JOIN go_timeline_history gth ON gtod.id = gth.timeline_one_day_id" +
            "   JOIN go_timeline_status gts ON gts.id = gth.timeline_status_id" +                   // 상태가 근무시간 포함인지(출근/외근 등)
            "   WHERE gtod.working_day = :workingDay AND gtod.company_id = :companyId" +
            "   AND gth.created_at >= TO_DATE(:before, 'YYYY-MM-DD hh24:mi:ss') AND gth.created_at < TO_DATE(:now, 'YYYY-MM-DD hh24:mi:ss')) sub" +
            " WHERE rn = 1", nativeQuery = true)
    List<Object[]> getIncludeWorkingTimeMap(Long companyId, String workingDay, String before, String now);
```

```java
// common/ehr/timeline/job/TimelineDisplayRelayJob.java:30-38
        TimelineDisplayRelayProperties props = applicationContext.getBean(TimelineDisplayRelayProperties.class);
        if (!props.isEnabled()) { ...; return; }          // 잡은 항상 등록, 실행 여부는 프로퍼티로
        TimelineBatchManager timelineBatchManager = applicationContext.getBean(TimelineBatchManager.class);
        Date fireTime = context.getFireTime();
        timelineBatchManager.timelineOneDayRelayPublishTimelineEvent(
                new DateTime(fireTime).withSecondOfMinute(0).minusMinutes(1),   // [09:00:00,
                new DateTime(fireTime).withSecondOfMinute(0));                  //  09:01:00)
```

**데이터·설정**

- 프로퍼티: `timeline.display.relay` (기본 `false`, 주석 "단독/설치형 전용 옵션, 대형 고객사 대상").
- Quartz: `QuartzAdminSerialTriggerConfig#timelineDisplayRelayJobTrigger`, cron `0 0/1 * * * ?`, `JobDetail` durable. 이전 조사 기준 admin serial 스케줄러는 클러스터드 JDBC JobStore·threadCount 1.
- 테이블: `go_timeline_one_days`(사용자·근무일), `go_timeline_history`(이력, `created_at`), `go_timeline_status`(`include_working_time`), `go_timeline_approvals`(휴가: `timeline_approval_type='VACATION'`).
- 메시지 타입: `PushMessage.type = "timeline"` → `XmppSenderImpl` 에서 모바일 failover 생략(`95616fd95a9`).

**왜 이렇게 짰나**

- 원인 세 가지를 코드에서 분리했다: (1) 이벤트 처리 트랜잭션이 쓰기 + `em.flush()` → dirty checking, (2) "수신자가 있나" 확인과 그룹 판정을 위해 전 사원 엔티티 로딩 + 사원마다 `Circle.isMember`, (3) 출근 1건마다 회사 전원 발송. (1)(2)는 `f143c382d99` 로 readOnly·`getUsedCount()`·ID 목록 집합 연산(`getTimelineDisplayTarget` 의 `retainAll/removeAll`)으로, (3)은 `a3482ae478a`(pull) + `f81be9162a9`(1분 묶음)로 풀었다.
- pull + 주기 push 조합: 화면을 처음 열 때는 전체 상태가 필요하므로 API 응답(pull)으로 주고, 그 뒤 변화만 1분마다 묶어 보낸다. 발송 수가 "출근 이벤트 수"가 아니라 "회사 수 × 분"에 묶인다.
- 프로퍼티로 감싼 이유: 1분 지연은 소규모 고객에게는 기능 후퇴다. 기본값 false 로 기존 즉시 발송을 유지했다.
- failover 생략: 근태 표시는 화면이 떠 있을 때만 의미가 있어 모바일 푸시로 대체 전달할 필요가 없다고 판단(커밋 메시지에는 이유 없음 — 본인 설명으로 보충).
- 버린 대안: 비동기 실행기 스레드 증설(엑셀 기록상 시도 후 원복, 저장소로는 확인 안 됨), 근태 상태 캐시(`feff2d34efe` 에서 `TimelineOneDayCacheableServiceImpl` 을 만들었으나 `feature/GO-44222_근태_동기화_개선` 브랜치에만 있고 develop 에는 없음).
- 트레이드오프: 최대 약 1분 지연, 잡 누락 시 해당 1분은 다음 화면 진입 때 `/display` 로만 맞춰짐.

**바뀌어 온 이력**

| 커밋 | 날짜 | 내용 |
|---|---|---|
| `3cded0178d4`, `14b143c1f03`, `feff2d34efe` | 2023-08~12 | GO-44222 브랜치(미반영): 대화방 멤버 변환에서 표시설정 조회를 루프 밖으로, 근태 캐시 시도 |
| `f143c382d99` | 2024-04-18 | `em.flush`·전 사원 로딩 제거, readOnly/@Async, `TimelineOneDayDisplayStatusModel`, `getTimelineDisplayTarget` |
| `d1a212cfa5f` | 2024-04-22 | `getTimelineDisplaySetting(companyId)` → `(company)` 로 재조회 제거, `TimelineStatusEntityConverter` 를 매번 `new` 대신 빈 사용(`/info` 응답 모델 포함) |
| `a3482ae478a` | 2024-04-22 | `/display` 응답 API, 겸직 대표 ID |
| `95616fd95a9` | 2024-04-24 | timeline 푸시 failover 생략 |
| `f81be9162a9` | 2024-04-26 | relay 잡·프로퍼티·즉시 발송 차단, RELAY 타입 |
| `b1628d8f484` | 2024-05-03 | Converter 에서 옛 그룹 로직 65줄 제거 |
| `9f3d92586e1`, `dc9f2837122`, `dc173c01542` | 2024-05~06 | 겸직 근태 표시 |
| `bd9c0c78972`, `db6419cc2c2` | 2024-06-12 | PostgreSQL 9 에서 문자열 비교 오류 → `TO_DATE(..., 'YYYY-MM-DD')` |
| `13580e920cc` | 2024-07-08 | relay 쿼리 포맷을 `'YYYY-MM-DD hh24:mi:ss'` 로 (GO-45487) |

**면접 30초 설명**

"근태 표시를 켠 고객사에서 출근 피크에 서버가 버티지 못했습니다. 코드를 보니 출근 한 건마다 `TimelineOneDayNotifier` 가 쓰기 트랜잭션에서 `em.flush()` 를 하고 전 사원 엔티티를 읽었고, `TimelinePushMessageConverter` 가 사원마다 공개 범위를 판정해 회사 전원에게 XMPP를 보냈습니다. 먼저 readOnly 로 바꾸고 전 사원 로딩을 `company.getUsedCount()` 와 ID 목록 집합 연산으로 대체했습니다. 그다음 구조를 바꿨습니다. 화면을 열 때는 `/ehr/timeline/display` 가 native `row_number()` 로 사용자별 최신 상태를 응답하고, 이후 변경은 `TimelineDisplayRelayJob` 이 1분마다 회사별로 '직전 1분간 바뀐 사람들'을 메시지 한 건으로 묶어 보냅니다. 1분 지연이 생기므로 `timeline.display.relay` 옵션으로 대형 고객사만 켜게 했습니다."

**헷갈리기 쉬운 점**

- **XMPP 를 없앤 게 아니다.** relay 도 XMPP 로 보낸다. "출근 건별 전원 발송 → 회사별 1분 묶음 발송"이 정확하다. relay 를 켜지 않은 고객사는 지금도 즉시 발송(`createMessageToEveryone`)이다. 즉시 발송 경로도 엔티티 로딩·그룹 판정은 가벼워졌다.
- **relay 쿼리의 `TO_DATE` (확인 필요, 면접 전 반드시 확인).** `db6419cc2c2`(06-12)에서 `TO_DATE(:before, 'YYYY-MM-DD')` 로 바꿔 시각이 잘려 `[당일 0시, 당일 0시)` 빈 구간이 되었고, `13580e920cc`(07-08)에서 포맷에 `hh24:mi:ss` 를 넣었다. 그런데 PostgreSQL 표준 `to_date` 는 반환형이 `date` 라 포맷에 시각을 넣어도 시각이 버려진다(Oracle `TO_DATE` 는 시각 유지). 저장소의 pg 스키마에 사용자 정의 `to_date` 함수는 찾지 못했다. 운영 PG 에서 `SELECT to_date('2024-07-08 09:01:00','YYYY-MM-DD hh24:mi:ss')` 결과를 확인할 것. 시각이 버려진다면 PG 환경의 relay 는 빈 결과가 되고 `to_timestamp` 가 맞다.
- **경계 누락.** 구간이 `[before, now)` 이고 기준이 `created_at`(앱이 넣은 시각)이다. 커밋이 다음 분으로 넘어간 기록은 두 구간 모두에서 빠질 수 있다.
- **`isValid` 안의 `userService.get(userId)` 로 사용자 1건, `company.getUsedCount()` 는 이미 로딩된 Company 의 컬럼**이라 추가 쿼리가 없다.
- **`@Async` + `@Transactional(REQUIRES_NEW)`** 를 같은 메서드에 둬서 호출 스레드(Quartz 1스레드)와 트랜잭션을 끊었다. 회사 수만큼 비동기 작업이 쌓이므로 실행기 큐 크기는 따로 봐야 한다(설정값 확인 필요).
- **`TimelineOneDayEventListener`** 는 `@TransactionalEventListener`(기본 AFTER_COMMIT) + `@Async` 라 원래 커밋 후 실행이었다. 문제는 그 안에서 다시 연 쓰기 트랜잭션이었다.

---

### 3. 대화방 목록 N+1 → native 프로젝션 + Slice  (2023-11 ~ 2024-01 · 대표 `f5726b33cde`/`9cc7b3a9711`(Slice), `df630cc5d66`, `5204ec10c66`, `2c4f2d51ae3`, `6cbac4b83e6`, `869e8404f7f` · `bugfix/GO-44731_채팅_대화방_쿼리_개선`, `bugfix/GO-44850_채팅방_쿼리_release3_5_21_1` → develop)

**내가 한 범위**: `ChatBuddyMap`, `getDataForChatBuddyModel(WithPin)`, `ChatModelConverter#convertToModel(ChatBuddyMap, me)` 와 하위 `create*ByMap`, `SliceModel` 전부 본인. 2024-10 `08fb08671d1`(yeonjungbae)이 Oracle 호환을 위해 `true/false → 1/0`, `-- #pageable` → `/*#pageable*/` 로 바꿨다(아래 발췌는 그 이후 모양).

**코드 지도**

| 파일 | 클래스/메서드 | 역할 |
|---|---|---|
| `web/chat/controller/api/ChatHistoryController.java:72-86` | `getNewChatBuddies` `GET /chat/new/buddies` | 신규 메신저 대화방 목록 |
| `common/chat/service/ChatHistoryServiceImpl.java:101-151` | `getChatBuddiesWithPin`, `getNotUsePinChatBuddiesCheckUserIntegrated`, `getUsePinBuddiesCheckUserIntegrated` | 첫 페이지면 상단고정 목록 + 일반 목록(Slice) 합치기 |
| `common/chat/repository/ChatBuddyRepository.java:139-166` | `getDataForChatBuddyModel`, `getDataForChatBuddyModelWithPin` | native 1회 |
| `common/chat/domain/model/ChatBuddyMap.java` | `getBuddyId()`=data[0] ... | 행 래퍼 |
| `common/chat/domain/model/converter/ChatModelConverter.java:624-651, 845-1036` | `convertToModel(ChatBuddyMap, Long)`, `createRoomModelByMap`, `createSingleOrMyModelByMap`, `createPeerModelByMap` | 모델 조립 |
| `common/core/domain/model/SliceModel.java` | `SliceModel(content, Slice)`, `prepend` | count 없는 페이지 응답, 기존 `PageInfo` 호환 |

**흐름**

개선 전 (`df630cc5d66^`)
```
GET /chat/new/buddies?page=0&offset=10
 → ChatHistoryServiceImpl.getChatBuddiesWithPin
     getUsePinBuddiesCheckUserIntegrated  → List<ChatBuddyInfo> (엔티티 프로젝션)
     getNotUsePinChatBuddiesCheckUserIntegrated → Slice<ChatBuddyInfo>
 → CollectionUtil.transform(result, modelConverter.transformChatBuddy(me))   행마다:
     chatMessageRepository.findOne(lastMessageId)                      쿼리 1
     getPushSetting(me, ROOM|BUDDY, id) → userPushBlackBoxService      쿼리 1
     chatMessageHistoryRepository.countByChatBuddyAndConfirmFalse      쿼리 1 (안 읽은 수)
     input.getChatRoom()/getBuddy()/getUser()/chatRoom.getMemberExceptUser/getChatRoomNotice   lazy 로딩 여러 번
```
개선 후 (develop)
```
 → getNotUsePinChatBuddiesCheckUserIntegrated(user, PageRequest(page, offset))
     userIds = 겸직이면 integratedUserIds, 아니면 [userId]
     ChatBuddyRepository.getDataForChatBuddyModel(userIds, pageable)   native 1회 (Slice: limit offset+1 로 hasNext 판정, count 없음)
        buddy ⨝ room ⨝ users(company_id) ⨝ 마지막 메시지 + 스칼라 서브쿼리 2개(알림 차단 수, 안 읽은 수)
     .map(ChatBuddyMap::new).map(map -> modelConverter.convertToModel(map, me))
 → SliceModel.prepend(상단고정 목록)   (첫 페이지만)
```

**핵심 코드**

```java
// common/chat/repository/ChatBuddyRepository.java:139-152
    @Query(value = "SELECT t.*, gcm.created_at as gcmCreatedAt, gcm.message as gcmMessage, gcm.message_type as gcmMessageType, gcm.from_user_id as gcmFromUserId," +
            // 알림 차단 여부: 단체/1:1 방이면 사용자의 push black box 에 이 방이 있는지 count (pubsub 이면 0)
            " CASE WHEN bChatPubsubId IS NULL THEN (select count(*) from go_user_push_black_boxes gp JOIN go_users gu ON gp.user_push_setting_id = gu.user_push_setting_id" +
            "   where gu.id = buserid AND gp.noti_category = 'ROOM' AND gp.push_filter_type = 'CHAT' AND gp.link_url = cast(bchatroomid as varchar(100)))" +
            " ELSE 0 END AS blackBoxCount," +
            // 안 읽은 메시지 수: 행마다 history 를 count
            " (SELECT count(*) FROM go_chat_message_histories gcmh WHERE gcmh.chat_buddy_id = bId AND gcmh.confirm = 0) as unreadCount FROM" +
            " (SELECT b.id as bId, b.join_room as bJoinRoom, b.chat_room_id as bChatRoomId, b.chat_pubsub_id as bChatPubsubId, b.chat_room_name as bChatRoomName, b.user_id as bUserId," +
            " u.company_id as bCompanyId, b.use_pin as bUsePin, b.buddy_id as bBuddyId, r.room_type as rRoomType, r.member_count as rMemberCount, r.chat_room_notice_id as rChatRoomNoticeId, r.creator_id as rCreatorId," +
            // 참여 중인 방이면 방의 최신 메시지, 나간 방이면 내가 본 마지막 메시지
            " CASE b.join_room WHEN 1 THEN COALESCE(r.chat_message_id, b.chat_message_id) ELSE b.chat_message_id END AS id" +
            " FROM go_chat_buddies b" +
            " LEFT OUTER JOIN go_chat_rooms r ON b.chat_room_id = r.id" +
            " JOIN go_users u ON b.user_id = u.id" +
            " WHERE b.user_id in (:userIds) AND b.use_pin = 0 " +
            " AND (CASE b.join_room WHEN 1 THEN COALESCE(r.chat_message_id, b.chat_message_id) ELSE b.chat_message_id END) IS NOT NULL) t" +
            " JOIN go_chat_messages gcm ON t.id = gcm.id ORDER BY t.id DESC /*#pageable*/ ", nativeQuery = true)
    Slice<Object[]> getDataForChatBuddyModel(@Param("userIds") List<Long> userIds, Pageable pageable);
```

```java
// common/chat/service/ChatHistoryServiceImpl.java:118-129
    @Override
    @Transactional(readOnly = true)
    public SliceModel<ChatBuddyModel> getNotUsePinChatBuddiesCheckUserIntegrated(User user, Pageable pageRequest) {
        List<Long> userIds = user.isIntegrated() ? user.getIntegratedUserIds() : Lists.newArrayList(user.getId()); // 겸직 계정 묶음
        Slice<Object[]> result = chatBuddyRepository.getDataForChatBuddyModel(userIds, pageRequest);              // native 1회
        List<ChatBuddyModel> transform = result.getContent().stream()
                .map(ChatBuddyMap::new)                                       // Object[] → 인덱스 getter 래퍼
                .map(map -> modelConverter.convertToModel(map, user.getId())) // 메모리 조립
                .collect(Collectors.toList());
        return new SliceModel<>(transform, result);                           // hasNext + 기존 PageInfo 형태 유지
    }
```

```java
// common/chat/domain/model/converter/ChatModelConverter.java:624-651
    public ChatBuddyModel convertToModel(ChatBuddyMap map, Long me) {
        ChatBuddyModel chatBuddyModel;
        boolean isUsePush;
        if (map.inGroupChat()) {          chatBuddyModel = createGroupModelByMap(map);  isUsePush = map.getUsePush(); } // blackBoxCount == 0
        else if (map.inPubSubChat()) {    chatBuddyModel = createPubSubModelByMap(map); isUsePush = true; }
        else {                            chatBuddyModel = createPeerModelByMap(map);   isUsePush = map.getUsePush(); }
        chatBuddyModel.setUsePush(isUsePush);
        chatBuddyModel.setUnreadMessageCount(map.getUnreadCount());   // 예전 countByChatBuddyAndConfirmFalse 대체
        if (Objects.nonNull(map.getMessageId())) {                    // 예전 chatMessageRepository.findOne 대체
            chatBuddyModel.setCreatedAt(map.getMessageCreatedAt());
            chatBuddyModel.setMessage(map.getMessageContent());
            ...
        }
        chatBuddyModel.setUsePin(map.getUsePin());
        return chatBuddyModel;
    }
```

**데이터·설정**

- 테이블: `go_chat_buddies`(사용자별 대화 상대/방 항목, `use_pin`, `join_room`, `chat_message_id`), `go_chat_rooms`(`room_type`, `member_count`, `chat_message_id`, `chat_room_notice_id`), `go_chat_messages`, `go_chat_message_histories`(`chat_buddy_id`, `confirm`), `go_user_push_black_boxes`.
- 페이징: `PageRequest(page, offset)` + `Slice`. Spring Data JPA 1.11 native 쿼리 페이징은 쿼리에 `#pageable` 주석 자리표시자를 둔다.
- 인덱스: `go_chat_message_histories(chat_buddy_id, ...)` 존재 여부는 확인 필요.

**왜 이렇게 짰나**

- 목록 1행에 필요한 값(마지막 메시지, 안 읽은 수, 알림 여부, 방 정보)이 서로 다른 테이블에 있어 엔티티 변환 중 행마다 쿼리가 났다. 한 쿼리에서 조인·스칼라 서브쿼리로 붙이면 DB 왕복이 페이지당 1회가 된다.
- Page → Slice(`f5726b33cde`, `9cc7b3a9711`): 메신저는 무한 스크롤이라 총 개수가 필요 없고, 큰 테이블의 `count(*)` 가 따로 비쌌다. 기존 앱이 `pageInfo` 를 읽으므로 `SliceModel` 이 `PageInfo` 를 계속 내려준다(클래스 주석에 이유 명시).
- `6cbac4b83e6`: `go_chat_buddies.unread_message_count`(비정규화 컬럼) 대신 history count 서브쿼리를 쓰고 알림 차단 서브쿼리를 추가했다. 왜 컬럼을 버렸는지는 커밋 메시지에 없다(컬럼 값이 정확하지 않았을 가능성 — 본인 기억으로 확인 필요).
- `869e8404f7f`: `b.company_id` → `u.company_id` (buddy 행이 아니라 사용자 테이블의 회사). 커밋 제목 "타겟 테이블 변경".
- 버린 대안: fetch join(컬렉션·조건부 메시지 선택 때문에 JPQL 로 표현이 어려움), batch size(쿼리 수는 줄지만 엔티티 로딩 비용 유지).
- 트레이드오프: `Object[]` 인덱스 매핑이라 컬럼 하나 빠지면 뒤 인덱스가 전부 밀린다(실제로 `6cbac4b83e6` 에서 `data[3]→data[2]` … 15개 getter 를 고쳤다). DB 종속(이후 Oracle 호환 수정 필요).

**바뀌어 온 이력**: `f5726b33cde`(2023-11-15, 고객사 브랜치: 알림/대화 count 제거) → `9cc7b3a9711`(11-20, GO-43488 제품 반영, `SliceModel`) → `df630cc5d66`(12-13, native + `ChatBuddyMap`) → `5204ec10c66`(12-14, converter 226줄, `ChatRoomMemberService`/`ChatRoomNoticeService` 메서드 추가) → `2c4f2d51ae3`(12-26) → `6cbac4b83e6`(2024-01-12, 서브쿼리 2개) → `869e8404f7f`/`1cc2d2c589e`(01-17, company_id) → `08fb08671d1`(2024-10, 타인: Oracle 호환).

**면접 30초 설명**

"메신저 대화방 목록은 `ChatBuddy` 엔티티를 페이지로 읽은 뒤 `ChatModelConverter.transformChatBuddy` 에서 행마다 마지막 메시지 `findOne`, 안 읽은 수 count, 알림 설정 조회를 하고 연관 엔티티를 lazy 로딩했습니다. 이걸 `ChatBuddyRepository.getDataForChatBuddyModel` native 쿼리 하나로 바꿔 방·사용자·마지막 메시지를 조인하고 안 읽은 수와 알림 차단 여부는 스칼라 서브쿼리로 붙였습니다. 결과 `Object[]` 는 `ChatBuddyMap` 으로 감싸 메모리에서 모델을 만듭니다. 총 개수 count 도 비싸서 `Slice` 로 바꾸고, 기존 앱 호환을 위해 `SliceModel` 이 `PageInfo` 형태를 유지하게 했습니다."

**헷갈리기 쉬운 점**

- **"쿼리 1개"는 과장이다.** 조립 단계에 행당 조회가 남아 있다: `userService.get(fromUserId)`(그룹방 발신자), `chatRoomMemberService.getMemberNamesExceptUser`/`getMemberExceptUser`(방 멤버 이름·1:1 상대), `chatRoomNoticeService.findOne`(공지), `userService.get(buddyId)`(1:1). User 는 엔티티 2차 캐시(`ENTITY_CORE`)가 걸려 있어 대부분 캐시 히트지만, 멤버 이름·공지는 DB 조회다. "목록 본체와 집계를 한 쿼리로, 남은 건 캐시되는 단건 조회"라고 말하는 게 정확하다.
- **스칼라 서브쿼리는 행마다 실행된다.** 페이지 크기(기본 10) 안에서만 돌기 때문에 감당 가능한 것이다. `ORDER BY t.id DESC` + limit 이 먼저 적용되는지는 실행 계획에 달렸다(서브쿼리 `t` 전체 정렬 후 limit — 확인 필요).
- **상단 고정 목록(`WithPin`)은 페이징 없이 전부**, 첫 페이지에만 `prepend` 한다.

---

### 4. notifier(openfire) GoCustomInterceptor 패치  (2024-06-20~21 · `713ec09e414`, `32110e63e42` · `bugfix/GO-45372_openfire_interceptor_모바일IQ_차단` 만, develop 반영은 2026-11-03 cherry-pick `e3a0ef14aac`·`ed72bbaf9cd` + 후속 `afd30758608`)

**내가 한 범위**: `PresenceInterceptor` → `GoCustomInterceptor` 이름 변경, IQ roster get 거부 분기, presence 를 PC 리소스 화이트리스트로 변경, 리소스 없는 presence 재전달 복구. `sendMessageToMultiDevice`, `ResourceHelper`, 웹 리소스 발신 차단, `sendPresenceToMultiDevice` 의 원형은 곽면순(2020~2021) 코드다.

**코드 지도**

| 파일 | 클래스/메서드 | 역할 |
|---|---|---|
| `notifier/plugins/openfire-goservice-plugin/src/java/org/jivesoftware/openfire/plugin/GoServicePlugin.java` | `initializePlugin`/`destroyPlugin` | `InterceptorManager` 에 인터셉터 등록/해제 |
| `plugin/GoCustomInterceptor.java` | `interceptPacket` | 패킷마다 호출되는 필터 |
| `plugin/GoCustomInterceptor.java` | `sendPresenceToMultiDevice` | bare JID 로 라우팅 테이블 조회 → PC 리소스에만 재전달 |
| `plugin/ResourceHelper.java` | `isPcResource`, `isWebResource`, `isMobileResource` | 리소스 문자열에 상수 포함 여부(빈 값이면 false) |

**흐름**
```
클라이언트 → openfire → InterceptorManager → GoCustomInterceptor.interceptPacket(packet, session, incoming, processed)
  processed == true            → return (처리 후 콜백은 무시)
  outgoing Presence            → from/to null → 거부
                                  from 이 웹(HTTP-Bind) 리소스 → 거부
                                  to 리소스가 있고 PC 가 아님 → 거부           (32110e63e42: 블랙리스트 → 화이트리스트)
                                  to 리소스가 없음 → sendPresenceToMultiDevice 로 PC 세션에만 재전달 후 원본 거부
  incoming Message             → sendMessageToMultiDevice (기존)
  incoming IQ get jabber:iq:roster → 거부                                      (713ec09e414)
```

**핵심 코드**
```java
// git show 32110e63e42:notifier/.../plugin/go/GoCustomInterceptor.java:34-72  (2024-06 배포본)
        if (incoming == false && (packet instanceof Presence)) {
            JID from = packet.getFrom();
            JID to = packet.getTo();
            if (from == null || to == null) throw new PacketRejectedException();
            String fromResource = from.getResource();
            String toResource = to.getResource();
            if (ResourceHelper.isWebResource(fromResource)) throw new PacketRejectedException(); // HTTP-Bind 발 presence 는 skip (기존)
            // PC메신저에게 전달하는 presence 만 처리 — 모바일/웹/알 수 없는 리소스 모두 차단
            if (toResource != null && !ResourceHelper.isPcResource(toResource)) throw new PacketRejectedException();
            // roster 기반 전달에서 리소스 없이 bare JID 로 오는 경우 → 라우팅 테이블에서 PC 세션을 찾아 다시 보내고 원본은 버림
            if (toResource == null) {
                sendPresenceToMultiDevice(packet);
                throw new PacketRejectedException();
            }
        } else if (incoming == true && (packet instanceof Message)) {
            sendMessageToMultiDevice(packet);
        } else if (incoming == true && (packet instanceof IQ)) {
            IQ iqPacket = (IQ) packet;
            // 클라이언트의 roster 조회 요청 자체를 거부 → 서버가 회사 전원 roster 를 만들어 보내는 일을 없앰
            if (iqPacket.getType() == IQ.Type.get && iqPacket.getChildElement() != null
                    && "jabber:iq:roster".equals(iqPacket.getChildElement().getNamespaceURI())) {
                throw new PacketRejectedException();
            }
        }
```
```java
// 같은 파일 :79-97 — 리소스 없는 presence 재전달 (2024-06 버전)
        Iterator<JID> addrIter = routingTable.getRoutes(new JID(toAddr.getNode(), toAddr.getDomain(), null), null).iterator();
        while (addrIter.hasNext()) {
            address = addrIter.next();
            resource = address.getResource();
            packet.setTo(address);                       // ← 같은 패킷 객체의 수신자를 바꿔 가며 보냄 (2026-11 afd30758608 에서 createCopy() 로 수정)
            if (ResourceHelper.isPcResource(resource)) { // 32110e63e42: "모바일·웹 아님" → "PC 임"
                routingTable.routePacket(address, packet, true);
            }
        }
```

**데이터·설정**: 리소스 형식 주석 `go_ios_{userId}_{tokenId}` (`ResourceHelper`), 상수 `Constants.PC_RESOURCE/WEB_RESOURCE/ANDROID_RESOURCE/IOS_RESOURCE`(값 확인 필요). 별도 프로퍼티 없음.

**왜 이렇게 짰나**

- 인터셉터는 openfire 가 모든 패킷마다 부르는 유일한 확장 지점이라, 서버 소스 수정 없이 플러그인만 바꿔 배포할 수 있다.
- roster 차단: 조직도·대화 상대는 메신저가 HTTP API(1번 캐시)로 받으므로 XMPP roster 가 필요 없다는 전제(커밋에 근거 없음 — "제가 확인한 바로는"으로 말할 것).
- 블랙리스트 → 화이트리스트: 차단 대상(모바일·웹)을 열거하면 새 리소스 종류나 리소스 없는 JID 가 통과한다. "PC 만 통과"가 안전하다.
- 첫 시도(`713ec09e414`)는 커밋 제목대로 "라우팅 로직 제거"였다. `isPcResource(null)` 이 false 라 리소스 없는 presence 를 전부 버렸다. 다음 날(`32110e63e42`) PC 세션 재전달을 되살렸다 → PC 메신저 상태 표시가 깨지지 않게.

**바뀌어 온 이력**: `713ec09e414`(06-20, 이름 변경 + IQ 차단 + null 리소스 재전달 제거) → `32110e63e42`(06-21, 화이트리스트 + null 리소스 PC 재전달 복구) → 2026-11-03 develop cherry-pick `e3a0ef14aac`, `ed72bbaf9cd` → `afd30758608`(대상별 `createCopy()`, `GoCustomInterceptorTest` 7건).

**면접 30초 설명**

"메신저 서버 오픈 직후 매일 같은 시각 openfire CPU 가 튀었습니다. openfire 플러그인의 패킷 인터셉터를 `GoCustomInterceptor` 로 바꿔 두 가지를 막았습니다. 하나는 클라이언트의 `jabber:iq:roster` get 요청을 거부해 접속할 때마다 회사 전원 roster 를 만드는 일을 없앤 것이고, 다른 하나는 presence 를 PC 리소스로 가는 것만 통과시키는 화이트리스트로 바꾼 것입니다. 리소스 없이 bare JID 로 오는 presence 는 라우팅 테이블에서 PC 세션만 찾아 다시 보내고 원본은 버립니다."

**헷갈리기 쉬운 점**

- **roster 차단은 모바일만이 아니다.** 커밋 제목은 "모바일 iq 차단"이지만 코드는 리소스 구분 없이 IQ get + roster 네임스페이스 전부를 거부한다.
- **"리소스 누락 reject" 가 아니라 "PC 로만 재전달 후 원본 reject"** 이다. 첫날 버전만 단순 reject 였다.
- **2024 당시 develop 미반영.** 고객사 버그픽스 브랜치로 배포됐다. 패킷 객체 재사용 문제는 2026-11 에 고쳤다.
- 18시 장애·GC·roster 1만 명 같은 원인 수치는 코드에 없다.

---

### 5. 2023 약 3,400명 고객사 조직도 API 개선  (2023-05 ~ 09 · `86c1e3ce598`, `904d25f5c95`, `f24a8b92c22`, `c7aed5f0a9a` · `bugfix/GO-43787_조직도_API_성능_분석` → develop / 근태 동기화 `3cded0178d4`, `14b143c1f03`, `feff2d34efe` · `feature/GO-44222_근태_동기화_개선` 만)

**내가 한 범위**: 아래 커밋 전부 본인. 다만 이 단계의 "변경분 조회" 구조 자체는 기존 설계이고, 본인은 그 안에서 쿼리·로딩·인덱스를 다듬었다.

**코드 지도**

| 파일 | 변경 | 커밋 |
|---|---|---|
| `common/core/service/UserWebServiceImpl.java#getMobileChangedList` → `getUsersDateBaseForMessenger` | rdate 있으면 `findByCompanyAndUpdatedAtAfterAndOpenType`, 없으면 ONLINE/DORMANT 만 | `86c1e3ce598` |
| `common/core/domain/model/converter/UserModelConverter.java#convertUserToMessengerUserChanged` | 메신저 전용 변환. `user.getDeptMembers()`(departmentIds) 를 빼 사용자마다 부서원 컬렉션 로딩 제거 | `86c1e3ce598` |
| `common/core/domain/User.java` | `@Cache(NONSTRICT_READ_WRITE, ENTITY_CORE)` 1줄 | `86c1e3ce598` |
| `common/core/domain/DeptMember.java` | `@ManyToOne(fetch = LAZY) user`, setter(duty/type/sortOrder/userDepartmentOrder)에서 `dirtyDepartment()` | `904d25f5c95` |
| `common/core/domain/Department.java` | `dirty()` = `setUpdatedAt(new Date())`, 정렬·자식 변경 시 호출 | `904d25f5c95` |
| `common/core/repository/spec/DepartmentSpecifications.java` | `byCompaniesAndDateAsRevisionIncludeDeptMember`(부서원 LEFT JOIN + OR 6조건) → `byCompaniesAndGreaterThanUpdatedAt`(부서 updated_at 하나) | `904d25f5c95` |
| `ladmin/autopatch/db/10.5.14.0.sql`, `10.5.15.0.sql` | `idx3_go_users(updated_at)`, `idx1_go_dept_members(department_id)`, `idx1_go_departments(company_id, updated_at)` | `86c1e3ce598`, `904d25f5c95`, `c7aed5f0a9a` |
| `web/core/controller/api/DepartmentController` `GET /departments/children/changed` | `MAX(updated_at)` 로 변경 여부만 boolean | `c7aed5f0a9a` |
| `DeptServiceImpl`/`DeptWebServiceImpl` 설정 조회 | `@Transactional(readOnly = true)` | `f24a8b92c22` |

**흐름 (부서 변경분 조회)**
```
개선 전: Department ⟕ DeptMember  WHERE d.created/updated/deleted ≥ rdate OR dm.created/updated/deleted ≥ rdate   (부서원 테이블 department_id 인덱스 없음)
개선 후: DeptMember setter → department.dirty() 로 "부서원 변경"을 부서 updated_at 에 모음
         Department WHERE company IN (...) AND updated_at ≥ rdate                                              (idx1_go_departments)
```

**핵심 코드**
```java
// 904d25f5c95 — DeptMember.java (변경 감지를 부서 단위로 모으는 장치)
    @ManyToOne(fetch = FetchType.LAZY)        // 기존 EAGER(기본값) → 부서원 로딩 때 User 즉시 로딩 제거
    private User user;
    public void setSortOrder(Integer sortOrder) {
        dirtyDepartment();                    // 부서원 정렬이 바뀌면 소속 부서 updated_at 갱신
        this.sortOrder = sortOrder;
    }
    private void dirtyDepartment() {
        if (Objects.nonNull(department)) department.dirty();
    }
// Department.java
    public void dirty() { setUpdatedAt(new Date()); }
```
```java
// 904d25f5c95 — DepartmentSpecifications (조인 제거)
    public static Specification<Department> byCompaniesAndGreaterThanUpdatedAt(List<Company> companies, Date dateAsRevision) {
        return dateAsRevision == null
                ? isCompanyIn(companies) : where(isCompanyIn(companies)).and(getGreaterThanUpdatedAt(dateAsRevision));
    }
```

근태 동기화(브랜치 전용) `3cded0178d4`: `ChatModelConverter.transformChatRoomMember` 가 멤버마다 `sessionContext` 로 세션 사용자를 찾고 `timelineDisplaySettingService.getTimelineDisplaySetting(companyId)` 를 호출하던 것을, `ChatRoomServiceImpl` 에서 한 번 조회해 파라미터로 넘기도록 바꿨다(루프 안 조회 → 루프 밖). 같은 아이디어가 develop 에는 2024-04 `f143c382d99` 로 들어갔다.

**왜 이렇게 짰나**: 조인을 없애려면 "부서원이 바뀌면 부서도 바뀐 것"이 성립해야 한다. 그래서 쿼리를 바꾸기 전에 엔티티 setter 에 `dirty()` 를 심어 쓰기 쪽에서 불변식을 만들었다. 메신저 전용 컨버터는 범용 변환을 건드리지 않고 메신저가 쓰지 않는 필드(부서 ID 목록)만 빼려는 것이다.

**면접 30초 설명**: "3,400명 고객사에서 출근 시간 조직도 API가 느렸습니다. 변경분 판정이 부서와 부서원을 조인해 OR 조건 여섯 개로 비교했고 부서원 테이블에 `department_id` 인덱스도 없었습니다. `DeptMember` setter 가 소속 `Department.dirty()` 를 불러 부서 `updated_at` 을 올리게 해서, 판정을 부서 테이블의 `(company_id, updated_at)` 인덱스 하나로 끝냈습니다. 사용자 쪽은 `convertUserToMessengerUserChanged` 라는 메신저 전용 변환을 만들어 사용자마다 부서원 컬렉션을 로딩하던 걸 없앴고, `DeptMember.user` 를 LAZY 로 바꿨습니다."

**헷갈리기 쉬운 점**
- 이 단계는 여전히 "변경분" 구조다. 이 개선 후 1만 명 규모에서 1번(전체 트리 캐시)으로 넘어갔다.
- `dirty()` 는 setter 를 거치는 변경만 잡는다. 벌크 update·native update 로 바뀌면 부서 `updated_at` 이 안 오른다.
- 근태 동기화 커밋 3개는 develop 에 없다. 면접에서 "제품 반영"이라고 말하면 안 된다.
- "부서 조회 큰 limit 풀스캔"은 코드에서 특정 못 했다(확인 필요). nGrinder TPS 수치도 저장소에 없다.

---

### 6. 2차 개선 중 본인 처리분 (코드로 찾은 것만)

| 항목 | 찾은 것 | 판단 |
|---|---|---|
| 채팅 쿼리 2차 (GO-45005, 2024-02-26 ~ 03-20) | `6e86ba59bb6`(대화방 검색), `cd9b43c07ab`(대화내용 native + `ChatMessageMap`/`ChatMessageHistoryMap`/`ChatRoomMemberMediator`), `5d090d26b01`, `975ea7a4dce`, `e3903a10ef2`, `93ce99e3dc4`. 모두 develop 포함 | 확인 |
| 근태 표시 (GO-45171) | 2번 항목 | 확인 |
| `/ehr/timeline/info` | `TimelineUserController.java:134` → `EhrWebServiceImpl`. 본인 변경은 `d1a212cfa5f`(GO-45171 묶음): 표시설정 조회를 `companyId` → `Company` 로 바꿔 재조회 제거, `TimelineInfoModel`·`TimelineHistoryModel` 이 `new TimelineStatusEntityConverter()` 대신 스프링 빈을 쓰게 함 | 코드 변경은 확인. 이것이 "/info 개선" 전부인지, 성능 효과가 있었는지는 확인 필요 |
| 게시판·커뮤니티 슬로우 쿼리 | 2023-09 ~ 2024-12 본인 커밋 중 board/community 관련 변경 없음 | **저장소로 확인 안 됨** (DB 인덱스·쿼리 힌트를 DBA 와 운영에서 적용했거나 다른 저장소일 가능성 — 본인 기억 확인 필요) |

채팅 대화내용 2차 핵심 (`cd9b43c07ab`)
```java
// common/chat/domain/model/converter/ChatModelConverter.java:692-711
    public List<ChatMessageHistoryModel> convertToModel(List<ChatMessageMap> chatMessageMapList) {
        ...
        // 페이지 안 메시지들의 읽음 이력을 IN 한 번으로 읽어 메시지 ID 로 묶는다 (예전: 메시지마다 confirm 사용자 조회)
        Map<Long, List<ChatMessageHistoryMap>> chatMessageHistoryMapGroup = chatMessageHistoryRepository
                .getDataForChatMessageHistoryMap(chatMessageMapList.stream().map(ChatMessageMap::getId).collect(Collectors.toList()))
                .stream()
                .map(ChatMessageHistoryMap::new)
                .collect(Collectors.groupingBy(map -> map.getChatMessageId()));
        for (ChatMessageMap chatMessageMap : chatMessageMapList) {
            models.add(convertToModel(chatMessageMap, chatMessageHistoryMapGroup.get(chatMessageMap.getId())));
        }
        ...
    }
```
흐름: 대화방 진입 → `ChatHistoryServiceImpl.getUpRangeChatMessages` → `ChatMessageHistoryRepository.getLatestDataForChatMessageMap(chatBuddyId, criteriaMessageId, PageRequest(0, size, DESC id))`(history ⨝ message ⟕ room, native Slice) → `ChatMessageMap` → 위 메서드(읽음 이력 IN 1회 + groupingBy). 남은 행당 조회: 첨부 파일 `chatMessageAttachRepository.findOne`, 발신자 `userService.getById`(2차 캐시).

면접 30초: "1차에서 대화방 목록을 풀고 나니 대화방 안 메시지 목록이 다음 병목이었습니다. 메시지마다 읽음 사용자 목록을 따로 조회하던 걸, 페이지 메시지 ID 들로 `go_chat_message_histories` 를 IN 한 번 읽어 `groupingBy` 로 붙이도록 바꿨습니다. 목록과 같은 패턴입니다. native 로 필요한 컬럼만 읽고, `Map` 래퍼로 감싸고, 메모리에서 조립합니다."

---

### 부록: 면접 전 직접 확인할 것

1. 운영 PostgreSQL 에서 `to_date('…09:01:00','YYYY-MM-DD hh24:mi:ss')` 가 시각을 유지하는지 (2번 relay 쿼리 정상 여부).
2. 게시판·커뮤니티 슬로우 쿼리를 어디서 고쳤는지 (저장소 밖 작업인지).
3. `go_chat_buddies.unread_message_count` 를 버린 이유 (`6cbac4b83e6`).
4. 메신저 클라이언트가 `/relation/accessible` 과 `/relation/entire` 중 무엇을 부르는지.
5. `@Async` 실행기 풀/큐 설정 (회사 수만큼 relay 작업이 동시에 쌓임).
