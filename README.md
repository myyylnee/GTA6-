# GTA6 采集卡 30→60 OBS 光流插帧优化

这个仓库整理了一套适合 **PS5 → UGREEN 25854 → macOS OBS** 的实时光流插帧配置。目标是让采集卡输入的 30 FPS 画面在 OBS 里以 60 FPS 预览，并重点减少快速转视角、急转镜头和剧烈晃动时的残影。

## 当前推荐配置

| 项目 | 值 |
|---|---:|
| 采集分辨率 | 1920×1080 |
| OBS 画布与输出帧率 | 60 FPS |
| 光流分辨率 | 1/2 |
| 插帧强度 | 100% |
| 遮挡保护 | 65% |
| 新帧检测阈值 | 0.10% |
| 低延迟模式 | 开启 |
| 调试视图 | 关闭 |

1/2 光流会比 1/4 多占一些 GPU，但快速运动的边缘匹配更准确。遮挡保护提高后，遇到不可靠的运动向量会更多地回退到安全混合，能减少人物、车辆和建筑边缘的拖影。

掉帧时改用 `profiles/fallback-low-gpu.json`：只把光流分辨率降到 1/4，其余抗残影参数保持不变。

## 先看清楚效果范围

PS5 游戏本身仍然按原始帧率运行。这个方案只处理 OBS 里的采集画面，所以提升的是 OBS 预览、投影窗口和录制画面的运动连续性。PS5 直通电视的 HDMI 画面不会经过 OBS 插帧。

## 快速开始

1. 安装 OBS Studio，并安装 [obs-optical-flow](https://github.com/qshiqshi/obs-optical-flow)。
2. OBS → 设置 → 视频：基础（画布）分辨率和输出分辨率都设为 `1920×1080`，常用 FPS 值设为 `60`。
3. 在“视频采集设备”上打开“滤镜”，添加 `Optical Flow Frame Interpolation`。
4. 按上面的推荐配置填写参数。插件没有中文语言包，面板是英文，中英对照见 `docs/教程.md`。
5. 右键“视频采集设备” → 投影，使用“窗口投影（源）”查看插帧后的采集画面。
6. 运行检查：

```bash
python3 scripts/validate_setup.py      # 只读本机 OBS 配置，17 项检查
python3 scripts/run_optimization.py    # 复现十轮参数搜索与得分
python3 -m unittest discover -s tests -v
```

脚本在 Python 3.9 及以上都能跑。`validate_setup.py` 只读 macOS 的 OBS 配置目录，非 macOS 环境请用 `tests/` 里的 fixture 测试。

## 目录说明

- `profiles/optimized-30-to-60.json`：当前推荐参数。
- `profiles/fallback-low-gpu.json`：掉帧时的低负载回退参数。
- `profiles/iterations.json`：十轮优化过程和每轮取舍。
- `config/filter-settings.example.json`：滤镜参数示例，可直接对照填写。
- `config/obs-video-settings.example.ini`：OBS 视频设置示例。
- `scripts/validate_setup.py`：检查本机 OBS 配置是否符合推荐值。
- `scripts/run_optimization.py`：复现十轮参数搜索和评分。
- `scripts/run_plugin_smoke_tests.sh`：编译并运行插件自带的 effect、flow、perf 测试。
- `docs/教程.md`：面向新手的完整教程。
- `reports/optimization-results.md`：测试结果和已知限制。

## 发现残影时的调整顺序

先保持 1/2 光流和 65% 遮挡保护。如果仍然残影，把插帧强度从 `1.00` 降到 `0.85`；如果画面变得像淡入淡出，再恢复到 `1.00`。如果 OBS 状态栏出现渲染延迟或掉帧，把光流分辨率改回 1/4。

不要把“窗口投影”当成 PS5 原生 60 FPS。插帧生成的是中间画面，快速运动时仍可能出现轻微变形，这是光流根据前后帧推测运动的结果。

## 测试结论

本机已验证（2026-11-22 复核，OBS 33.0.2）：

- `validate_setup.py` 17 项检查全部 PASS，滤镜参数与推荐配置一致。
- 单元测试 8 项全部通过。
- 开启 1/2 光流跑 1080p60 画布的 OBS 会话中，`obs_graphics_thread` 中位 3.614 ms、99 分位 8.201 ms，99.9966% 的帧在 16.667 ms 预算内，无 lagged frames 告警。
- 插件独立烟雾测试（上一轮在插件源码目录执行）：effect 与 flow 测试通过，1080p 光流约 `2.66 ms`、插值约 `0.25 ms`。

完整数据、复现命令和已知限制见 `reports/optimization-results.md`。
