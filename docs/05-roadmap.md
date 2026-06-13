# 05 · 구축 로드맵

"신호+실행은 이미 있다"는 사실을 최대한 활용하는 순서. 새 코드를 많이 쓰는 게 아니라
**기존 부품을 연결**하는 게 핵심. 각 Phase는 페이퍼로 검증 후 다음으로 간다.

## Phase 0 — 기반 통일 (1~2주)

목표: 모노레포 + 공통 코어 추출.

- [ ] `masterplan`을 모노레포로: `packages/{exchanges,signal-bus,brain,cost-oracle,executor,risk,ops}`.
- [ ] **공통 거래소 라이브러리** 추출: 여러 레포에 중복된 Hyperliquid/Lighter/Paradex/Nado/Extended 클라이언트를 하나로. 인터페이스 3종(`marketData`/`account`/`trading`).
- [ ] **공통 심볼맵·비용모델**: slippage의 거래소별 수수료 테이블 + autotrading의 bps 유틸 통합.
- [ ] 감사 로그 스키마(Postgres/SQLite) + 시크릿 관리(read-only 키 / 거래 키 분리).

산출물: 신규 코드가 의존할 코어. 아직 거래 안 함.

## Phase 1 — Signal Bus (1~2주)

목표: 흩어진 알람을 표준 신호 한 스트림으로.

- [ ] `Signal` 스키마 확정 + 버스 구현(인메모리 EventEmitter로 시작 → 필요 시 Redis Streams).
- [ ] 어댑터: `perpdex_arbitrage_alarm` → `cross_venue_spread` 신호 publish (기존 `alertManager.on('alert')` 훅 재사용).
- [ ] 어댑터: `fundingrate_auto` 펀딩 8h → `funding_carry` 신호.
- [ ] Python 신호 레포(`bn_hl`, `hl_lighter`)는 HTTP/큐로 신호만 publish(전면 이관 불필요).
- [ ] 신호 로그 영속화(이후 백테스트·페이퍼 리플레이용).

산출물: 한 화면에서 모든 신호가 흐른다. 아직 거래 안 함.

## Phase 2 — Brain + Cost Oracle (2~3주)

목표: 신호를 순익 기준으로 랭킹·배분(페이퍼).

- [ ] `slippage`를 서비스로 승격: `quote(exchange, coin, side, qty)` API.
- [ ] Opportunity Ranker: `net_bps = gross − allInCost − funding − riskPremium`.
- [ ] Capital Allocator: 계층 한도(트레이드/심볼/거래소/전략/전체) + 순델타 합산 + 분수 켈리.
- [ ] Order Intent 출력 → **PaperExecutor**로만 연결.
- [ ] Ops 대시보드 v1: 신호·랭킹·가상 PnL.

산출물: 시스템이 "거래했다면" 얼마 벌었을지 페이퍼로 측정. 라이브 승격 판단 근거.

## Phase 3 — 실행 연결 (2~3주)

목표: A1(크로스-거래소 perp 스프레드)부터 소액 라이브.

- [ ] `autotrading_btc_eth` 실행 엔진을 Executor로 일반화(Cascade/RISEx 외 거래소 추가).
- [ ] **안전 수정 필수**: 라이브 게이트 버그(`TRADING_MODE`+`TRADING_ENABLED` AND), 고아 leg 복구, 부분체결 사이징, stale 게이팅 1~2s.
- [ ] Risk Guard 승격: `perpdex_assets`에 디레버리지/평탄화 권한 부여(별도 거래 키), 20/10/5% 임계 + 전역 킬스위치.
- [ ] **소액 라이브** A1 가동(기존 $20~$250 사이즈). 1~2주 관찰.
- [ ] 안정 확인 후 A2(펀딩 캐리) 자동 실행 연결.

산출물: 첫 자동 실거래 수익. 죽지 않는 것 확인.

## Phase 4 — 전략 확장 & 스케일 (지속)

목표: 수익원 다변화 + 복리.

- [ ] A4 mark/index + A3 현물-선물 베이시스 추가(인프라 재사용).
- [ ] B1 마켓메이킹(헷지 인프라 완성 후) → 회전율·복리 가속.
- [ ] AI 보조 레이어(3c): 레짐 감지·뉴스 게이트·이상징후 분류(claude-fable-5 / haiku).
- [ ] A5 김치/CEX×DEX (chiparbi OFT·브리지 승격) — **법률검토 통과 후에만**.
- [ ] B2/B3 기회성 전략(작은 캡).
- [ ] 자본 스케일업: 한도 비율 유지하며 NAV 확대, 정기 이익 인출.

산출물: 다수 중립 엣지를 동시·고회전·복리로 굴리는 완성형 Master AI.

---

## 마일스톤 요약

| Phase | 기간(목표) | 끝나면 |
|---|---|---|
| 0 | 1~2주 | 공통 코어 완성 |
| 1 | 1~2주 | 모든 신호가 한 버스에 |
| 2 | 2~3주 | 페이퍼 PnL 측정 가능 |
| 3 | 2~3주 | **첫 자동 실거래 수익** |
| 4 | 지속 | 다전략 복리 시스템 |

대략 2~3개월이면 A1/A2 자동 실거래까지 도달 가능. 이미 부품이 다 있기 때문.

## 다음 액션 (지금 바로)

1. 이 마스터플랜 리뷰 → 우선순위/자본규모 확정.
2. Phase 0 시작: 모노레포 스캐폴딩 + 공통 거래소 라이브러리 첫 거래소(Hyperliquid) 추출.
3. autotrading 라이브 게이트 버그 즉시 패치(실거래 전 가장 위험한 항목).
