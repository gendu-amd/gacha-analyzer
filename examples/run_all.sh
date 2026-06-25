#!/usr/bin/env bash
# 运行全部参考场景（原神 · 从零状态）
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
# shellcheck disable=SC1091
source .venv/bin/activate

echo "========== 00: C0 R0 — 1 个 UP 角色 =========="
gacha analyze --copies 1

echo ""
echo "========== 00: 武器基座 R1 前置 — 1 把 UP 武器 =========="
gacha analyze --banner weapon --copies 1

echo ""
echo "========== 01: C0 R1 — 角色 + 武器 =========="
gacha combine --char-copies 1 --weap-copies 1

echo ""
echo "========== 21: C2 R1 — 3 角色拷贝 + R1 武器 =========="
gacha combine --char-copies 3 --weap-copies 1

echo ""
echo "========== 65: C6 R5 — 满命 + 满精 =========="
gacha combine --char-copies 7 --weap-copies 5

echo ""
echo "========== 网格速览 C0~C2 × R0~R1 =========="
gacha grid --max-const 2 --max-refine 1

# --- 可选：星铁 / 绝区零常驻池 ---
if [[ "${RUN_HSR_ZZZ_STANDARD:-}" == "1" ]]; then
  echo ""
  echo "========== HSR 常驻任意 5★ =========="
  gacha analyze --game hsr --banner standard --copies 1
  echo ""
  echo "========== ZZZ 常驻任意 S 级 =========="
  gacha analyze --game zzz --banner standard --copies 1
fi

echo ""
echo "All scenarios completed."
