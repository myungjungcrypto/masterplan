# 01 · 현재 보유 자산 인벤토리

이미 만들어 둔 레포들을 "자동매매 스택의 부품"으로 재분류한 표.
대부분은 **알람/모니터링 전용(주문 미실행)** 이고, 실행 엔진은 하나뿐이다.

## 계층별 분류

| 계층 | 레포 | 역할 | 현재 상태 |
|---|---|---|---|
| **신호 (Signal)** | `perpdex_arbitrage_alarm` | 5개 perp DEX 교차 스프레드 알람 (BTC/ETH/SOL/HYPE/BNB) | 알람만 |
| | `bn_hl_arbitrage` | Binance↔Hyperliquid 오일 perp 베이시스 | 알람만 |
| | `hl_lighter_arbitrage` | trade.xyz(HL)↔Lighter 오일 perp 베이시스 + mark/index 괴리 | 알람만 |
| | `chiparbi` | CEX×DEX + 김치프리미엄 스프레드 (CHIP/OFT 토큰) | 모니터만 (실행 명시적 배제) |
| | `hyperliquid-alert` | 단일 토큰(XPL) 가격 돌파 알람 | 알람만 (Vercel cron) |
| **비용 오라클** | `slippage` | 13개 거래소 올인비용(슬리피지+수수료) 시뮬레이터 | 대시보드 |
| **펀딩 최적화** | `fundingrate_auto` | 9개 거래소 펀딩 캐리 배분 최적화 | 스프레드시트 출력 |
| **실행 (Execution)** | `autotrading_btc_eth` | Cascade/RISEx vs Lighter 델타중립 차익 엔진 | **실행 가능** (기본 paper) |
| **리스크 가드** | `perpdex_assets` | 8개 perp DEX 담보/마진 감시 + 청산위험 경보 | 모니터만 (read-only) |
| **인프라** | `binance-proxy` | Binance API 프록시 | 보조 |

## 부품별 핵심 스펙 (코드에서 추출한 실제 수치)

### perpdex_arbitrage_alarm (신호)
- 거래소: Hyperliquid, Paradex, Nado, Lighter, Extended (WS) + Variational (REST 1s poll).
- 엣지: 최저 ask 거래소(롱) vs 최고 bid 거래소(숏), `spreadPct = (shortBid − longAsk)/longAsk × 100`.
- 임계값: 기본 **0.3%** / 지속 **2s** / 쿨다운 **30s**; BTC·ETH는 **0.2%**; 느린(REST) 거래소는 **1.0%** / 5s / 60s, fresh fast 소스 ≥2개 필요.
- 신호 페이로드가 이미 실행 가능: `longExchange/shortExchange + longAsk/shortBid + spreadPct + durationMs`.

### bn_hl_arbitrage / hl_lighter_arbitrage (신호)
- 엣지: 동일 perp의 두 거래소 베이시스 → 싼 곳 롱 / 비싼 곳 숏 (델타중립 페어).
- 펀딩비용/시간 계산 + breakeven_hours 산출 (funding ≤ 0이면 무기한 보유 가능).
- 기본 스프레드 임계 **$0.50**, poll **10s**, 쿨다운 **300s**.
- `hl_lighter`는 WebSocket 스트리밍 + SQLite 영속화 + mark/index 괴리 2차 신호 추가.

### slippage (비용 오라클)
- 13개 거래소 오더북 깊이에 시장가 주문 시뮬레이션 → `slippageBps`.
- `allInCostBps = slippageBps + feeBps`. 테이커 수수료(bps): Lighter/Variational/Paradex(retail) **0**, Hyperliquid **4.5**, 대부분 CEX/DEX **5**, Bybit **5.5**.
- **이게 Brain의 진입 필터 핵심이다**: 신호의 총스프레드가 이 올인비용을 넘어야만 실제 엣지.

### fundingrate_auto (펀딩 최적화)
- 9개 거래소 펀딩을 표준 8h로 정규화, `pnl_8h = −notional × funding_rate_8h`.
- 제약: 거래소별 OI 캡 **deposit의 5배**, Binance 방향한도 **2.0×**, SOL·BNB **0.8× 댐핑**, Variational 최소 OI **$3M**.
- 리밸런스 비용(턴오버·수수료·슬리피지)을 펀딩수익에서 차감.

### autotrading_btc_eth (실행 엔진 — 유일하게 실거래 가능)
- 거래소: Lighter(공통 leg, 읽기전용) vs Cascade / RISEx. 심볼 BTC·ETH.
- 엣지: 오더북 깊이 walk로 `levelNetBps = bps(sell−buy) − costBps`, `costBps = takerFee×2 + slippageBuffer`(기본 3bps).
- 진입 **netBps ≥ 50bps(0.5%)**, 청산 spread ≤ **0bps** & PnL ≥ $0.
- 사이징: 트레이드당 **$20~$250**, 심볼당 포지션 캡 **$1,000**, 일일 손실 한도 **$100**.
- 리스크 게이트: 북 스프레드 ≤100bps, 북 mid 이동 ≤500bps, 교차거래소 mid 차 ≤300bps, stale book 15s, 쿨다운 5s, 최소보유 3s, 건강한 거래소 ≥2개.
- 루프 **50ms**. PaperExecutor(기본) / LiveExecutor(양 leg 동시 `Promise.allSettled`, half-fill 시 일시정지).
- ⚠️ **안전버그**: README는 라이브 진입에 `TRADING_MODE=live` + `TRADING_ENABLED=true` 둘 다 필요하다고 하지만, 실제 코드는 `mode`만 검사하고 `enabled`는 로깅만 한다. 실거래 전 반드시 수정.

### perpdex_assets (리스크 가드 — read-only)
- 8개 perp DEX 계정 잔고/포지션 정규화(`ExchangeBalance`/`Position`).
- 위험단계: `marginFreePercent` 기준 경고 **20%** / 위험 **10%** / 치명 **5%**, 쿨다운 30분.
- 멀티 지갑/멀티 계정 지원(콤마 구분), Google Sheets 로깅, 텔레그램 경보.
- Variational fetcher는 미구현 placeholder. 시장데이터(펀딩/오더북) 미수집 — 계정상태 전용.

## 공통 패턴 (통합이 쉬운 이유)

- **공통 거래소 유니버스**: Lighter, Hyperliquid, Paradex, Nado, Extended, Variational가 여러 레포에 반복 등장 → 거래소 클라이언트를 공통 라이브러리로 추출 가능.
- **공통 알림 채널**: 전부 텔레그램 봇 → 이벤트 버스로 대체 가능.
- **공통 언어 분포**: Python(신호/모니터) + TypeScript/Node(신호/리스크) + JS(실행) + Apps Script(펀딩). 통합 시 Brain은 단일 런타임(권장: TypeScript 또는 Python) 하나로 모으는 게 유지보수에 유리.

## 결론: 이미 가진 것 vs 빠진 것

**가진 것** — 다양한 신호 소스, 정확한 비용모델, 작동하는 실행 엔진, 펀딩 최적화, 포지션/마진 감시. 즉 스택의 *수평 부품*은 거의 완비.

**빠진 것 (= 이 마스터플랜이 만들 것)**:
1. 신호를 한 곳에 모으는 **Signal Bus**.
2. 신호를 순익 기준으로 랭킹·자본배분하는 **중앙 Brain**.
3. 신호→실행 **자동 연결** (지금은 사람이 텔레그램 보고 수동).
4. 전 거래소를 아우르는 **통합 리스크/킬스위치**.
5. 성과측정·복리·전략 ON/OFF를 관리하는 **운영 레이어**.
