# 02 · Master AI 아키텍처

흩어진 부품을 하나의 자율 트레이딩 시스템으로 묶는 6계층 구조.
지금은 사람이 텔레그램 알람 보고 손으로 거래하는데, 그 "사람" 자리를 Brain이 대체한다.

```
                 ┌─────────────────────────────────────────────┐
                 │              (6) OPS / CONTROL PLANE          │
                 │  대시보드 · 전략 ON/OFF · 성과 · 킬스위치 · 백테스트   │
                 └───────────────▲──────────────────┬────────────┘
                                 │ metrics/PnL       │ commands
   ┌───────────┐   prices   ┌────┴───────────┐  signals  ┌──────────────┐
   │(1) ADAPTERS│──────────▶│ (2) SIGNAL BUS │──────────▶│  (3) BRAIN    │
   │ 거래소 클라이언트│  포지션/펀딩 │  표준 신호 스트림  │  ranked   │ 기회 랭킹·자본배분 │
   └───────────┘            └────────────────┘           └──────┬───────┘
        ▲                          ▲                            │ orders
        │ books/funding/balance     │ cost quote                ▼
        │                    ┌──────┴────────┐           ┌──────────────┐
   거래소 REST/WS            │(4) COST ORACLE │◀──────────│ (5) EXECUTOR  │
                            │ slippage+fee  │  pre-trade │  주문 라우팅·헷지 │
                            └───────────────┘           └──────┬───────┘
                                                               │ fills
                                              ┌────────────────▼───────┐
                                              │  (R) RISK GUARD          │
                                              │ 마진·손실·이상 → 킬스위치   │
                                              └──────────────────────────┘
```

## (1) Adapters — 거래소 연결 계층

기존 레포들에 흩어진 거래소 클라이언트를 **공통 라이브러리(`@core/exchanges`)** 로 추출.
한 거래소당 하나의 클라이언트가 세 가지 인터페이스를 구현:

- `marketData`: 오더북/mark/index/펀딩 스트림 (WS 우선, REST 폴백).
- `account`: 잔고·포지션·마진 (출처: `perpdex_assets`의 정규화 모델 `ExchangeBalance`/`Position` 재사용).
- `trading`: `placeOrder`/`cancel`/`positions` (출처: `autotrading_btc_eth`의 Cascade/RISEx 실행 코드).

대상 거래소 유니버스(이미 코드 보유): **Hyperliquid, Lighter, Paradex, Nado, Extended, Variational, Pacifica, 01/N1, Cascade, RISEx** + CEX **Binance, Bybit, OKX, Upbit, Bithumb**.

> 원칙: 한 거래소는 한 번만 구현한다. 지금처럼 레포마다 Hyperliquid 클라이언트를 재구현하지 않는다.

## (2) Signal Bus — 표준 신호 스트림

모든 신호 소스를 단일 이벤트 스키마로 정규화하는 메시지 버스(Redis Streams / NATS / 간단히는 인메모리 EventEmitter로 시작).

```ts
interface Signal {
  id: string;
  strategy: "perp_basis" | "cross_venue_spread" | "funding_carry"
          | "kimchi_premium" | "mark_index" | "price_cross";
  pair: string;                 // "BTC-PERP"
  legs: { exchange: string; side: "buy"|"sell"; ref_price: number }[];
  gross_bps: number;            // 총 스프레드(엣지) bps
  sustained_ms: number;         // 지속 시간
  meta: Record<string, unknown>;// funding, mark/index gap 등
  ts: number;
}
```

기존 레포의 신호 발생 지점을 이 버스로 연결:
- `perpdex_arbitrage_alarm`의 `alertManager.on('alert')` → `cross_venue_spread` 신호.
- `bn_hl_arbitrage`/`hl_lighter_arbitrage` → `perp_basis` + `mark_index`.
- `fundingrate_auto`의 8h 정규화 펀딩 → `funding_carry`.
- `chiparbi`의 spread matrix `best` → `kimchi_premium`.

## (3) Brain — 중앙 결정 엔진 (이 프로젝트의 핵심)

신호를 받아 **무엇을, 어디서, 얼마나** 거래할지 결정. 두 개의 서브모듈:

### 3a. Opportunity Ranker
모든 활성 신호를 **예상 순익**으로 정렬:

```
net_bps = gross_bps
        − cost_oracle.quote(legs, size)   // (4)에서 실측 슬리피지+수수료
        − funding_cost_bps(hold_horizon)  // 펀딩 보유비용
        − risk_premium_bps                // 변동성/체결리스크 버퍼
expected_pnl_usd = size_usd × net_bps / 10000
```

`net_bps > min_edge` 인 기회만 후보. (autotrading의 50bps, perpdex_alarm의 0.2~0.3%는 *알람 등급*이지 *비용차감 후 엣지*가 아니므로, Brain은 항상 cost oracle을 통과시킨 net_bps로 재평가한다.)

### 3b. Capital Allocator
- 후보를 expected_pnl 내림차순으로 자본 배분, 단 제약 준수:
  - 심볼당 포지션 캡 (autotrading의 $1,000 → 자본비례로 스케일).
  - 거래소당 OI 캡 (fundingrate_auto의 deposit×5).
  - 전략간 상관 고려(같은 BTC 델타 중복 방지).
  - 분수 켈리(fractional Kelly, 1/4~1/2) 또는 고정 위험비율로 사이징.
- 출력: `Order Intent` 리스트 → Executor로.

### 3c. (선택) AI 보조 레이어
규칙 기반이 본체이되, Claude API로 보강:
- **레짐 감지**: 변동성/추세 국면 분류 → min_edge·사이징 동적 조정.
- **이상징후 설명**: 비정상 스프레드가 진짜 기회인지 데이터오류/디페그/상장폐지 리스크인지 분류(특히 chiparbi의 OFT 브리지 가능성 미확인 같은 케이스).
- **뉴스/공시 게이트**: 청산캐스케이드·상장·해킹 뉴스 시 해당 심볼 자동 차단.
- 모델: `claude-fable-5` 또는 비용 민감 시 `claude-haiku-4-5`. AI는 **거부권(veto)·파라미터 조정**만, 직접 주문 생성은 하지 않는다(결정론적 안전성 유지).

## (4) Cost Oracle — 사전 체결비용 검증

`slippage` 레포를 서비스로 승격. Brain이 주문 직전 호출:
`quote(exchange, coin, side, qty)` → `{ slippageBps, feeBps, allInBps, fillRatio }`.
13개 거래소 테이커 수수료 테이블 내장(Lighter/Variational/Paradex 0bps … Bybit 5.5bps). 오더북 깊이 walk로 부분체결·미체결도 반환 → Allocator가 사이즈 자동 축소.

## (5) Executor — 주문 라우팅 & 헷지

`autotrading_btc_eth`의 실행 엔진을 일반화:
- **델타중립 동시 체결**: 양 leg `Promise.allSettled` 동시 발사, half-fill 시 즉시 반대 leg로 평탄화 후 일시정지(기존 `leg_failed` → `setPaused` 로직 재사용·강화).
- Paper / Live 모드. **실거래 전 필수 수정**: `autotrading`의 라이브 게이트 버그(현재 `TRADING_MODE`만 검사, `TRADING_ENABLED` 미검사) — Brain·Executor 통합 시 *두 플래그 AND* 를 하드 게이트로 강제.
- 멱등성(idempotent) `clientOrderId`, 재시도, 미체결 타임아웃 취소.

## (R) Risk Guard — 전역 안전망

`perpdex_assets`를 read-only에서 **제어 권한 보유**로 승격(별도 권한 키):
- 전 거래소 마진 집계, `marginFreePercent` 경고20%/위험10%/치명5% (기존 임계).
- 트리거 시: 신규 진입 차단 → 디레버리지 → 최악 시 전 포지션 청산.
- 전역 킬스위치: 일일손실 한도(기존 $100→자본비례), 이상 변동성, 피드 stale(>10s), 거래소 API 장애.
- Risk Guard는 Brain보다 **상위 권한**. Brain이 뭘 시키든 거부 가능.

## (6) Ops / Control Plane

- 단일 대시보드: 실시간 PnL, 포지션, 전략별 성과, 활성 신호.
- 전략 ON/OFF 토글, 파라미터 핫리로드.
- 백테스트/페이퍼 리플레이: 과거 신호 로그로 전략 검증 후 라이브 승격.
- 일일 리포트(기존 autotrading의 09:00 KST 리포트 확장).
- 감사 로그: 모든 신호·결정·주문·체결 기록(분쟁/디버깅/세무).

## 런타임/배포 권장

- **단일 언어로 수렴**: 신규 코어는 TypeScript(Node 20+) 권장 — 기존 TS 자산(perpdex_arbitrage_alarm, perpdex_assets, chiparbi)이 가장 많고 거래소 WS 생태계가 풍부. Python 신호 레포는 Signal Bus에 신호만 publish하면 되므로 점진 이관 가능.
- **모노레포**: `packages/{exchanges,signal-bus,brain,cost-oracle,executor,risk,ops}` 워크스페이스.
- **배포**: 기존처럼 EC2 + PM2/systemd로 시작 → 신호/실행 분리 후 컨테이너화. 지연민감 leg는 거래소 리전 근처(co-location)에 배치.
