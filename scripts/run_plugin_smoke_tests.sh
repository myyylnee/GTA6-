#!/usr/bin/env bash
# 编译并运行 obs-optical-flow 自带的 effect / flow / perf 测试。
# 需要插件源码树（本机安装的 .plugin 只有编译产物，没有 test/*.c）：
#   git clone https://github.com/qshiqshi/obs-optical-flow
#   OPTICAL_FLOW_DIR=$PWD/obs-optical-flow bash scripts/run_plugin_smoke_tests.sh
# 可选环境变量：OBS_APP（默认 /Applications/OBS.app）
set -euo pipefail

PLUGIN_DIR="${OPTICAL_FLOW_DIR:-}"
if [[ -z "$PLUGIN_DIR" || ! -f "$PLUGIN_DIR/data/effects/optical-flow.effect" ]]; then
  echo "用法：OPTICAL_FLOW_DIR=/path/to/obs-optical-flow $0"
  echo "先克隆源码：git clone https://github.com/qshiqshi/obs-optical-flow"
  exit 2
fi

OBS_APP="${OBS_APP:-/Applications/OBS.app}"
HEADERS="$PLUGIN_DIR/deps/libobs-headers"
BUILD="$PLUGIN_DIR/build/gta6-smoke"
mkdir -p "$BUILD"
CFLAGS=(-std=c17 -O1 -arch arm64 -I"$HEADERS" -F "$OBS_APP/Contents/Frameworks" -framework libobs -Wl,-rpath,"$OBS_APP/Contents/Frameworks")

clang "${CFLAGS[@]}" -o "$BUILD/effect-test" "$PLUGIN_DIR/test/effect-test.c"
clang "${CFLAGS[@]}" -o "$BUILD/flow-test" "$PLUGIN_DIR/test/flow-test.c"
clang "${CFLAGS[@]}" -o "$BUILD/perf-test" "$PLUGIN_DIR/test/perf-test.c"

"$BUILD/effect-test" "$PLUGIN_DIR/data/effects/optical-flow.effect"
"$BUILD/flow-test" "$PLUGIN_DIR/data/effects/optical-flow.effect"
(
  cd "$PLUGIN_DIR"
  "$BUILD/perf-test"
)
