#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app.py — 星耀启程人格测评 FastAPI 后端（Web + 微信小程序共用）

启动方式:
    cd webapp/backend
    uvicorn app:app --reload --port 8000

小程序新增接口（带 token 鉴权）:
    POST /api/login              code2session → openid → token
    POST /api/report/order       创建 29.9 元订单，返回 wx.requestPayment 参数
    POST /api/pay/notify         微信支付 v3 回调（验签+解密+幂等）
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
from pathlib import Path
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
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


class StatusRequest(BaseModel):
    session_id: str


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
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(session_id) DO UPDATE SET
                 openid=excluded.openid, profile=excluded.profile, questions=excluded.questions,
                 answers=excluded.answers, results=excluded.results, free_summary=excluded.free_summary,
                 status=excluded.status, ai_sections=excluded.ai_sections, ai_error=excluded.ai_error,
                 updated_at=excluded.updated_at""",
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
        row = db.execute("SELECT * FROM sessions WHERE session_id=?", (session_id,)).fetchone()
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
    """校验会话归属（仅当会话绑定了 openid 时校验）。"""
    if session.get("openid") and session["openid"] != openid:
        raise HTTPException(status_code=403, detail="无权访问该会话")


def _require_paid(session_id: str, openid: str):
    """校验该会话已支付（小程序会话必须付费才能取 AI 内容）。"""
    with database.get_db() as db:
        o = db.execute(
            "SELECT status FROM orders WHERE session_id=? AND openid=? ORDER BY id DESC LIMIT 1",
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

    results = session["results"]
    profile = session["profile"]

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
    """创建付费订单（29.9 元），返回 wx.requestPayment 调起参数。

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

    amount_fen = 2990

    with database.get_db() as db:
        existing = db.execute(
            "SELECT * FROM orders WHERE session_id=? ORDER BY id DESC LIMIT 1", (req.session_id,)
        ).fetchone()

        if existing is not None:
            if existing["status"] == "paid":
                return {"code": 0, "message": "ok", "data": {
                    "order_id": existing["id"], "out_trade_no": existing["out_trade_no"],
                    "status": "paid", "pay_params": None,
                }}
            if existing["status"] == "pending":
                # 复用原订单（重新调起支付）
                return {"code": 0, "message": "ok", "data": {
                    "order_id": existing["id"], "out_trade_no": existing["out_trade_no"],
                    "status": "pending", "pay_params": None,
                }}
            # closed/refunded → 新建订单

        out_trade_no = _out_trade_no()
        try:
            pay_params = wxpay.create_jsapi_order(openid, out_trade_no, amount_fen)
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"下单失败: {e}")

        prepay_id = pay_params.get("package", "").replace("prepay_id=", "")
        db.execute(
            "INSERT INTO orders (out_trade_no, session_id, openid, amount_fen, status, prepay_id, created_at) "
            "VALUES (?,?,?,?,?,?,?)",
            (out_trade_no, req.session_id, openid, amount_fen, "pending", prepay_id, database.now()),
        )
        order_id = db.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]

    return {"code": 0, "message": "ok", "data": {
        "order_id": order_id, "out_trade_no": out_trade_no,
        "amount_fen": amount_fen, "status": "pending", "pay_params": pay_params,
    }}


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
            order = db.execute("SELECT * FROM orders WHERE out_trade_no=?", (out_trade_no,)).fetchone()
            if order is None:
                log_pay(f"[pay/notify] 未知订单 out_trade_no={out_trade_no}")
                return {"code": "SUCCESS", "message": "成功"}  # 未知订单不阻塞微信
            if trade_state == "SUCCESS" and amount_total == order["amount_fen"]:
                # 幂等更新：仅 pending → paid
                cur = db.execute(
                    "UPDATE orders SET status='paid', transaction_id=?, notify_raw=?, paid_at=? "
                    "WHERE id=? AND status='pending'",
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
            "SELECT * FROM orders WHERE session_id=? AND status='pending' ORDER BY id DESC LIMIT 1",
            (req.session_id,),
        ).fetchone()
        if order is None:
            raise HTTPException(status_code=400, detail="未找到待支付订单")
        db.execute(
            "UPDATE orders SET status='paid', transaction_id=?, paid_at=? WHERE id=? AND status='pending'",
            (f"MOCK_{int(time.time())}", database.now(), order["id"]),
        )
    report_service.start_report_generation(req.session_id)
    return {"code": 0, "message": "模拟支付成功", "data": {"paid": True}}


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


def log_pay(msg: str):
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)


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
# 健康检查
# ============================================================
@app.get("/api/health")
def health():
    return {"code": 0, "message": "ok", "data": {"status": "ok", "bank_size": len(BANK), "pay_mock": wxpay.is_mock()}}
