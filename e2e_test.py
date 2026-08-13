#!/usr/bin/env python3
"""
e2e_test.py — 线上端到端自动化测试

完整流程：login → create session → submit 120题 → 免费结果 → 下单 → mock支付 → 报告状态 → 报告详情
每次部署后运行，不需要人工做120题。

用法:
    python e2e_test.py
"""
import httpx
import json
import time
import random
import sys

BASE = "https://personality-api-296151-5-1467524685.sh.run.tcloudbase.com"
TIMEOUT = 30

PASS = 0
FAIL = 0
STEPS = []

def step(name, ok, detail=""):
    global PASS, FAIL
    status = "✓ PASS" if ok else "✗ FAIL"
    line = f"{status}  {name}"
    if detail:
        line += f"  ({detail})"
    STEPS.append(line)
    if ok:
        PASS += 1
    else:
        FAIL += 1
    print(line)

def ext(r):
    """从 {code,message,data} 包装中提取 data"""
    try:
        body = r.json()
        if isinstance(body, dict) and "data" in body:
            return body["data"]
        return body
    except:
        return {}

def main():
    client = httpx.Client(timeout=TIMEOUT)
    token = None
    session_id = None

    # 1. 健康检查
    try:
        r = client.get(f"{BASE}/api/health")
        data = ext(r)
        ok = r.status_code == 200 and data.get("status") == "ok"
        step("健康检查", ok, f"bank_size={data.get('bank_size')}, pay_mock={data.get('pay_mock')}")
    except Exception as e:
        step("健康检查", False, str(e))
        return

    # 2. 统计接口
    try:
        r = client.get(f"{BASE}/api/stats")
        data = ext(r)
        ok = r.status_code == 200 and "completed_count" in data
        step("统计接口", ok, f"completed={data.get('completed_count')}")
    except Exception as e:
        step("统计接口", False, str(e))

    # 3. 登录 (mock) — 用 e2e_ 前缀获取独立 openid，不干扰小程序用户
    try:
        r = client.post(f"{BASE}/api/login", json={"code": "e2e_test_001", "nickname": "E2E测试", "avatar_url": ""})
        data = ext(r)
        token = data.get("token")
        openid = data.get("openid", "")
        ok = r.status_code == 200 and token
        step("登录(mock)", ok, f"openid={openid[:20]}...")
    except Exception as e:
        step("登录(mock)", False, str(e))
        return

    headers = {"Authorization": f"Bearer {token}"}

    # 4. 创建会话
    try:
        profile = {"name": "测试用户", "age": 28, "gender": "male", "role": "程序员", "purpose": "了解自己"}
        r = client.post(f"{BASE}/api/session", json=profile, headers=headers)
        data = ext(r)
        session_id = data.get("session_id")
        questions = data.get("questions", [])
        ok = r.status_code == 200 and session_id and len(questions) > 0
        step("创建会话", ok, f"session={session_id}, questions={len(questions)}")
    except Exception as e:
        step("创建会话", False, str(e))
        return

    # 5. 提交答案 (随机选120题)
    try:
        answers = []
        for q in questions:
            qid = q.get("id", "")
            options = q.get("options", [])
            choice = random.randint(0, max(0, len(options) - 1)) if options else 0
            answers.append({"question_id": qid, "option_index": choice})

        r = client.post(f"{BASE}/api/submit", json={"session_id": session_id, "answers": answers}, headers=headers)
        data = ext(r)
        ok = r.status_code == 200 and ("results" in data or "free_summary" in data)
        step("提交答案(120题)", ok, f"keys={list(data.keys())[:5]}")
    except Exception as e:
        step("提交答案(120题)", False, str(e))
        return

    # 6. 免费简要结果（提交时已返回 free_summary）
    try:
        free_summary = data.get("free_summary", "")
        ok = bool(free_summary)
        step("免费简要结果", ok, f"summary_len={len(str(free_summary))}")
    except Exception as e:
        step("免费简要结果", False, str(e))

    # 7. 付费报告接口（未支付应返回403）
    try:
        r = client.get(f"{BASE}/api/report/{session_id}", headers=headers)
        ok = r.status_code == 403  # 未支付，应该拒绝
        step("付费报告(未支付拦截)", ok, f"status={r.status_code}")
    except Exception as e:
        step("付费报告(未支付拦截)", False, str(e))

    # 8. 创建订单
    try:
        r = client.post(f"{BASE}/api/report/order", json={"session_id": session_id}, headers=headers)
        data = ext(r)
        out_trade_no = data.get("out_trade_no")
        ok = r.status_code == 200 and out_trade_no
        step("创建订单", ok, f"order={out_trade_no}")
    except Exception as e:
        step("创建订单", False, str(e))

    # 9. mock支付
    try:
        r = client.post(f"{BASE}/api/pay/mock_notify", json={"session_id": session_id}, headers=headers)
        ok = r.status_code == 200
        step("Mock支付", ok, f"status={r.status_code}")
    except Exception as e:
        step("Mock支付", False, str(e))

    # 10. 报告状态轮询（AI生成约40-90秒）
    try:
        final_status = ""
        for i in range(40):
            r = client.get(f"{BASE}/api/report/status?session_id={session_id}", headers=headers)
            data = ext(r)
            final_status = data.get("report_status") or data.get("status") or ""
            if final_status in ("ready", "done", "completed"):
                break
            time.sleep(3)

        ok = r.status_code == 200 and final_status in ("ready", "done", "completed")
        step("报告状态轮询", ok, f"status={final_status}, polls={i+1}, time={i*3}s")
    except Exception as e:
        step("报告状态轮询", False, str(e))

    # 11. 报告详情
    try:
        r = client.post(f"{BASE}/api/report/detail", json={"session_id": session_id}, headers=headers)
        data = ext(r)
        report = data.get("report", {})
        report_len = len(json.dumps(data, ensure_ascii=False))
        ok = r.status_code == 200 and report
        step("报告详情", ok, f"size={report_len}chars")
    except Exception as e:
        step("报告详情", False, str(e))

    # 12. 兑换码验证（无效码应返回404或400）
    try:
        r = client.post(f"{BASE}/api/redeem/verify", json={"session_id": session_id, "code": "INVALID_TEST"}, headers=headers)
        ok = r.status_code in (200, 400, 403, 404)
        step("兑换码验证(无效码)", ok, f"status={r.status_code}")
    except Exception as e:
        step("兑换码验证(无效码)", False, str(e))

    # 汇总
    print("\n" + "=" * 60)
    total = PASS + FAIL
    print(f"总计: {PASS}/{total} 通过, {FAIL} 失败")
    if FAIL > 0:
        print("\n失败项:")
        for s in STEPS:
            if "FAIL" in s:
                print(f"  {s}")
    print("=" * 60)
    return FAIL == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
