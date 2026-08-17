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
配置（环境变量，.env 或云托管控制台）：
    XPAY_OFFER_ID     — 虚拟支付 offerId（MP后台→虚拟支付→基本配置）
    XPAY_APP_KEY      — 虚拟支付 AppKey（沙箱/现网，由 XPAY_ENV 决定）
    XPAY_ENV          — 0=现网, 1=沙箱（默认1沙箱）
    XPAY_PRODUCT_ID   — 道具ID（MP后台→虚拟支付→道具管理）
    XPAY_GOODS_PRICE  — 道具单价（分，默认2990，须与MP后台道具价格一致）
    PAY_MOCK=1        — mock模式，返回假签名，配合 /api/pay/mock_notify 使用
"""
import os
import hmac
import hashlib
import json
import logging

log = logging.getLogger("xpay")

# ---------------------------------------------------------------------------
# 配置
# ---------------------------------------------------------------------------
OFFER_ID = os.getenv("XPAY_OFFER_ID", "")
APP_KEY = os.getenv("XPAY_APP_KEY", "")
ENV = int(os.getenv("XPAY_ENV", "1"))  # 默认沙箱
PRODUCT_ID = os.getenv("XPAY_PRODUCT_ID", "report_unlock")
GOODS_PRICE = int(os.getenv("XPAY_GOODS_PRICE", "2990"))
PAY_MOCK = os.getenv("PAY_MOCK", "0") == "1"
# 道具直购模式（MP后台道具管理创建的道具）
MODE = "short_series_goods"


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
    """序列化 signData 为紧凑 JSON 字符串。

    注意：前端必须原样传递该字符串（不可重新 JSON.stringify），
    否则 paySig/signature 校验失败（错误码 -15005/-15006/-15016）。
    """
    return json.dumps(params, separators=(",", ":"), ensure_ascii=False)


def create_payment_params(
    session_key: str,
    out_trade_no: str,
    attach: str = "",
    product_id: str = "",
    buy_quantity: int = 1,
) -> dict:
    """生成 wx.requestVirtualPayment 所需的完整参数。

    参数:
        session_key   — 用户登录 session_key（用户态签名用）
        out_trade_no  — 业务订单号（8-32位，数字/字母/_-|*@，不能以_开头）
        attach        — 透传数据（发货通知时原样返回），这里传 session_id
        product_id    — 道具ID，缺省用 PRODUCT_ID
        buy_quantity  — 购买数量

    返回:
        {
            "mode": "short_series_goods",
            "signData": '{"offerId":...}',  # JSON 字符串，前端原样传递
            "paySig": str,
            "signature": str,
        }

    mock 模式下返回 paySig="MOCK_SIGN"，前端跳过真实调起。
    """
    pid = product_id or PRODUCT_ID

    sign_params = {
        "offerId": OFFER_ID or "mock_offer",
        "buyQuantity": buy_quantity,
        "env": ENV,
        "currencyType": "CNY",
        "productId": pid,
        "goodsPrice": GOODS_PRICE,
        "outTradeNo": out_trade_no,
        "attach": attach or out_trade_no,
    }
    sign_data = _build_sign_data(sign_params)

    if PAY_MOCK:
        return {
            "mode": MODE,
            "signData": sign_data,
            "paySig": "MOCK_SIGN",
            "signature": "MOCK_SIGN",
        }

    if not (OFFER_ID and APP_KEY):
        raise RuntimeError("虚拟支付未配置：请设置 XPAY_OFFER_ID 和 XPAY_APP_KEY")

    if not session_key or session_key == "mock_session_key":
        raise RuntimeError("session_key 缺失，请重新登录后重试")

    pay_sig = _calc_pay_sig("requestVirtualPayment", sign_data, APP_KEY)
    signature = _calc_signature(sign_data, session_key)

    return {
        "mode": MODE,
        "signData": sign_data,
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


def make_callback_response(err_code: int = 0, err_msg: str = "success", xml: bool = False):
    """构造回调响应。微信要求：JSON 对 JSON、XML 对 XML。"""
    if xml:
        return f"<xml><ErrCode>{err_code}</ErrCode><ErrMsg><![CDATA[{err_msg}]]></ErrMsg></xml>"
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
