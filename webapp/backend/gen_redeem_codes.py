#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量生成 100 个兑换密钥，写入 app.db 并输出文档。
"""
import random
import sqlite3
import time
from pathlib import Path

BACKEND_DIR = Path(__file__).parent.resolve()
DB_PATH = BACKEND_DIR / "app.db"
DOC_PATH = BACKEND_DIR.parent.parent / "兑换密钥清单.md"

REDEEM_CHARS = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # 去除易混淆字符 O/0/I/1
COUNT = 100
BATCH_LABEL = "首批合作方赠品"
EXPIRES_DAYS = 0  # 0 = 永不过期


def gen_code() -> str:
    part = lambda: "".join(random.choices(REDEEM_CHARS, k=4))
    return f"XY-{part()}-{part()}-{part()}"


def main():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")

    # 确保表存在
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS redeem_codes (
            code             TEXT PRIMARY KEY,
            batch_label      TEXT    DEFAULT '',
            status           TEXT    DEFAULT 'unused',
            created_at       REAL    DEFAULT 0,
            expires_at       REAL    DEFAULT 0,
            used_at          REAL    DEFAULT 0,
            used_by_openid   TEXT    DEFAULT '',
            used_session_id  TEXT    DEFAULT '',
            created_by       TEXT    DEFAULT ''
        );
    """)

    now = time.time()
    expires_at = 0 if EXPIRES_DAYS == 0 else int(now) + EXPIRES_DAYS * 86400

    codes = []
    for _ in range(COUNT):
        while True:
            code = gen_code()
            exists = conn.execute("SELECT 1 FROM redeem_codes WHERE code=?", (code,)).fetchone()
            if not exists:
                break
        conn.execute(
            "INSERT INTO redeem_codes (code, batch_label, status, created_at, expires_at, created_by) "
            "VALUES (?,?,?,?,?,?)",
            (code, BATCH_LABEL, "unused", now, expires_at, "admin"),
        )
        codes.append(code)

    conn.commit()
    conn.close()

    # 生成文档
    lines = [
        "# 兑换密钥清单",
        "",
        f"**批次**: {BATCH_LABEL}",
        f"**生成时间**: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(now))}",
        f"**数量**: {COUNT} 个",
        f"**有效期**: {'永不过期' if EXPIRES_DAYS == 0 else f'{EXPIRES_DAYS} 天'}",
        f"**状态**: 每个密钥仅限使用一次，使用后自动作废",
        "",
        "## 密钥列表",
        "",
        "| 序号 | 兑换码 | 状态 |",
        "|------|--------|------|",
    ]
    for i, code in enumerate(codes, 1):
        lines.append(f"| {i:03d} | `{code}` | 未使用 |")

    lines.extend([
        "",
        "## 使用说明",
        "",
        "1. 将兑换码发送给合作方",
        "2. 合作方在小程序中完成测评答题后，在付费页面选择「兑换密钥」",
        "3. 输入兑换码即可免费解锁详细报告",
        "4. 每个兑换码仅可使用一次，使用后自动失效",
        "",
        "## 管理端查询",
        "",
        "```bash",
        f'curl "https://你的域名/api/admin/redeem/list?admin_secret=YOUR_SECRET"',
        "```",
        "",
        "## 注意事项",
        "",
        "- 请妥善保管密钥，遗失无法补发",
        "- 密钥不绑定用户，任何用户均可使用",
        "- 如需停用未使用的密钥，可在数据库中将 status 改为 disabled",
    ])

    DOC_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"✅ 已生成 {len(codes)} 个兑换码并写入数据库")
    print(f"📄 文档已保存至: {DOC_PATH}")
    print()
    print("前5个兑换码预览:")
    for c in codes[:5]:
        print(f"  {c}")


if __name__ == "__main__":
    main()
