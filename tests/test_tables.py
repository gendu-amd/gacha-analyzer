"""终端表格格式化测试：CJK 显示宽度与对齐（基于 wcwidth）。"""

from gacha.viz.text_width import display_width, ljust_display, rjust_display


def test_display_width_cjk_alignment():
    assert display_width("原神") == 4
    assert display_width("abc") == 3
    padded = ljust_display("原神", 8)
    assert display_width(padded) == 8


def test_display_width_zero_width_and_control():
    # 组合/零宽字符不增加显示宽度；控制字符按 0 宽处理而非报错。
    assert display_width("e\u0301") == 1   # e + combining acute → 显示为单字符宽
    assert display_width("a\tb") == 2       # 制表符不可打印，计 0 宽


def test_rjust_display_cjk():
    padded = rjust_display("原神", 8)
    assert display_width(padded) == 8
    assert padded.endswith("原神")
