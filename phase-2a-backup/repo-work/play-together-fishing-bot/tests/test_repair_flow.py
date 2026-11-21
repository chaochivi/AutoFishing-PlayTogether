"""End-to-end repair-state tests: real FishingBot + real input backend (both), scripted screens."""
from __future__ import annotations

import pytest

from autofishing import constants as C
from autofishing.bot import State
from autofishing.bot import fishing_bot as fb
from autofishing.safety import PaidRepairBlocked, RepairDecision, RepairDialog
from conftest import POS, build_bot, d

BAG = POS["bag"]
REPAIR = POS[C.REPAIR_BUTTON]
DONE_BTN = POS[C.REPAIR_DONE_BUTTON]
DONE_TXT = POS[C.REPAIR_DONE_TEXT]
TAB = POS[C.TOOL_TAB]
PAID_POSITIONS = {POS[C.PAID_REPAIR_BUTTON], POS[C.PAID_REPAIR_TEXT]}


def run_repair(script, backend, cycle=False, **cfg):
    bot, keys = build_bot(script, backend, cycle=cycle, **cfg)
    result = bot.s_repair()
    return bot, keys, result


# ------------------------------------------------------------------ paid repair
class TestPaidRepairNeverConfirmed:
    @pytest.mark.parametrize("allow", [False, True])
    @pytest.mark.parametrize("paid", [C.PAID_REPAIR_BUTTON, C.PAID_REPAIR_TEXT])
    def test_paid_dialog_is_not_clicked_and_bot_stops(self, backend, allow, paid):
        bot, keys, res = run_repair([[d(paid)]], backend, allow_paid_repair=allow)
        assert backend.clicks == [BAG]                  # only the backpack tap, nothing else
        assert keys.stopped and res is State.COOLDOWN
        assert bot.stats.repairs == 0
        assert any("NOT confirming" in m for m in bot.logs)

    @pytest.mark.parametrize("allow", [False, True])
    def test_paid_button_plus_text_not_clicked(self, backend, allow):
        run_repair([[d(C.PAID_REPAIR_BUTTON), d(C.PAID_REPAIR_TEXT)]], backend, allow_paid_repair=allow)
        assert backend.clicks == [BAG]

    @pytest.mark.parametrize("allow", [False, True])
    def test_repair_button_alongside_paid_evidence_is_not_clicked(self, backend, allow):
        """Ambiguous: looks like free repair AND paid. Paid wins; nothing clicked."""
        run_repair([[d(C.REPAIR_BUTTON, 0.99), d(C.PAID_REPAIR_TEXT, 0.4)]], backend, allow_paid_repair=allow)
        assert backend.clicks == [BAG]

    def test_done_alongside_paid_evidence_is_not_clicked(self, backend):
        run_repair([[d(C.REPAIR_DONE_BUTTON, 0.99), d(C.PAID_REPAIR_BUTTON, 0.4)]], backend)
        assert backend.clicks == [BAG]

    @pytest.mark.parametrize("allow", [False, True])
    def test_free_repair_click_then_paid_dialog_appears(self, backend, allow):
        """Realistic: tap repair -> cost dialog. The paid confirm must not be tapped."""
        script = [[d(C.REPAIR_BUTTON)]] * 4 + [[d(C.PAID_REPAIR_BUTTON), d(C.PAID_REPAIR_TEXT)]]
        bot, keys, _ = run_repair(script, backend, allow_paid_repair=allow)
        assert REPAIR in backend.clicks
        assert not (set(backend.clicks) & PAID_POSITIONS)
        assert keys.stopped and bot.stats.repairs == 0

    def test_paid_dialog_appearing_during_confirmation_blocks_the_click(self, backend):
        """Screen flips free -> paid between the first look and the pre-click re-check."""
        script = [[d(C.REPAIR_BUTTON)], [d(C.PAID_REPAIR_BUTTON)]]
        bot, keys, _ = run_repair(script, backend)
        assert backend.clicks == [BAG]  # the repair button was NOT clicked
        assert keys.stopped

    def test_paid_never_clicked_even_with_close_coordinates_set(self, backend):
        run_repair([[d(C.PAID_REPAIR_BUTTON)]], backend, close_x=1600, close_y=40)
        assert backend.clicks == [BAG]  # no blind close-tap on top of a paid dialog


# ------------------------------------------------------------------ unknown / ambiguous
class TestUnknownAndAmbiguousBlocked:
    def test_unknown_dialog_never_clicked(self, backend):
        bot, keys, res = run_repair([[]], backend)       # nothing recognised for the whole timeout
        assert backend.clicks == [BAG]
        assert res is State.COOLDOWN
        assert not keys.stopped                           # nothing ambiguous seen -> legacy timeout path
        assert bot.stats.repairs == 0

    def test_unrelated_detections_never_clicked(self, backend):
        run_repair([[d(C.STORE_BUTTON), d(C.TOOL_BROKEN)]], backend)
        assert backend.clicks == [BAG]

    def test_low_confidence_repair_button_not_clicked_and_bot_stops(self, backend):
        bot, keys, _ = run_repair([[d(C.REPAIR_BUTTON, 0.40)]], backend)
        assert backend.clicks == [BAG]
        assert keys.stopped
        assert any("ambiguous" in m for m in bot.logs)

    def test_low_confidence_done_not_clicked(self, backend):
        bot, keys, _ = run_repair([[d(C.REPAIR_DONE_BUTTON, 0.40)]], backend)
        assert backend.clicks == [BAG] and bot.stats.repairs == 0 and keys.stopped

    def test_no_blind_bag_retap_on_unrecognised_screen(self, backend):
        """The old code re-tapped the bag every 6 idle polls; an unrecognised screen may be a dialog."""
        run_repair([[]], backend, repair_timeout_ms=600)
        assert backend.clicks.count(BAG) == 1

    def test_single_frame_flicker_is_not_enough(self, backend):
        script = [[d(C.REPAIR_BUTTON)], []]  # appears one frame at a time, never two in a row
        run_repair(script, backend, cycle=True)
        assert REPAIR not in backend.clicks

    def test_target_jumping_between_frames_is_not_clicked(self, backend):
        from conftest import det
        script = [[det(C.REPAIR_BUTTON, 0.9, 100, 100)], [det(C.REPAIR_BUTTON, 0.9, 900, 700)]]
        run_repair(script, backend, cycle=True)
        assert backend.clicks == [BAG]

    def test_tab_that_never_opens_rod_list_stops_clicking_after_three(self, backend):
        run_repair([[d(C.TOOL_TAB)]], backend, repair_timeout_ms=600)
        assert backend.clicks.count(TAB) == 3


# ------------------------------------------------------------------ free repair preserved
class TestFreeRepairStillWorks:
    def test_free_repair_flow(self, backend):
        script = [[d(C.REPAIR_BUTTON)]] * 4 + [[d(C.REPAIR_DONE_BUTTON)]]
        bot, keys, res = run_repair(script, backend)
        assert backend.clicks[0] == BAG
        assert REPAIR in backend.clicks
        assert backend.clicks[-1] == DONE_BTN
        assert bot.stats.repairs == 1
        assert res is State.COOLDOWN and not keys.stopped

    def test_free_repair_via_done_text_only(self, backend):
        script = [[d(C.REPAIR_BUTTON)]] * 4 + [[d(C.REPAIR_DONE_TEXT)]]
        bot, keys, _ = run_repair(script, backend)
        assert backend.clicks[-1] == DONE_TXT and bot.stats.repairs == 1 and not keys.stopped

    def test_tools_tab_then_repair(self, backend):
        script = [[d(C.TOOL_TAB)]] * 2 + [[d(C.REPAIR_BUTTON)]] * 4 + [[d(C.REPAIR_DONE_BUTTON)]]
        bot, keys, _ = run_repair(script, backend)
        assert backend.clicks[:2] == [BAG, TAB]
        assert REPAIR in backend.clicks and bot.stats.repairs == 1 and not keys.stopped

    def test_rod_slot_and_close_navigation_still_work(self, backend):
        script = [[d(C.TOOL_TAB)]] * 2 + [[d(C.REPAIR_BUTTON)]] * 4 + [[d(C.REPAIR_DONE_BUTTON)]]
        run_repair(script, backend, rod_x=222, rod_y=333, close_x=1600, close_y=40)
        assert (222, 333) in backend.clicks
        assert backend.clicks[-1] == (1600, 40)

    def test_repair_at_exact_min_confidence_works(self, backend):
        script = [[d(C.REPAIR_BUTTON, 0.50)]] * 4 + [[d(C.REPAIR_DONE_BUTTON, 0.50)]]
        bot, _, _ = run_repair(script, backend)
        assert bot.stats.repairs == 1

    def test_min_confidence_is_configurable(self, backend):
        script = [[d(C.REPAIR_BUTTON, 0.40)]] * 4 + [[d(C.REPAIR_DONE_BUTTON, 0.40)]]
        bot, _, _ = run_repair(script, backend, repair_min_confidence=0.30)
        assert bot.stats.repairs == 1

    def test_allow_paid_repair_true_does_not_change_free_flow(self, backend):
        script = [[d(C.REPAIR_BUTTON)]] * 4 + [[d(C.REPAIR_DONE_BUTTON)]]
        bot, keys, _ = run_repair(script, backend, allow_paid_repair=True)
        assert bot.stats.repairs == 1 and not keys.stopped

    def test_confirm_frames_config_cannot_go_below_two(self, backend):
        """repair_confirm_frames=0/1 must not disable the pre-click re-check."""
        script = [[d(C.REPAIR_BUTTON)], [d(C.PAID_REPAIR_BUTTON)]]
        bot, keys, _ = run_repair(script, backend, repair_confirm_frames=1)
        assert backend.clicks == [BAG] and keys.stopped

    def test_normal_gameplay_clicks_still_use_input(self, backend):
        bot, _ = build_bot([[]], backend)
        bot.act(11, 22, "tap")                      # cast / reel / store path (GENERIC intent)
        assert backend.clicks == [(11, 22)]


# ------------------------------------------------------------------ defence in depth
class TestDefenceInDepth:
    def test_input_layer_stops_a_buggy_classifier(self, backend, monkeypatch):
        """If the classifier were wrong and called a paid button 'free', the input layer still refuses."""
        paid = d(C.PAID_REPAIR_BUTTON)
        monkeypatch.setattr(fb, "classify_repair_ui",
                            lambda ui, min_conf=0.5: RepairDecision(RepairDialog.FREE, paid, "bug"))
        bot, keys = build_bot([[paid]], backend, allow_paid_repair=True)
        with pytest.raises(PaidRepairBlocked):
            bot.s_repair()
        assert backend.clicks == [BAG]
        assert not backend.inp.in_repair_session        # session closed even on error (finally)

    def test_session_closed_after_normal_and_aborted_repairs(self, backend):
        run_repair([[d(C.PAID_REPAIR_BUTTON)]], backend)
        assert not backend.inp.in_repair_session
        run_repair([[]], backend)
        assert not backend.inp.in_repair_session

    def test_bot_refuses_repair_if_input_backend_has_no_guard(self):
        from conftest import FakeCap, FakeDetector, FakeKeys, make_cfg
        from autofishing.bot import FishingBot

        class Bare:                       # an input object with no safety layer
            def __init__(self): self.calls = []
            def act(self, *a, **k): self.calls.append(("act", a))
            def click(self, *a, **k): self.calls.append(("click", a))

        cap, keys, inp = FakeCap([[d(C.REPAIR_BUTTON)]]), FakeKeys(), Bare()
        bot = FishingBot(make_cfg(), cap, inp, FakeDetector(cap), keys)
        bot.log = lambda m: None
        assert bot.s_repair() is State.COOLDOWN
        assert keys.stopped and inp.calls == []

    def test_allow_paid_repair_true_logs_warning_at_startup(self):
        from conftest import FakeCap, FakeDetector, FakeKeys, make_cfg
        from autofishing.bot import FishingBot
        import io, contextlib

        cap = FakeCap([[]])
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            FishingBot(make_cfg(allow_paid_repair=True), cap, object(), FakeDetector(cap), FakeKeys())
        assert "IGNORED" in buf.getvalue()
