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
- decrypt_message / verify_url / handle_msg
    → 支持微信通用消息推送（开发管理→开发设置→消息推送）

依赖：无外部依赖（标准库 hmac/hashlib/json/xml/base64/crypto 通过 cryptography）
配置（环境变量，.env 或云托管控制台）：
    XPAY_OFFER_ID     — 虚拟支付 offerId（MP后台→虚拟支付→基本配置）
    XPAY_APP_KEY      — 虚拟支付 AppKey（沙箱/现网，由 XPAY_ENV 决定）
    XPAY_ENV          — 0=现网, 1=沙箱（默认1沙箱）
    XPAY_PRODUCT_ID   — 道具ID（MP后台→虚拟支付→道具管理）
    XPAY_GOODS_PRICE  — 道具单价（分，默认2990，须与MP后台道具价格一致）
    MSG_TOKEN         — 消息推送 Token（开发管理→开发设置→消息推送 自定义）
    MSG_AES_KEY       — 消息推送 EncodingAESKey（43位Base64，解密用）
    PAY_MOCK=1        — mock模式，返回假签名，配合 /api/pay/mock_notify 使用
"""
import os
import hmac
import hashlib
import json
import base64
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
# 消息推送配置（开发管理→开发设置→消息推送）
MSG_TOKEN = os.getenv("MSG_TOKEN", "")
MSG_AES_KEY = os.getenv("MSG_AES_KEY", "")  # 43位Base64编码的EncodingAESKey
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


# ---------------------------------------------------------------------------
# 微信通用消息推送（开发管理 → 开发设置 → 消息推送）
# 文档：https://developers.weixin.qq.com/miniprogram/dev/framework/server-ability/message-push.html
# ---------------------------------------------------------------------------
def _sha1_sign(items: list) -> str:
    """按 token+timestamp+nonce+echostr 字典序排序后 sha1 加密。"""
    return hashlib.sha1("".join(sorted(items)).encode("utf-8")).hexdigest()


def verify_msg_signature(
    msg_signature: str, timestamp: str, nonce: str, encrypted: str
) -> bool:
    """验证消息推送签名：sha1(sort([token, timestamp, nonce, encrypted]))"""
    if not MSG_TOKEN:
        log.warning("消息推送验签跳过：未配置 MSG_TOKEN")
        return True
    expected = _sha1_sign([MSG_TOKEN, timestamp or "", nonce or "", encrypted or ""])
    return hmac.compare_digest(expected, (msg_signature or "").lower())


def verify_url(msg_signature: str, timestamp: str, nonce: str, echostr: str) -> str | None:
    """GET URL 校验：返回 echostr 表示通过，返回 None 表示失败。"""
    if not MSG_TOKEN:
        # 未配置 Token 时直接回显 echostr（开发模式）
        return echostr
    expected = _sha1_sign([MSG_TOKEN, timestamp or "", nonce or "", echostr or ""])
    if hmac.compare_digest(expected, (msg_signature or "").lower()):
        return echostr
    log.warning("URL 校验失败: expected=%s, got=%s", expected[:8], (msg_signature or "")[:8])
    return None


def _aes_key_bytes() -> bytes:
    """EncodingAESKey（43位Base64）→ AESKey（32字节） + IV（前16字节）"""
    aes_key_b64 = (MSG_AES_KEY + "=") if MSG_AES_KEY else ""
    if len(aes_key_b64) != 44:
        raise RuntimeError(f"MSG_AES_KEY 长度错误：期望43位Base64，实际{len(MSG_AES_KEY)}位")
    key = base64.b64decode(aes_key_b64)
    return key  # 后16字节作为 IV


def decrypt_message(encrypted_b64: str) -> str:
    """AES-256-CBC + PKCS#7 解密微信加密消息。

    解密后明文结构：random(16B) + msg_len(4B) + msg + receiveid
    返回纯 msg XML/JSON 字符串。
    """
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives import padding as sym_padding

    key = _aes_key_bytes()
    iv = key[16:32]
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    decryptor = cipher.decryptor()
    raw = base64.b64decode(encrypted_b64)
    padded = decryptor.update(raw) + decryptor.finalize()
    # 去除 PKCS#7 填充
    unpadder = sym_padding.PKCS7(128).unpadder()
    plain = unpadder.update(padded) + unpadder.finalize()
    # 去掉前16字节随机串和4字节长度
    if len(plain) < 20:
        raise ValueError("解密后消息长度异常")
    content = plain[16:]
    msg_len = int.from_bytes(content[:4], "big")
    msg = content[4:4 + msg_len].decode("utf-8")
    # 末尾的 receiveid（小程序原始ID）丢弃
    return msg


def encrypt_message(reply_xml: str, timestamp: str = "", nonce: str = "") -> str:
    """加密被动回复消息（AES-256-CBC + PKCS#7）。返回密文Base64。"""
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives import padding as sym_padding
    import os as _os
    import struct

    key = _aes_key_bytes()
    iv = key[16:32]
    # 拼接：random(16B) + msg_len(4B) + msg + receiveid
    receiveid = os.getenv("WECHAT_ORIGIN_ID", "gh_placeholder")
    msg_bytes = reply_xml.encode("utf-8")
    rand_bytes = _os.urandom(16)
    len_bytes = struct.pack(">I", len(msg_bytes))
    plain = rand_bytes + len_bytes + msg_bytes + receiveid.encode("utf-8")
    # PKCS#7 填充到16字节倍数
    padder = sym_padding.PKCS7(128).padder()
    padded = padder.update(plain) + padder.finalize()
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    encryptor = cipher.encryptor()
    enc = encryptor.update(padded) + encryptor.finalize()
    return base64.b64encode(enc).decode("utf-8")


def make_msg_signature(timestamp: str, nonce: str, encrypted: str) -> str:
    """生成消息推送签名（用于加密回复时拼装返回XML）。"""
    return _sha1_sign([MSG_TOKEN, timestamp or "", nonce or "", encrypted or ""])


def msg_push_ready() -> bool:
    """消息推送是否就绪（已配置 Token + AESKey）。"""
    return bool(MSG_TOKEN) and bool(MSG_AES_KEY)


def build_encrypted_reply_xml(reply_inner_xml: str) -> str:
    """构造被动回复的加密XML：<xml><Encrypt>...</Encrypt><MsgSignature>...</MsgSignature><TimeStamp>...</TimeStamp><Nonce>...</Nonce></xml>"""
    import time as _time
    import uuid as _uuid
    ts = str(int(_time.time()))
    nonce = _uuid.uuid4().hex
    enc = encrypt_message(reply_inner_xml, ts, nonce)
    sig = make_msg_signature(ts, nonce, enc)
    return (
        f"<xml>"
        f"<Encrypt><![CDATA[{enc}]]></Encrypt>"
        f"<MsgSignature><![CDATA[{sig}]]></MsgSignature>"
        f"<TimeStamp>{ts}</TimeStamp>"
        f"<Nonce><![CDATA[{nonce}]]></Nonce>"
        f"</xml>"
    )
