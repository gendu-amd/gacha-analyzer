"""Gacha 抽卡概率分析工具.

建立在 GGanalysis 之上的二次开发：算得准 / 看得懂 / 比得了。
分层：engine(引擎) -> games(游戏) -> analysis(分析) -> viz/cli(表现)。
"""

import os as _os
import tempfile as _tempfile

# 必须在导入 GGanalysis / matplotlib 之前设定可写的 matplotlib 配置目录，避免环境告警。
_os.environ.setdefault(
    "MPLCONFIGDIR", _os.path.join(_tempfile.gettempdir(), "gacha-mpl")
)

__version__ = "0.1.0"
