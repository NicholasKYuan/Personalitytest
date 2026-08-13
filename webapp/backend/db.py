#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
db.py — MySQL 数据层（users / sessions / orders / redeem_codes）

使用 pymysql 驱动，通过环境变量配置连接：
  MYSQL_HOST / MYSQL_PORT / MYSQL_USER / MYSQL_PASSWORD / MYSQL_DATABASE

接口与原 SQLite 版本兼容：get_db() 返回带 execute() 方法的上下文管理器。
"""
import os
import time
from contextlib import contextmanager

import pymysql

# ---------------------------------------------------------------------------
# MySQL 兼容的建表语句（inline index，无需 CREATE INDEX IF NOT EXISTS）
# ---------------------------------------------------------------------------
SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    openid           VARCHAR(128) PRIMARY KEY,
    nickname         VARCHAR(255) DEFAULT '',
    avatar_url       TEXT,
    token            VARCHAR(255) DEFAULT '',
    token_expire_at  DOUBLE DEFAULT 0,
    created_at       DOUBLE DEFAULT 0,
    last_login_at    DOUBLE DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS sessions (
    session_id   VARCHAR(128) PRIMARY KEY,
    openid       VARCHAR(128) NOT NULL DEFAULT '',
    profile      TEXT NOT NULL,
    questions    MEDIUMTEXT NOT NULL,
    answers      MEDIUMTEXT,
    results      MEDIUMTEXT,
    free_summary TEXT,
    status       VARCHAR(32) DEFAULT 'created',
    ai_sections  MEDIUMTEXT,
    ai_error     TEXT,
    regenerate_count INT DEFAULT 0,
    created_at   DOUBLE DEFAULT 0,
    updated_at   DOUBLE DEFAULT 0,
    INDEX idx_sessions_openid (openid)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS orders (
    id             INT PRIMARY KEY AUTO_INCREMENT,
    out_trade_no   VARCHAR(64) UNIQUE,
    session_id     VARCHAR(128) NOT NULL,
    openid         VARCHAR(128) NOT NULL,
    amount_fen     INT DEFAULT 2990,
    status         VARCHAR(32) DEFAULT 'pending',
    prepay_id      VARCHAR(128) DEFAULT '',
    transaction_id VARCHAR(64) DEFAULT '',
    notify_raw     TEXT,
    created_at     DOUBLE DEFAULT 0,
    paid_at        DOUBLE DEFAULT 0,
    INDEX idx_orders_session (session_id),
    INDEX idx_orders_openid_st (openid, status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS redeem_codes (
    code             VARCHAR(64) PRIMARY KEY,
    batch_label      VARCHAR(128) DEFAULT '',
    status           VARCHAR(32) DEFAULT 'unused',
    created_at       DOUBLE DEFAULT 0,
    expires_at       DOUBLE DEFAULT 0,
    used_at          DOUBLE DEFAULT 0,
    used_by_openid   VARCHAR(128) DEFAULT '',
    used_session_id  VARCHAR(128) DEFAULT '',
    created_by       VARCHAR(128) DEFAULT '',
    INDEX idx_redeem_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""


class _DBWrapper:
    """模拟 sqlite3.Connection.execute() 接口，简化迁移。"""

    def __init__(self, conn):
        self._conn = conn

    def execute(self, sql, params=()):
        cur = self._conn.cursor()
        cur.execute(sql, params)
        return cur

    def executescript(self, script):
        """执行多条 SQL（按 ; 分割）。"""
        cur = self._conn.cursor()
        for stmt in script.split(";"):
            stmt = stmt.strip()
            if stmt:
                cur.execute(stmt)
        cur.close()


@contextmanager
def get_db():
    """获取数据库连接（上下文管理器）。

    用法与 SQLite 版完全一致：
        with get_db() as db:
            row = db.execute("SELECT ... WHERE id=%s", (id,)).fetchone()
    """
    conn = pymysql.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", ""),
        database=os.getenv("MYSQL_DATABASE", "personality"),
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
        connect_timeout=10,
        read_timeout=30,
        write_timeout=30,
    )
    wrapper = _DBWrapper(conn)
    try:
        yield wrapper
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def now() -> float:
    return time.time()


def init_db():
    """建表（幂等）+ 安全添加新列（兼容已有数据库）。"""
    with get_db() as db:
        db.executescript(SCHEMA)
        # 安全添加 regenerate_count 列（MySQL 不支持 ADD COLUMN IF NOT EXISTS）
        try:
            db.execute("ALTER TABLE sessions ADD COLUMN regenerate_count INT DEFAULT 0")
        except Exception:
            pass  # 列已存在，忽略


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
