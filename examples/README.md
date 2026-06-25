# 示例场景（原神 · 从零状态）

本目录提供可复制的参考场景，编码为 **命座×精炼** 两位数：

| 代码 | 含义 | 角色拷贝 | 武器拷贝 |
|------|------|----------|----------|
| **00** | C0 R0 | 1（只要角色本体） | 0 |
| **01** | C0 R1 | 1 | 1（精 1） |
| **21** | C2 R1 | 3（C0+C1+C2） | 1 |
| **65** | C6 R5 | 7（满命） | 5（满精） |

## 期望抽数（从零、小保底、GGanalysis 校验）

| 场景 | 命令 | 期望抽数（约） |
|------|------|----------------|
| 00 角色 | `gacha analyze --copies 1` | **93.45** |
| 00 武器 | `gacha analyze --banner weapon --copies 1` | **86.53** |
| 01 组合 | `gacha combine --char-copies 1 --weap-copies 1` | **179.98** (=93.45+86.53) |
| 21 组合 | `gacha combine --char-copies 3 --weap-copies 1` | **≈373** |
| 65 组合 | `gacha combine --char-copies 7 --weap-copies 5` | **≈1400+** |

组合目标假设角色池与武器池**独立**，总抽数为两者分布的卷积期望之和。

## 快速运行

```bash
cd gacha
. .venv/bin/activate
bash examples/run_all.sh
```

### 星铁 / 绝区零常驻池（可选）

```bash
# 任意 5★ / S 级，期望约 62.30 抽（common_5star）
gacha analyze --game hsr --banner standard --copies 1
gacha analyze --game zzz --banner standard --copies 1
```

## 带水位场景

`states/mid_pity.json` 记录了一组中间水位参数，对应 CLI 标志：

```bash
# 角色垫 50 抽 + 大保底，再抽 1 个 UP
gacha analyze --copies 1 --pity 50 --guaranteed

# 组合：角色大保底垫 50 + 武器无定轨
gacha combine --char-copies 1 --weap-copies 1 \
  --char-pity 50 --char-guaranteed --weap-pity 20
```

## UIGF 样例

`uigf_sample.json` 为演示用 UIGF v4.2 文件（非真实 UID），可用于：

```bash
gacha history --file examples/uigf_sample.json
```
