#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
db.py — SQLite 数据层（users / sessions / orders）

初期使用 SQLite（单文件、零运维），上线可切换 MySQL（结构兼容，表定义见
miniprogram/BACKEND_SPEC.md §5）。JSON 字段一律存 TEXT。
"""
import os
import sqlite3
import threading
import time
from pathlib import Path

BACKEND_DIR = Path(__file__).parent.resolve()
DEFAULT_DB = str(BACKEND_DIR / "app.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    openid           TEXT PRIMARY KEY,
    nickname         TEXT    DEFAULT '',
    avatar_url       TEXT    DEFAULT '',
    token            TEXT    DEFAULT '',
    token_expire_at  REAL    DEFAULT 0,
    created_at       REAL    DEFAULT 0,
    last_login_at    REAL    DEFAULT 0
);

CREATE TABLE IF NOT EXISTS sessions (
    session_id   TEXT PRIMARY KEY,
    openid       TEXT NOT NULL DEFAULT '',   -- 小程序会话绑定 openid；Web 遗留会话为空串
    profile      TEXT NOT NULL,   -- JSON
    questions    TEXT NOT NULL,   -- JSON（完整题，含 score，仅服务端）
    answers      TEXT,            -- JSON
    results      TEXT,            -- JSON（四体系评分）
    free_summary TEXT,
    status       TEXT DEFAULT 'created',  -- created | answered | generating | ready | failed
    ai_sections  TEXT,            -- JSON（付费正文，服务端保护）
    ai_error     TEXT,
    created_at   REAL DEFAULT 0,
    updated_at   REAL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_sessions_openid ON sessions(openid);

CREATE TABLE IF NOT EXISTS orders (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    out_trade_no   TEXT UNIQUE,
    session_id     TEXT NOT NULL,
    openid         TEXT NOT NULL,
    amount_fen     INTEGER DEFAULT 2990,   -- 固定 29.90 元
    status         TEXT DEFAULT 'pending', -- pending | paid | closed | refunded
    prepay_id      TEXT DEFAULT '',
    transaction_id TEXT DEFAULT '',
    notify_raw     TEXT,                   -- 微信回调原文（对账用）
    created_at     REAL DEFAULT 0,
    paid_at        REAL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_orders_session    ON orders(session_id);
CREATE INDEX IF NOT EXISTS idx_orders_openid_st  ON orders(openid, status);

CREATE TABLE IF NOT EXISTS redeem_codes (
    code             TEXT PRIMARY KEY,
    batch_label      TEXT    DEFAULT '',
    status           TEXT    DEFAULT 'unused',   -- unused | used | disabled
    created_at       REAL    DEFAULT 0,
    expires_at       REAL    DEFAULT 0,           -- 0 = 永不过期
    used_at          REAL    DEFAULT 0,
    used_by_openid   TEXT    DEFAULT '',
    used_session_id  TEXT    DEFAULT '',
    created_by       TEXT    DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_redeem_status ON redeem_codes(status);
"""

_lock = threading.Lock()


def _db_path() -> str:
    url = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB}")
    if url.startswith("sqlite:///"):
        return url[len("sqlite:///"):]
    if url.startswith("sqlite:"):
        return url[len("sqlite:"):]
    raise RuntimeError(f"暂仅支持 SQLite，DATABASE_URL={url}")


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(_db_path(), timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def now() -> float:
    return time.time()


def init_db():
    with _lock, get_db() as db:
        db.executescript(SCHEMA)


# ---------------------------------------------------------------------------
# 通用 JSON 读写辅助
# ---------------------------------------------------------------------------
def dumps(obj) -> str:
    import json
    return json.dumps(obj, ensure_ascii=False)


def loads(s, default=None):
    import json
    if not s:
        return default
    try:
        return json.loads(s)
    except (json.JSONDecodeError, TypeError):
        return default
