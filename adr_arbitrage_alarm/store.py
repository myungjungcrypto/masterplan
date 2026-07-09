"""SQLite 영속화 — hl_lighter_arbitrage 패턴. 틱 기록 + 당일 앵커 환율."""
import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS ticks (
    ts REAL NOT NULL,
    session TEXT NOT NULL,
    krx_price REAL NOT NULL,
    adr_price REAL NOT NULL,
    usdkrw REAL NOT NULL,
    parity_krw REAL NOT NULL,
    premium_pct REAL NOT NULL,
    fx_contrib_pct REAL NOT NULL,
    net_edge_pct REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_ticks_ts ON ticks (ts);
CREATE TABLE IF NOT EXISTS fx_anchor (
    kst_date TEXT PRIMARY KEY,
    usdkrw REAL NOT NULL
);
"""


class Store:
    def __init__(self, path: str):
        self.conn = sqlite3.connect(path)
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def record(self, s) -> None:
        self.conn.execute(
            "INSERT INTO ticks VALUES (?,?,?,?,?,?,?,?,?)",
            (s.ts, s.session, s.krx_price, s.adr_price, s.usdkrw,
             s.parity_krw, s.premium_pct, s.fx_contrib_pct, s.net_edge_pct))
        self.conn.commit()

    def premium_at(self, ts_before: float) -> float | None:
        """ts_before 이전 가장 최근 틱의 프리미엄 (급변 감지용)."""
        row = self.conn.execute(
            "SELECT premium_pct FROM ticks WHERE ts <= ? ORDER BY ts DESC LIMIT 1",
            (ts_before,)).fetchone()
        return row[0] if row else None

    def get_fx_anchor(self, kst_date: str) -> float | None:
        row = self.conn.execute(
            "SELECT usdkrw FROM fx_anchor WHERE kst_date = ?", (kst_date,)).fetchone()
        return row[0] if row else None

    def set_fx_anchor(self, kst_date: str, usdkrw: float) -> None:
        self.conn.execute(
            "INSERT OR IGNORE INTO fx_anchor VALUES (?,?)", (kst_date, usdkrw))
        self.conn.commit()
