# Adapter GachaEngine from gacha_cli for use in Flask app
from gacha_cli import GachaEngine


class GachaService:
    def __init__(self, engine: GachaEngine):
        self.engine = engine

    def draw_n(self, n: int, start_pity: int = 0, start_guarantee: bool = False):
        results, pity, guarantee = self.engine.draw_n(n, start_pity, start_guarantee)
        # convert Item objects to dict, include was_featured
        out = []
        for item, rarity, was_featured in results:
            out.append({"id": item.id, "name": item.name, "rarity": rarity, "featured": was_featured})
        return out, pity, guarantee
