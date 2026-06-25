"""UIGF v4.x 抽卡记录标准格式 导入/导出.

参考 https://uigf.org 。顶层按游戏代号分区：hk4e(原神)/hkrpg(星铁)/nap(绝区零)。
关键约定：
- ``time`` 保留原始字符串，绝不转 Date（设备时区≠服务器时区会算错 pity 顺序）。
- pity 顺序以 ``id`` 升序为准，不用本地时间排序。
- ``version`` 形如 ``v4.2``。
"""

from __future__ import annotations

import json
import re
import time as _time
import warnings
from dataclasses import dataclass, field
from typing import Any

# UIGF 游戏代号 <-> 本项目 game key
GAME_CODE_TO_KEY = {"hk4e": "genshin", "hkrpg": "hsr", "nap": "zzz"}
GAME_KEY_TO_CODE = {v: k for k, v in GAME_CODE_TO_KEY.items()}

UIGF_VERSION = "v4.2"
# UIGF 版本号形如 v4.2 / v4.0；不匹配则告警（可能是非标准/损坏文件）。
_VERSION_RE = re.compile(r"^v\d+\.\d+$")
# 单条记录必需字段（缺失则该记录无法用于水位还原，跳过并告警）。
_REQUIRED_RECORD_FIELDS = ("id", "gacha_type")


@dataclass
class GachaRecord:
    """单条抽卡记录（UIGF 字段）。"""

    id: str
    gacha_type: str
    item_id: str
    time: str
    name: str = ""
    rank_type: str = ""
    item_type: str = ""
    count: str = "1"
    uigf_gacha_type: str = ""

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "GachaRecord":
        return cls(
            id=str(d["id"]),
            gacha_type=str(d.get("gacha_type", "")),
            item_id=str(d.get("item_id", "")),
            time=str(d.get("time", "")),
            name=str(d.get("name", "")),
            rank_type=str(d.get("rank_type", "")),
            item_type=str(d.get("item_type", "")),
            count=str(d.get("count", "1")),
            uigf_gacha_type=str(d.get("uigf_gacha_type", d.get("gacha_type", ""))),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "gacha_type": self.gacha_type,
            "item_id": self.item_id,
            "time": self.time,
            "name": self.name,
            "rank_type": self.rank_type,
            "item_type": self.item_type,
            "count": self.count,
            "uigf_gacha_type": self.uigf_gacha_type or self.gacha_type,
        }


@dataclass
class GachaArchive:
    """单个账号（uid）在某游戏下的抽卡记录集合。"""

    game: str  # 本项目 game key，如 "genshin"
    uid: str
    timezone: int = 8
    lang: str = "zh-cn"
    records: list[GachaRecord] = field(default_factory=list)

    def sorted_records(self) -> list[GachaRecord]:
        """按 id 升序（时间先后）返回记录。"""
        return sorted(self.records, key=lambda r: int(r.id))

    def by_uigf_type(self, uigf_gacha_type: str) -> list[GachaRecord]:
        return [r for r in self.sorted_records()
                if (r.uigf_gacha_type or r.gacha_type) == uigf_gacha_type]


@dataclass
class UigfFile:
    """一个 UIGF 文件：info + 各游戏的账号档案。"""

    archives: list[GachaArchive] = field(default_factory=list)
    version: str = UIGF_VERSION
    export_app: str = "gacha"
    export_app_version: str = "0.1.0"
    export_timestamp: int = field(default_factory=lambda: int(_time.time()))

    def archives_for(self, game_key: str) -> list[GachaArchive]:
        return [a for a in self.archives if a.game == game_key]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UigfFile":
        info = data.get("info", {})
        version = str(info.get("version", UIGF_VERSION))
        if not _VERSION_RE.match(version):
            warnings.warn(
                f"UIGF version '{version}' 不符合 ^v\\d+\\.\\d+$ 格式，文件可能非标准或已损坏。",
                stacklevel=2,
            )
        archives: list[GachaArchive] = []
        for code, game_key in GAME_CODE_TO_KEY.items():
            for acc in data.get(code, []) or []:
                records = []
                for r in acc.get("list", []) or []:
                    missing = [f for f in _REQUIRED_RECORD_FIELDS
                               if not str(r.get(f, "")).strip()]
                    if missing:
                        warnings.warn(
                            f"UIGF 记录缺少必需字段 {missing}（uid={acc.get('uid', '?')}），"
                            f"已跳过该条。",
                            stacklevel=2,
                        )
                        continue
                    records.append(GachaRecord.from_dict(r))
                archives.append(
                    GachaArchive(
                        game=game_key,
                        uid=str(acc.get("uid", "")),
                        timezone=int(acc.get("timezone", 8)),
                        lang=str(acc.get("lang", "zh-cn")),
                        records=records,
                    )
                )
        return cls(
            archives=archives,
            version=version,
            export_app=str(info.get("export_app", "gacha")),
            export_app_version=str(info.get("export_app_version", "0.1.0")),
            export_timestamp=int(info.get("export_timestamp", int(_time.time()))),
        )

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "info": {
                "export_timestamp": self.export_timestamp,
                "export_app": self.export_app,
                "export_app_version": self.export_app_version,
                "version": self.version,
            }
        }
        for arch in self.archives:
            code = GAME_KEY_TO_CODE.get(arch.game)
            if code is None:
                continue
            out.setdefault(code, []).append({
                "uid": arch.uid,
                "timezone": arch.timezone,
                "lang": arch.lang,
                "list": [r.to_dict() for r in arch.sorted_records()],
            })
        return out


def load_uigf(path: str) -> UigfFile:
    with open(path, "r", encoding="utf-8") as f:
        return UigfFile.from_dict(json.load(f))


def save_uigf(uigf: UigfFile, path: str) -> str:
    import os

    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(uigf.to_dict(), f, ensure_ascii=False, indent=2)
    return path
