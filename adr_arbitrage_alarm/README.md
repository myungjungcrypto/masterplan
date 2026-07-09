# adr_arbitrage_alarm

SK하이닉스 나스닥 ADR(**SKHY**) ↔ KRX 본주(**000660**) 프리미엄 실시간 추적·알람봇.
[docs/06-skhynix-adr-arbitrage.md](../docs/06-skhynix-adr-arbitrage.md) Phase 1 구현체.

```
premium_% = (ADR_USD × USDKRW ÷ 0.1 − 본주_KRW) / 본주_KRW × 100   # 1 ADR = 본주 0.1주
net_edge  = |premium| − 올인비용(기본 0.5%)
```

## 실행

```bash
pip install -r requirements.txt
cp .env.example .env   # 텔레그램 토큰 입력 (없으면 stdout 출력)

# 상장 전(7/10 이전): ADR 가격을 목값으로 합성해서 파이프라인 테스트
set -a; source .env; set +a
python main.py --dry-run

# 동작 1회 확인
python main.py --dry-run --once

# 상장 후 라이브
python main.py
```

## 동작

- **세션 스케줄러**: KRX 정규장(09:00–15:30 KST)·미국 정규장은 15초, 프리/애프터는 60초 폴링,
  둘 다 휴장이면 5분 슬립. 두 장이 안 겹치므로 항상 "한쪽 실시간가 vs 다른 쪽 마지막가" 괴리를 본다.
- **가격 소스**: 본주는 네이버 실시간(폴백: 야후 지연), ADR·USDKRW는 야후(프리/애프터 포함).
  추후 KIS OpenAPI / IBKR로 교체 시 `sources.py`만 수정.
- **FX 분해**: 당일(KST) 첫 틱 환율을 앵커로 저장, 프리미엄 중 환율 변동 기여분을 분리 표기.
- **알람** (텔레그램):
  - `🚨 ACTION` — 비용 차감 순엣지 ≥ 1% (쿨다운 10분, 방향 포함)
  - `ℹ️ INFO` — |프리미엄| ≥ 2% (쿨다운 30분)
  - `⚡ RAPID` — 1시간 내 프리미엄 ±1.5%p 급변 (뉴스/전환규정 발표 감지)
- **기록**: 모든 틱을 SQLite(`adr_premium.sqlite3`)에 저장 → Phase 2 밴드 통계(z-score)의 원천 데이터.

## 파라미터 근거 / 주의

| 파라미터 | 값 | 근거 |
|---|---|---|
| `ADR_SYMBOL` | SKHY | 2026-07-09 언론 보도 (상장 후 실제 시세로 재확인) |
| `ADR_RATIO` | 0.1 | 1 ADR = 본주 0.1주 (F-1 공시 보도. **상장일에 야후 시세로 패리티 검증 필수**) |
| `ALL_IN_COST_PCT` | 0.5 | docs/06 4절 초기 추정치. 실측 후 교체 |
| 알람 임계값 | 2 / 1 / 1.5 | 초기값. 상장 후 2주 데이터로 재조정 |

- 야후 무료 시세는 지연·불안정할 수 있음(MVP 용). 실거래 판단 전에 KIS/IBKR 소스로 승격할 것.
- 공휴일 캘린더 미구현 — 휴장일엔 가격이 안 움직여 알람이 나가지 않으므로 무해하지만,
  전일 종가 기반 프리미엄이 계속 찍히는 건 감안하고 볼 것.
- 이 봇은 **주문을 넣지 않는다**. 실행(Phase 3)은 docs/06의 3a/3b/3c 경로 검증 후.
