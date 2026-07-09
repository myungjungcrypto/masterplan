"""네트워크 없이 핵심 로직 검증: 프리미엄 수식, FX 분해, 알람 규칙, 세션, 저장.

python test_offline.py
"""
import os
import time
from datetime import datetime, timezone

from config import Config
from premium import compute
from sessions import current_session
from store import Store
from alerts import AlertEngine


def approx(a, b, tol=1e-6):
    assert abs(a - b) < tol, f"{a} != {b}"


cfg = Config()
assert cfg.adr_ratio == 0.1 and cfg.adr_symbol == "SKHY"

# --- 프리미엄 수식: KRX 2,000,000원, FX 1,400 → 패리티가격 ADR $142.857...
# ADR $150이면 parity_krw = 150*1400/0.1 = 2,100,000 → 프리미엄 +5%
s = compute(ts=1000.0, session="US_REG", krx_price=2_000_000, adr_price=150.0,
            usdkrw=1400.0, anchor_fx=1400.0, ratio=0.1, all_in_cost_pct=0.5)
approx(s.parity_krw, 2_100_000)
approx(s.premium_pct, 5.0)
approx(s.fx_contrib_pct, 0.0)
approx(s.net_edge_pct, 4.5)
assert "고평가" in s.direction()

# --- FX 분해: 환율만 1400→1428(+2%)이면 프리미엄 +2.1%p 전부 FX 기여
s2 = compute(1000.0, "US_REG", 2_000_000, 150.0, usdkrw=1428.0, anchor_fx=1400.0,
             ratio=0.1, all_in_cost_pct=0.5)
approx(s2.premium_pct - s2.fx_contrib_pct, 5.0)  # FX 제거 시 원래 5%

# --- 디스카운트 방향
s3 = compute(1000.0, "KRX", 2_000_000, 130.0, 1400.0, 1400.0, 0.1, 0.5)
assert s3.premium_pct < 0 and "저평가" in s3.direction()

# --- 세션 스케줄러 (2026-07-09 목요일)
kx, _ = current_session(datetime(2026, 7, 9, 1, 0, tzinfo=timezone.utc), cfg)   # 10:00 KST
assert kx == "KRX"
us, _ = current_session(datetime(2026, 7, 9, 15, 0, tzinfo=timezone.utc), cfg)  # 11:00 NYT
assert us == "US_REG"
idle, _ = current_session(datetime(2026, 7, 9, 7, 0, tzinfo=timezone.utc), cfg)  # 16:00 KST / 03:00 NYT
assert idle == "IDLE"
wknd, _ = current_session(datetime(2026, 7, 11, 1, 0, tzinfo=timezone.utc), cfg)  # 토요일
assert wknd == "IDLE"

# --- 저장 + 알람 (임시 DB)
db = "/tmp/test_adr.sqlite3"
if os.path.exists(db):
    os.remove(db)
store = Store(db)
engine = AlertEngine(cfg, store)

now = time.time()
# 1시간 전 틱: 프리미엄 1% (급변 비교 기준)
old = compute(now - 3700, "US_REG", 2_000_000, 144.428, 1400.0, 1400.0, 0.1, 0.5)
store.record(old)
approx(store.premium_at(now - 3600), old.premium_pct, 1e-3)

# 현재 틱: 프리미엄 +5% → ACTION(엣지 4.5%) + INFO(|5|≥2) + RAPID(1%→5% 급변) 모두 발동
cur = compute(now, "US_REG", 2_000_000, 150.0, 1400.0, 1400.0, 0.1, 0.5)
store.record(cur)
msgs = engine.check(cur)
kinds = "".join(msgs)
assert len(msgs) == 3, f"expected 3 alerts, got {len(msgs)}: {msgs}"
assert "ACTION" in kinds and "INFO" in kinds and "RAPID" in kinds

# 쿨다운: 즉시 재체크 시 아무것도 안 나감
assert engine.check(cur) == []

# FX 앵커 영속화
store.set_fx_anchor("2026-07-09", 1400.0)
approx(store.get_fx_anchor("2026-07-09"), 1400.0)
store.set_fx_anchor("2026-07-09", 9999.0)  # INSERT OR IGNORE — 최초값 유지
approx(store.get_fx_anchor("2026-07-09"), 1400.0)

print("ALL OFFLINE TESTS PASSED")
