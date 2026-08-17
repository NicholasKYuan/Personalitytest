#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
xpay.py — 微信小程序虚拟支付集成

能力：
- create_payment_params(session_key, out_trade_no, product_id, buy_quantity)
    → 生成 wx.requestVirtualPayment 所需参数（paySig + signature）
- parse_callback(xml_or_json)
    → 解析发货推送 xpay_goods_deliver_notify
- verify_callback_sig(body, sig, appkey)
    → 验证回调签名

依赖：无外部依赖（标准库 hmac/hashlib/json/xml）
配置（环境变量）：
    XPAY_OFFER_ID     — 虚拟支付 offerId（MP后台→虚拟支付→基本配置）
    XPAY_APP_KEY      — 虚拟支付 AppKey（沙箱/现网，由 XPAY_ENV 决定）
    XPAY_ENV          — 0=现网, 1=沙箱（默认1沙箱）
    XPAY_PRODUCT_ID   — 道具ID（MP后台→道具管理）
    PAY_MOCK=1        — mock模式，返回假签名，配合 /api/pay/mock_notify 使用
"""
import os
import hmac
import hashlib
import json
import time
import uuid
import logging

log = logging.getLogger("xpay")

# ---------------------------------------------------------------------------
# 配置
# ---------------------------------------------------------------------------
OFFER_ID = os.getenv("XPAY_OFFER_ID", "")
APP_KEY = os.getenv("XPAY_APP_KEY", "")
ENV = int(os.getenv("XPAY_ENV", "1"))  # 默认沙箱
PRODUCT_ID = os.getenv("XPAY_PRODUCT_ID", "report_unlock")
PAY_MOCK = os.getenv("PAY_MOCK", "0") == "1"


def is_mock() -> bool:
    return PAY_MOCK


def _calc_pay_sig(uri: str, sign_data: str, appkey: str) -> str:
    """支付签名: HMAC-SHA256(appkey, uri + '&' + signData)"""
    msg = f"{uri}&{sign_data}"
    return hmac.new(
        appkey.encode("utf-8"), msg.encode("utf-8"), hashlib.sha256
    ).hexdigest()


def _calc_signature(sign_data: str, session_key: str) -> str:
    """用户态签名: HMAC-SHA256(sessionKey, signData)"""
    return hmac.new(
        session_key.encode("utf-8"), sign_data.encode("utf-8"), hashlib.sha256
    ).hexdigest()


def _build_sign_data(params: dict) -> str:
    """将参数按 key 排序后拼接成 key=value&key=value 格式。"""
    sorted_keys = sorted(params.keys())
    return "&".join(f"{k}={params[k]}" for k in sorted_keys)


def create_payment_params(
    session_key: str,
    out_trade_no: str,
    product_id: str = "",
    buy_quantity: int = 1,
) -> dict:
    """生成 wx.requestVirtualPayment 所需的完整参数。

    返回:
        {
            "offerId": str,
            "env": int,
            "buyQuantity": int,
            "outTradeNo": str,
            "productId": str,
            "paySig": str,
            "signature": str,
        }

    mock 模式下返回 paySig="MOCK_SIGN"，前端跳过真实调起。
    """
    pid = product_id or PRODUCT_ID

    if PAY_MOCK:
        return {
            "offerId": OFFER_ID or "mock_offer",
            "env": ENV,
            "buyQuantity": buy_quantity,
            "outTradeNo": out_trade_no,
            "productId": pid,
            "paySig": "MOCK_SIGN",
            "signature": "MOCK_SIGN",
        }

    if not (OFFER_ID and APP_KEY):
        raise RuntimeError("虚拟支付未配置：请设置 XPAY_OFFER_ID 和 XPAY_APP_KEY")

    if not session_key or session_key == "mock_session_key":
        raise RuntimeError("session_key 缺失，请重新登录后重试")

    # 签名参数（不含 paySig / signature）
    sign_params = {
        "offerId": OFFER_ID,
        "env": ENV,
        "buyQuantity": buy_quantity,
        "outTradeNo": out_trade_no,
        "productId": pid,
    }

    sign_data = _build_sign_data(sign_params)

    pay_sig = _calc_pay_sig("requestVirtualPayment", sign_data, APP_KEY)
    signature = _calc_signature(sign_data, session_key)

    return {
        "offerId": OFFER_ID,
        "env": ENV,
        "buyQuantity": buy_quantity,
        "outTradeNo": out_trade_no,
        "productId": pid,
        "paySig": pay_sig,
        "signature": signature,
    }


# ---------------------------------------------------------------------------
# 回调处理
# ---------------------------------------------------------------------------
def parse_callback(body: str, content_type: str = "") -> dict:
    """解析虚拟支付发货推送 xpay_goods_deliver_notify。

    支持 XML 和 JSON 两种格式。返回统一 dict:
        {
            "openid": str,
            "out_trade_no": str,
            "product_id": str,
            "quantity": int,
            "actual_price": int,  # 分
            "attach": str,
            "env": int,
            "mch_order_no": str,
            "transaction_id": str,
            "paid_time": int,
        }
    """
    body = body.strip()

    # XML 格式
    if body.startswith("<") or "xml" in content_type.lower():
        import xml.etree.ElementTree as ET
        root = ET.fromstring(body)
        data = {child.tag: child.text or "" for child in root}
    else:
        # JSON 格式
        data = json.loads(body)

    # 统一字段名
    goods_info = {}
    wechat_pay_info = {}

    # XML: 直接在顶层；JSON: 可能有嵌套
    if isinstance(data.get("GoodsInfo"), dict):
        goods_info = data["GoodsInfo"]
    elif isinstance(data.get("GoodsInfo"), str):
        goods_info = json.loads(data["GoodsInfo"])
    else:
        # XML 解析后 GoodsInfo 子节点
        goods_info = data

    if isinstance(data.get("WeChatPayInfo"), dict):
        wechat_pay_info = data["WeChatPayInfo"]
    elif isinstance(data.get("WeChatPayInfo"), str):
        wechat_pay_info = json.loads(data["WeChatPayInfo"])
    else:
        wechat_pay_info = data

    return {
        "openid": data.get("OpenId", data.get("openid", "")),
        "out_trade_no": data.get("OutTradeNo", data.get("out_trade_no", "")),
        "product_id": goods_info.get("ProductId", data.get("ProductId", "")),
        "quantity": int(goods_info.get("Quantity", data.get("Quantity", 1))),
        "actual_price": int(goods_info.get("ActualPrice", data.get("ActualPrice", 0))),
        "attach": goods_info.get("Attach", data.get("Attach", "")),
        "env": int(data.get("Env", data.get("env", 0))),
        "mch_order_no": wechat_pay_info.get("MchOrderNo", data.get("MchOrderNo", "")),
        "transaction_id": wechat_pay_info.get("TransactionId", data.get("TransactionId", "")),
        "paid_time": int(wechat_pay_info.get("PaidTime", data.get("PaidTime", 0))),
    }


def make_callback_response(err_code: int = 0, err_msg: str = "success") -> dict:
    """构造回调响应（JSON 格式）。"""
    return {"ErrCode": err_code, "ErrMsg": err_msg}


def verify_callback(body: str, sig: str, appkey: str = "") -> bool:
    """验证回调签名。

    微信推送的签名方式：HMAC-SHA256(appkey, body)
    其中 appkey 取决于 Env 字段（沙箱/现网）。
    """
    key = appkey or APP_KEY
    if not key:
        log.warning("回调验签跳过：未配置 XPAY_APP_KEY")
        return True  # 未配置时跳过验证（开发期）

    expected = hmac.new(
        key.encode("utf-8"), body.encode("utf-8"), hashlib.sha256
    ).hexdigest()

    if expected != sig:
        log.warning("回调验签失败: expected=%s, got=%s", expected[:16], (sig or "")[:16])
        return False
    return True
