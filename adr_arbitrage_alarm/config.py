"""설정 — 전부 환경변수로 오버라이드 가능. 파라미터 출처는 README 참고."""
import os
from dataclasses import dataclass, field


def _f(key: str, default: float) -> float:
    return float(os.environ.get(key, default))


def _s(key: str, default: str) -> str:
    return os.environ.get(key, default)


@dataclass
class Config:
    # --- 종목 파라미터 (2026-07-09 언론 보도 기준, 상장 공시로 최종 확인할 것) ---
    krx_code: str = field(default_factory=lambda: _s("KRX_CODE", "000660"))
    krx_yahoo_symbol: str = field(default_factory=lambda: _s("KRX_YAHOO_SYMBOL", "000660.KS"))
    adr_symbol: str = field(default_factory=lambda: _s("ADR_SYMBOL", "SKHY"))
    fx_symbol: str = field(default_factory=lambda: _s("FX_SYMBOL", "KRW=X"))
    # 1 ADR이 대표하는 본주 수. SKHY는 1 ADR = 0.1주 (본주 1주 = ADR 10주).
    adr_ratio: float = field(default_factory=lambda: _f("ADR_RATIO", 0.1))

    # --- 비용 모델 (%) — docs/06 4절. 실측 후 교체 ---
    # 왕복 올인비용: KRX 매도세 0.15 + 위탁수수료 + 미국 수수료 + FX 스프레드 + 슬리피지
    all_in_cost_pct: float = field(default_factory=lambda: _f("ALL_IN_COST_PCT", 0.5))

    # --- 알람 임계값 (%) — docs/06 Phase 1 초기값 ---
    info_threshold_pct: float = field(default_factory=lambda: _f("INFO_THRESHOLD_PCT", 2.0))
    action_threshold_pct: float = field(default_factory=lambda: _f("ACTION_THRESHOLD_PCT", 1.0))
    rapid_move_pct: float = field(default_factory=lambda: _f("RAPID_MOVE_PCT", 1.5))
    rapid_window_min: int = field(default_factory=lambda: int(_f("RAPID_WINDOW_MIN", 60)))
    info_cooldown_s: int = field(default_factory=lambda: int(_f("INFO_COOLDOWN_S", 1800)))
    action_cooldown_s: int = field(default_factory=lambda: int(_f("ACTION_COOLDOWN_S", 600)))
    rapid_cooldown_s: int = field(default_factory=lambda: int(_f("RAPID_COOLDOWN_S", 1800)))

    # --- 폴링 주기 (초) ---
    poll_fast_s: int = field(default_factory=lambda: int(_f("POLL_FAST_S", 15)))
    poll_slow_s: int = field(default_factory=lambda: int(_f("POLL_SLOW_S", 60)))
    poll_idle_s: int = field(default_factory=lambda: int(_f("POLL_IDLE_S", 300)))

    # --- 인프라 ---
    db_path: str = field(default_factory=lambda: _s("DB_PATH", "adr_premium.sqlite3"))
    telegram_bot_token: str = field(default_factory=lambda: _s("TELEGRAM_BOT_TOKEN", ""))
    telegram_chat_id: str = field(default_factory=lambda: _s("TELEGRAM_CHAT_ID", ""))

    # --- dry-run: ADR 상장 전 목값 테스트 (목표 프리미엄 %, 노이즈 %p) ---
    mock_premium_pct: float = field(default_factory=lambda: _f("MOCK_PREMIUM_PCT", 3.0))
    mock_noise_pct: float = field(default_factory=lambda: _f("MOCK_NOISE_PCT", 0.8))
