# 十轮优化与测试记录

## 最终参数

- 光流分辨率：1/2
- 插帧强度：1.00
- 遮挡保护：0.65
- 新帧检测阈值：0.10%
- 低延迟：开启

回退配置在 `profiles/fallback-low-gpu.json`：只把光流分辨率降到 1/4，其余抗残影参数不变。

## 参数搜索复现

`scripts/run_optimization.py` 按 `profiles/iterations.json` 复现十轮取舍，输出每轮得分：

```text
 1. 建立基线       score=0.8860 decision=继续
 2. 开启低延迟      score=0.9172 decision=保留
 3. 光流改为 1/8   score=0.8060 decision=淘汰
 4. 光流改为 1/2   score=0.9376 decision=保留
 5. 插帧强度 0.85  score=0.8858 decision=备用
 6. 插帧强度 1.00  score=0.8948 decision=保留
 7. 遮挡保护 0.35  score=0.8564 decision=淘汰
 8. 遮挡保护 0.65  score=0.8948 decision=保留
 9. 新帧阈值 0.10  score=0.8948 decision=保留
10. 最终组合       score=0.9600 decision=采用
```

得分是公开的排序启发式，用来固定参数取舍顺序，不是画质测量值。画面结论仍以 OBS 状态栏和游戏内快速转镜头的主观检查为准。

## 本机验证（2026-11-22 复核）

`python3 scripts/validate_setup.py` 在这台 Mac 上 17 项检查全部 PASS：

- OBS：33.0.2（mac）
- 基础与输出分辨率：1920×1080，fps 60/1
- 采集设备：UGREEN 25854，preset `AVCaptureSessionPreset1920x1080`
- 光流插件：obs-optical-flow 1.0.0，已加载
- 滤镜：`GTA6 30→60 插帧`（optical_flow_interpolation_filter），参数与 `profiles/optimized-30-to-60.json` 一致

OBS 日志 `2026-11-21 23-41-54.txt`（运行到 01:12 关闭）中的性能剖析：

- `obs_graphics_thread(16.6667 ms)`：中位 3.614 ms，99 分位 8.201 ms，99.9966% 的帧在 16.667 ms 预算内
- `render_main_texture`：中位 2.513 ms，99 分位 4.46 ms
- `output_frame`：中位 2.622 ms，99 分位 4.63 ms
- 该次会话没有出现 lagged frames 或渲染延迟告警，退出时内存泄漏计数为 0

也就是说，1/2 光流分辨率在这台 Apple Silicon 机器上跑 1080p60 画布仍有充足余量。

## 单元测试

`python3 -m unittest discover -s tests -v`：8 项全部通过（Python 3.9.6）。覆盖十轮记录完整性、最后一轮与采用配置一致、滤镜示例与采用配置一致、回退配置只改光流分辨率，以及验证脚本对正确/错误滤镜的判定。

本轮修复了两个脚本的语法错误：`scripts/validate_setup.py` 和 `scripts/run_optimization.py` 里的 f-string 被写成了真实换行，且使用了 Python 3.12 才支持的同类引号嵌套，导致脚本无法执行、`test_good_fixture_passes` 失败。修复后两个脚本在 Python 3.9 上正常运行。

## 插件烟雾测试

`scripts/run_plugin_smoke_tests.sh` 需要插件源码树（含 `test/effect-test.c` 等），本机只安装了编译好的 `obs-optical-flow.plugin`，所以本轮没有重跑。上一轮在插件源码目录执行的结果：

- effect-test：全部 effect technique 编译通过
- flow-test：前向流约 `+16 px`，反向流约 `-16 px`，合成位置检查通过
- perf-test：1080p 光流约 `2.66 ms`，插值约 `0.25 ms`

要重跑，先克隆插件源码，再指定目录：

```bash
git clone https://github.com/qshiqshi/obs-optical-flow
OPTICAL_FLOW_DIR=$PWD/obs-optical-flow bash scripts/run_plugin_smoke_tests.sh
```

perf-test 输出里的 `flow_quant` 参数提示不影响检查结果。

## 已知限制

- 插件没有 zh-CN 语言包（安装目录只有 `en-US.ini` 和 `de-DE.ini`），滤镜面板显示英文。`docs/教程.md` 提供了中英对照表。
- 这些测试验证的是插件能加载、shader 能编译、合成算法能运行、配置是否与推荐值一致。残影属于输入画面内容问题，最终还要用游戏里的快速转向、车辆急转弯和剧烈晃动做主观检查。
- 插帧只作用于 OBS 内的采集画面。PS5 直通电视的 HDMI 信号不经过 OBS，帧率不变。

## 出现掉帧时的处理顺序

1. 把 `flow_div` 从 2 改成 4（直接用 `profiles/fallback-low-gpu.json`）。
2. 仍有问题就把插帧强度从 `1.00` 降到 `0.85`。
3. 再不行就关闭其他占用 GPU 的程序，或降低投影窗口分辨率。
