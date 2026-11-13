from __future__ import annotations

from PIL import Image

from printplay.i18n import Translator
from printplay.printer import PrinterInfo, PrintOptions, _confirm, _print_plan
from printplay.rendering import Page


def test_print_plan_hides_printer_details(capsys) -> None:
    info = PrinterInfo(
        display_name="MXW-W5",
        model_key="v5x",
        profile_key="v5x",
        paper_key="plain_384r",
        width=384,
        dpi=203,
        address="AA:BB:CC:DD:EE:FF",
    )
    page = Page(image=Image.new("L", (384, 10), 255), label="Puzzle")
    _print_plan(info, [page], PrintOptions(), Translator("en"))
    output = capsys.readouterr().out
    assert "Printer" not in output
    assert "MXW-W5" not in output
    assert "plain_384r" in output


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
