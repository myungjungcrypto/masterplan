"""시장 세션 스케줄러 — KRX와 나스닥은 장이 전혀 안 겹친다 (docs/06 2절).

세션별 폴링 주기를 반환하고, 두 시장 다 닫혀 있으면 idle.
휴장일(공휴일)은 미처리 — 가격이 안 움직이면 알람도 안 나가므로 무해.
"""
from datetime import datetime, time
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")
NYT = ZoneInfo("America/New_York")


def current_session(now_utc: datetime, cfg) -> tuple[str, int]:
    """(세션 이름, 폴링 주기 초). 세션 없음 → ("IDLE", poll_idle_s)."""
    kst = now_utc.astimezone(KST)
    if kst.weekday() < 5 and time(9, 0) <= kst.time() <= time(15, 30):
        return "KRX", cfg.poll_fast_s

    nyt = now_utc.astimezone(NYT)
    if nyt.weekday() < 5:
        t = nyt.time()
        if time(9, 30) <= t < time(16, 0):
            return "US_REG", cfg.poll_fast_s
        if time(4, 0) <= t < time(9, 30):
            return "US_PRE", cfg.poll_slow_s
        if time(16, 0) <= t < time(20, 0):
            return "US_POST", cfg.poll_slow_s

    return "IDLE", cfg.poll_idle_s
