#!/usr/bin/env python3
"""Reproduce the ten-round parameter search used for the fast-motion profile."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILES = json.loads((ROOT / "profiles/iterations.json").read_text(encoding="utf-8"))
FINAL = json.loads((ROOT / "profiles/optimized-30-to-60.json").read_text(encoding="utf-8"))["filter"]


def score(p: dict) -> float:
    # This is a transparent ranking heuristic, not a claim of measuring image quality.
    div = p.get("flow_div", 4)
    flow = {2: 1.00, 4: 0.86, 8: 0.67}.get(div, 0.40)
    strength = 1.0 - abs(p.get("strength", 1.0) - 1.0) * 0.5
    occl = 1.0 - abs(p.get("occlusion_sensitivity", 0.65) - 0.65) * 0.8
    detect = 1.0 - min(abs(p.get("detect_threshold", 0.10) - 0.10) * 2.0, 1.0)
    latency = 1.0 if p.get("low_latency") else 0.72
    gpu_penalty = {2: 0.04, 4: 0.01, 8: 0.0}.get(div, 0.08)
    return round(0.52*flow + 0.12*strength + 0.16*occl + 0.12*detect + 0.08*latency - gpu_penalty, 4)


def main() -> int:
    print("十轮高速运动参数搜索：")
    ranked = []
    for item in PROFILES:
        params = item["change"]
        s = score(params)
        ranked.append((s, item["iteration"], item["name"]))
        print(f"{item['iteration']:>2}. {item['name']:<10} score={s:.4f} decision={item['decision']}")
    final_score = score(FINAL)
    print()
    print(f"最终配置 score={final_score:.4f}")
    print("说明：分数用于复现参数取舍；实际画面仍应以 OBS 状态栏和快速转镜头测试为准。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
