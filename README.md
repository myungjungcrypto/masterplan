# Crypto Master AI — Masterplan

`myungjungcrypto`가 흩어서 만들어 둔 크립토 트레이딩/모니터링 레포들을
**하나의 자율 트레이딩 시스템(Crypto Master AI)** 으로 통합·확장하기 위한 마스터플랜.

> 한 줄 요약: 신호(아비트라지 알람) → 비용검증(slippage) → 실행(autotrading) →
> 리스크 가드(perpdex_assets) → 펀딩 최적화(fundingrate_auto) 부품은 이미 다 있다.
> **빠진 건 이 부품들을 묶는 "중앙 두뇌(Brain)"와 실거래 연결이다.** 그걸 만든다.

---

## 이 문서들의 목적

당신은 이미 27개 레포에 걸쳐 트레이딩 스택의 거의 모든 조각을 만들어 놨다.
문제는 (1) 대부분이 *알람만 보내고 주문은 안 넣는다*, (2) 서로 연결돼 있지 않고
텔레그램/스프레드시트로 흩어져 있다, (3) 자본배분·복리·전략우선순위를 정하는
중앙 의사결정 로직이 없다는 것.

이 마스터플랜은 그 조각들을 **단일 자동매매 시스템**으로 묶고, 기존 전략을
응용해 수익원을 더 공격적으로 늘리는 단계별 계획이다.

## 문서 인덱스

| 문서 | 내용 |
|---|---|
| [docs/01-current-assets.md](docs/01-current-assets.md) | 현재 보유 자산(레포) 인벤토리와 역할 분류 |
| [docs/02-architecture.md](docs/02-architecture.md) | Master AI 시스템 아키텍처 (6계층) |
| [docs/03-strategy-playbook.md](docs/03-strategy-playbook.md) | 전략 카탈로그 — 기존 전략 + 신규/응용 전략, 진입조건·임계값 |
| [docs/04-risk-capital-ops.md](docs/04-risk-capital-ops.md) | 리스크 프레임워크, 자본배분, 운영, 컴플라이언스 |
| [docs/05-roadmap.md](docs/05-roadmap.md) | 단계별 구축 로드맵 (Phase 0~4) |
| [docs/06-operator-profile.md](docs/06-operator-profile.md) | 실전 수익 구조 분석 → 우선순위 재조정 (2026-08) |
| [docs/07-extended-inventory.md](docs/07-extended-inventory.md) | 확장 인벤토리 — 신규/비공개 레포 12개 분석 (KRX 베이시스·김프·상장 스나이퍼·라이브 갭봇) |

## 핵심 원칙

1. **엣지는 측정된 것만 믿는다.** 모든 진입은 `예상 순익(net bps) = 총스프레드 − 올인비용(slippage+fee) − 펀딩비용 − 리스크프리미엄 > 0` 일 때만.
2. **델타 중립 우선.** 방향성 베팅이 아니라 시장간/펀딩 차익이 본진. 변동성에 잡아먹히지 않는다.
3. **자동화하되 킬스위치를 둔다.** AI가 24/7 굴리되, 마진·손실·이상징후 시 즉시 디레버리지/정지.
4. **복리.** 수익은 자동 재투자하되 OI 캡(예: deposit의 5배) 안에서.
5. **합법적 엣지만.** 시장조작·스푸핑·워시트레이딩·내부정보 금지. 차익거래·마켓메이킹·펀딩캐리·실행속도 우위만 추구.

## 빠른 시작 (요약 로드맵)

- **Phase 0** — 공통 코어 라이브러리 추출(거래소 클라이언트·심볼맵·비용모델 통일).
- **Phase 1** — Signal Bus: 흩어진 알람들을 표준 신호 포맷으로 한 곳에 모은다.
- **Phase 2** — Brain: 신호를 순익 기준으로 랭킹하고 자본을 배분하는 중앙 결정엔진.
- **Phase 3** — 실행 연결: `autotrading_btc_eth` 엔진을 Brain에 붙여 paper→live 전환.
- **Phase 4** — 전략 확장: 펀딩캐리·김치프리미엄·마켓메이킹·신규상장 차익 추가.

자세한 내용은 각 문서 참고.
