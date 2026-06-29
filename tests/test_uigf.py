"""UIGF 解析测试：版本正则校验、必需字段校验与跳过。"""

import warnings

import pytest

from gacha.io.uigf import UigfFile


def test_uigf_bad_version_warns():
    data = {"info": {"version": "4.2"}, "hk4e": []}  # 缺前缀 v
    with pytest.warns(UserWarning, match="version"):
        UigfFile.from_dict(data)


def test_uigf_good_version_no_version_warning():
    data = {"info": {"version": "v4.2"}, "hk4e": []}
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        UigfFile.from_dict(data)


def test_uigf_missing_id_record_skipped_with_warning():
    data = {
        "info": {"version": "v4.2"},
        "hk4e": [{
            "uid": "1", "lang": "zh-cn",
            "list": [
                {"id": "1", "gacha_type": "301", "rank_type": "5", "name": "x"},
                {"gacha_type": "301", "rank_type": "3", "name": "y"},  # 缺 id
            ],
        }],
    }
    with pytest.warns(UserWarning, match="必需字段"):
        uigf = UigfFile.from_dict(data)
    arch = uigf.archives_for("genshin")[0]
    assert len(arch.records) == 1  # 缺 id 的被跳过
