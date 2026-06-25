# 扩展指南（Extensibility）

本文说明如何在不破坏架构的前提下扩展 gacha 工具。核心原则见 `PROJECT_PROPOSAL.md` §6：

```
viz/cli → analysis → io → games → engine
```

**单向依赖**：`engine/` 不得 `import gacha.games.*`；游戏机制通过 `GameSpec` / 依赖注入向上提供。

---

## 1. 新增一款游戏

### 检查清单

1. **确认 GGanalysis 支持**  
   在 REPL 中验证 `GGanalysis.games.<module>` 是否有对应池子的 `up_5star_*` API。

2. **创建 `src/gacha/games/<key>.py`**  
   参考 `games/_template.py` 或 `games/hsr.py`：
   - 定义 `dist_fn(state, copies)` 绑定 GGanalysis
   - 组装 `GameSpec`（经济参数：`currency_per_pull`, `money_per_pull_cny`, `free_pulls_per_month`）
   - 各 `BannerSpec` 填写 `hard_pity`, `has_5050`, `has_capturing_radiance`

3. **注册到 `games/registry.py`**  
   ```python
   from gacha.games.mygame import MYGAME
   _REGISTRY[MYGAME.key] = MYGAME
   ```

4. **（可选）HistoryPolicy**  
   若需 UIGF 历史还原，填充 `history_policy`：
   - `character_uigf_gacha_types`：归入角色历史的 UIGF 类型
   - `detect_standard(record) -> StandardDetection`：游戏专属 50/50 判定（见 `genshin._detect_genshin_standard`）
   - `has_capturing_radiance` / `max_radiance_losses`（如适用）

5. **（可选）reference_mc_mechanism**  
   若该池子需要 MC 交叉校验，在 `BannerSpec` 上设置 `reference_mc_mechanism` 工厂（见原神角色池）。

6. **测试**  
   - `tests/test_<key>.py`：PMF 与 GGanalysis 逐点 `allclose(1e-12)`
   - 期望抽数回归一个社区共识值

7. **文档**  
   - `docs/games/<key>.md` 机制说明
   - `DECISIONS.md` 登记经济参数口径

### 不需要改动的层

- `engine/gg_adapter.py`（通用）
- `analysis/metrics.py`, `combine.py`（通用）
- `cli.py` 子命令（`--game` 已参数化）

---

## 2. 为已有游戏新增卡池

1. 在对应 `games/<key>.py` 的 `banners` 字典增加一项：
   ```python
   BANNER_FOO: BannerSpec(
       key=BANNER_FOO,  # 或在 base.py 新增常量
       name="显示名",
       dist_fn=_foo_dist,
       ...
   )
   ```
2. 若为新池子类型，在 `engine/base.py` 增加 `BANNER_*` 常量（**须登记 DECISIONS**）。
3. 实现 `_foo_dist(state, copies)` → 返回 GGanalysis `FiniteDist`。
4. 添加 pytest 与 GGanalysis 对照。

---

## 3. 新增指标

1. 在 `analysis/metrics.py` 添加纯函数，输入 `PullDistribution` 或 `np.ndarray` pmf。
2. 若需货币换算，使用 `analysis/budget.py` 的 `pulls_to_currency` / `pulls_to_money_cny`。
3. 在 `metrics.summary()` 中注册（若属核心指标）。
4. 可选：CLI `_print_core_metrics` / `viz/report.py` 指标卡展示。
5. 单元测试：手算小例 + 真实分布 sanity check。

**不要**在 `engine/` 或 `games/` 里算派生指标。

---

## 4. 新增 CLI 命令

1. 在 `cli.py` 添加 `_cmd_<name>(args)`。
2. 在 `build_parser()` 注册 `sub.add_parser(...)` 并 `set_defaults(func=...)`。
3. 业务逻辑放在 `analysis/` 或 `io/`，CLI 只做参数解析与打印。
4. 表格输出使用 `gacha.viz.tables` + `gacha.viz.text_width` 保证中文对齐。
5. `tests/test_cli_smoke.py` 或集成测试覆盖 `--help` 与 happy path。

---

## 5. 扩展点 vs 冻结契约

### 可自由扩展

| 位置 | 用途 |
|------|------|
| `games/*.py` | 机制常量、dist_fn、经济参数、HistoryPolicy |
| `analysis/*` | 指标、组合、比对、网格 |
| `viz/*` | 图表、HTML 报告 |
| `io/*` | UIGF、历史还原 |
| `cli.py` | 命令行入口 |

### 冻结（改动须走 DECISIONS.md）

| 位置 | 内容 |
|------|------|
| `engine/base.py` | `PullState`, `Target`, `PullDistribution`, `Solver` Protocol |
| `BANNER_*` 常量 | 池子键全局一致 |
| `max_pulls <= 0` 语义 | 自动上限，求解器可互换 |

已登记的兼容增补见 D34（`source` 字段、`from_finite_dist` 等）。

---

## 6. 常见陷阱

| 陷阱 | 后果 | 对策 |
|------|------|------|
| `engine` import `games` | 循环依赖、架构破坏 | 用 `CharacterMechanism` 等依赖注入 |
| 散落 `"character"` 字符串 | 静默错配 | 使用 `BANNER_CHARACTER` 等常量 |
| 截断分布未归一化 | EV/σ 低估 | `metrics.expectation` 已按 mass 归一化；勿手算未归一化点积 |
| history 只靠角色名 | 新常驻/非中英文不可靠 | 优先 `item_id`，名字回退 |
| 跨游戏直接比基础出率 | 误导结论 | 用 `compare` 模块 + `COMPARE_CAVEAT` |
| `PullState` 大保底但 `losses=0` | 与 GGanalysis 分叉 | 适配层折算 `cr_pity=1`；MC 同步（D28） |
| reference-MC 用于武器池 | 未实现 EP 定轨 | CLI 明确跳过；见 README |

---

## 7. 文件索引

| 任务 | 首要阅读 |
|------|----------|
| 新游戏 | `games/hsr.py`, `games/_template.py`, `registry.py` |
| 新卡池 | `games/genshin.py`（4 池示例） |
| 新指标 | `analysis/metrics.py` |
| 新命令 | `cli.py` |
| UIGF 历史 | `io/history.py`, `games/base.HistoryPolicy` |
| 教学 MC | `engine/reference/mc.py`, `genshin_character_mechanism()` |

---

## 8. 相关文档

- [`PROJECT_PROPOSAL.md`](PROJECT_PROPOSAL.md) — 范围与方法论
- [`DECISIONS.md`](DECISIONS.md) — 架构决策日志
- [`STREAMLIT_DESIGN.md`](STREAMLIT_DESIGN.md) — Web UI 预备设计
- [`examples/README.md`](../examples/README.md) — 可运行参考场景
