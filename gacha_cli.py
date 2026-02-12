"""Prototype CLI pour la logique gacha (pure Python, sans dépendances externes).
Fournit :
- Classes simples Item, Pool, GachaEngine
- Pity system (soft + hard)
- CLI `main()` pour effectuer des tirages
"""
from dataclasses import dataclass
import random
from typing import List, Dict, Tuple


@dataclass
class Item:
    id: int
    name: str
    rarity: int  # ex: 3,4,5
    is_featured: bool = False


class Pool:
    def __init__(self, tag: str, items: List[Item], base_rates: Dict[int, float], soft_start: int = 60, hard_pity: int = 90, featured_5_rate: float = 0.5):
        self.tag = tag
        self.items = items
        self.base_rates = base_rates.copy()  # rarity -> rate (sums ~1.0)
        self.soft_start = soft_start
        self.hard_pity = hard_pity
        self.featured_5_rate = featured_5_rate

    def items_by_rarity(self, rarity: int) -> List[Item]:
        return [it for it in self.items if it.rarity == rarity]

    def featured_items(self, rarity: int) -> List[Item]:
        return [it for it in self.items if it.rarity == rarity and it.is_featured]

    def non_featured_items(self, rarity: int) -> List[Item]:
        return [it for it in self.items if it.rarity == rarity and not it.is_featured]


class GachaEngine:
    def __init__(self, pool: Pool):
        self.pool = pool

    def _effective_rates(self, pity_count: int) -> Dict[int, float]:
        # Compute effective rates applying a simple soft-pity linear increase for 5-star
        rates = self.pool.base_rates.copy()
        base_5 = rates.get(5, 0.0)
        if pity_count >= self.pool.hard_pity:
            # hard pity: guarantee a 5-star
            rates[5] = 1.0
            for r in list(rates.keys()):
                if r != 5:
                    rates[r] = 0.0
            return rates

        if pity_count >= self.pool.soft_start:
            # each pull after soft_start increases 5-star rate by an increment
            # define increment so that by hard_pity it's very likely; simple linear increment
            steps = max(1, self.pool.hard_pity - self.pool.soft_start)
            increment_per_step = (1.0 - base_5) / steps * 0.5  # conservative increase
            extra = (pity_count - self.pool.soft_start + 1) * increment_per_step
            rates[5] = min(1.0, base_5 + extra)
            # normalize other rates proportionally to keep sum=1.0
            non5_total = sum(v for k, v in self.pool.base_rates.items() if k != 5)
            if non5_total > 0:
                scale = max(0.0, 1.0 - rates[5]) / non5_total
                for k in rates:
                    if k != 5:
                        rates[k] = self.pool.base_rates[k] * scale
        return rates

    def _choose_rarity(self, effective_rates: Dict[int, float]) -> int:
        # weighted random based on effective_rates
        items = sorted(effective_rates.items())  # list of (rarity, rate)
        cum = 0.0
        r = random.random()
        for rarity, rate in items:
            cum += rate
            if r < cum:
                return rarity
        # fallback
        return items[-1][0]

    def _choose_item(self, rarity: int, guarantee_featured: bool = False) -> Tuple['Item', bool]:
        # returns (item, was_featured)
        if rarity != 5:
            pool_items = self.pool.items_by_rarity(rarity)
            if not pool_items:
                raise ValueError(f"No items of rarity {rarity} in pool")
            return random.choice(pool_items), False

        # rarity == 5: apply featured / guarantee logic
        featured = self.pool.featured_items(5)
        non_featured = self.pool.non_featured_items(5)
        if guarantee_featured and featured:
            return random.choice(featured), True

        # not guaranteed: roll featured chance
        if featured and random.random() < self.pool.featured_5_rate:
            return random.choice(featured), True

        # otherwise choose non-featured if any, else fallback to featured
        if non_featured:
            return random.choice(non_featured), False
        if featured:
            return random.choice(featured), True
        raise ValueError('No 5-star items in pool')

    def draw_once(self, pity_count: int, guarantee_featured: bool = False) -> Tuple[Item, int, int, bool, bool]:
        """Return (item, rarity, new_pity_count, was_featured, new_guarantee_flag)"""
        if pity_count >= self.pool.hard_pity:
            # guarantee 5-star and respect guarantee_featured
            item, was_featured = self._choose_item(5, guarantee_featured=True)
            # reset pity and guarantee
            return item, 5, 0, was_featured, False

        eff = self._effective_rates(pity_count)
        rarity = self._choose_rarity(eff)
        if rarity == 5:
            item, was_featured = self._choose_item(5, guarantee_featured)
            new_pity = 0
            new_guarantee = False if was_featured else True
        else:
            item, _ = self._choose_item(rarity)
            new_pity = pity_count + 1
            new_guarantee = guarantee_featured
            was_featured = False
        return item, rarity, new_pity, was_featured, new_guarantee

    def draw_n(self, n: int, start_pity: int = 0, start_guarantee: bool = False) -> Tuple[List[Tuple[Item, int, bool]], int, bool]:
        results = []
        pity = start_pity
        guarantee = start_guarantee
        for _ in range(n):
            item, rarity, pity, was_featured, guarantee = self.draw_once(pity, guarantee)
            results.append((item, rarity, was_featured))
        return results, pity, guarantee


def _make_sample_pool() -> Pool:
    # create a small sample pool with a few items per rarity
    items = []
    idc = 1
    for i in range(3):
        items.append(Item(idc, f"3★_Common_{i+1}", 3)); idc += 1
    for i in range(2):
        items.append(Item(idc, f"4★_Rare_{i+1}", 4)); idc += 1
    # mark the 5-star as featured
    items.append(Item(idc, "5★_Legendary_1", 5, is_featured=True)); idc += 1

    base_rates = {5: 0.01, 4: 0.05, 3: 0.94}
    return Pool(tag="standard", items=items, base_rates=base_rates)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Prototype Gacha CLI")
    parser.add_argument("-n", type=int, default=10, help="number of pulls")
    args = parser.parse_args()

    pool = _make_sample_pool()
    engine = GachaEngine(pool)
    pity = 0
    results, pity = engine.draw_n(args.n, start_pity=pity)

    counts = {}
    for item, rarity, was_featured in results:
        feat_str = " (featured)" if was_featured else ""
        counts.setdefault(rarity, 0)
        counts[rarity] += 1
        print(f"Pulled: {item.name} ({rarity}★){feat_str}")

    print("--- Summary ---")
    for r in sorted(counts.keys(), reverse=True):
        print(f"{r}★ : {counts[r]}")
    print(f"Ending pity: {pity}")


if __name__ == '__main__':
    main()

