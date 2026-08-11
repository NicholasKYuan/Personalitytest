#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_p0.py — P0 缺陷回归测试 (自包含, 无第三方测试框架依赖)

覆盖:
  a. 最小 profile (仅 age/role/purpose) 全链路: 建会话 -> 随机作答 ->
     免费简评无 "None" 且以 "你的" 开头; 报告接口 200 且正文无 None 泄漏。
  b. 同一份题目下两套完全相反的答案, top_themes 与 MBTI 判型必须不同。
  c. session_id 路径穿越 ("../evil") 在 submit/analyze/report 一律 404,
     且不落任何 evil.json 文件。
  d. 出题确定性: 不同 PYTHONHASHSEED 的两个子进程, 同 profile 的 120 题
     id 序列完全一致 (回归内置 hash() 哈希盐问题)。
  e. 归一化判型单元测试: raw 比较会错判的用例, 归一化后判型正确。

用法:
    <repo>/.venv/bin/python webapp/backend/test_p0.py
测试会用 subprocess 在 8001 端口拉起 uvicorn, 结束时自动杀掉。
"""
import json
import os
import random
import subprocess
import sys
import tempfile
import time
import traceback
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BACKEND_DIR = Path(__file__).parent.resolve()
WEBAPP_DIR = BACKEND_DIR.parent
PROJECT_ROOT = WEBAPP_DIR.parent
SELECTOR_DIR = PROJECT_ROOT / "selector"
BANK_PATH = PROJECT_ROOT / "question-bank" / "items.jsonl"
SESSION_DIR = BACKEND_DIR / "sessions"

_VENV_PY = PROJECT_ROOT / ".venv" / "bin" / "python"
PYTHON = str(_VENV_PY) if _VENV_PY.exists() else sys.executable

PORT = 8001
BASE = f"http://127.0.0.1:{PORT}"

MINIMAL_PROFILE = {"age": 25, "role": "employed", "purpose": "career-planning"}

# 测试期间创建的会话, 结束时清理
_created_sessions = []


# ============================================================
# HTTP 工具 (仅标准库)
# ============================================================
def http_request(method, path, payload=None, timeout=180):
    """返回 (status_code, body_text)。HTTP 错误码不抛异常。"""
    url = BASE + path
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(
        url, data=data, method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8")


def post_json(path, payload, timeout=180):
    status, body = http_request("POST", path, payload, timeout)
    return status, body


def create_session(profile):
    status, body = post_json("/api/session", profile)
    assert status == 200, f"建会话失败: {status} {body[:200]}"
    data = json.loads(body)
    _created_sessions.append(data["session_id"])
    return data


def submit_answers(session_id, answers):
    status, body = post_json(
        "/api/submit", {"session_id": session_id, "answers": answers}
    )
    assert status == 200, f"提交答案失败: {status} {body[:200]}"
    return json.loads(body)


# ============================================================
# 服务器管理
# ============================================================
def start_server(log_file):
    env = dict(os.environ)
    env["MINIMAX_API_KEY"] = "placeholder"
    # 指向本机闭合端口, 让 AI 调用快速失败走降级路径, 测试不出真实网络
    env["MINIMAX_BASE_URL"] = "http://127.0.0.1:9/v1"

    # 端口占用预检
    try:
        http_request("GET", "/api/health", timeout=2)
        raise RuntimeError(f"端口 {PORT} 已被占用, 请先释放再运行测试")
    except (urllib.error.URLError, TimeoutError, ConnectionError, OSError):
        pass

    proc = subprocess.Popen(
        [PYTHON, "-m", "uvicorn", "app:app", "--port", str(PORT)],
        cwd=str(BACKEND_DIR), env=env,
        stdout=log_file, stderr=subprocess.STDOUT,
    )

    deadline = time.time() + 30
    while time.time() < deadline:
        if proc.poll() is not None:
            raise RuntimeError("uvicorn 提前退出, 请查看日志")
        try:
            status, _ = http_request("GET", "/api/health", timeout=2)
            if status == 200:
                return proc
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError):
            pass
        time.sleep(0.5)
    proc.terminate()
    raise RuntimeError("uvicorn 30 秒内未就绪")


def stop_server(proc):
    if proc is None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5)


# ============================================================
# 测试用例
# ============================================================
def test_a_minimal_profile_full_flow():
    """最小 profile 全链路: 免费简评与报告都不得泄漏 None。"""
    data = create_session(MINIMAL_PROFILE)
    sid = data["session_id"]
    questions = data["questions"]
    assert len(questions) == 120, f"应返回 120 题, 实际 {len(questions)}"

    rng = random.Random(20260811)
    answers = [
        {"question_id": q["id"],
         "option_index": rng.randrange(len(q["options"]))}
        for q in questions
    ]
    result = submit_answers(sid, answers)

    summary = result["free_summary"]
    assert summary.startswith("你的"), f"免费简评应以'你的'开头: {summary[:50]}"
    assert "None" not in summary, f"免费简评泄漏 None: {summary[:100]}"

    status, body = http_request("GET", f"/api/report/{sid}")
    assert status == 200, f"报告接口应 200, 实际 {status}: {body[:200]}"
    assert ">None<" not in body, "报告正文出现 >None<"
    assert "None的" not in body, "报告正文出现 None的"


def test_b_opposite_answers_differ():
    """完全相反的两套答案必须得到不同的 top_themes 和 MBTI。"""
    data = create_session(MINIMAL_PROFILE)
    sid = data["session_id"]
    questions = data["questions"]

    answers_first = [
        {"question_id": q["id"], "option_index": 0} for q in questions
    ]
    answers_last = [
        {"question_id": q["id"], "option_index": len(q["options"]) - 1}
        for q in questions
    ]

    r1 = submit_answers(sid, answers_first)["results"]
    r2 = submit_answers(sid, answers_last)["results"]

    t1, t2 = r1["gallup"]["top_themes"], r2["gallup"]["top_themes"]
    m1, m2 = r1["mbti"]["type"], r2["mbti"]["type"]
    assert t1 != t2, f"相反答案 top_themes 竟相同: {t1}"
    assert m1 != m2, f"相反答案 MBTI 竟相同: {m1}"


def test_c_path_traversal_rejected():
    """session_id 传 '../evil' 时三个接口都 404, 且不落盘任何 evil 文件。"""
    evil = "../evil"

    status, body = post_json("/api/submit", {"session_id": evil, "answers": []})
    assert status == 404, f"submit 应 404, 实际 {status}"
    assert "会话不存在" in body, f"submit 404 文案异常: {body[:100]}"

    status, body = post_json("/api/analyze", {"session_id": evil})
    assert status == 404, f"analyze 应 404, 实际 {status}"
    assert "会话不存在" in body, f"analyze 404 文案异常: {body[:100]}"

    # 路径段整体编码, 避免客户端先行归一化 ../
    status, _ = http_request(
        "GET", "/api/report/" + urllib.parse.quote(evil, safe="")
    )
    assert status == 404, f"report 应 404, 实际 {status}"

    # 非 UUID 但无穿越意图的 id 同样 404
    status, _ = http_request("GET", "/api/report/not-a-uuid")
    assert status == 404, "非 UUID session_id 应 404"

    for p in (
        SESSION_DIR / "evil.json",
        BACKEND_DIR / "evil.json",
        WEBAPP_DIR / "evil.json",
        PROJECT_ROOT / "evil.json",
    ):
        assert not p.exists(), f"路径穿越落盘: {p}"


def test_d_selection_deterministic_across_processes():
    """不同 PYTHONHASHSEED 的子进程, 同 profile 出题序列必须一致。"""
    snippet = (
        "import json, sys\n"
        f"sys.path.insert(0, {str(SELECTOR_DIR)!r})\n"
        "from selector import select, load_bank\n"
        f"bank = load_bank({str(BANK_PATH)!r})\n"
        f"profile = json.loads({json.dumps(MINIMAL_PROFILE)!r})\n"
        "qs = select(profile, bank)\n"
        "print(json.dumps([q['id'] for q in qs]))\n"
    )

    id_lists = []
    for hash_seed in ("0", "424242"):
        env = dict(os.environ)
        env["PYTHONHASHSEED"] = hash_seed
        out = subprocess.run(
            [PYTHON, "-c", snippet], env=env,
            capture_output=True, text=True, timeout=120,
        )
        assert out.returncode == 0, f"子进程失败: {out.stderr[:300]}"
        id_lists.append(json.loads(out.stdout.strip()))

    assert len(id_lists[0]) == 120, f"应选 120 题, 实际 {len(id_lists[0])}"
    assert id_lists[0] == id_lists[1], "不同 PYTHONHASHSEED 下出题序列不一致"


def test_e_normalized_typing_unit():
    """归一化判型: raw 比较会错判 I 的用例, 归一化后应判 E。"""
    sys.path.insert(0, str(BACKEND_DIR))
    from scorer import score_answers

    # E 极本卷最大可得 10 分, I 极最大可得 30 分
    questions = [
        {"id": "QS1", "options": [
            {"text": "a", "score": {"mbti.E": 10}},
            {"text": "b", "score": {"mbti.E": 8}},
        ]},
        {"id": "QS2", "options": [
            {"text": "a", "score": {"mbti.I": 30}},
            {"text": "b", "score": {"mbti.I": 12}},
        ]},
    ]
    # raw: E=8, I=12 (raw 比较会错判 I); normalized: E=0.8, I=0.4
    answers = [
        {"question_id": "QS1", "option_index": 1},
        {"question_id": "QS2", "option_index": 1},
    ]
    result = score_answers(questions, answers)

    dims = result["mbti"]["dimensions"]
    assert dims["E"] == 8 and dims["I"] == 12, f"raw 分数不应改变: {dims}"

    norm = result["mbti"]["normalized"]
    assert norm["E"] == 0.8, f"E 归一化应为 0.8, 实际 {norm['E']}"
    assert norm["I"] == 0.4, f"I 归一化应为 0.4, 实际 {norm['I']}"

    assert result["mbti"]["type"][0] == "E", (
        f"归一化后应判 E, 实际 {result['mbti']['type']} (raw 比较会错判 I)"
    )

    # 近平手回归用例: E=1/3≈0.33333, I=1667/5000=0.3340,
    # 差 0.00067, 四舍五入到 3 位小数会变成平手 (0.333 vs 0.334 边界内),
    # 判型必须用未舍入值 → 判 I
    questions2 = [
        {"id": "QT1", "options": [
            {"text": "a", "score": {"mbti.E": 3}},
            {"text": "b", "score": {"mbti.E": 1}},
        ]},
        {"id": "QT2", "options": [
            {"text": "a", "score": {"mbti.I": 5000}},
            {"text": "b", "score": {"mbti.I": 1667}},
        ]},
    ]
    answers2 = [
        {"question_id": "QT1", "option_index": 1},
        {"question_id": "QT2", "option_index": 1},
    ]
    result2 = score_answers(questions2, answers2)
    assert result2["mbti"]["type"][0] == "I", (
        f"近平手 (E=1/3 vs I=0.3340) 应判 I, 实际 {result2['mbti']['type']} "
        "(舍入后比较会错判 E)"
    )


# ============================================================
# 主流程
# ============================================================
def cleanup_sessions():
    for sid in _created_sessions:
        try:
            (SESSION_DIR / f"{sid}.json").unlink(missing_ok=True)
        except OSError:
            pass


def main():
    tests = [
        test_a_minimal_profile_full_flow,
        test_b_opposite_answers_differ,
        test_c_path_traversal_rejected,
        test_d_selection_deterministic_across_processes,
        test_e_normalized_typing_unit,
    ]

    proc = None
    failed = 0
    with tempfile.TemporaryFile(mode="w+", encoding="utf-8") as log_file:
        try:
            print(f"[setup] 启动 uvicorn (port {PORT}) ...")
            proc = start_server(log_file)
            print("[setup] 服务就绪\n")

            for test in tests:
                name = test.__name__
                try:
                    test()
                    print(f"PASS  {name}")
                except Exception:
                    failed += 1
                    print(f"FAIL  {name}")
                    traceback.print_exc()
        except Exception:
            failed += 1
            traceback.print_exc()
            log_file.seek(0)
            tail = log_file.read()[-3000:]
            if tail:
                print("--- uvicorn 日志尾部 ---")
                print(tail)
        finally:
            stop_server(proc)
            cleanup_sessions()

    print()
    if failed:
        print(f"结果: {failed} 个失败")
        return 1
    print("结果: 全部通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
