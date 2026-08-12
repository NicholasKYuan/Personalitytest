#!/usr/bin/env python3
"""端到端 API 测试脚本 - 验证小程序后端全流程"""
import json, time, sys
import urllib.request

BASE = "http://127.0.0.1:8012"
TOKEN = ""
SESSION_ID = ""

def api(method, path, body=None, token=True):
    url = BASE + path
    data = json.dumps(body).encode() if body else None
    headers = {"Content-Type": "application/json"}
    if token and TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(req, timeout=120)
        return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return json.loads(e.read())
    except Exception as e:
        return {"error": str(e)}

def test(name, cond, detail=""):
    status = "PASS" if cond else "FAIL"
    print(f"[{status}] {name}" + (f" - {detail}" if detail else ""))
    return cond

all_pass = True

# 1. Health
r = api("GET", "/api/health", token=False)
all_pass &= test("健康检查", r.get("code") == 0 and r.get("data",{}).get("bank_size") == 2000)

# 2. Login
r = api("POST", "/api/login", {"code": "MOCK_e2e_test_001", "nickname": "测试用户"}, token=False)
TOKEN = r.get("data", {}).get("token", "")
all_pass &= test("微信登录", bool(TOKEN), f"token={TOKEN[:16]}...")
openid = r.get("data", {}).get("openid", "")
all_pass &= test("获取openid", bool(openid), f"openid={openid[:20]}...")

# 3. Create session
r = api("POST", "/api/session", {"name": "小明", "age": 22, "gender": "male", "role": "student-undergrad", "purpose": "career-planning"})
SESSION_ID = r.get("session_id", "")
q_count = len(r.get("questions", []))
all_pass &= test("创建会话", bool(SESSION_ID), f"sid={SESSION_ID[:20]}...")
all_pass &= test("题目数量=120", q_count == 120, f"actual={q_count}")

# 4. Score stripping
qs = r.get("questions", [])
no_score = all("score" not in o for q in qs for o in q.get("options", []))
all_pass &= test("score已剥离", no_score)

# 5. Submit answers
answers = [{"question_id": q["id"], "option_index": 0} for q in qs]
r = api("POST", "/api/submit", {"session_id": SESSION_ID, "answers": answers})
has_results = "results" in r
all_pass &= test("提交答案", has_results)
if has_results:
    res = r["results"]
    enneagram = res.get("enneagram", {}).get("type_name", "?")
    mbti = res.get("mbti", {}).get("type", "?")
    holland = res.get("holland", {}).get("code", "?")
    all_pass &= test("九型结果", bool(enneagram) and enneagram != "?", f"type={enneagram}")
    all_pass &= test("MBTI结果", bool(mbti) and mbti != "?", f"type={mbti}")
    all_pass &= test("霍兰德结果", bool(holland) and holland != "?", f"code={holland}")
    free_summary = r.get("free_summary", "")
    all_pass &= test("免费简述", bool(free_summary), f"len={len(free_summary)}")

# 6. Create order (29.9 yuan)
r = api("POST", "/api/report/order", {"session_id": SESSION_ID})
order_id = r.get("data", {}).get("order_id", "")
pay_params = r.get("data", {}).get("pay_params", {})
all_pass &= test("创建订单", bool(order_id) or "pay_params" in r.get("data", {}), f"resp keys={list(r.get('data',{}).keys())}")
all_pass &= test("支付参数", bool(pay_params), f"keys={list(pay_params.keys())}")
all_pass &= test("金额=2990分", r.get("data", {}).get("amount_fen") == 2990)

# 7. Check status before payment
r = api("GET", f"/api/report/status?session_id={SESSION_ID}")
payment_status = r.get("data", {}).get("payment_status", "")
all_pass &= test("支付状态(支付前)", payment_status in ("unpaid", "pending"), f"status={payment_status}")

# 8. Mock payment success
r = api("POST", "/api/pay/mock_notify", {"session_id": SESSION_ID})
all_pass &= test("模拟支付成功", r.get("code") == 0 or "ok" in str(r).lower(), f"resp={str(r)[:100]}")

# 9. Check status after payment
time.sleep(1)
r = api("GET", f"/api/report/status?session_id={SESSION_ID}")
paid = r.get("data", {}).get("paid", False)
report_status = r.get("data", {}).get("report_status", "")
all_pass &= test("支付状态(支付后)", paid, f"paid={paid}, report_status={report_status}")

# 10. Get report detail (may be generating or ready)
r = api("POST", "/api/report/detail", {"session_id": SESSION_ID})
code = r.get("code", 0)
all_pass &= test("报告详情接口", code in (0, 2001), f"code={code}")
if code == 2001:
    print("[INFO] 报告生成中（预期行为，AI分析需要时间）")
elif code == 0:
    sections = r.get("data", {}).get("report", {}).get("sections", [])
    all_pass &= test("报告章节数", len(sections) > 0, f"count={len(sections)}")

print("\n" + "=" * 50)
print(f"总计: {'ALL PASS' if all_pass else 'SOME FAILED'}")
print("=" * 50)
