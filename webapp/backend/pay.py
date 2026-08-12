#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pay.py — 微信支付 v3（JSAPI）集成 + 开发期 Mock 模式

能力：
- create_jsapi_order(openid, out_trade_no, amount_fen, description)
    → 统一下单，返回 wx.requestPayment 所需 pay_params
- parse_and_verify_notify(raw_body, headers)
    → 验签 + AES-256-GCM 解密回调，返回 {out_trade_no, transaction_id, trade_state, amount_total}
- PAY_MOCK=1 时：下单返回假参数；配合 POST /api/pay/mock_notify 模拟支付成功，方便无真实商户号联调。

依赖：cryptography（已安装）、httpx、db.py
配置（环境变量）：
    WX_APPID / MCH_ID / MCH_SERIAL_NO / MCH_PRIVATE_KEY_PATH / WXPAY_API_V3_KEY
    WXPAY_NOTIFY_URL / WXPAY_PLATFORM_CERT_PATH / PAY_MOCK
"""
import os
import json
import time
import base64
import uuid
import logging

import httpx
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

log = logging.getLogger("pay")

WX_APPID = os.getenv("WX_APPID", "wx95a916e6c9b3d382")
MCH_ID = os.getenv("MCH_ID", "")
MCH_SERIAL_NO = os.getenv("MCH_SERIAL_NO", "")
MCH_PRIVATE_KEY_PATH = os.getenv("MCH_PRIVATE_KEY_PATH", "./certs/apiclient_key.pem")
WXPAY_API_V3_KEY = os.getenv("WXPAY_API_V3_KEY", "")
WXPAY_NOTIFY_URL = os.getenv("WXPAY_NOTIFY_URL", "")
WXPAY_PLATFORM_CERT_PATH = os.getenv("WXPAY_PLATFORM_CERT_PATH", "")
PAY_MOCK = os.getenv("PAY_MOCK", "0") == "1"

API_BASE = "https://api.mch.weixin.qq.com"
JSAPI_ORDER_URL = API_BASE + "/v3/pay/transactions/jsapi"
CERT_URL = API_BASE + "/v3/certificates"


# ---------------------------------------------------------------------------
# 内部工具
# ---------------------------------------------------------------------------
def _load_private_key() -> bytes:
    if not os.path.exists(MCH_PRIVATE_KEY_PATH):
        raise FileNotFoundError(f"商户私钥不存在: {MCH_PRIVATE_KEY_PATH}")
    with open(MCH_PRIVATE_KEY_PATH, "rb") as f:
        return serialization.load_pem_private_key(f.read(), password=None)


def _rsa_sign(key, message: str) -> str:
    sig = key.sign(message.encode("utf-8"), padding.PKCS1v15(), hashes.SHA256())
    return base64.b64encode(sig).decode("utf-8")


def _auth_header(method: str, url_path: str, body: str) -> str:
    """构造微信支付 v3 请求签名头。"""
    nonce = uuid.uuid4().hex
    timestamp = str(int(time.time()))
    sign_str = f"{method}\n{url_path}\n{timestamp}\n{nonce}\n{body}\n"
    signature = _rsa_sign(_load_private_key(), sign_str)
    return (
        'WECHATPAY2-SHA256-RSA2048 '
        f'mchid="{MCH_ID}",nonce_str="{nonce}",signature="{signature}",'
        f'timestamp="{timestamp}",serial_no="{MCH_SERIAL_NO}"'
    )


def _request(method: str, url: str, payload: dict = None) -> dict:
    body = json.dumps(payload, ensure_ascii=False) if payload is not None else ""
    path = url.replace(API_BASE, "")
    headers = {
        "Authorization": _auth_header(method.upper(), path, body),
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "xingyao-personality-test/1.0",
    }
    resp = httpx.request(method.upper(), url, content=body.encode("utf-8"), headers=headers, timeout=15)
    if resp.status_code != 200:
        raise RuntimeError(f"微信支付接口失败 {resp.status_code}: {resp.text[:500]}")
    return resp.json()


# ---------------------------------------------------------------------------
# 平台证书（验签 + 回调解密）
# ---------------------------------------------------------------------------
_platform_cert_cache = None


def _decrypt_resource(resource: dict) -> dict:
    """用 APIv3 密钥解密回调/证书接口的 resource。"""
    if not WXPAY_API_V3_KEY:
        raise RuntimeError("缺少 WXPAY_API_V3_KEY")
    key = WXPAY_API_V3_KEY.encode("utf-8")
    aesgcm = AESGCM(key)
    plain = aesgcm.decrypt(
        resource["nonce"].encode("utf-8"),
        base64.b64decode(resource["ciphertext"]),
        resource.get("associated_data", "").encode("utf-8"),
    )
    return json.loads(plain.decode("utf-8"))


def _fetch_platform_cert() -> bytes:
    """从微信下载平台证书并解密，返回 PEM 字节；结果缓存在进程内。"""
    global _platform_cert_cache
    if _platform_cert_cache is not None:
        return _platform_cert_cache
    data = _request("GET", CERT_URL)
    for cert in data.get("data", []):
        try:
            plain = _decrypt_resource(cert["encrypt_certificate"])
            pem = plain["certificate"].encode("utf-8")
            _platform_cert_cache = pem
            return pem
        except Exception:
            continue
    raise RuntimeError("无法获取微信支付平台证书")


def _platform_cert() -> bytes:
    if WXPAY_PLATFORM_CERT_PATH and os.path.exists(WXPAY_PLATFORM_CERT_PATH):
        with open(WXPAY_PLATFORM_CERT_PATH, "rb") as f:
            return f.read()
    return _fetch_platform_cert()


def _verify_signature(raw_body: str, headers: dict) -> bool:
    """验证回调签名。headers 为小写键名 dict。"""
    ts = headers.get("wechatpay-timestamp", "")
    nonce = headers.get("wechatpay-nonce", "")
    signature = headers.get("wechatpay-signature", "")
    if not (ts and nonce and signature):
        return False
    pem = _platform_cert()
    pub = serialization.load_pem_public_key(pem)
    message = f"{ts}\n{nonce}\n{raw_body}\n".encode("utf-8")
    try:
        pub.verify(base64.b64decode(signature), message, padding.PKCS1v15(), hashes.SHA256())
        return True
    except Exception as e:
        log.warning("回调验签失败: %s", e)
        return False


# ---------------------------------------------------------------------------
# 对外接口
# ---------------------------------------------------------------------------
def is_mock() -> bool:
    return PAY_MOCK


def create_jsapi_order(openid: str, out_trade_no: str, amount_fen: int,
                       description: str = "星耀启程人格测评深度报告") -> dict:
    """统一下单，返回 wx.requestPayment 调起参数 pay_params。"""
    if PAY_MOCK:
        # ---- 开发/联调模式：不真实调用微信，返回假 pay_params ----
        return {
            "appId": WX_APPID,
            "timeStamp": str(int(time.time())),
            "nonceStr": uuid.uuid4().hex,
            "package": f"prepay_id=mock_{out_trade_no}",
            "signType": "RSA",
            "paySign": "MOCK_SIGN",
        }

    if not (MCH_ID and MCH_SERIAL_NO and WXPAY_API_V3_KEY and WXPAY_NOTIFY_URL):
        raise RuntimeError("微信支付未配置完整（MCH_ID/MCH_SERIAL_NO/WXPAY_API_V3_KEY/WXPAY_NOTIFY_URL）")

    payload = {
        "appid": WX_APPID,
        "mchid": MCH_ID,
        "description": description,
        "out_trade_no": out_trade_no,
        "notify_url": WXPAY_NOTIFY_URL,
        "amount": {"total": amount_fen, "currency": "CNY"},
        "payer": {"openid": openid},
    }
    data = _request("POST", JSAPI_ORDER_URL, payload)
    prepay_id = data["prepay_id"]

    # 生成 JSAPI 调起参数并签名
    time_stamp = str(int(time.time()))
    nonce_str = uuid.uuid4().hex
    package = f"prepay_id={prepay_id}"
    sign_str = f"{WX_APPID}\n{time_stamp}\n{nonce_str}\n{package}\n"
    pay_sign = _rsa_sign(_load_private_key(), sign_str)

    return {
        "appId": WX_APPID,
        "timeStamp": time_stamp,
        "nonceStr": nonce_str,
        "package": package,
        "signType": "RSA",
        "paySign": pay_sign,
    }


def parse_and_verify_notify(raw_body: str, headers: dict) -> dict:
    """解析微信支付回调。

    验签通过后解密 resource，返回:
        {"out_trade_no", "transaction_id", "trade_state", "amount_total"}
    """
    if PAY_MOCK:
        # mock 模式下回调由 /api/pay/mock_notify 构造，直接走解密路径
        pass
    elif not _verify_signature(raw_body, headers):
        raise PermissionError("微信支付回调验签失败")

    body = json.loads(raw_body)
    if body.get("event_type") == "TRANSACTION.SUCCESS":
        plain = _decrypt_resource(body["resource"])
        return {
            "out_trade_no": plain["out_trade_no"],
            "transaction_id": plain.get("transaction_id", ""),
            "trade_state": plain.get("trade_state", "SUCCESS"),
            "amount_total": (plain.get("amount") or {}).get("total", 0),
        }
    raise ValueError(f"不支持的 event_type: {body.get('event_type')}")
