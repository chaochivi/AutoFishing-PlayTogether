"""Input-layer enforcement. Every test runs against BOTH DesktopInput and AdbInput
(the `backend` fixture is parametrised) and asserts that blocked actions never
reach the OS / adb layer."""
from __future__ import annotations

import pytest

from autofishing import constants as C
from autofishing.input import AdbInput, DesktopInput
from autofishing.safety import ClickIntent, PaidRepairBlocked


def test_fixture_covers_both_backends(backend):
    assert isinstance(backend.inp, (DesktopInput, AdbInput))


class TestNormalGameplayPreserved:
    def test_generic_click_outside_session_works(self, backend):
        backend.inp.click(10, 20)
        assert backend.clicks == [(10, 20)]

    @pytest.mark.parametrize("mode", ["tap", "hold"])
    def test_act_tap_and_hold_work(self, backend, mode):
        backend.inp.act(30, 40, mode)
        assert backend.clicks == [(30, 40)]

    def test_key_mode_works_outside_session(self, backend):
        backend.inp.act(0, 0, "key")
        assert len(backend.keys) == 1 and backend.clicks == []

    def test_escape_works(self, backend):
        backend.inp.escape()
        assert len(backend.keys) == 1


class TestPaidConfirmAlwaysBlocked:
    @pytest.mark.parametrize("session", [False, True])
    def test_paid_confirm_intent_blocked(self, backend, session):
        if session:
            backend.inp.begin_repair_session()
        with pytest.raises(PaidRepairBlocked):
            backend.inp.click(500, 600, intent=ClickIntent.PAID_REPAIR_CONFIRM)
        assert backend.clicks == []
        assert backend.inp.blocked_actions == 1

    @pytest.mark.parametrize("session", [False, True])
    def test_unknown_dialog_intent_blocked(self, backend, session):
        if session:
            backend.inp.begin_repair_session()
        with pytest.raises(PaidRepairBlocked):
            backend.inp.click(1, 1, intent=ClickIntent.UNKNOWN_DIALOG)
        assert backend.clicks == []

    @pytest.mark.parametrize("target", [C.PAID_REPAIR_BUTTON, C.PAID_REPAIR_TEXT])
    @pytest.mark.parametrize("intent", [ClickIntent.GENERIC, ClickIntent.FREE_REPAIR,
                                         ClickIntent.REPAIR_DONE, ClickIntent.NAVIGATION])
    def test_mislabelled_paid_target_blocked(self, backend, target, intent):
        """Even if the bot mislabels a paid control as 'free repair', the input layer refuses."""
        backend.inp.begin_repair_session()
        with pytest.raises(PaidRepairBlocked):
            backend.inp.click(500, 600, intent=intent, target=target)
        assert backend.clicks == []

    @pytest.mark.parametrize("allow", [False, True])
    def test_allow_paid_repair_true_cannot_bypass(self, backend, allow):
        backend.inp.cfg["allow_paid_repair"] = allow
        backend.inp.begin_repair_session()
        with pytest.raises(PaidRepairBlocked):
            backend.inp.click(500, 600, intent=ClickIntent.PAID_REPAIR_CONFIRM,
                              target=C.PAID_REPAIR_BUTTON)
        with pytest.raises(PaidRepairBlocked):
            backend.inp.act(500, 600, "tap", intent=ClickIntent.PAID_REPAIR_CONFIRM)
        assert backend.clicks == []

    @pytest.mark.parametrize("mode", ["tap", "hold", "key"])
    def test_act_with_blocked_intent_blocked_in_every_mode(self, backend, mode):
        with pytest.raises(PaidRepairBlocked):
            backend.inp.act(1, 1, mode, intent=ClickIntent.PAID_REPAIR_CONFIRM)
        assert backend.clicks == [] and backend.keys == []


class TestRepairSession:
    def test_unlabelled_click_blocked_in_session(self, backend):
        backend.inp.begin_repair_session()
        with pytest.raises(PaidRepairBlocked):
            backend.inp.click(5, 5)
        assert backend.clicks == []

    def test_unlabelled_act_blocked_in_session(self, backend):
        backend.inp.begin_repair_session()
        with pytest.raises(PaidRepairBlocked):
            backend.inp.act(5, 5, "tap")
        assert backend.clicks == []

    @pytest.mark.parametrize("intent", [ClickIntent.NAVIGATION, ClickIntent.TOOLS_TAB,
                                         ClickIntent.FREE_REPAIR, ClickIntent.REPAIR_DONE])
    def test_free_labelled_clicks_work_in_session(self, backend, intent):
        backend.inp.begin_repair_session()
        backend.inp.click(7, 8, intent=intent, target=C.REPAIR_BUTTON)
        assert backend.clicks == [(7, 8)]

    def test_act_navigation_works_in_session(self, backend):
        backend.inp.begin_repair_session()
        backend.inp.act(9, 9, "tap", intent=ClickIntent.NAVIGATION)
        assert backend.clicks == [(9, 9)]

    @pytest.mark.parametrize("key", ["space", "enter"])
    def test_confirm_keys_blocked_in_session(self, backend, key):
        backend.inp.begin_repair_session()
        with pytest.raises(PaidRepairBlocked):
            backend.inp.key(key)
        assert backend.keys == []

    def test_key_mode_act_blocked_in_session(self, backend):
        backend.inp.begin_repair_session()
        with pytest.raises(PaidRepairBlocked):
            backend.inp.act(0, 0, "key", intent=ClickIntent.NAVIGATION)
        assert backend.keys == []

    def test_escape_allowed_in_session(self, backend):
        backend.inp.begin_repair_session()
        backend.inp.escape()
        assert len(backend.keys) == 1

    def test_session_ends_and_gameplay_resumes(self, backend):
        backend.inp.begin_repair_session()
        assert backend.inp.in_repair_session
        backend.inp.end_repair_session()
        assert not backend.inp.in_repair_session
        backend.inp.click(1, 2)
        assert backend.clicks == [(1, 2)]

    def test_sessions_nest(self, backend):
        backend.inp.begin_repair_session()
        backend.inp.begin_repair_session()
        backend.inp.end_repair_session()
        assert backend.inp.in_repair_session
        backend.inp.end_repair_session()
        backend.inp.end_repair_session()  # extra end never goes negative
        assert not backend.inp.in_repair_session

    def test_session_is_per_instance(self, backend):
        backend.inp.begin_repair_session()
        other = type(backend.inp)(backend.inp.cfg, backend.inp.cap)
        assert not other.in_repair_session
