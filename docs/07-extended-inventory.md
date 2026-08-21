# 07 · 확장 인벤토리 — 2026-08 현재 실제 운용 스택

01 문서 작성 후 추가 분석한 12개 레포(비공개 1 + 최근 활동 공개 11). 결론:
**현재 실전 수익의 중심은 한국 특화 베이시스/갭 북**이고, 01에서 본 perp DEX
스택은 그 일부였다. 그리고 "DEX 갭 자동화"와 "CEX/KRX 자동 실행"은 이미
부분적으로 존재한다 — 06의 우선순위 1·4가 생각보다 훨씬 가깝다.

## A. 실행 가능(라이브) 봇 — 이미 2개 더 있다

### `variational` — Ostium↔Variational 달러갭 아비봇 ⭐ "DEX 갭 워크플로우의 자동화 버전"
- 양방향 달러갭: `gap_short = ostium_bid − var_ask`, `gap_long = var_bid − ostium_ask`.
- 진입 `|gap| ≥ $20`(권장 $15~30), 청산 합산 PnL ≥ $15. 담보 기본 $300, 레버 3×.
- **완전 라이브**: Ostium 온체인 tx 직접 브로드캐스트 + Variational quotes_accept. 5ms 가격 루프.
- 텔레그램 조작 변형, 중앙 config-server에서 파라미터 원격 배포(→ `config-server` 레포의 정체).
- 시사점: 06에서 "DEX 갭 반자동화가 1순위"라 했는데, **이미 한 venue쌍은 완전 자동화 완료**. 남은 건 이 패턴을 다른 venue쌍/자산으로 일반화하는 것.

### `hynix_samsung_premium` — KRX↔Hyperliquid 단일주 베이시스 (모니터+라이브 자동매매)
- (a) 알림봇: `xyz:SKHX`/`xyz:SMSN` perp vs KRX 현물(네이버 폴링) + NXT 시간외, 환율 폴백 3중. 진입 프리미엄 1% / 청산 0.1%, 15s 폴링.
- (b) **autotrader**: perp vs **KRX 주식선물** 듀얼레그 실주문 봇.
  - 신호는 절대값이 아니라 **베이스라인 상대**: `entry − baseline ≥ 0.5%p` (baseline = 7일 롤링 미드 프리미엄), 청산 `exit − baseline ≤ 0`.
  - 실행: KIS 시세 + 키움 게이트웨이(127.0.0.1:8899) 선물 지정가 → HL 시장가 숏(격리 3×). 편체결 시 즉시 되돌림.
  - 리스크: 계약 1개, 일 3사이클, 세션가드, 스프레드/프리미엄 새니티, PAUSE 킬파일, 만기 롤 가드, 재시작 포지션 대조.
  - **현재 `mode: monitor`** — live 플래그만 켜면 실주문. 텔레그램으로 런타임 파라미터 튜닝.
- 시사점: **CEX/KRX 자동화의 브로커 추상화(KIS+키움+HL)가 이미 완성**돼 있다. "하닉 삼전 크게 나갈 때 주워먹기"의 시스템화가 진행 중이었던 것.

### `monk_trading_bot` — ETH/BTC 상대강도 페어 트레이딩 (4 venue)
- `spread = ETH수익률 − BTC수익률`의 z-score 평균회귀. 3프로파일(스캘프/스윙/포지션): 진입 z 1.5/2.0/2.5, TP +0.8%, SL −3%, 레버 3×, $500/페어.
- Pacifica/Extended/Lighter/Backpack + Variational. 라이브 실행 코드 존재(EXECUTION_LIVE), FastAPI+React 대시보드, PostgreSQL.
- 참고: 유일한 통계적(비차익) 전략 — 마스터플랜 B군에 해당. 캡 작게 유지 원칙 적용 대상.

## B. 신호/어드바이저 — 수동 워크플로우 보조

### `wonsang_bot` — KRW 신규상장 스나이퍼 ⭐ "수동 갭매매 어시스턴트"의 원형
- 업비트/빗썸 공지 감지 → 컨트랙트 주소 해석 → 매수처(해외 CEX/DEX/브리지) 추천 → 등급화(0.80 대성공 / 0.62 성공 / 0.42 약성공) → 텔레그램.
- 매도 계획: 해외가 대비 KRW +1.5% 초과 시 전량 청산 타깃. 김프 실현수익 백테스트 내장.
- **자동화 사다리 원칙이 명문화돼 있음**: 추천 → 반자동(원클릭) → 자동. 자금이동 수동, 출금 비활성 API 키, 화이트리스트 주소. ← 06에서 제안한 하이브리드 원칙과 정확히 일치. 이 원칙을 전 시스템 표준으로 채택.

### `upbit_bithumb_arbitrage_bot` — 김프 엔진 (수수료·용량 인지형)
- 업비트/빗썸 KRW vs Binance/Bybit/OKX USDT, 최대 150코인, WS 오더북.
- **3-leg VWAP 왕복 순엣지**: 해외 매수→국내 매도→USDT 재매수까지 오더북 walk (전송비 암묵 반영). `capacity_at_threshold()`가 순엣지 ≥ 임계를 유지하는 최대 노셔널을 이진탐색.
- 수수료 내장(업비트 0.05%, 빗썸 0.25%, 해외 0.1% + 코인별 출금비). 순엣지 ≥ 0.5% 알림.
- 시사점: 01의 chiparbi보다 훨씬 발전된 김프 엔진. **size-aware net edge + capacity**를 이미 계산 → Brain의 Opportunity Ranker에 그대로 들어갈 수 있는 출력.

### `overbought_oversold_assets` — 크로스에셋 과열/과냉 온도계
- 35개 자산(크립토/지수/채권/원자재/FX) 온도 [-100,100]: 단기(RSI·스토캐스틱·볼밴·CCI 등 6~7개 오실레이터) 40% + 장기(SMA200 괴리 백분위·52주 레인지 등) 60%.
- ≥60 mania / ≤−60 deep exhaustion. GitHub Actions 일일 한국어 리포트.
- 시사점: "하닉/삼전/오라클 급락 시 줍기"의 정량화 + Brain의 **레짐 게이트**(과열 시 방향성 전략 차단, 과냉 시 분할매수 알림)로 활용.

### `dimae_index` — 한국 커뮤니티 심리 지수
- 네이버카페/디시/보배/코인판 크롤링 → attention 30% + FOMO 25% + 감성 15% + ... 백분위 0~100, panic/euphoria 레짐 분류. 역발상 신호 연구용.

## C. 교훈이 담긴 레포

### `rwa_arbitrage` — 오일 perp vs CME 선물 베이시스 (페이퍼)
- 볼린저-온-베이시스: 진입 `basis > mean + 2σ` AND > 50bps, 왕복비용 13.4bp.
- **기록된 실패**: 이전 버전 49트레이드 −$599.65, 승률 16% — 원인은 조기 청산. M7에서 수렴-홀드 방식(펀딩 수취하며 대기)으로 전환.
- **시스템 전체에 적용할 교훈**: 갭 전략의 죽음은 진입이 아니라 **청산 규율**에서 온다. Brain의 exit 로직에 "수렴 전 조기청산 금지 + 보유비용(펀딩)이 우호적이면 대기" 원칙 반영 (bn_hl의 breakeven_hours와 동일 사상).

### `variational_calculation` — Variational 계정 실체결/펀딩 CSV
- 코드 없음. 실제 체결·펀딩·PnL 기록 → **비용모델 캘리브레이션 데이터**로 가치(cost oracle의 이론치를 실체결로 검증).

## D. 계획 단계

### `bnbchain_stock_lp` — PancakeSwap SKHYB/USDT 집중유동성 LP (플랜만)
- 진입: fee-only 7d APR ≥ 50%, vol/TVL ≥ 0.5, CEX-DEX 괴리 p95 < 0.7%, 리밸런스비 < 월수수료 30%. 관찰모드 3~7일 의무.
- 토큰화 주식 LP = 새 수익원 후보. 단 구현 0%, 우선순위 낮게.

### 빈 껍데기: `web3_m_auto`(빈 레포), `trade.xyz`(plan.md 1개 — rwa_arbitrage의 전신)

## E. 종합 — 마스터플랜 수정 사항

1. **아키텍처(02)는 유효하되, 채울 내용물이 예상보다 많다.** Executor에 넣을 실행 코드가 3개(autotrading_btc_eth, variational, hynix autotrader), 브로커 추상화는 KIS/키움/HL/Ostium/Variational까지 이미 커버.
2. **우선순위(06) 구체화**:
   - ① DEX 갭 반자동화 = `variational` 봇의 **venue쌍 일반화** + `wonsang_bot` 자동화 사다리 적용.
   - ② 펀딩 캐리 = `xyz100funding` 증액 규칙 + 자동 리밸런스.
   - ③ 디페그 워처 = 신규 개발 (기존 페그 감시 레포 없음 — 유일한 진짜 공백).
   - ④ CEX/KRX 자동화 = `hynix autotrader` live 전환 + `upbit_bithumb` 엔진에 실행 레이어.
3. **원칙 표준화**: wonsang_bot의 자동화 사다리(추천→원클릭→자동), rwa_arbitrage의 청산 규율, hynix autotrader의 세이프티 패턴(편체결 되돌림·킬파일·세션가드·포지션 대조)을 전 전략 공통 표준으로.
4. **알파 노출 재경고**: 위 전략 전부(임계값·수수료·용량 계산까지) 공개 레포다. private 전환이 시급하다.
