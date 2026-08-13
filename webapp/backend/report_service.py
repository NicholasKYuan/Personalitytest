#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
report_service.py — 付费报告生成服务

支付成功后由后台线程异步调用 ai_analyzer（MiniMax M3，耗时 30~90s），
完成后把 AI 章节落库并将会话置为 ready/failed；AI 失败时降级为规则化模板报告，
保证付费用户始终能看到内容。

会话状态机：answered → generating → ready | failed
"""
import json
import logging
import threading
import traceback
import time
from datetime import datetime

from db import get_db, now, dumps, loads

log = logging.getLogger("report")

MAX_RETRY = 2          # AI 调用失败重试次数
RETRY_BACKOFF = 3      # 指数退避基数（秒）


# ---------------------------------------------------------------------------
# 规则化降级章节（AI 不可用时兜底，保证付费用户有报告可看）
# ---------------------------------------------------------------------------
def _fallback_sections(results, profile) -> list:
    en = results["enneagram"]
    mb = results["mbti"]
    ho = results["holland"]
    ga = results["gallup"]

    en_scores = ", ".join(f"{k}型 {v}分" for k, v in sorted(en["scores"].items(), key=lambda x: -x[1])[:3])
    mb_scores = ", ".join(f"{k} 维度 {v}分" for k, v in mb["dimensions"].items())
    ho_scores = ", ".join(f"{k} {v}分" for k, v in sorted(ho["scores"].items(), key=lambda x: -x[1]))
    ga_scores = ", ".join(f"{k} {v}分" for k, v in ga["domains"].items())

    sections = [
        {
            "title": "九型人格深度解读",
            "content": (
                f"## {en['main_type']}号 {en['type_name']}\n\n"
                f"你的九型人格主型为 **{en['main_type']}号 · {en['type_name']}**。\n\n"
                f"各类型得分：{en_scores}。\n\n"
                f"{en['type_name']}在压力情境与成长路径上有其独特规律。建议结合完整深度报告了解具体发展建议。"
            ),
        },
        {
            "title": "MBTI深度分析",
            "content": (
                f"## {mb['type']}\n\n"
                f"你的 MBTI 类型为 **{mb['type']}**。\n\n"
                f"维度得分：{mb_scores}。\n\n"
                "该类型在信息获取与决策方式上存在稳定的偏好结构，可参考对应的认知功能描述做进一步了解。"
            ),
        },
        {
            "title": "霍兰德职业方向",
            "content": (
                f"## 代码 {ho['code']}\n\n"
                f"你的霍兰德职业兴趣代码为 **{ho['code']}**。\n\n"
                f"各类型得分：{ho_scores}。\n\n"
                "对应职业方向建议结合你的角色与目标，在完整报告中查看推荐路径。"
            ),
        },
        {
            "title": "盖洛普优势发挥",
            "content": (
                f"## 主导领域 {ga['top_domain']}\n\n"
                f"你的盖洛普优势主导领域为 **{ga['top_domain']}**，核心主题：{', '.join(ga['top_themes']) if ga['top_themes'] else '暂无'}。\n\n"
                f"领域得分：{ga_scores}。\n\n"
                "优势发挥的关键是把高频主题组合成个人化的工作方式。"
            ),
        },
        {
            "title": "四体系综合交叉解读",
            "content": (
                "## 综合视角\n\n"
                f"九型【{en['main_type']}号 {en['type_name']}】关注内在动机，MBTI【{mb['type']}】关注认知方式，"
                f"霍兰德【{ho['code']}】关注职业兴趣，盖洛普【{ga['top_domain']}】关注优势表现。\n\n"
                "四个体系相互印证：动机决定方向感，认知方式决定学习路径，兴趣决定投入意愿，优势决定落地方式。"
            ),
        },
    ]
    return sections


# ---------------------------------------------------------------------------
# 异步生成入口
# ---------------------------------------------------------------------------
def start_report_generation(session_id: str):
    """在后台线程中生成 AI 报告（支付回调成功后调用，幂等：generating/ready/failed 不再触发）。"""
    # 用 DB 状态做幂等保护：只有 answered 状态才能触发
    with get_db() as db:
        row = db.execute("SELECT status FROM sessions WHERE session_id=%s", (session_id,)).fetchone()
        if row is None or row["status"] != "answered":
            log.info("跳过报告生成: session=%s status=%s", session_id, row["status"] if row else None)
            return

    t = threading.Thread(target=_generate_worker, args=(session_id,), daemon=True)
    t.start()


def _generate_worker(session_id: str):
    from ai_analyzer import generate_detailed_analysis

    # 把状态改为 generating（带重试保护：状态竞争时以先到者为准）
    with get_db() as db:
        row = db.execute("SELECT status FROM sessions WHERE session_id=%s", (session_id,)).fetchone()
        if row and row["status"] == "answered":
            db.execute("UPDATE sessions SET status='generating', updated_at=%s WHERE session_id=%s AND status='answered'",
                       (now(), session_id))
        else:
            return

    with get_db() as db:
        s = db.execute("SELECT results, profile FROM sessions WHERE session_id=%s", (session_id,)).fetchone()
    if s is None:
        return
    results = loads(s["results"], {})
    profile = loads(s["profile"], {})

    last_err = ""
    for attempt in range(MAX_RETRY + 1):
        try:
            analysis = generate_detailed_analysis(results, profile)
            sections = analysis.get("sections") or []
            if not sections:
                raise RuntimeError("AI 返回空章节")
            with get_db() as db:
                db.execute(
                    "UPDATE sessions SET ai_sections=%s, status='ready', ai_error=NULL, updated_at=%s WHERE session_id=%s",
                    (dumps(sections), now(), session_id),
                )
            log.info("报告生成成功: session=%s sections=%d", session_id, len(sections))
            return
        except Exception as e:
            last_err = f"{type(e).__name__}: {e}"
            log.warning("AI 生成第 %d 次失败: session=%s %s", attempt + 1, session_id, last_err)
            traceback.print_exc()
            if attempt < MAX_RETRY:
                time.sleep(RETRY_BACKOFF ** (attempt + 1))

    # 全部失败 → 降级为规则化模板
    sections = _fallback_sections(results, profile)
    with get_db() as db:
        db.execute(
            "UPDATE sessions SET ai_sections=%s, status='failed', ai_error=%s, updated_at=%s WHERE session_id=%s",
            (dumps(sections), last_err, now(), session_id),
        )
    log.error("AI 生成失败已降级: session=%s err=%s", session_id, last_err)


# ---------------------------------------------------------------------------
# 读取报告
# ---------------------------------------------------------------------------
def get_report_status(session_id: str) -> dict:
    """返回支付/报告状态（供 GET /api/report/status 使用）。"""
    with get_db() as db:
        s = db.execute("SELECT status FROM sessions WHERE session_id=%s", (session_id,)).fetchone()
        o = db.execute("SELECT status FROM orders WHERE session_id=%s ORDER BY id DESC LIMIT 1", (session_id,)).fetchone()

    payment_status = o["status"] if o else "unpaid"
    report_status = s["status"] if s else "none"
    if payment_status != "paid":
        report_status = "none"
    return {
        "payment_status": payment_status,
        "report_status": report_status,
        "paid": payment_status == "paid",
        "is_ready": payment_status == "paid" and report_status in ("ready", "failed"),
    }


def get_report(session_id: str) -> dict:
    """返回完整报告 JSON（需外部已校验 paid）。"""
    with get_db() as db:
        s = db.execute("SELECT * FROM sessions WHERE session_id=%s", (session_id,)).fetchone()
    if s is None:
        return None
    generated_at = s["updated_at"]
    if generated_at:
        generated_at = datetime.fromtimestamp(generated_at).strftime("%Y-%m-%d %H:%M:%S")
    return {
        "session_id": session_id,
        "profile": loads(s["profile"], {}),
        "results": loads(s["results"], {}),
        "sections": loads(s["ai_sections"], []),
        "generated_at": generated_at,
        "fallback_used": s["status"] == "failed",
    }
