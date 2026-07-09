"""프리미엄 계산 — docs/06 1절 수식 그대로.

parity_KRW = ADR_USD × USDKRW ÷ ratio       (ADR을 본주 1주 기준 원화로 환산)
premium_%  = (parity_KRW − KRX_KRW) / KRX_KRW × 100
net_edge_% = |premium_%| − allInCost_%
fx_contrib = 당일 앵커 환율 대비 환율 변동이 프리미엄에 기여한 부분(%p)
"""
from dataclasses import dataclass


@dataclass
class Snapshot:
    ts: float
    session: str
    krx_price: float
    adr_price: float
    usdkrw: float
    parity_krw: float
    premium_pct: float
    fx_contrib_pct: float
    net_edge_pct: float

    def direction(self) -> str:
        return "ADR 고평가 (본주→ADR 스위치 / ADR 매도측 유리)" if self.premium_pct > 0 \
            else "ADR 저평가 (ADR→본주 스위치 / ADR 매수측 유리)"


def compute(ts: float, session: str, krx_price: float, adr_price: float,
            usdkrw: float, anchor_fx: float, ratio: float, all_in_cost_pct: float) -> Snapshot:
    parity = adr_price * usdkrw / ratio
    premium = (parity - krx_price) / krx_price * 100

    parity_anchor = adr_price * anchor_fx / ratio
    premium_anchor = (parity_anchor - krx_price) / krx_price * 100
    fx_contrib = premium - premium_anchor

    net_edge = abs(premium) - all_in_cost_pct
    return Snapshot(ts, session, krx_price, adr_price, usdkrw,
                    parity, premium, fx_contrib, net_edge)
