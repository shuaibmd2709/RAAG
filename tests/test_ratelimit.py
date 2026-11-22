from app.ratelimit import RateLimiter


def test_per_minute_limit_and_window():
    t = [0.0]
    rl = RateLimiter(2, 100, clock=lambda: t[0])
    assert rl.check("a") is None and rl.check("a") is None
    assert rl.check("a") is not None          # third request in a minute
    assert rl.check("b") is None              # other client unaffected
    t[0] = 61
    assert rl.check("a") is None              # window has passed


def test_daily_cap_applies_to_everyone():
    rl = RateLimiter(100, 2, clock=lambda: 0.0)
    assert rl.check("a") is None and rl.check("b") is None
    assert rl.check("c") is not None