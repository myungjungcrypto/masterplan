"""SK하이닉스 ADR(SKHY) ↔ 본주(000660) 프리미엄 알람봇 — docs/06 Phase 1.

사용:
    python main.py             # 라이브 (ADR 상장 후)
    python main.py --dry-run   # 상장 전 테스트: ADR 가격을 목값으로 합성
    python main.py --once      # 1틱만 실행하고 종료 (동작 확인용)
"""
import argparse
import logging
import time
from datetime import datetime, timezone

from config import Config
from premium import compute
from sessions import KST, current_session
from store import Store
from alerts import AlertEngine
from notify import Notifier
import sources

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("main")


def tick(cfg, store, engine, notifier, session: str, dry_run: bool) -> None:
    krx = sources.fetch_krx(cfg)
    fx = sources.fetch_usdkrw(cfg)
    adr = sources.fetch_adr_mock(cfg, krx, fx) if dry_run else sources.fetch_adr(cfg)

    now = datetime.now(timezone.utc)
    kst_date = now.astimezone(KST).strftime("%Y-%m-%d")
    anchor = store.get_fx_anchor(kst_date)
    if anchor is None:
        store.set_fx_anchor(kst_date, fx)
        anchor = fx

    snap = compute(now.timestamp(), session, krx, adr, fx, anchor,
                   cfg.adr_ratio, cfg.all_in_cost_pct)
    store.record(snap)
    log.info("[%s] KRX %.0f | ADR %.2f | FX %.1f | prem %+.2f%% (fx %+.2f) | edge %+.2f%%",
             session, krx, adr, fx, snap.premium_pct, snap.fx_contrib_pct, snap.net_edge_pct)

    for msg in engine.check(snap):
        notifier.send(("[DRY-RUN] " if dry_run else "") + msg)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true", help="ADR 가격 목값 합성 (상장 전 테스트)")
    p.add_argument("--once", action="store_true", help="1틱만 실행")
    args = p.parse_args()

    cfg = Config()
    store = Store(cfg.db_path)
    engine = AlertEngine(cfg, store)
    notifier = Notifier(cfg)
    log.info("start: ADR=%s ratio=%s cost=%.2f%% dry_run=%s",
             cfg.adr_symbol, cfg.adr_ratio, cfg.all_in_cost_pct, args.dry_run)

    while True:
        session, interval = current_session(datetime.now(timezone.utc), cfg)
        if session != "IDLE" or args.once:
            try:
                tick(cfg, store, engine, notifier, session, args.dry_run)
            except Exception as e:
                log.error("tick failed: %s", e)
        else:
            log.info("both markets closed, sleeping %ss", interval)
        if args.once:
            break
        time.sleep(interval)


if __name__ == "__main__":
    main()
