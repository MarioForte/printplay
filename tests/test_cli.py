from __future__ import annotations

from printplay.i18n import Translator
from printplay.printer import PrintOptions, _confirm


def test_confirm_accepts_yes(monkeypatch) -> None:
    monkeypatch.setattr("builtins.input", lambda prompt: "y")
    assert _confirm(Translator("en"), PrintOptions()) is True


def test_confirm_accepts_empty_answer(monkeypatch) -> None:
    monkeypatch.setattr("builtins.input", lambda prompt: "")
    assert _confirm(Translator("en"), PrintOptions()) is True


def test_confirm_rejects_no(monkeypatch) -> None:
    monkeypatch.setattr("builtins.input", lambda prompt: "n")
    assert _confirm(Translator("en"), PrintOptions()) is False


def test_confirm_skips_prompt_with_yes_flag() -> None:
    assert _confirm(Translator("en"), PrintOptions(yes=True)) is True


def test_confirm_skips_prompt_for_dry_run() -> None:
    assert _confirm(Translator("en"), PrintOptions(dry_run=True)) is True


def test_confirm_cancels_on_eof(monkeypatch) -> None:
    def raise_eof(prompt):
        raise EOFError

    monkeypatch.setattr("builtins.input", raise_eof)
    assert _confirm(Translator("en"), PrintOptions()) is False
