#!/usr/bin/env python3
"""Read-only validation for the macOS OBS GTA6 interpolation setup."""
from __future__ import annotations

import argparse
import configparser
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = json.loads((ROOT / "profiles/optimized-30-to-60.json").read_text(encoding="utf-8"))


def check(name: str, ok: bool, detail: str, failures: list[str]) -> None:
    mark = "PASS" if ok else "FAIL"
    print(f"[{mark}] {name}: {detail}")
    if not ok:
        failures.append(f"{name}: {detail}")


def find_scene(obs_root: Path, requested: str | None) -> Path | None:
    if requested:
        p = Path(requested).expanduser()
        return p if p.exists() else None
    scene_dir = obs_root / "basic" / "scenes"
    candidates = sorted(scene_dir.glob("*.json"))
    for p in candidates:
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if any(
            f.get("id") == "optical_flow_interpolation_filter"
            for s in data.get("sources", [])
            for f in s.get("filters", [])
        ):
            return p
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--obs-root", default="~/Library/Application Support/obs-studio")
    ap.add_argument("--scene-file")
    args = ap.parse_args()
    obs_root = Path(args.obs_root).expanduser()
    failures: list[str] = []

    ini_path = obs_root / "basic" / "profiles" / "未命名" / "basic.ini"
    parser = configparser.ConfigParser()
    parser.read(ini_path, encoding="utf-8")
    video = parser["Video"] if parser.has_section("Video") else {}
    check("OBS 视频配置存在", ini_path.exists() and parser.has_section("Video"), str(ini_path), failures)
    expected_video = {"BaseCX":"1920","BaseCY":"1080","OutputCX":"1920","OutputCY":"1080","FPSCommon":"60"}
    for key, expected in expected_video.items():
        check(f"视频.{key}", video.get(key) == expected, f"当前={video.get(key)!r} 期望={expected!r}", failures)

    module_path = obs_root / "plugin_manager" / "modules.json"
    modules = []
    if module_path.exists():
        try:
            modules = json.loads(module_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    loaded = any(m.get("module_name") == "obs-optical-flow" and m.get("enabled") for m in modules)
    check("光流插件已加载", loaded, str(module_path), failures)

    scene_path = find_scene(obs_root, args.scene_file)
    check("场景文件存在", scene_path is not None, str(scene_path), failures)
    if scene_path:
        data = json.loads(scene_path.read_text(encoding="utf-8"))
        source = next((s for s in data.get("sources", []) if s.get("name") == "视频采集设备"), None)
        check("采集源存在", source is not None, "视频采集设备", failures)
        if source:
            check("采集源为 1080p", source.get("settings", {}).get("preset") == "AVCaptureSessionPreset1920x1080", str(source.get("settings", {})), failures)
            filt = next((f for f in source.get("filters", []) if f.get("id") == "optical_flow_interpolation_filter"), None)
            check("光流滤镜存在", filt is not None, "optical_flow_interpolation_filter", failures)
            if filt:
                settings = filt.get("settings", {})
                for key, expected in EXPECTED["filter"].items():
                    check(f"滤镜.{key}", settings.get(key) == expected, f"当前={settings.get(key)!r} 期望={expected!r}", failures)

    status = "通过" if not failures else "失败"
    print()
    print(f"结果：{status}（{len(failures)} 个问题）")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
