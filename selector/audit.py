#!/usr/bin/env python3
"""
题目审核脚本：用 GLM 对一批融合测评题做质检。

输入：question-bank/items.jsonl（一批题目 JSONL，每行一题）
输出：question-bank/audit.json（审核结果 JSON）

环境变量：
  GLM_API_KEY    必填，智谱 API key
  GLM_BASE_URL   可选，默认 https://open.bigmodel.cn/api/paas/v4/
  GLM_MODEL      可选，默认 glm-4-plus；用户指定 glm-5.2 时覆盖

用法：
  python selector/audit.py question-bank/items.jsonl
"""
import os
import sys
import json
import urllib.request
import urllib.error
from pathlib import Path
from typing import List

API_KEY = os.environ.get("GLM_API_KEY")
BASE_URL = os.environ.get("GLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4/").rstrip("/")
MODEL = os.environ.get("GLM_MODEL", "glm-4-plus")

if not API_KEY:
    print("错误：未配置 GLM_API_KEY 环境变量", file=sys.stderr)
    print("  在项目根目录 .env 文件中配置，或设置系统环境变量", file=sys.stderr)
    sys.exit(1)


SYSTEM_PROMPT = """你是测评题目质检专家，专长九型人格（Enneagram）、MBTI、霍兰德职业兴趣（Holland/RIASEC）、盖洛普优势（CliftonStrengths）四大体系的融合测评。请按以下维度对每道题做严格审核，并输出**严格 JSON 格式**（不要 markdown 代码块包装）。

## 审核维度

1. **题干质量**
   - 是否清晰具体（≤30字）？
   - 是否避免双关和复合句？
   - 是否避免社会赞许性偏差（选项不全"正面"）？
   - 是否给出具体情境（具体场景 > 抽象概念）？

2. **选项区分度**
   - 4 个选项是否明显区分 4 种不同人格画像？
   - 是否存在"都对"或"都模糊"的题？
   - forced-choice 题的选项是否互斥而非递进？

3. **计分映射合理性**
   score key 形如 `enneagram.type1` / `mbti.E` / `holland.S` / `gallup.executing`，分值范围 -3~+3。
   - 选项对应画像在该维度上的得分是否逻辑一致？（例：选 E/I 题的"主动找话题"选项是否真的映射 mbti.E 正分？）
   - 是否至少映射 2 个体系？
   - 分值强度是否反映该画像的真实强度？

4. **适用状态标签**
   - applicable_states 是否与题干场景匹配？
   - 是否漏标（题干提到但没标的状态）？
   - 是否错标（题干无关但标了的状态）？

6. **多样性**
   - 与同类别（category）已有题是否重复/过于相似？

## 输出格式（严格 JSON）

```json
{
  "items": [
    {
      "id": "Q0001",
      "verdict": "pass | revise | reject",
      "score": 0,
      "issues": [
        {"dimension": "题干质量|选项区分度|计分映射|状态标签|多样性", "severity": "low|medium|high", "suggestion": "具体修改建议"}
      ],
      "strengths": ["亮点1", "亮点2"]
    }
  ],
  "summary": {
    "total": 0,
    "pass": 0,
    "revise": 0,
    "reject": 0,
    "main_issues": ["本批主要问题1", "本批主要问题2"],
    "recommendation": "整体建议：是否可接受入库/需要返工"
  }
}
```

verdict 判定：
- pass：≤1 个 low issue，无 medium/high issue
- revise：1-3 个 medium issue，或多个 low issue
- reject：≥1 个 high issue，或多个 medium issue"""


def call_glm(messages: list, temperature: float = 0.3) -> str:
    url = f"{BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL,
        "messages": messages,
        "temperature": temperature,
        "response_format": {"type": "json_object"},
    }
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST"
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data["choices"][0]["message"]["content"]


def load_items(path: Path) -> List[dict]:
    items = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    return items


def build_user_prompt(items: List[dict], taxonomy_path: Path, schema_path: Path) -> str:
    taxonomy = taxonomy_path.read_text(encoding="utf-8")
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    # schema 摘要以节省 token
    schema_brief = json.dumps({
        "required": schema["required"],
        "systems_enum": schema["properties"]["systems"]["items"]["enum"],
        "category_enum": schema["properties"]["category"]["enum"],
        "applicable_states_enum": schema["properties"]["applicable_states"]["items"]["enum"],
        "gallup_themes_enum": schema["properties"].get("gallup_themes", {}).get("items", {}).get("enum", []),
        "score_example": schema["properties"]["options"]["items"]["properties"]["score"]["examples"],
        "score_range": "-3 ~ +3",
    }, ensure_ascii=False, indent=2)

    items_json = json.dumps(items, ensure_ascii=False, separators=(",", ":"))

    return f"""## Taxonomy（融合体系与出题原则）
{taxonomy}

## Schema 摘要
{schema_brief}

## 待审核题目批次（共 {len(items)} 题）
{items_json}

请按 system prompt 中定义的审核维度，逐题审核并输出 JSON 格式结果。注意输出必须是合法 JSON，不要任何 markdown 包装。"""


def main():
    if len(sys.argv) < 2:
        print("用法: python selector/audit.py <items.jsonl路径>", file=sys.stderr)
        sys.exit(1)

    items_path = Path(sys.argv[1]).resolve()
    if not items_path.exists():
        print(f"错误：文件不存在 {items_path}", file=sys.stderr)
        sys.exit(1)

    workspace = Path(__file__).resolve().parent.parent
    taxonomy_path = workspace / "question-bank" / "taxonomy.md"
    schema_path = workspace / "question-bank" / "schema.json"

    items = load_items(items_path)
    print(f"加载 {len(items)} 道题目 from {items_path.name}")

    user_prompt = build_user_prompt(items, taxonomy_path, schema_path)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    print(f"调用 {MODEL} 审核...")
    try:
        result = call_glm(messages)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        print(f"API 错误：{e.code} {e.reason}", file=sys.stderr)
        print(body, file=sys.stderr)
        sys.exit(2)

    # 输出路径
    if items_path.name == "items.jsonl":
        output_path = items_path.parent / "audit.json"
    else:
        output_path = items_path.with_name(items_path.stem.replace("items_", "audit_") + ".json")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(result)

    # 简要汇总
    try:
        report = json.loads(result)
        s = report.get("summary", {})
        print(f"\n审核完成：总数 {s.get('total', '?')} / "
              f"通过 {s.get('pass', '?')} / 需修改 {s.get('revise', '?')} / 拒绝 {s.get('reject', '?')}")
        main_issues = s.get("main_issues", [])
        if main_issues:
            print("主要问题：")
            for m in main_issues:
                print(f"  - {m}")
        rec = s.get("recommendation", "")
        if rec:
            print(f"\n整体建议：{rec}")
        print(f"\n完整报告：{output_path}")
    except json.JSONDecodeError:
        print(f"⚠ GLM 返回无法解析为 JSON（可能是模型未严格遵守格式）")
        print(f"原始响应已保存到 {output_path}")


if __name__ == "__main__":
    main()