#!/usr/bin/env python3
"""
test_fresh_records.py — 清理旧记录 + 生成两份新的完整测评报告

流程：
1. 调用 admin 接口删除所有 e2e 测试会话
2. 用两个不同 e2e code 登录，创建两份不同 profile 的测评
3. 走完整流程：创建会话 → 提交120题 → 下单 → mock支付 → 等待AI报告生成
"""
import httpx
import json
import time
import random
import sys

BASE = "https://personality-api-296151-5-1467524685.sh.run.tcloudbase.com"
ADMIN_USER = "admin"
ADMIN_PASS = "admin123"
TIMEOUT = 30

# 两份测试数据：不同身份/年龄/角色/目的
TEST_PROFILES = [
    {
        "code": "e2e_fresh_01",
        "nickname": "小林",
        "profile": {
            "name": "小林",
            "age": 26,
            "gender": "female",
            "role": "产品经理",
            "purpose": "想了解自己的性格优势，找到适合的职业方向"
        }
    },
    {
        "code": "e2e_fresh_02",
        "nickname": "阿杰",
        "profile": {
            "name": "阿杰",
            "age": 32,
            "gender": "male",
            "role": "设计师",
            "purpose": "希望深入认识自己，改善人际关系"
        }
    }
]


def ext(r):
    """从 {code,message,data} 包装中提取 data"""
    try:
        body = r.json()
        if isinstance(body, dict) and "data" in body:
            return body["data"]
        return body
    except:
        return {}


def cleanup_old_records():
    """删除所有旧 e2e 测试会话"""
    print("=" * 60)
    print("【1】清理旧测试记录")
    print("=" * 60)
    client = httpx.Client(timeout=TIMEOUT)

    # 先看有多少条
    r = client.post(f"{BASE}/api/admin/sessions/delete", json={
        "username": ADMIN_USER,
        "password": ADMIN_PASS,
        "openid_prefix": "mock_openid_e2e_",
        "keep_latest": 0
    })
    data = ext(r)
    print(f"  删除结果: {data}")
    print()
    return data.get("deleted", 0)


def run_one_test(profile_info, index):
    """跑一份完整测评流程"""
    print("=" * 60)
    print(f"【{index + 2}】生成测评报告 #{index + 1}: {profile_info['nickname']}")
    print("=" * 60)

    client = httpx.Client(timeout=TIMEOUT)
    token = None
    session_id = None

    # 登录
    r = client.post(f"{BASE}/api/login", json={
        "code": profile_info["code"],
        "nickname": profile_info["nickname"],
        "avatar_url": ""
    })
    data = ext(r)
    token = data.get("token")
    print(f"  登录: token={token[:20]}..., openid={data.get('openid', '')[:30]}...")
    headers = {"Authorization": f"Bearer {token}"}

    # 创建会话
    r = client.post(f"{BASE}/api/session", json=profile_info["profile"], headers=headers)
    data = ext(r)
    session_id = data.get("session_id")
    questions = data.get("questions", [])
    print(f"  会话: {session_id[:36]}..., 题目数={len(questions)}")

    # 提交答案（随机选，但确保分布不太集中）
    answers = []
    for q in questions:
        qid = q.get("id", "")
        options = q.get("options", [])
        choice = random.randint(0, max(0, len(options) - 1)) if options else 0
        answers.append({"question_id": qid, "option_index": choice})

    r = client.post(f"{BASE}/api/submit", json={
        "session_id": session_id,
        "answers": answers
    }, headers=headers)
    data = ext(r)
    results = data.get("results", {})
    free_summary = data.get("free_summary", "")
    print(f"  提交: results keys={list(results.keys())[:5]}, summary_len={len(str(free_summary))}")

    # 创建订单
    r = client.post(f"{BASE}/api/report/order", json={
        "session_id": session_id
    }, headers=headers)
    data = ext(r)
    order_no = data.get("out_trade_no", "")
    print(f"  订单: {order_no}")

    # mock 支付
    r = client.post(f"{BASE}/api/pay/mock_notify", json={
        "session_id": session_id
    }, headers=headers)
    print(f"  支付: status={r.status_code}")

    # 轮询报告状态
    print(f"  等待AI报告生成...", end="", flush=True)
    final_status = ""
    for i in range(60):
        time.sleep(3)
        r = client.get(f"{BASE}/api/report/status?session_id={session_id}", headers=headers)
        data = ext(r)
        final_status = data.get("report_status", "")
        if final_status in ("ready", "failed"):
            break
        print(".", end="", flush=True)
    print(f" done (status={final_status})")

    # 获取报告
    r = client.post(f"{BASE}/api/report/detail", json={
        "session_id": session_id
    }, headers=headers)
    data = ext(r)
    report = data.get("report", {})
    sections = report.get("sections", [])
    total_chars = sum(len(s.get("content", "")) for s in sections)
    incomplete = sum(1 for s in sections if s.get("incomplete"))
    results = report.get("results", {})

    print(f"  报告: {len(sections)} 章节, {total_chars} 字, 不完整={incomplete}")
    print(f"  结果: {json.dumps(results, ensure_ascii=False)[:200]}")
    print()
    return session_id


def main():
    print()
    print("*" * 60)
    print("  生成两份最新测评报告（清理旧记录）")
    print("*" * 60)
    print()

    # 1. 清理旧记录
    deleted = cleanup_old_records()

    # 2. 生成两份新报告
    session_ids = []
    for i, profile in enumerate(TEST_PROFILES):
        sid = run_one_test(profile, i)
        session_ids.append(sid)

    # 汇总
    print("=" * 60)
    print("汇总")
    print("=" * 60)
    print(f"  旧记录删除: {deleted} 条")
    for i, sid in enumerate(session_ids):
        print(f"  新报告 #{i+1}: {sid}")
    print()
    print("完成!")
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
