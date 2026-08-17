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

WX_APPID = os.getenv("WX_APPID", "wx95a916e6c9b3d382")
WX_SECRET = os.getenv("WX_SECRET", "")
CODEX2SESSION_URL = "https://api.weixin.qq.com/sns/jscode2session"
TOKEN_TTL = 7 * 24 * 3600  # 7 天


def _code2session(code: str) -> dict:
    """调用微信 code2session，返回 {openid, session_key} 或 {errcode, errmsg}。

    PAY_MOCK=1 时跳过真实调用，返回确定性 mock openid
    （便于无小程序登录凭证或云托管网络受限时联调全流程）。
    """
    pay_mock = os.getenv("PAY_MOCK", "0") == "1"

    # PAY_MOCK 模式：直接返回 mock openid，不调用微信 API
    # 所有 mock 登录共用同一 openid（固定），避免 token 过期重登后 403
    # 测试脚本用 e2e_ 前缀的 code 可获得独立 openid，不干扰小程序用户
    if pay_mock:
        if code.startswith("e2e_"):
            openid = f"mock_openid_e2e_{code[4:16]}"
        else:
            openid = "mock_openid_default_user"
        return {"openid": openid, "session_key": "mock_session_key"}

    # 真实模式：调用微信 code2session
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
    session_key = data.get("session_key", "")
    t = now()
    is_new = False
    pay_mock = os.getenv("PAY_MOCK", "0") == "1"

    with get_db() as db:
        row = db.execute("SELECT openid FROM users WHERE openid=%s", (openid,)).fetchone()
        if row is None:
            is_new = True
            db.execute(
                "INSERT INTO users (openid, nickname, avatar_url, created_at, last_login_at, session_key) VALUES (%s,%s,%s,%s,%s,%s)",
                (openid, nickname, avatar_url, t, t, session_key),
            )
        else:
            db.execute(
                "UPDATE users SET last_login_at=%s, nickname=CASE WHEN %s<>'' THEN %s ELSE nickname END, "
                "avatar_url=CASE WHEN %s<>'' THEN %s ELSE avatar_url END, "
                "session_key=%s WHERE openid=%s",
                (t, nickname, nickname, avatar_url, avatar_url, session_key, openid),
            )

        # mock 模式：复用已有有效 token，避免多客户端互相覆盖
        if pay_mock:
            existing = db.execute(
                "SELECT token, token_expire_at FROM users WHERE openid=%s AND token IS NOT NULL AND token_expire_at>%s",
                (openid, t),
            ).fetchone()
            if existing:
                return {"token": existing["token"], "openid": openid, "is_new": is_new, "expires_in": int(existing["token_expire_at"] - t)}

        token = secrets.token_urlsafe(32)
        expire = t + TOKEN_TTL
        db.execute("UPDATE users SET token=%s, token_expire_at=%s WHERE openid=%s", (token, expire, openid))

    return {"token": token, "openid": openid, "is_new": is_new, "expires_in": TOKEN_TTL}


def verify_token(token: str):
    """校验 token，返回 openid；无效返回 None。"""
    if not token:
        return None
    with get_db() as db:
        row = db.execute(
            "SELECT openid, token_expire_at FROM users WHERE token=%s AND token_expire_at>%s",
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


def get_session_key(openid: str) -> str:
    """查询用户最新的 session_key（虚拟支付签名需要）。"""
    with get_db() as db:
        row = db.execute("SELECT session_key FROM users WHERE openid=%s", (openid,)).fetchone()
    return row["session_key"] if row else ""
