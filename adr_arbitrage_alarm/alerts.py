"""알람 규칙 + 쿨다운 — docs/06 Phase 1.

- INFO   : |premium| ≥ info_threshold (기본 2%), 쿨다운 30분
- ACTION : net_edge ≥ action_threshold (기본 1%), 쿨다운 10분
- RAPID  : 1시간 내 프리미엄 ±rapid_move 이상 급변, 쿨다운 30분
"""
import time


class AlertEngine:
    def __init__(self, cfg, store):
        self.cfg = cfg
        self.store = store
        self._last_sent: dict[str, float] = {}

    def _ready(self, kind: str, cooldown_s: int) -> bool:
        return time.time() - self._last_sent.get(kind, 0) >= cooldown_s

    def _mark(self, kind: str) -> None:
        self._last_sent[kind] = time.time()

    def check(self, s) -> list[str]:
        cfg = self.cfg
        msgs: list[str] = []
        base = (f"KRX {s.krx_price:,.0f}원 | ADR ${s.adr_price:,.2f} "
                f"(패리티 {s.parity_krw:,.0f}원) | USDKRW {s.usdkrw:,.1f}\n"
                f"프리미엄 {s.premium_pct:+.2f}% (FX 기여 {s.fx_contrib_pct:+.2f}%p) | "
                f"순엣지 {s.net_edge_pct:+.2f}% (비용 {cfg.all_in_cost_pct}%) | 세션 {s.session}")

        if s.net_edge_pct >= cfg.action_threshold_pct and self._ready("action", cfg.action_cooldown_s):
            msgs.append(f"🚨 [ACTION] SKHY 순엣지 {s.net_edge_pct:+.2f}%\n{s.direction()}\n{base}")
            self._mark("action")

        if abs(s.premium_pct) >= cfg.info_threshold_pct and self._ready("info", cfg.info_cooldown_s):
            msgs.append(f"ℹ️ [INFO] SKHY 프리미엄 {s.premium_pct:+.2f}%\n{base}")
            self._mark("info")

        prev = self.store.premium_at(s.ts - cfg.rapid_window_min * 60)
        if (prev is not None and abs(s.premium_pct - prev) >= cfg.rapid_move_pct
                and self._ready("rapid", cfg.rapid_cooldown_s)):
            msgs.append(f"⚡ [RAPID] 프리미엄 급변 {prev:+.2f}% → {s.premium_pct:+.2f}% "
                        f"({cfg.rapid_window_min}분)\n뉴스/전환규정 발표 확인 필요\n{base}")
            self._mark("rapid")

        return msgs
