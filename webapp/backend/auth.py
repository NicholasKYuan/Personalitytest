#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
auth.py — 微信小程序登录与 token 鉴权

流程：wx.login() 取 code → POST /api/login → code2session 换 openid → 生成
opaque token（存 users 表，7 天有效）→ 后续接口带 Authorization: Bearer <token>。

依赖：httpx（已有）、db.py
"""
import os
import time
import secrets
import hashlib
import httpx

from db import get_db, now, dumps, loads

WX_APPID = os.getenv("WX_APPID", "wx7e7815dfe8498fc6")
WX_SECRET = os.getenv("WX_SECRET", "")
CODEX2SESSION_URL = "https://api.weixin.qq.com/sns/jscode2session"
TOKEN_TTL = 7 * 24 * 3600  # 7 天


def _code2session(code: str) -> dict:
    """调用微信 code2session，返回 {openid, session_key} 或 {errcode, errmsg}。

    PAY_MOCK=1 且 code 以 MOCK 开头时，跳过真实调用，返回确定性 mock openid
    （便于无小程序登录凭证时联调全流程）。
    """
    if os.getenv("PAY_MOCK", "0") == "1" and code.startswith("MOCK"):
        openid = "mock_openid_" + hashlib.md5(code.encode()).hexdigest()[:16]
        return {"openid": openid, "session_key": "mock_session_key"}
    params = {
        "appid": WX_APPID,
        "secret": WX_SECRET,
        "js_code": code,
        "grant_type": "authorization_code",
    }
    resp = httpx.get(CODEX2SESSION_URL, params=params, timeout=10)
    data = resp.json()
    if data.get("errcode"):
        raise ValueError(f"code2session 失败: errcode={data.get('errcode')} errmsg={data.get('errmsg')}")
    return data


def login_with_code(code: str, nickname: str = "", avatar_url: str = "") -> dict:
    """code2session + upsert 用户 + 颁发 token。

    Returns:
        {"token": str, "openid": str, "is_new": bool, "expires_in": int}
    """
    data = _code2session(code)
    openid = data["openid"]
    t = now()
    is_new = False

    with get_db() as db:
        row = db.execute("SELECT openid FROM users WHERE openid=?", (openid,)).fetchone()
        if row is None:
            is_new = True
            db.execute(
                "INSERT INTO users (openid, nickname, avatar_url, created_at, last_login_at) VALUES (?,?,?,?,?)",
                (openid, nickname, avatar_url, t, t),
            )
        else:
            db.execute(
                "UPDATE users SET last_login_at=?, nickname=CASE WHEN ?<>'' THEN ? ELSE nickname END, "
                "avatar_url=CASE WHEN ?<>'' THEN ? ELSE avatar_url END WHERE openid=?",
                (t, nickname, nickname, avatar_url, avatar_url, openid),
            )

        token = secrets.token_urlsafe(32)
        expire = t + TOKEN_TTL
        db.execute("UPDATE users SET token=?, token_expire_at=? WHERE openid=?", (token, expire, openid))

    return {"token": token, "openid": openid, "is_new": is_new, "expires_in": TOKEN_TTL}


def verify_token(token: str):
    """校验 token，返回 openid；无效返回 None。"""
    if not token:
        return None
    with get_db() as db:
        row = db.execute(
            "SELECT openid, token_expire_at FROM users WHERE token=? AND token_expire_at>?",
            (token, now()),
        ).fetchone()
    return row["openid"] if row else None


def get_openid_from_authorization(header: str):
    """解析 Authorization: Bearer <token>，返回 openid 或 None。"""
    if not header:
        return None
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        return None
    return verify_token(token.strip())
