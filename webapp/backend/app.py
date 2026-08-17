#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app.py — 星耀启程人格测评 FastAPI 后端（Web + 微信小程序共用）

启动方式:
    cd webapp/backend
    uvicorn app:app --reload --port 8000

小程序新增接口（带 token 鉴权）:
    POST /api/login              code2session → openid → token
    POST /api/report/order       创建虚拟支付订单，返回 wx.requestVirtualPayment 参数
    POST /api/report/confirm_payment  客户端支付成功通知（服务端 query_order 核实，发货轮询分支）
    POST /api/xpay/notify        虚拟支付消息推送回调（备用，需配置 MSG_TOKEN/MSG_AES_KEY）
    POST /api/pay/mock_notify    开发期模拟支付成功（PAY_MOCK=1 时可用）
    GET  /api/report/status      轮询支付/报告状态
    POST /api/report/detail      支付成功后获取完整报告

兼容 Web 旧接口（保持原响应格式，不破坏 webapp/frontend）:
    POST /api/session  /api/submit  /api/analyze
    GET  /api/report/{session_id}
"""
import os
import sys
import json
import time
import random
import uuid
import string as _string
from pathlib import Path
from typing import Optional, List

from dotenv import load_dotenv
load_dotenv()  # 加载 .env 环境变量（云托管/Docker 部署用）

from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, Response
from pydantic import BaseModel

# ============================================================
# 路径配置
# ============================================================
BACKEND_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = BACKEND_DIR.parent.parent          # d:/workbuddy/2026-08-11-09-28-12/
SELECTOR_DIR = PROJECT_ROOT / "selector"
BANK_PATH = PROJECT_ROOT / "question-bank" / "items.jsonl"
WEBAPP_DIR = BACKEND_DIR.parent                    # webapp/
FRONTEND_DIR = WEBAPP_DIR / "frontend"              # webapp/frontend/
SESSION_DIR = BACKEND_DIR / "sessions"              # 遗留 JSON 会话（只读兼容）

SESSION_DIR.mkdir(exist_ok=True)

# 导入 selector（复用现有筛选器）
sys.path.insert(0, str(SELECTOR_DIR))
from selector import select, load_bank
from scorer import score_answers, generate_free_summary
from ai_analyzer import generate_detailed_analysis
from report_generator import generate_report_html

# 数据层 / 认证 / 支付 / 报告服务
import db as database
import auth as wxauth
import pay as wxpay
import xpay as vpay
import report_service

database.init_db()

# ============================================================
# FastAPI 应用
# ============================================================
app = FastAPI(title="星耀启程人格测评", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局题库（启动时一次性加载）
BANK: list = []


@app.on_event("startup")
def startup_load_bank():
    global BANK
    BANK = load_bank(str(BANK_PATH))
    print(f"[startup] 题库加载完成: {len(BANK)} 题")


# ============================================================
# 请求/响应模型
# ============================================================
class ProfileRequest(BaseModel):
    name: Optional[str] = None
    age: int
    gender: Optional[str] = None
    role: str
    purpose: str
    current_state: Optional[str] = None
    decision_horizon: Optional[str] = None
    birth_date: Optional[str] = None


class AnswerItem(BaseModel):
    question_id: str
    option_index: int


class SubmitRequest(BaseModel):
    session_id: str
    answers: List[AnswerItem]


class AnalyzeRequest(BaseModel):
    session_id: str


class LoginRequest(BaseModel):
    code: str
    nickname: Optional[str] = ""
    avatar_url: Optional[str] = ""


class OrderRequest(BaseModel):
    session_id: str


class ConfirmPayRequest(BaseModel):
    session_id: str = ""
    out_trade_no: str = ""


class StatusRequest(BaseModel):
    session_id: str


class RedeemRequest(BaseModel):
    session_id: str
    code: str


class RegenerateRequest(BaseModel):
    session_id: str


class RedeemGenRequest(BaseModel):
    count: int = 1
    batch_label: str = ""
    expires_days: int = 0          # 0 = 永不过期
    username: str = ""
    password: str = ""


# ============================================================
# 辅助函数
# ============================================================
def strip_scores(questions: list) -> list:
    """移除题目 options 中的 score 字段，只保留 text。前端不应看到分数信息。"""
    stripped = []
    for q in questions:
        q_copy = {k: v for k, v in q.items() if k != "options"}
        q_copy["options"] = [{"text": opt["text"]} for opt in q["options"]]
        stripped.append(q_copy)
    return stripped


# ---------- 会话存取（优先 SQLite，兼容遗留 JSON 文件） ----------
def save_session(session_id: str, data: dict):
    with database.get_db() as db:
        db.execute(
            """INSERT INTO sessions (session_id, openid, profile, questions, answers, results,
                                    free_summary, status, ai_sections, ai_error, created_at, updated_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
               ON DUPLICATE KEY UPDATE
                 openid=VALUES(openid), profile=VALUES(profile), questions=VALUES(questions),
                 answers=VALUES(answers), results=VALUES(results), free_summary=VALUES(free_summary),
                 status=VALUES(status), ai_sections=VALUES(ai_sections), ai_error=VALUES(ai_error),
                 updated_at=VALUES(updated_at)""",
            (
                session_id,
                data.get("openid") or "",
                database.dumps(data.get("profile", {})),
                database.dumps(data.get("questions", [])),
                database.dumps(data.get("answers")),
                database.dumps(data.get("results")),
                data.get("free_summary"),
                data.get("status", "created"),
                database.dumps(data.get("ai_sections")),
                data.get("ai_error"),
                data.get("created_at") or database.now(),
                database.now(),
            ),
        )


def load_session(session_id: str) -> dict:
    """加载会话。优先 SQLite；遗留 JSON 文件作为只读回退。"""
    with database.get_db() as db:
        row = db.execute("SELECT * FROM sessions WHERE session_id=%s", (session_id,)).fetchone()
    if row is not None:
        return {
            "session_id": row["session_id"],
            "openid": row["openid"] or None,
            "profile": database.loads(row["profile"], {}),
            "questions": database.loads(row["questions"], []),
            "answers": database.loads(row["answers"]),
            "results": database.loads(row["results"]),
            "free_summary": row["free_summary"],
            "status": row["status"],
            "ai_sections": database.loads(row["ai_sections"]),
            "ai_error": row["ai_error"],
            "regenerate_count": row["regenerate_count"] if "regenerate_count" in row.keys() else 0,
        }

    # 遗留 JSON 文件回退
    path = SESSION_DIR / f"{session_id}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    raise FileNotFoundError(f"会话不存在: {session_id}")


def _get_openid(request: Request) -> Optional[str]:
    return wxauth.get_openid_from_authorization(request.headers.get("Authorization", ""))


def _require_openid(request: Request) -> str:
    openid = _get_openid(request)
    if not openid:
        raise HTTPException(status_code=401, detail="未登录或登录已过期")
    return openid


def _owns_session(openid: str, session: dict):
    """校验会话归属（仅当会话绑定了 openid 时校验）。

    PAY_MOCK 模式下，所有 mock_openid_* 视为同一用户，
    避免旧 mock openid 的会话在新部署后 403。
    """
    sess_openid = session.get("openid")
    if not sess_openid:
        return
    if sess_openid == openid:
        return
    # mock 模式：新旧 mock openid 都视为同一用户
    pay_mock = os.getenv("PAY_MOCK", "0") == "1"
    if pay_mock and sess_openid.startswith("mock_openid_") and openid.startswith("mock_openid_"):
        return
    raise HTTPException(status_code=403, detail="无权访问该会话")


def _require_paid(session_id: str, openid: str):
    """校验该会话已支付（小程序会话必须付费才能取 AI 内容）。

    PAY_MOCK 模式下，所有 mock_openid_* 视为同一用户。
    """
    pay_mock = os.getenv("PAY_MOCK", "0") == "1"
    with database.get_db() as db:
        if pay_mock and openid.startswith("mock_openid_"):
            o = db.execute(
                "SELECT status FROM orders WHERE session_id=%s AND openid LIKE 'mock_openid_%%' ORDER BY id DESC LIMIT 1",
                (session_id,),
            ).fetchone()
        else:
            o = db.execute(
                "SELECT status FROM orders WHERE session_id=%s AND openid=%s ORDER BY id DESC LIMIT 1",
                (session_id, openid),
            ).fetchone()
    if o is None or o["status"] != "paid":
        raise HTTPException(status_code=403, detail="请先完成支付解锁深度报告")


def _out_trade_no() -> str:
    """生成商户订单号（≤32 位）。"""
    return f"SX{int(time.time())}{random.randint(100000, 999999)}"


# ============================================================
# 微信登录
# ============================================================
@app.post("/api/login")
def login(req: LoginRequest):
    """code2session → openid → 颁发 token。"""
    try:
        data = wxauth.login_with_code(req.code, req.nickname or "", req.avatar_url or "")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"登录内部错误: {e}")
    return {"code": 0, "message": "ok", "data": data}


# ============================================================
# 兼容 Web 旧接口（保持原始响应格式）
# ============================================================
@app.post("/api/session")
def create_session(req: ProfileRequest, request: Request):
    """创建会话：接收 profile，筛选120题，返回题目列表（不含分数）。"""
    profile = req.model_dump()

    # 调用 selector 筛选120题
    questions = select(profile, BANK)

    session_id = str(uuid.uuid4())
    openid = _get_openid(request)  # 小程序带 token 时绑定 openid

    # 保存完整会话（含完整题目数据，用于后续评分）
    save_session(session_id, {
        "session_id": session_id,
        "openid": openid,
        "profile": profile,
        "questions": questions,
        "answers": None,
        "results": None,
        "status": "created",
    })

    # 返回给前端的题目不含 score 字段
    return {
        "session_id": session_id,
        "total": len(questions),
        "questions": strip_scores(questions),
    }


@app.post("/api/submit")
def submit_answers(req: SubmitRequest, request: Request):
    """提交答案：计算四体系结果，返回免费结果。"""
    try:
        session = load_session(req.session_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="会话不存在，请重新开始测评")

    openid = _get_openid(request)
    _owns_session(openid, session)

    questions = session["questions"]

    # 转换 answers 为 dict 列表
    answers = [a.model_dump() for a in req.answers]

    # 评分
    results = score_answers(questions, answers)
    free_summary = generate_free_summary(results, session["profile"])

    # 更新会话
    session["answers"] = answers
    session["results"] = results
    session["free_summary"] = free_summary
    session["status"] = "answered"
    save_session(req.session_id, session)

    return {
        "session_id": req.session_id,
        "results": results,
        "free_summary": free_summary,
        "detailed_available": True,
    }


@app.post("/api/analyze")
def analyze(req: AnalyzeRequest, request: Request):
    """深度分析：调用 Minimax M3 生成 AI 深度解读。

    小程序会话（已绑定 openid）必须已支付；Web 遗留会话（无 openid）保持原免费逻辑。
    """
    try:
        session = load_session(req.session_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="会话不存在")

    if not session.get("results"):
        raise HTTPException(status_code=400, detail="请先完成答题并提交")

    if session.get("openid"):
        _require_paid(req.session_id, session["openid"])

    results = session["results"]
    profile = session["profile"]

    analysis = generate_detailed_analysis(results, profile)

    # 缓存 AI 分析到会话
    session["ai_sections"] = analysis["sections"]
    session["status"] = "ready"
    save_session(req.session_id, session)

    return {
        "session_id": req.session_id,
        "detailed_analysis": analysis["detailed_analysis"],
        "sections": analysis["sections"],
    }


@app.get("/api/report/status")
def report_status(session_id: str = Query(...), request: Request = None):
    """查询支付/报告状态（前端轮询）。注意：本路由必须定义在 /api/report/{session_id} 之前。"""
    openid = _require_openid(request)
    try:
        session = load_session(session_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="会话不存在")
    _owns_session(openid, session)

    return {"code": 0, "message": "ok", "data": report_service.get_report_status(session_id)}


@app.get("/api/report/free")
def report_free(session_id: str = Query(...), request: Request = None):
    """获取免费预览结果（四体系分数 + 简述），无需付费。

    供测评记录页点入未付费会话时展示简要版报告。
    注意：本路由必须定义在 /api/report/{session_id} 之前。
    """
    openid = _require_openid(request)
    try:
        session = load_session(session_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="会话不存在")
    _owns_session(openid, session)

    if not session.get("results"):
        raise HTTPException(status_code=400, detail="请先完成答题并提交")

    with database.get_db() as db:
        o = db.execute(
            "SELECT status FROM orders WHERE session_id=%s ORDER BY id DESC LIMIT 1",
            (session_id,),
        ).fetchone()
    paid = bool(o and o["status"] == "paid")

    return {"code": 0, "message": "ok", "data": {
        "session_id": session_id,
        "results": session["results"],
        "free_summary": session.get("free_summary", ""),
        "profile": session.get("profile", {}),
        "paid": paid,
    }}


SESSION_TTL_UNPAID = 7 * 24 * 3600   # 未付费保留7天
SESSION_TTL_PAID = 30 * 24 * 3600    # 已付费保留30天


@app.get("/api/my/sessions")
def my_sessions(request: Request):
    """查询当前用户的测评记录（未付费7天内，已付费30天内）。"""
    openid = _require_openid(request)
    now_ts = time.time()
    max_cutoff = now_ts - SESSION_TTL_PAID  # 最长保留30天，先查出再按付费状态过滤

    with database.get_db() as db:
        # mock 模式下所有 mock_openid_* 视为同一用户
        pay_mock = os.getenv("PAY_MOCK", "0") == "1"
        if pay_mock and openid.startswith("mock_openid_"):
            rows = db.execute(
                """SELECT s.session_id, s.status, s.free_summary, s.created_at,
                          MAX(CASE WHEN o.status='paid' THEN 1 ELSE 0 END) AS has_paid
                   FROM sessions s
                   LEFT JOIN orders o ON o.session_id = s.session_id
                   WHERE s.openid LIKE 'mock_openid_%%' AND s.created_at > %s AND s.status IN ('answered','ready','failed')
                   GROUP BY s.session_id
                   ORDER BY s.created_at DESC""",
                (max_cutoff,),
            ).fetchall()
        else:
            rows = db.execute(
                """SELECT s.session_id, s.status, s.free_summary, s.created_at,
                          MAX(CASE WHEN o.status='paid' THEN 1 ELSE 0 END) AS has_paid
                   FROM sessions s
                   LEFT JOIN orders o ON o.session_id = s.session_id
                   WHERE s.openid = %s AND s.created_at > %s AND s.status IN ('answered','ready','failed')
                   GROUP BY s.session_id
                   ORDER BY s.created_at DESC""",
                (openid, max_cutoff),
            ).fetchall()

    records = []
    for r in rows:
        paid = bool(r["has_paid"])
        ttl = SESSION_TTL_PAID if paid else SESSION_TTL_UNPAID
        if r["created_at"] < now_ts - ttl:
            continue  # 已过期的跳过

        summary = r.get("free_summary") or ""
        preview = summary[:50] + "..." if len(summary) > 50 else summary
        records.append({
            "session_id": r["session_id"],
            "status": r["status"],
            "paid": paid,
            "preview": preview,
            "created_at": r["created_at"],
        })

    return {"code": 0, "message": "ok", "data": {"records": records, "total": len(records)}}


@app.get("/api/report/{session_id}")
def get_report(session_id: str, request: Request):
    """生成可下载的 HTML 报告文件（Web 兼容；小程序会话需已支付）。"""
    try:
        session = load_session(session_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="会话不存在")

    if not session.get("results"):
        raise HTTPException(status_code=400, detail="请先完成答题并提交")

    if session.get("openid"):
        _require_paid(session_id, session["openid"])

    results = session.get("results", {})
    profile = session.get("profile", {})
    if not profile:
        raise HTTPException(status_code=400, detail="会话缺少用户信息，请重新答题")

    # 如果已缓存 AI 分析，使用缓存；否则实时生成
    ai_sections = session.get("ai_sections", [])
    if not ai_sections:
        analysis = generate_detailed_analysis(results, profile)
        ai_sections = analysis["sections"]
        # 缓存到会话
        session["ai_sections"] = ai_sections
        session["status"] = "ready"
        save_session(session_id, session)

    html = generate_report_html(results, profile, ai_sections)
    return HTMLResponse(content=html)


# ============================================================
# 小程序付费接口（统一 {code, message, data} 包装）
# ============================================================
@app.post("/api/report/order")
def create_order(req: OrderRequest, request: Request):
    """创建虚拟支付订单，返回 wx.requestVirtualPayment 调起参数。

    幂等：同一 session 已有 pending 订单则复用；已 paid 直接返回已购状态。
    """
    openid = _require_openid(request)
    try:
        session = load_session(req.session_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="会话不存在")
    _owns_session(openid, session)
    if session.get("status") not in ("answered", "ready", "failed"):
        raise HTTPException(status_code=400, detail="请先完成答题再解锁报告")

    amount_fen = vpay.GOODS_PRICE

    with database.get_db() as db:
        existing = db.execute(
            "SELECT * FROM orders WHERE session_id=%s ORDER BY id DESC LIMIT 1", (req.session_id,)
        ).fetchone()

        if existing is not None:
            if existing["status"] == "paid":
                return {"code": 0, "message": "ok", "data": {
                    "order_id": existing["id"], "out_trade_no": existing["out_trade_no"],
                    "status": "paid", "pay_params": None,
                }}
            if existing["status"] == "pending":
                out_trade_no = existing["out_trade_no"]

                # 兜底核实：用户可能已支付但 confirm_payment 网络失败，
                # 重新进入支付页时先向微信查一次，已支付则直接放行
                if not vpay.is_mock():
                    try:
                        q = vpay.query_order(openid, out_trade_no)
                        if q.get("is_paid"):
                            db.execute(
                                "UPDATE orders SET status='paid', transaction_id=%s, paid_at=%s "
                                "WHERE id=%s AND status='pending'",
                                (q.get("wx_order_id", ""), database.now(), existing["id"]),
                            )
                            report_service.start_report_generation(req.session_id)
                            return {"code": 0, "message": "ok", "data": {
                                "order_id": existing["id"], "out_trade_no": out_trade_no,
                                "status": "paid", "pay_params": None,
                            }}
                    except Exception as e:
                        log_pay(f"[order] pending 兜底核实失败(忽略): {e}")

                # 复用原订单（重新调起支付）
                session_key = wxauth.get_session_key(openid)
                try:
                    pay_params = vpay.create_payment_params(
                        session_key, out_trade_no, attach=req.session_id)
                except RuntimeError as e:
                    raise HTTPException(status_code=400, detail=str(e))
                return {"code": 0, "message": "ok", "data": {
                    "order_id": existing["id"], "out_trade_no": out_trade_no,
                    "status": "pending", "pay_params": pay_params,
                }}
            # closed/refunded → 新建订单

        out_trade_no = _out_trade_no()

        # 虚拟支付模式
        if vpay.is_mock():
            pay_params = vpay.create_payment_params(
                "mock_session_key", out_trade_no, attach=req.session_id)
        else:
            session_key = wxauth.get_session_key(openid)
            if not session_key:
                raise HTTPException(status_code=400, detail="登录已过期，请重新进入小程序")
            try:
                pay_params = vpay.create_payment_params(
                    session_key, out_trade_no, attach=req.session_id)
            except RuntimeError as e:
                raise HTTPException(status_code=400, detail=str(e))

        prepay_id = ""  # 虚拟支付不需要 prepay_id
        db.execute(
            "INSERT INTO orders (out_trade_no, session_id, openid, amount_fen, status, prepay_id, created_at) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (out_trade_no, req.session_id, openid, amount_fen, "pending", prepay_id, database.now()),
        )
        order_id = db.execute("SELECT LAST_INSERT_ID() AS id").fetchone()["id"]

    return {"code": 0, "message": "ok", "data": {
        "order_id": order_id, "out_trade_no": out_trade_no,
        "amount_fen": amount_fen, "status": "pending", "pay_params": pay_params,
    }}


@app.post("/api/report/confirm_payment")
def confirm_payment(req: ConfirmPayRequest, request: Request):
    """客户端支付成功后通知服务端验证（发货轮询分支，替代消息推送回调）。

    背景：云托管默认域名不可用于正式环境消息推送，因此采用官方推荐的
    「发货轮询」分支——wx.requestVirtualPayment success 后由客户端调此接口，
    服务端调 /xpay/query_order 向微信核实订单状态，核实通过才标记 paid。

    幂等：订单已是 paid 直接返回 confirmed；验证失败不标记，客户端轮询兜底。
    """
    openid = _require_openid(request)
    if not req.out_trade_no:
        raise HTTPException(status_code=400, detail="缺少 out_trade_no")

    with database.get_db() as db:
        order = db.execute(
            "SELECT * FROM orders WHERE out_trade_no=%s", (req.out_trade_no,)
        ).fetchone()

    if order is None:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order["openid"] != openid:
        raise HTTPException(status_code=403, detail="无权操作此订单")
    if order["status"] == "paid":
        # 幂等：已支付直接确认（报告生成可能在路上）
        return {"code": 0, "message": "ok", "data": {"confirmed": True, "already_paid": True}}

    # mock 模式：跳过微信核实，直接标记
    if vpay.is_mock():
        with database.get_db() as db:
            db.execute(
                "UPDATE orders SET status='paid', paid_at=%s "
                "WHERE out_trade_no=%s AND status='pending'",
                (database.now(), req.out_trade_no),
            )
        report_service.start_report_generation(order["session_id"])
        return {"code": 0, "message": "ok", "data": {"confirmed": True, "mock": True}}

    # 真实模式：向微信核实（最多 3 次，间隔 1s，覆盖支付落库延迟）
    last_err = ""
    for attempt in range(3):
        try:
            result = vpay.query_order(openid, req.out_trade_no)
        except RuntimeError as e:
            last_err = str(e)
            log_pay(f"[confirm_payment] query_order 异常({attempt+1}/3): {e}")
            time.sleep(1)
            continue

        if result.get("is_paid"):
            with database.get_db() as db:
                cur = db.execute(
                    "UPDATE orders SET status='paid', transaction_id=%s, notify_raw=%s, paid_at=%s "
                    "WHERE out_trade_no=%s AND status='pending'",
                    (result.get("wx_order_id", ""),
                     json.dumps(result, ensure_ascii=False), database.now(), req.out_trade_no),
                )
                paid_now = cur.rowcount > 0
            log_pay(f"[confirm_payment] 核实通过 status={result['status']} paid_fee={result['paid_fee']}")
            if paid_now:
                report_service.start_report_generation(order["session_id"])
            return {"code": 0, "message": "ok", "data": {
                "confirmed": True, "wx_status": result["status"]}}

        last_err = f"wx_status={result.get('status', -1)}"
        log_pay(f"[confirm_payment] 未支付({attempt+1}/3): {last_err}")
        time.sleep(1)

    # 微信侧重试期间未确认：不报错，客户端轮询 /api/report/status 兜底
    # （后续用户重新进入支付页时 create_order 也会再次触发核实机会）
    return {"code": 0, "message": "ok", "data": {
        "confirmed": False, "pending_verify": True, "detail": last_err}}


@app.post("/api/pay/notify")
async def pay_notify(request: Request):
    """微信支付 v3 回调。验签 + 解密 → 幂等更新订单 → 异步生成报告。

    必须 5 秒内返回 {"code":"SUCCESS"}。无论业务成败都应返回确认（让微信停止重试），
    业务失败记日志由对账兜底。
    """
    raw = (await request.body()).decode("utf-8")
    headers = {k.lower(): v for k, v in request.headers.items()}
    try:
        data = wxpay.parse_and_verify_notify(raw, headers)
        out_trade_no = data["out_trade_no"]
        trade_state = data["trade_state"]
        amount_total = data["amount_total"]
        transaction_id = data.get("transaction_id", "")

        with database.get_db() as db:
            order = db.execute("SELECT * FROM orders WHERE out_trade_no=%s", (out_trade_no,)).fetchone()
            if order is None:
                log_pay(f"[pay/notify] 未知订单 out_trade_no={out_trade_no}")
                return {"code": "SUCCESS", "message": "成功"}  # 未知订单不阻塞微信
            if trade_state == "SUCCESS" and amount_total == order["amount_fen"]:
                # 幂等更新：仅 pending → paid
                cur = db.execute(
                    "UPDATE orders SET status='paid', transaction_id=%s, notify_raw=%s, paid_at=%s "
                    "WHERE id=%s AND status='pending'",
                    (transaction_id, raw, database.now(), order["id"]),
                )
                paid = cur.rowcount > 0
            else:
                log_pay(f"[pay/notify] 非成功回调 trade_state={trade_state} amount={amount_total}")
                return {"code": "SUCCESS", "message": "成功"}
    except PermissionError as e:
        log_pay(f"[pay/notify] 验签失败: {e}")
        raise HTTPException(status_code=400, detail="验签失败")
    except Exception as e:
        log_pay(f"[pay/notify] 处理异常: {e}")
        raise HTTPException(status_code=500, detail="处理失败")

    if paid:
        report_service.start_report_generation(order["session_id"])
    return {"code": "SUCCESS", "message": "成功"}


@app.post("/api/pay/mock_notify")
def mock_notify(req: OrderRequest):
    """【仅开发/联调】模拟微信支付成功回调。PAY_MOCK=1 时可用。"""
    if not wxpay.is_mock():
        raise HTTPException(status_code=404, detail="仅开发模式可用")
    with database.get_db() as db:
        order = db.execute(
            "SELECT * FROM orders WHERE session_id=%s AND status='pending' ORDER BY id DESC LIMIT 1",
            (req.session_id,),
        ).fetchone()
        if order is None:
            raise HTTPException(status_code=400, detail="未找到待支付订单")
        db.execute(
            "UPDATE orders SET status='paid', transaction_id=%s, paid_at=%s WHERE id=%s AND status='pending'",
            (f"MOCK_{int(time.time())}", database.now(), order["id"]),
        )
    report_service.start_report_generation(req.session_id)
    return {"code": 0, "message": "模拟支付成功", "data": {"paid": True}}


@app.get("/api/xpay/notify")
def xpay_notify_verify(
    msg_signature: str = "",
    timestamp: str = "",
    nonce: str = "",
    echostr: str = "",
):
    """消息推送 URL 校验。

    在 MP 后台「开发管理 → 开发设置 → 消息推送」填写本回调地址并启用消息推送时，
    微信会发 GET 请求验证 URL 可达性（携带 msg_signature/timestamp/nonce/echostr）。
    服务端用 Token 校验后原样返回 echostr。
    """
    log_pay(f"[xpay/notify GET] ts={timestamp} nonce={nonce}")
    if not echostr:
        return JSONResponse(content={"ErrCode": -1, "ErrMsg": "missing echostr"})
    verified = vpay.verify_url(msg_signature, timestamp, nonce, echostr)
    if verified is None:
        return JSONResponse(content={"ErrCode": -1, "ErrMsg": "signature mismatch"}, status_code=403)
    return PlainTextResponse(content=verified)


@app.post("/api/xpay/notify")
async def xpay_notify(
    request: Request,
    msg_signature: str = "",
    timestamp: str = "",
    nonce: str = "",
):
    """微信通用消息推送接收端（开发管理 → 开发设置 → 消息推送）。

    本端点接收两类消息：
    1. msgType=text         — 用户客服消息（当前业务不接客服，回复 success 即可）
    2. msgType=event        — 虚拟支付事件，重点处理 xpay_goods_deliver_notify 发货推送
    其他消息类型一律返回 success（不让微信重试）。

    消息默认走加密模式（MSG_AES_KEY 已配置时）：
    body XML 结构: <xml><ToUserName>...</ToUserName><Encrypt>...</Encrypt></xml>
    解密后再按 msgType 分发。

    简化规则（微信官方）：
    - 返回空 / "success" / {"success":true} 均视为处理成功
    """
    raw = (await request.body()).decode("utf-8")
    log_pay(f"[xpay/notify POST] ts={timestamp} nonce={nonce} body_len={len(raw)}")

    def ok():
        # 响应：明文模式 → 字符串 "success"；加密模式 → 加密的 success XML
        if vpay.msg_push_ready():
            reply_inner = "<xml><Content><![CDATA[success]]></Content></xml>"
            return Response(
                content=vpay.build_encrypted_reply_xml(reply_inner),
                media_type="application/xml",
            )
        return PlainTextResponse(content="success")

    # --- 1. 解密（加密模式下） ---
    body_for_parse = raw
    if vpay.msg_push_ready() and raw.lstrip().startswith("<"):
        try:
            import xml.etree.ElementTree as _ET
            root = _ET.fromstring(raw)
            enc = root.findtext("Encrypt", "") or ""
            if not enc:
                log_pay("[xpay/notify] 加密消息但 Encrypt 字段为空")
                return ok()
            if not vpay.verify_msg_signature(msg_signature, timestamp, nonce, enc):
                log_pay(f"[xpay/notify] 签名校验失败 msg_sig={msg_signature[:16]}")
                return ok()
            body_for_parse = vpay.decrypt_message(enc)
            log_pay(f"[xpay/notify] 解密成功 明文={body_for_parse[:200]}")
        except Exception as e:
            log_pay(f"[xpay/notify] 解密失败: {e}")
            return ok()

    # --- 2. 解析 msgType ---
    msg_type = ""
    event_type = ""
    out_trade_no = ""
    try:
        if body_for_parse.lstrip().startswith("<"):
            import xml.etree.ElementTree as _ET
            root = _ET.fromstring(body_for_parse)
            msg_type = (root.findtext("MsgType") or "").strip()
            event_type = (root.findtext("Event") or "").strip()
            out_trade_no = (root.findtext("OutTradeNo") or "").strip()
        else:
            data = json.loads(body_for_parse)
            msg_type = (data.get("MsgType") or "").strip()
            event_type = (data.get("Event") or "").strip()
            out_trade_no = (data.get("OutTradeNo") or "").strip()
    except Exception as e:
        log_pay(f"[xpay/notify] 解析失败: {e} body={body_for_parse[:200]}")
        return ok()

    log_pay(f"[xpay/notify] msg_type={msg_type} event={event_type} out_trade_no={out_trade_no}")

    # --- 3. 分发处理 ---
    # 仅处理道具发货推送
    if msg_type == "event" and event_type == "xpay_goods_deliver_notify":
        try:
            return _handle_xpay_goods_deliver(body_for_parse)
        except Exception as e:
            log_pay(f"[xpay/notify] 发货处理异常: {e}")
            return ok()

    # 退款 / 投诉 / 风控事件 —— 当前业务暂不处理，仅记录
    if msg_type == "event" and event_type in (
        "xpay_refund_notify", "xpay_complaint_notify",
        "xpay_wxpay_callback_notify", "xpay_coin_pay_notify",
        "xpay_subscribe_ios_refund_query_notify",
    ):
        log_pay(f"[xpay/notify] 收到事件 {event_type}（暂不处理）")
        return ok()

    # 客服消息 (msgType=text/event 且不是虚拟支付事件) —— 当前不接入，回复 success
    return ok()


def _handle_xpay_goods_deliver(body: str):
    """处理虚拟支付道具发货推送 xpay_goods_deliver_notify。"""
    out_trade_no = ""
    transaction_id = ""
    actual_price = 0
    try:
        if body.lstrip().startswith("<"):
            import xml.etree.ElementTree as _ET
            root = _ET.fromstring(body)
            out_trade_no = (root.findtext("OutTradeNo") or "").strip()
            transaction_id = (root.findtext("TransactionId") or "").strip()
            ap = (root.findtext("ActualPrice") or "0").strip()
            actual_price = int(ap) if ap.isdigit() else 0
        else:
            data = json.loads(body)
            out_trade_no = (data.get("OutTradeNo") or "").strip()
            wpi = data.get("WeChatPayInfo") or {}
            transaction_id = (wpi.get("TransactionId") or "").strip()
            gi = data.get("GoodsInfo") or {}
            ap = gi.get("ActualPrice", 0)
            actual_price = int(ap) if ap else 0
    except Exception as e:
        log_pay(f"[xpay/notify] 解析发货消息失败: {e}")
        return PlainTextResponse(content="success")

    if not out_trade_no:
        log_pay("[xpay/notify] 发货消息缺 OutTradeNo")
        return PlainTextResponse(content="success")

    log_pay(f"[xpay/notify] 发货 out_trade_no={out_trade_no} price={actual_price} txn={transaction_id}")

    paid = False
    session_id_for_report = None
    try:
        with database.get_db() as db:
            order = db.execute(
                "SELECT * FROM orders WHERE out_trade_no=%s", (out_trade_no,)
            ).fetchone()
            if order is None:
                log_pay(f"[xpay/notify] 未知订单 out_trade_no={out_trade_no}")
            else:
                # 幂等更新：仅 pending → paid
                cur = db.execute(
                    "UPDATE orders SET status='paid', transaction_id=%s, notify_raw=%s, paid_at=%s "
                    "WHERE id=%s AND status='pending'",
                    (transaction_id or f"XPAY_{int(time.time())}", body, database.now(), order["id"]),
                )
                paid = cur.rowcount > 0
                session_id_for_report = order["session_id"]
    except Exception as e:
        log_pay(f"[xpay/notify] 更新订单失败: {e}")

    if paid and session_id_for_report:
        try:
            report_service.start_report_generation(session_id_for_report)
        except Exception as e:
            log_pay(f"[xpay/notify] 启动报告生成失败: {e}")

    # 响应：明文模式 → 字符串 "success"；加密模式 → 加密的 success XML
    if vpay.msg_push_ready():
        reply_inner = "<xml><Content><![CDATA[success]]></Content></xml>"
        return Response(
            content=vpay.build_encrypted_reply_xml(reply_inner),
            media_type="application/xml",
        )
    return PlainTextResponse(content="success")


# ============================================================
# 兑换密钥系统
# ============================================================
_REDEEM_CHARS = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # 去除易混淆字符 O/0/I/1


def _gen_redeem_code() -> str:
    """生成格式 XY-XXXX-XXXX-XXXX 的兑换码。"""
    part = lambda: "".join(random.choices(_REDEEM_CHARS, k=4))
    return f"XY-{part()}-{part()}-{part()}"


@app.post("/api/admin/redeem/generate")
def admin_redeem_generate(req: RedeemGenRequest):
    """管理员批量生成兑换密钥。

    需要管理员账号密码验证。每个密钥可替代一次付费解锁报告。
    """
    _check_admin(req.username, req.password)
    if req.count < 1 or req.count > 500:
        raise HTTPException(status_code=400, detail="生成数量需在 1-500 之间")

    expires_at = 0
    if req.expires_days > 0:
        expires_at = int(time.time()) + req.expires_days * 86400

    codes = []
    with database.get_db() as db:
        for _ in range(req.count):
            # 确保唯一
            while True:
                code = _gen_redeem_code()
                exists = db.execute("SELECT 1 FROM redeem_codes WHERE code=%s", (code,)).fetchone()
                if not exists:
                    break
            db.execute(
                "INSERT INTO redeem_codes (code, batch_label, status, created_at, expires_at, created_by) "
                "VALUES (%s,%s,%s,%s,%s,%s)",
                (code, req.batch_label, "unused", database.now(), expires_at, "admin"),
            )
            codes.append(code)

    return {"code": 0, "message": f"已生成 {len(codes)} 个兑换密钥", "data": {
        "codes": codes, "batch_label": req.batch_label,
        "expires_at": expires_at, "count": len(codes),
    }}


@app.get("/api/admin/redeem/list")
def admin_redeem_list(username: str = Query(...), password: str = Query(...), status: str = Query("")):
    """管理员查询兑换密钥列表。"""
    _check_admin(username, password)

    with database.get_db() as db:
        if status:
            rows = db.execute(
                "SELECT * FROM redeem_codes WHERE status=%s ORDER BY created_at DESC", (status,)
            ).fetchall()
        else:
            rows = db.execute(
                "SELECT * FROM redeem_codes ORDER BY created_at DESC"
            ).fetchall()

    def _fmt(row):
        return {
            "code": row["code"],
            "batch_label": row["batch_label"],
            "status": row["status"],
            "created_at": row["created_at"],
            "expires_at": row["expires_at"],
            "used_at": row["used_at"],
            "used_by_openid": row["used_by_openid"],
            "used_session_id": row["used_session_id"],
            "reusable": bool(row["reusable"]) if "reusable" in row.keys() else False,
        }
    return {"code": 0, "data": [_fmt(r) for r in rows]}


@app.post("/api/redeem/verify")
def redeem_verify(req: RedeemRequest, request: Request):
    """用户输入兑换密钥，替代付费解锁报告。

    成功后创建一笔 amount_fen=0 的 paid 订单，复用现有支付流程触发 AI 报告生成。
    """
    openid = _require_openid(request)
    try:
        session = load_session(req.session_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="会话不存在")
    _owns_session(openid, session)

    code = req.code.strip().upper()

    # 先检查兑换码状态（优先于会话状态检查，确保错误信息准确）
    with database.get_db() as db:
        row = db.execute("SELECT * FROM redeem_codes WHERE code=%s", (code,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="兑换码不存在")
        if row["status"] == "disabled":
            raise HTTPException(status_code=403, detail="该兑换码已被停用")
        if row["status"] == "used":
            raise HTTPException(status_code=409, detail="该兑换码已被使用")
        if row["expires_at"] and row["expires_at"] < time.time():
            raise HTTPException(status_code=403, detail="该兑换码已过期")

        # 幂等：已有 paid 订单则跳过
        existing = db.execute(
            "SELECT status FROM orders WHERE session_id=%s AND openid=%s ORDER BY id DESC LIMIT 1",
            (req.session_id, openid),
        ).fetchone()
        if existing and existing["status"] == "paid":
            return {"code": 0, "message": "该会话已解锁", "data": {"paid": True, "redeemed": True}}

    # 再检查会话状态
    if session.get("status") not in ("answered", "ready", "failed"):
        raise HTTPException(status_code=400, detail="请先完成答题再兑换报告")

    with database.get_db() as db:
        # 创建 paid 订单（amount_fen=0，标记为兑换）
        out_trade_no = _out_trade_no()
        db.execute(
            "INSERT INTO orders (out_trade_no, session_id, openid, amount_fen, status, "
            "transaction_id, notify_raw, created_at, paid_at) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (out_trade_no, req.session_id, openid, 0, "paid",
             f"REDEEM-{code}", json.dumps({"redeem_code": code}), database.now(), database.now()),
        )

        # 标记兑换码已使用（可复用码除外）
        if not row["reusable"]:
            db.execute(
                "UPDATE redeem_codes SET status='used', used_at=%s, used_by_openid=%s, used_session_id=%s "
                "WHERE code=%s AND status='unused'",
                (database.now(), openid, req.session_id, code),
            )

    # 触发 AI 报告生成（与支付回调流程一致）
    report_service.start_report_generation(req.session_id)

    return {"code": 0, "message": "兑换成功，正在生成报告", "data": {"paid": True, "redeemed": True}}


@app.post("/api/report/detail")
def report_detail(req: StatusRequest, request: Request):
    """支付成功后获取完整报告（AI 章节）。生成中返回 code=2001，前端继续轮询。"""
    openid = _require_openid(request)
    try:
        session = load_session(req.session_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="会话不存在")
    _owns_session(openid, session)

    status = report_service.get_report_status(req.session_id)
    if not status["paid"]:
        raise HTTPException(status_code=403, detail="请先完成支付解锁深度报告")
    if status["report_status"] == "generating":
        return {"code": 2001, "message": "报告生成中，请稍候", "data": status}
    if status["report_status"] == "none":
        return {"code": 2001, "message": "报告生成中，请稍候", "data": status}

    report = report_service.get_report(req.session_id)
    return {"code": 0, "message": "ok", "data": {"report": report}}


@app.post("/api/report/regenerate")
def report_regenerate(req: RegenerateRequest, request: Request):
    """重新生成 AI 报告（已付费会话可免费重试，不重复收费）。

    适用场景：AI 生成内容不完整、用户对结果不满意想重新生成。
    """
    openid = _require_openid(request)
    try:
        session = load_session(req.session_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="会话不存在")
    _owns_session(openid, session)

    # 校验已付费
    _require_paid(req.session_id, openid)

    if session.get("status") == "generating":
        raise HTTPException(status_code=409, detail="报告正在生成中，请稍候")

    if session.get("status") not in ("ready", "failed", "answered"):
        raise HTTPException(status_code=400, detail="当前状态不允许重新生成")

    # 校验重新生成次数（每个会话最多1次）
    regen_count = session.get("regenerate_count") or 0
    if regen_count >= 1:
        raise HTTPException(status_code=403, detail="每个测评报告最多重新生成1次")

    # 标记已使用重试次数（在生成前写入，防止并发重复调用）
    with database.get_db() as db:
        db.execute(
            "UPDATE sessions SET regenerate_count=regenerate_count+1 WHERE session_id=%s",
            (req.session_id,),
        )

    # 强制重新生成（不清除订单，不重复付费）
    report_service.start_report_generation(req.session_id, force=True)

    return {"code": 0, "message": "正在重新生成报告", "data": {"regenerating": True}}


def log_pay(msg: str):
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)


# ============================================================
# 管理后台 API
# ============================================================
def _check_admin(username: str, password: str):
    if username != "admin" or password != "admin123":
        raise HTTPException(status_code=403, detail="用户名或密码错误")


class AdminMakeSessionsRequest(BaseModel):
    username: str
    password: str
    openid: str
    count: int = 2
    profile: dict = {"age": 30, "gender": "male", "role": "professional", "purpose": "career"}


@app.post("/api/admin/test/make_sessions")
def admin_make_test_sessions(req: AdminMakeSessionsRequest):
    """管理员造数：给指定 openid 生成 N 条「已答完题、未付款」的测评记录。

    用于支付链路联调：记录与真实答题流程完全一致（selector 选题 +
    随机答案评分 + free_summary），不创建订单（点支付时才创建）。
    """
    _check_admin(req.username, req.password)
    if req.count < 1 or req.count > 10:
        raise HTTPException(status_code=400, detail="count 需在 1-10 之间")
    if not req.openid or len(req.openid) < 10:
        raise HTTPException(status_code=400, detail="openid 无效")

    created = []
    for _ in range(req.count):
        profile = req.profile
        questions = select(profile, BANK)
        answers = [
            {"question_id": q["id"], "option_index": random.randrange(len(q["options"]))}
            for q in questions
        ]
        results = score_answers(questions, answers)
        free_summary = generate_free_summary(results, profile)

        session_id = str(uuid.uuid4())
        save_session(session_id, {
            "session_id": session_id,
            "openid": req.openid,
            "profile": profile,
            "questions": questions,
            "answers": answers,
            "results": results,
            "free_summary": free_summary,
            "status": "answered",
        })
        created.append({"session_id": session_id, "preview": (free_summary or "")[:50]})

    return {"code": 0, "message": f"已生成 {len(created)} 条未付款测评记录", "data": {
        "openid": req.openid, "count": len(created), "sessions": created,
    }}


@app.get("/api/admin/stats")
def admin_stats(username: str = Query(...), password: str = Query(...)):
    """总览统计：用户数、会话数、订单数、收入、兑换码使用情况。"""
    _check_admin(username, password)
    with database.get_db() as db:
        total_users = db.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"]
        total_sessions = db.execute("SELECT COUNT(*) AS c FROM sessions").fetchone()["c"]
        total_orders = db.execute("SELECT COUNT(*) AS c FROM orders").fetchone()["c"]
        paid_orders = db.execute("SELECT COUNT(*) AS c FROM orders WHERE status='paid'").fetchone()["c"]
        total_revenue = db.execute(
            "SELECT COALESCE(SUM(amount_fen),0) AS s FROM orders WHERE status='paid' AND amount_fen>0"
        ).fetchone()["s"]
        redeem_unused = db.execute("SELECT COUNT(*) AS c FROM redeem_codes WHERE status='unused'").fetchone()["c"]
        redeem_used = db.execute("SELECT COUNT(*) AS c FROM redeem_codes WHERE status='used'").fetchone()["c"]
        redeem_disabled = db.execute("SELECT COUNT(*) AS c FROM redeem_codes WHERE status='disabled'").fetchone()["c"]
        # 最近7天每日新增用户
        week_ago = time.time() - 7 * 86400
        recent_users = db.execute(
            "SELECT COUNT(*) AS c FROM users WHERE created_at > %s", (week_ago,)
        ).fetchone()["c"]
        # 会话状态分布
        status_rows = db.execute(
            "SELECT status, COUNT(*) AS c FROM sessions GROUP BY status"
        ).fetchall()
        status_dist = {r["status"]: r["c"] for r in status_rows}

    return {"code": 0, "data": {
        "total_users": total_users,
        "total_sessions": total_sessions,
        "total_orders": total_orders,
        "paid_orders": paid_orders,
        "total_revenue_yuan": round(total_revenue / 100, 2),
        "redeem": {"unused": redeem_unused, "used": redeem_used, "disabled": redeem_disabled, "total": redeem_unused + redeem_used + redeem_disabled},
        "recent_users_7d": recent_users,
        "session_status_dist": status_dist,
    }}


@app.get("/api/admin/users")
def admin_users(username: str = Query(...), password: str = Query(...), page: int = Query(1), size: int = Query(20)):
    """用户列表（分页）。"""
    _check_admin(username, password)
    page = max(1, page)
    size = min(max(1, size), 100)
    offset = (page - 1) * size
    with database.get_db() as db:
        total = db.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"]
        rows = db.execute(
            "SELECT openid, nickname, avatar_url, created_at, last_login_at "
            "FROM users ORDER BY created_at DESC LIMIT %s OFFSET %s",
            (size, offset),
        ).fetchall()
    users = []
    for r in rows:
        users.append({
            "openid": r["openid"],
            "nickname": r["nickname"] or "",
            "avatar_url": r["avatar_url"] or "",
            "created_at": r["created_at"],
            "last_login_at": r["last_login_at"],
        })
    return {"code": 0, "data": {"total": total, "page": page, "size": size, "users": users}}


@app.get("/api/admin/sessions")
def admin_sessions(username: str = Query(...), password: str = Query(...), page: int = Query(1), size: int = Query(20)):
    """会话列表（分页）。"""
    _check_admin(username, password)
    page = max(1, page)
    size = min(max(1, size), 100)
    offset = (page - 1) * size
    with database.get_db() as db:
        total = db.execute("SELECT COUNT(*) AS c FROM sessions").fetchone()["c"]
        rows = db.execute(
            "SELECT session_id, openid, status, created_at, updated_at "
            "FROM sessions ORDER BY created_at DESC LIMIT %s OFFSET %s",
            (size, offset),
        ).fetchall()
    sessions = []
    for r in rows:
        sessions.append({
            "session_id": r["session_id"],
            "openid": r["openid"] or "",
            "status": r["status"],
            "created_at": r["created_at"],
            "updated_at": r["updated_at"],
        })
    return {"code": 0, "data": {"total": total, "page": page, "size": size, "sessions": sessions}}


class AdminDeleteSessionsRequest(BaseModel):
    username: str
    password: str
    openid_prefix: str = ""  # 只删匹配前缀的会话，如 "mock_openid_e2e_"
    keep_latest: int = 0    # 保留最近 N 条，0=全删


@app.post("/api/admin/sessions/delete")
def admin_delete_sessions(req: AdminDeleteSessionsRequest):
    """批量删除会话及其关联订单（仅限 mock/e2e 测试数据）。"""
    _check_admin(req.username, req.password)
    prefix = req.openid_prefix or "mock_openid_e2e_"
    with database.get_db() as db:
        # 找到要删的 session_id
        if req.keep_latest > 0:
            # 先查出最新的 N 条（要保留）
            keep_rows = db.execute(
                "SELECT session_id FROM sessions WHERE openid LIKE %s "
                "ORDER BY created_at DESC LIMIT %s",
                (prefix + "%", req.keep_latest),
            ).fetchall()
            keep_ids = {r["session_id"] for r in keep_rows}
            # 其余的都删
            all_rows = db.execute(
                "SELECT session_id FROM sessions WHERE openid LIKE %s",
                (prefix + "%",),
            ).fetchall()
            del_ids = [r["session_id"] for r in all_rows if r["session_id"] not in keep_ids]
        else:
            rows = db.execute(
                "SELECT session_id FROM sessions WHERE openid LIKE %s",
                (prefix + "%",),
            ).fetchall()
            del_ids = [r["session_id"] for r in rows]

        if not del_ids:
            return {"code": 0, "message": "没有匹配的会话", "data": {"deleted": 0}}

        # 删关联订单
        placeholders = ",".join(["%s"] * len(del_ids))
        db.execute(f"DELETE FROM orders WHERE session_id IN ({placeholders})", del_ids)
        # 删会话
        db.execute(f"DELETE FROM sessions WHERE session_id IN ({placeholders})", del_ids)

    return {"code": 0, "message": f"已删除 {len(del_ids)} 条会话", "data": {"deleted": len(del_ids)}}


class AdminRegenRequest(BaseModel):
    username: str
    password: str
    session_id: str


@app.post("/api/admin/regenerate")
def admin_regenerate(req: AdminRegenRequest):
    """管理员强制重新生成报告（不受 regenerate_count 限制）。"""
    _check_admin(req.username, req.password)
    try:
        session = load_session(req.session_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="会话不存在")
    # 重置 regenerate_count
    with database.get_db() as db:
        db.execute(
            "UPDATE sessions SET regenerate_count=0 WHERE session_id=%s",
            (req.session_id,),
        )
    # 触发重新生成
    report_service.start_report_generation(req.session_id, force=True)
    return {"code": 0, "message": "正在重新生成报告", "data": {"session_id": req.session_id}}


@app.get("/api/admin/orders")
def admin_orders(username: str = Query(...), password: str = Query(...), page: int = Query(1), size: int = Query(20)):
    """订单列表（分页）。"""
    _check_admin(username, password)
    page = max(1, page)
    size = min(max(1, size), 100)
    offset = (page - 1) * size
    with database.get_db() as db:
        total = db.execute("SELECT COUNT(*) AS c FROM orders").fetchone()["c"]
        rows = db.execute(
            "SELECT id, out_trade_no, session_id, openid, amount_fen, status, "
            "transaction_id, created_at, paid_at "
            "FROM orders ORDER BY created_at DESC LIMIT %s OFFSET %s",
            (size, offset),
        ).fetchall()
    orders = []
    for r in rows:
        orders.append({
            "id": r["id"],
            "out_trade_no": r["out_trade_no"],
            "session_id": r["session_id"],
            "openid": r["openid"],
            "amount_yuan": round(r["amount_fen"] / 100, 2),
            "status": r["status"],
            "transaction_id": r["transaction_id"] or "",
            "created_at": r["created_at"],
            "paid_at": r["paid_at"],
        })
    return {"code": 0, "data": {"total": total, "page": page, "size": size, "orders": orders}}


class RedeemDisableRequest(BaseModel):
    code: str
    username: str
    password: str


class RedeemCustomRequest(BaseModel):
    code: str                      # 自定义兑换码
    username: str
    password: str
    reusable: bool = False         # 是否可复用（长期测试码）
    batch_label: str = ""


@app.post("/api/admin/redeem/create-custom")
def admin_redeem_create_custom(req: RedeemCustomRequest):
    """管理员创建自定义兑换码（可设置可复用，用于长期测试）。"""
    _check_admin(req.username, req.password)
    code = req.code.strip().upper()
    if not code:
        raise HTTPException(status_code=400, detail="兑换码不能为空")
    with database.get_db() as db:
        exists = db.execute("SELECT 1 FROM redeem_codes WHERE code=%s", (code,)).fetchone()
        if exists:
            raise HTTPException(status_code=409, detail="该兑换码已存在")
        db.execute(
            "INSERT INTO redeem_codes (code, batch_label, status, created_at, expires_at, created_by, reusable) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (code, req.batch_label or "custom", "unused", database.now(), 0, "admin", 1 if req.reusable else 0),
        )
    return {"code": 0, "message": f"兑换码已创建{'（可复用）' if req.reusable else ''}", "data": {
        "code": code, "reusable": req.reusable, "batch_label": req.batch_label,
    }}


class RedeemDeleteRequest(BaseModel):
    code: str
    username: str
    password: str


@app.post("/api/admin/redeem/delete")
def admin_redeem_delete(req: RedeemDeleteRequest):
    """管理员删除兑换码（彻底删除，非停用）。"""
    _check_admin(req.username, req.password)
    code = req.code.strip().upper()
    with database.get_db() as db:
        row = db.execute("SELECT status FROM redeem_codes WHERE code=%s", (code,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="兑换码不存在")
        db.execute("DELETE FROM redeem_codes WHERE code=%s", (code,))
    return {"code": 0, "message": f"兑换码 {code} 已删除"}


@app.post("/api/admin/redeem/disable")
def admin_redeem_disable(req: RedeemDisableRequest):
    """停用/启用兑换码。"""
    _check_admin(req.username, req.password)
    code = req.code.strip().upper()
    with database.get_db() as db:
        row = db.execute("SELECT status FROM redeem_codes WHERE code=%s", (code,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="兑换码不存在")
        if row["status"] == "used":
            raise HTTPException(status_code=400, detail="已使用的兑换码不可变更")
        new_status = "disabled" if row["status"] == "unused" else "unused"
        db.execute("UPDATE redeem_codes SET status=%s WHERE code=%s", (new_status, code))
    return {"code": 0, "message": f"已{'停用' if new_status == 'disabled' else '启用'}", "data": {"code": code, "status": new_status}}


# ============================================================
# 静态文件服务（前端页面，Web 兼容）
# ============================================================
@app.get("/", response_class=HTMLResponse)
def index():
    index_path = FRONTEND_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="前端页面未找到")
    return HTMLResponse(content=index_path.read_text(encoding="utf-8"))


@app.get("/css/{filename}")
def serve_css(filename: str):
    css_path = FRONTEND_DIR / "css" / filename
    if not css_path.exists():
        raise HTTPException(status_code=404, detail=f"CSS 文件不存在: {filename}")
    return HTMLResponse(content=css_path.read_text(encoding="utf-8"), media_type="text/css")


@app.get("/js/{filename}")
def serve_js(filename: str):
    js_path = FRONTEND_DIR / "js" / filename
    if not js_path.exists():
        raise HTTPException(status_code=404, detail=f"JS 文件不存在: {filename}")
    return HTMLResponse(content=js_path.read_text(encoding="utf-8"), media_type="application/javascript")


# ============================================================
# 健康检查 & 公开统计
# ============================================================
@app.get("/api/health")
def health():
    return {"code": 0, "message": "ok", "data": {
        "status": "ok", "bank_size": len(BANK), "pay_mock": wxpay.is_mock(),
        "xpay": {"offer_id": vpay.OFFER_ID, "env": vpay.ENV,
                 "product_id": vpay.PRODUCT_ID, "goods_price": vpay.GOODS_PRICE,
                 "app_key_set": bool(vpay.APP_KEY)},
        "msg_push": {"ready": vpay.msg_push_ready(),
                     "token_set": bool(vpay.MSG_TOKEN),
                     "aes_key_set": bool(vpay.MSG_AES_KEY)},
    }}


@app.get("/api/stats")
def public_stats():
    """公开统计：返回完成测评人数（无需鉴权）。"""
    with database.get_db() as db:
        row = db.execute(
            "SELECT COUNT(*) AS c FROM sessions WHERE status IN ('answered','generating','ready')"
        ).fetchone()
    completed = row["c"] if row else 0
    # 基础偏移量，让数字有一定体量
    display_count = 12580 + completed
    return {"code": 0, "message": "ok", "data": {"completed_count": display_count}}


# ============================================================
# 管理后台页面
# ============================================================
@app.get("/admin", response_class=HTMLResponse)
def admin_page():
    admin_path = BACKEND_DIR / "admin.html"
    if not admin_path.exists():
        raise HTTPException(status_code=404, detail="管理后台页面未找到")
    return HTMLResponse(content=admin_path.read_text(encoding="utf-8"))
