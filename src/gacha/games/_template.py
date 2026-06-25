# 新游戏模板（复制为 `games/mygame.py` 并注册到 `registry.py`）
#
# 详见 docs/EXTENSIBILITY.md
#
# from gacha.engine.base import BANNER_CHARACTER, BANNER_WEAPON, PullState
# from gacha.games.base import BannerSpec, GameSpec
#
# import GGanalysis.games.my_game as MG
#
# def _character_dist(state: PullState, copies: int):
#     up_pity = 1 if state.is_guaranteed else 0
#     return MG.up_5star_character(item_num=copies, item_pity=state.item_pity, up_pity=up_pity)
#
# MYGAME = GameSpec(
#     key="mygame",
#     name="示例游戏",
#     currency_name="代币",
#     currency_per_pull=160,
#     money_per_pull_cny=16.0,
#     money_note="按常规充值档折算（近似）",
#     free_pulls_per_month=50.0,
#     banners={
#         BANNER_CHARACTER: BannerSpec(
#             key=BANNER_CHARACTER,
#             name="角色限定池",
#             top_rarity_label="5★",
#             hard_pity=90,
#             has_5050=True,
#             has_capturing_radiance=False,
#             dist_fn=_character_dist,
#             reference_mc_mechanism=None,  # 可选：MC 校验机制工厂
#         ),
#     },
#     history_policy=None,  # 可选：HistoryPolicy(detect_standard=...)
# )
