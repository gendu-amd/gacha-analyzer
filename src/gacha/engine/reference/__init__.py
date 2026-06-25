"""学习副线：自研引擎，用于独立校验 GGanalysis + 讲清概率论原理。

不追求性能与覆盖度，仅作为「玻璃盒」教学实现与交叉验证用途。
"""

from gacha.engine.reference.mc import ReferenceMCSolver

__all__ = ["ReferenceMCSolver"]
