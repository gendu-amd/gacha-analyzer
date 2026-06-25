# 绝区零（Zenless Zone Zero）抽卡机制事实卡

> 用途：作为建模的「事实来源」。数值基于 GGanalysis 与官方公示综合概率。
> 角色频段 50/50（无捕获明光）；音擎频段 75/25（非原神 EP 定轨）。

## 卡池覆盖总览

| 卡池 | banner 键 | 机制 | GGanalysis 模型 | 状态 |
|---|---|---|---|---|
| 独家频段（角色）| `character` | 50/50 + 大保底（无捕获明光）| `up_5star_character` | ✅ 已实现并验证 |
| 音擎频段（武器）| `weapon` | 75/25 + 大保底必出当期（**非 EP 定轨**）| `up_5star_weapon` | ✅ 已实现并验证 |
| 常驻频段（任意S级）| `standard` | 纯保底，无 50/50 | `common_5star` | ✅ 已实现并验证 |
| 新手频段 | — | 一次性 | ❌ GGanalysis 无 | ⬜ 推迟（D23）|
| 4 星频段 | — | 独立保底 | ❌ 未建模 | ⬜ 范围外 |

> 所有「已验证」均指适配层输出与 GGanalysis 对应模型逐点一致（误差 < 1e-12）。

### 联动 / 特殊频段

若出现联动或特殊 UP 频段，**无独立概率模型**：机制与角色频段相同。本项目当前**未实现**绝区零 UIGF 历史还原（`history_policy=None`）。

## 独家频段（Character Channel）

| 机制 | 数值 |
|---|---|
| S 级基础概率 | 0.6% / 抽 |
| S 级软保底起点 | 第 74 抽起 |
| S 级硬保底 | 第 90 抽 100% |
| 50/50 | 出 S 级时 50% 为当期 UP；歪则下个 S 级必为 UP |
| 捕获明光 | **无** |

### 已实测核对（GGanalysis 0.4.2）

- 1 个 UP S 级期望：**≈ 89.55 抽**
- 任意 S 级（常驻频段）期望：**≈ 62.30 抽**

## 音擎频段（W-Engine Channel）

| 机制 | 数值 |
|---|---|
| S 级基础概率 | 0.8% / 抽 |
| S 级硬保底 | 第 80 抽 |
| UP 概率 | 75% 当期 / 25% 常驻；歪则下个 S 级必为当期 |

> **与原神武器池的区别**：绝区零音擎池使用 `up_5star_weapon`（经典 75/25），**没有**原神定轨命定值（EP）。

## 常驻频段（Standard Channel）—— 任意 S 级

| 机制 | 数值 |
|---|---|
| S 级硬保底 | 第 90 抽 |
| 50/50 | **无** |
| GGanalysis | `common_5star` |
| 1 个 S 级期望 | **≈ 62.30 抽** |

`is_guaranteed` / `radiance_losses` 对该池无效。

## 经济参数

- 抽卡货币：菲林，**160 菲林 = 1 抽**。
- 充值：≈ **¥16/抽**。
- 零氪约 **48 抽/月**（社区统计，近似）。

## CLI 示例

```bash
gacha analyze --game zzz --copies 1                    # 独家频段
gacha analyze --game zzz --banner weapon --copies 1      # 音擎频段
gacha analyze --game zzz --banner standard --copies 1    # 常驻任意 S 级
```

## 来源

- GGanalysis `games/zenless_zone_zero/gacha_model.py`
- 官方公示综合概率
