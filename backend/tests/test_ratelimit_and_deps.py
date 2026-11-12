import pytest

from app.deps import client_key
from app.ratelimit import SlidingWindowLimiter


class Clock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


def test_allows_up_to_limit_then_blocks_with_retry_after():
    clock = Clock()
    lim = SlidingWindowLimiter(3, 60, clock)
    assert all(lim.check("a")[0] for _ in range(3))
    clock.now = 10
    allowed, retry = lim.check("a")
    assert not allowed and retry == pytest.approx(50)


def test_window_slides():
    clock = Clock()
    lim = SlidingWindowLimiter(3, 60, clock)
    for t in (0, 30, 59):
        clock.now = t
        assert lim.check("a")[0]
    clock.now = 60.5  # first hit has expired, the other two have not
    assert lim.check("a")[0]
    assert not lim.check("a")[0]


def test_keys_are_independent():
    lim = SlidingWindowLimiter(1, 60, Clock())
    assert lim.check("a")[0]
    assert not lim.check("a")[0]
    assert lim.check("b")[0]


def test_invalid_limit():
    with pytest.raises(ValueError):
        SlidingWindowLimiter(0)


class Req:
    def __init__(self, headers=None, host="1.2.3.4"):
        self.headers = headers or {}
        self.client = type("C", (), {"host": host})() if host else None


def test_client_key_ignores_forwarded_header_by_default():
    assert client_key(Req({"x-forwarded-for": "9.9.9.9"}), trust_proxy=False) == "1.2.3.4"


def test_client_key_uses_last_forwarded_entry_when_trusted():
    # Earlier entries are client-supplied and forgeable; the last one was added by our proxy.
    assert client_key(Req({"x-forwarded-for": "6.6.6.6, 7.7.7.7"}), trust_proxy=True) == "7.7.7.7"


def test_client_key_fallbacks():
    assert client_key(Req(), trust_proxy=True) == "1.2.3.4"
    assert client_key(Req(host=None), trust_proxy=False) == "unknown"


# ------------------------------------------------------------- failure throttle
from app.ratelimit import FailureThrottle  # noqa: E402


def test_throttle_blocks_after_max_failures_and_reports_wait():
    clock = Clock()
    t = FailureThrottle(3, 900, clock)
    for _ in range(2):
        t.record_failure("k")
    assert t.retry_after("k") == 0  # two failures: still allowed
    t.record_failure("k")
    clock.now = 100
    assert t.retry_after("k") == pytest.approx(800)


def test_throttle_unblocks_when_old_failures_expire():
    clock = Clock()
    t = FailureThrottle(2, 60, clock)
    t.record_failure("k")
    clock.now = 30
    t.record_failure("k")
    assert t.retry_after("k") == pytest.approx(30)
    clock.now = 61  # the first failure has aged out
    assert t.retry_after("k") == 0


def test_throttle_success_clears_and_keys_are_independent():
    t = FailureThrottle(1, 60, Clock())
    t.record_failure("a")
    assert t.retry_after("a") > 0 and t.retry_after("b") == 0
    t.reset("a")
    assert t.retry_after("a") == 0
    t.reset("never-seen")  # resetting an unknown key is harmless


def test_throttle_checking_does_not_count_as_a_failure():
    t = FailureThrottle(2, 60, Clock())
    for _ in range(10):
        assert t.retry_after("k") == 0
    t.record_failure("k")
    assert t.retry_after("k") == 0


def test_throttle_invalid_limit():
    with pytest.raises(ValueError):
        FailureThrottle(0, 60)


def test_throttle_old_failures_do_not_hide_new_ones():
    # One stale failure must not make the throttle forget that three fresh ones already happened.
    clock = Clock()
    t = FailureThrottle(3, 60, clock)
    t.record_failure("k")  # at t=0, will be stale by t=100
    clock.now = 100
    for _ in range(3):
        t.record_failure("k")
    assert t.retry_after("k") == pytest.approx(60)
