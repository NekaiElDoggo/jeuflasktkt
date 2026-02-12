from gacha_cli import _make_sample_pool, GachaEngine


def test_draw_returns_valid_rarity():
    pool = _make_sample_pool()
    engine = GachaEngine(pool)
    results, pity, guarantee = engine.draw_n(5, start_pity=0)
    assert len(results) == 5
    for item, rarity, was_featured in results:
        assert rarity in (3, 4, 5)
        assert item.rarity == rarity


def test_pity_resets_on_5():
    pool = _make_sample_pool()
    engine = GachaEngine(pool)
    # simulate until a 5-star appears
    pity = 0
    found = False
    for _ in range(200):
        item, rarity, pity, was_featured, guarantee = engine.draw_once(pity)
        if rarity == 5:
            found = True
            assert pity == 0
            break
    assert found
