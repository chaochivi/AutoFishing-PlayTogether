"""Pure-logic tests: dialog classification, click/key policy and config defaults."""
from __future__ import annotations

import os

import pytest
import yaml

from autofishing import constants as C
from autofishing.config import DEFAULTS, load_config
from autofishing.safety import (
    ClickIntent,
    PaidRepairBlocked,
    RepairDialog,
    check_click,
    check_key,
    classify_repair_ui,
    paid_repair_allowed,
)
from conftest import d

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_CONFIG = os.path.join(os.path.dirname(HERE), "config.yaml")


def ui(*dets):
    return {x.name: x for x in dets}


# ---------------------------------------------------------------- classification
class TestClassification:
    def test_generic_repair_button_is_never_proof_of_free_repair(self):
        r = classify_repair_ui(ui(d(C.REPAIR_BUTTON, 0.99)))
        assert r.state is RepairDialog.UNKNOWN
        assert not r.clickable and r.ambiguous
        assert r.intent is ClickIntent.UNKNOWN_DIALOG

    def test_generic_repair_button_at_threshold_is_still_unknown(self):
        r = classify_repair_ui(ui(d(C.REPAIR_BUTTON, 0.50)), 0.50)
        assert r.state is RepairDialog.UNKNOWN and not r.clickable

    def test_low_confidence_repair_button_is_unknown_and_ambiguous(self):
        r = classify_repair_ui(ui(d(C.REPAIR_BUTTON, 0.40)), 0.50)
        assert r.state is RepairDialog.UNKNOWN and not r.clickable and r.ambiguous
        assert r.intent is ClickIntent.UNKNOWN_DIALOG

    def test_empty_screen_is_unknown_not_ambiguous(self):
        r = classify_repair_ui({})
        assert r.state is RepairDialog.UNKNOWN and not r.clickable and not r.ambiguous

    @pytest.mark.parametrize("name", [C.PAID_REPAIR_BUTTON, C.PAID_REPAIR_TEXT])
    @pytest.mark.parametrize("conf", [0.05, 0.35, 0.99])
    def test_any_paid_evidence_is_paid_at_any_confidence(self, name, conf):
        r = classify_repair_ui(ui(d(name, conf)))
        assert r.state is RepairDialog.PAID and not r.clickable
        assert r.intent is ClickIntent.PAID_REPAIR_CONFIRM

    @pytest.mark.parametrize("other", [
        d(C.REPAIR_BUTTON, 0.99), d(C.REPAIR_DONE_BUTTON, 0.99),
        d(C.REPAIR_DONE_TEXT, 0.99), d(C.TOOL_TAB, 0.99),
    ])
    def test_paid_evidence_beats_everything_else(self, other):
        r = classify_repair_ui(ui(other, d(C.PAID_REPAIR_TEXT, 0.4)))
        assert r.state is RepairDialog.PAID

    def test_done_requires_confidence(self):
        assert classify_repair_ui(ui(d(C.REPAIR_DONE_BUTTON, 0.9))).state is RepairDialog.DONE
        low = classify_repair_ui(ui(d(C.REPAIR_DONE_TEXT, 0.4)))
        assert low.state is RepairDialog.UNKNOWN and low.ambiguous

    def test_low_confidence_done_does_not_fall_through_to_free(self):
        r = classify_repair_ui(ui(d(C.REPAIR_DONE_TEXT, 0.4), d(C.REPAIR_BUTTON, 0.99)))
        assert r.state is RepairDialog.UNKNOWN

    def test_done_takes_priority_over_free_when_both_confident(self):
        r = classify_repair_ui(ui(d(C.REPAIR_DONE_BUTTON, 0.9), d(C.REPAIR_BUTTON, 0.9)))
        assert r.state is RepairDialog.DONE

    def test_tab_only_when_no_repair_evidence(self):
        assert classify_repair_ui(ui(d(C.TOOL_TAB))).state is RepairDialog.TAB
        both = classify_repair_ui(ui(d(C.TOOL_TAB), d(C.REPAIR_BUTTON, 0.9)))
        assert both.state is RepairDialog.UNKNOWN and not both.clickable

    def test_low_confidence_repair_with_tab_navigates_tab(self):
        assert classify_repair_ui(ui(d(C.TOOL_TAB), d(C.REPAIR_BUTTON, 0.4))).state is RepairDialog.TAB

    def test_unrelated_classes_are_unknown(self):
        assert classify_repair_ui(ui(d(C.STORE_BUTTON), d(C.TOOL_BROKEN))).state is RepairDialog.UNKNOWN


# ---------------------------------------------------------------- policy functions
class TestPolicy:
    @pytest.mark.parametrize("cfg", [None, {}, {"allow_paid_repair": False}, {"allow_paid_repair": True}])
    def test_paid_repair_never_allowed(self, cfg):
        assert paid_repair_allowed(cfg) is False

    @pytest.mark.parametrize("session", [False, True])
    @pytest.mark.parametrize("intent", [ClickIntent.PAID_REPAIR_CONFIRM, ClickIntent.UNKNOWN_DIALOG])
    def test_blocked_intents_always_raise(self, intent, session):
        with pytest.raises(PaidRepairBlocked):
            check_click(intent, session)

    @pytest.mark.parametrize("session", [False, True])
    @pytest.mark.parametrize("target", [C.PAID_REPAIR_BUTTON, C.PAID_REPAIR_TEXT])
    @pytest.mark.parametrize("intent", list(ClickIntent))
    def test_paid_target_raises_for_every_intent(self, intent, target, session):
        with pytest.raises(PaidRepairBlocked):
            check_click(intent, session, target)

    def test_generic_click_allowed_outside_session(self):
        check_click(ClickIntent.GENERIC, False)  # cast / reel / store keep working

    def test_generic_click_blocked_inside_session(self):
        with pytest.raises(PaidRepairBlocked):
            check_click(ClickIntent.GENERIC, True)

    @pytest.mark.parametrize("intent", [ClickIntent.NAVIGATION, ClickIntent.TOOLS_TAB,
                                         ClickIntent.FREE_REPAIR, ClickIntent.REPAIR_DONE])
    def test_labelled_free_intents_allowed_in_session(self, intent):
        check_click(intent, True, C.REPAIR_BUTTON)

    @pytest.mark.parametrize("key", ["space", "enter", "Enter", "y", "return"])
    def test_confirm_keys_blocked_in_session(self, key):
        with pytest.raises(PaidRepairBlocked):
            check_key(key, True)

    @pytest.mark.parametrize("key", ["esc", "escape", "ESC", "back"])
    def test_cancel_keys_allowed_in_session(self, key):
        check_key(key, True)

    def test_any_key_allowed_outside_session(self):
        check_key("space", False)


# ---------------------------------------------------------------- config
class TestConfigDefaults:
    def test_builtin_default_is_false(self):
        assert DEFAULTS["allow_paid_repair"] is False

    def test_load_config_without_file_defaults_false(self, tmp_path):
        assert load_config(str(tmp_path / "missing.yaml"))["allow_paid_repair"] is False

    def test_config_without_key_defaults_false(self, tmp_path):
        p = tmp_path / "c.yaml"
        p.write_text("backend: window\n")
        assert load_config(str(p))["allow_paid_repair"] is False

    def test_shipped_config_yaml_is_false(self):
        with open(REPO_CONFIG, encoding="utf-8") as f:
            assert yaml.safe_load(f)["allow_paid_repair"] is False
        assert load_config(REPO_CONFIG)["allow_paid_repair"] is False

    def test_true_is_honoured_as_a_value_but_warns(self, tmp_path, capsys):
        p = tmp_path / "c.yaml"
        p.write_text("allow_paid_repair: true\n")
        cfg = load_config(str(p))
        assert cfg["allow_paid_repair"] is True            # not silently rewritten
        assert paid_repair_allowed(cfg) is False            # ...but grants nothing
        assert "NO effect" in capsys.readouterr().err

    def test_default_load_is_silent(self, tmp_path, capsys):
        load_config(str(tmp_path / "missing.yaml"))
        assert capsys.readouterr().err == ""

    def test_evidence_defaults(self):
        assert DEFAULTS["repair_min_confidence"] >= 0.5
        assert DEFAULTS["repair_confirm_frames"] >= 2
