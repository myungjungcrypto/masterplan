"""가격 소스 — 무료 공개 엔드포인트(네이버/야후) 기반 MVP.

KRX 본주: 네이버 실시간 폴링 API(장중 실시간) → 실패 시 야후(지연) 폴백.
ADR / USDKRW: 야후 chart API (includePrePost=true → 프리·애프터 마지막 체결 포함).
추후 KIS OpenAPI / IBKR로 교체 시 이 모듈만 갈아끼우면 된다.
"""
import logging
import random

import requests

log = logging.getLogger("sources")

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) adr-arbitrage-alarm/0.1"}
TIMEOUT = 10


class SourceError(Exception):
    pass


def yahoo_last_price(symbol: str) -> float:
    """야후 chart API에서 프리/애프터 포함 마지막 체결가."""
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    params = {"interval": "1m", "range": "1d", "includePrePost": "true"}
    r = requests.get(url, params=params, headers=UA, timeout=TIMEOUT)
    r.raise_for_status()
    result = r.json().get("chart", {}).get("result")
    if not result:
        raise SourceError(f"yahoo: no chart result for {symbol}")
    res = result[0]
    closes = (res.get("indicators", {}).get("quote") or [{}])[0].get("close") or []
    last = next((c for c in reversed(closes) if c is not None), None)
    if last is None:
        last = res.get("meta", {}).get("regularMarketPrice")
    if last is None:
        raise SourceError(f"yahoo: no price for {symbol}")
    return float(last)


def naver_krx_price(code: str) -> float:
    """네이버 국내주식 실시간 폴링 API."""
    url = f"https://polling.finance.naver.com/api/realtime/domestic/stock/{code}"
    r = requests.get(url, headers=UA, timeout=TIMEOUT)
    r.raise_for_status()
    datas = r.json().get("datas") or []
    if not datas or "closePrice" not in datas[0]:
        raise SourceError(f"naver: no price for {code}")
    return float(str(datas[0]["closePrice"]).replace(",", ""))


def fetch_krx(cfg) -> float:
    try:
        return naver_krx_price(cfg.krx_code)
    except Exception as e:
        log.warning("naver KRX source failed (%s), falling back to yahoo", e)
        return yahoo_last_price(cfg.krx_yahoo_symbol)


def fetch_usdkrw(cfg) -> float:
    return yahoo_last_price(cfg.fx_symbol)


def fetch_adr(cfg) -> float:
    return yahoo_last_price(cfg.adr_symbol)


def fetch_adr_mock(cfg, krx_price: float, usdkrw: float) -> float:
    """상장 전 dry-run용: 목표 프리미엄 ± 노이즈로 ADR 가격을 합성."""
    premium = cfg.mock_premium_pct + random.uniform(-cfg.mock_noise_pct, cfg.mock_noise_pct)
    parity_krw = krx_price * (1 + premium / 100)
    return parity_krw * cfg.adr_ratio / usdkrw
