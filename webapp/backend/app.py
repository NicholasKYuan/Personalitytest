#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app.py — 星耀启程人格测评 FastAPI 后端

启动方式:
    cd webapp/backend
    uvicorn app:app --reload --port 8000
"""
import os
import sys
import json
import uuid
from pathlib import Path
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field

# ============================================================
# 路径配置
# ============================================================
BACKEND_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = BACKEND_DIR.parent.parent          # d:/workbuddy/2026-08-11-09-28-12/
SELECTOR_DIR = PROJECT_ROOT / "selector"
BANK_PATH = PROJECT_ROOT / "question-bank" / "items.jsonl"
WEBAPP_DIR = BACKEND_DIR.parent                    # webapp/
FRONTEND_DIR = WEBAPP_DIR / "frontend"              # webapp/frontend/
SESSION_DIR = BACKEND_DIR / "sessions"

SESSION_DIR.mkdir(exist_ok=True)

# 导入 selector（复用现有筛选器）
sys.path.insert(0, str(SELECTOR_DIR))
from selector import select, load_bank
from scorer import score_answers, generate_free_summary
from ai_analyzer import generate_detailed_analysis
from report_generator import generate_report_html

# ============================================================
# FastAPI 应用
# ============================================================
app = FastAPI(title="星耀启程人格测评", version="1.0.0")

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


# ============================================================
# 辅助函数
# ============================================================
def strip_scores(questions: list) -> list:
    """
    移除题目 options 中的 score 字段，只保留 text。
    前端不应看到分数信息。
    """
    stripped = []
    for q in questions:
        q_copy = {k: v for k, v in q.items() if k != "options"}
        q_copy["options"] = [{"text": opt["text"]} for opt in q["options"]]
        stripped.append(q_copy)
    return stripped


def save_session(session_id: str, data: dict):
    """保存会话到 JSON 文件。"""
    path = SESSION_DIR / f"{session_id}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)


def load_session(session_id: str) -> dict:
    """加载会话。"""
    path = SESSION_DIR / f"{session_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"会话不存在: {session_id}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ============================================================
# API 接口
# ============================================================
@app.post("/api/session")
def create_session(req: ProfileRequest):
    """创建会话：接收 profile，筛选120题，返回题目列表（不含分数）。"""
    profile = req.model_dump()

    # 调用 selector 筛选120题
    questions = select(profile, BANK)

    session_id = str(uuid.uuid4())

    # 保存完整会话（含完整题目数据，用于后续评分）
    save_session(session_id, {
        "session_id": session_id,
        "profile": profile,
        "questions": questions,
        "answers": None,
        "results": None,
    })

    # 返回给前端的题目不含 score 字段
    return {
        "session_id": session_id,
        "questions": strip_scores(questions),
    }


@app.post("/api/submit")
def submit_answers(req: SubmitRequest):
    """提交答案：计算四体系结果，返回免费结果。"""
    try:
        session = load_session(req.session_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="会话不存在，请重新开始测评")

    questions = session["questions"]

    # 转换 answers 为 dict 列表
    answers = [a.model_dump() for a in req.answers]

    # 评分
    results = score_answers(questions, answers)
    free_summary = generate_free_summary(results, session["profile"])

    # 更新会话
    session["answers"] = answers
    session["results"] = results
    save_session(req.session_id, session)

    return {
        "session_id": req.session_id,
        "results": results,
        "free_summary": free_summary,
        "detailed_available": True,
    }


@app.post("/api/analyze")
def analyze(req: AnalyzeRequest):
    """深度分析：调用 Minimax M3 生成 AI 深度解读（付费功能）。"""
    try:
        session = load_session(req.session_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="会话不存在")

    if not session.get("results"):
        raise HTTPException(status_code=400, detail="请先完成答题并提交")

    results = session["results"]
    profile = session["profile"]

    analysis = generate_detailed_analysis(results, profile)

    # 缓存 AI 分析到会话
    session["ai_sections"] = analysis["sections"]
    save_session(req.session_id, session)

    return {
        "session_id": req.session_id,
        "detailed_analysis": analysis["detailed_analysis"],
        "sections": analysis["sections"],
    }


@app.get("/api/report/{session_id}")
def get_report(session_id: str):
    """生成可下载的 HTML 报告文件。"""
    try:
        session = load_session(session_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="会话不存在")

    if not session.get("results"):
        raise HTTPException(status_code=400, detail="请先完成答题并提交")

    results = session["results"]
    profile = session["profile"]

    # 如果已缓存 AI 分析，使用缓存；否则实时生成
    ai_sections = session.get("ai_sections", [])
    if not ai_sections:
        analysis = generate_detailed_analysis(results, profile)
        ai_sections = analysis["sections"]
        # 缓存到会话
        session["ai_sections"] = ai_sections
        save_session(session_id, session)

    html = generate_report_html(results, profile, ai_sections)
    return HTMLResponse(content=html)


# ============================================================
# 静态文件服务（前端页面）
# ============================================================
@app.get("/", response_class=HTMLResponse)
def index():
    """返回前端首页。"""
    index_path = FRONTEND_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="前端页面未找到")
    return HTMLResponse(content=index_path.read_text(encoding="utf-8"))


@app.get("/css/{filename}")
def serve_css(filename: str):
    """返回 CSS 文件。"""
    css_path = FRONTEND_DIR / "css" / filename
    if not css_path.exists():
        raise HTTPException(status_code=404, detail=f"CSS 文件不存在: {filename}")
    return HTMLResponse(content=css_path.read_text(encoding="utf-8"), media_type="text/css")


@app.get("/js/{filename}")
def serve_js(filename: str):
    """返回 JS 文件。"""
    js_path = FRONTEND_DIR / "js" / filename
    if not js_path.exists():
        raise HTTPException(status_code=404, detail=f"JS 文件不存在: {filename}")
    return HTMLResponse(content=js_path.read_text(encoding="utf-8"), media_type="application/javascript")


# ============================================================
# 健康检查
# ============================================================
@app.get("/api/health")
def health():
    return {"status": "ok", "bank_size": len(BANK)}
