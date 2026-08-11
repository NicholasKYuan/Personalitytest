#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_static_data.py — 把 question-bank/items.jsonl 转成 docs/data/items.json

用于 GitHub Pages 纯前端部署：浏览器一次 fetch 加载全部题库。
输出为紧凑 JSON 数组（无缩进、无多余空格），保持题目原始字段不变。

用法:
    python3 scripts/build_static_data.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "question-bank" / "items.jsonl"
OUT_DIR = ROOT / "docs" / "data"
OUT = OUT_DIR / "items.json"


def main():
    items = []
    with open(SRC, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, separators=(",", ":"))

    size_kb = OUT.stat().st_size / 1024
    print(f"已生成 {OUT}（{len(items)} 题，{size_kb:.0f} KB）")


if __name__ == "__main__":
    main()
