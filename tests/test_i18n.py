from __future__ import annotations

from printplay.i18n import detect_lang


class _Result:
    def __init__(self, stdout: str, returncode: int = 0) -> None:
        self.stdout = stdout
        self.returncode = returncode


def test_explicit_language_wins(monkeypatch) -> None:
    monkeypatch.setenv("LANG", "ru_RU.UTF-8")
    assert detect_lang("en") == "en"
    assert detect_lang("ru") == "ru"


def test_macos_preferred_language_beats_shell_locale(monkeypatch) -> None:
    monkeypatch.delenv("PRINTPLAY_LANG", raising=False)
    monkeypatch.setenv("LANG", "en_US.UTF-8")
    monkeypatch.setattr(
        "printplay.i18n.subprocess.run",
        lambda *args, **kwargs: _Result('(\n    "ru-RU",\n    "en-US"\n)\n'),
    )
    assert detect_lang() == "ru"


def test_shell_locale_is_used_when_macos_has_no_answer(monkeypatch) -> None:
    monkeypatch.delenv("PRINTPLAY_LANG", raising=False)
    monkeypatch.setenv("LANG", "ru_RU.UTF-8")
    monkeypatch.setattr(
        "printplay.i18n.subprocess.run",
        lambda *args, **kwargs: _Result("", returncode=1),
    )
    assert detect_lang() == "ru"


def test_unknown_language_falls_back_to_english(monkeypatch) -> None:
    monkeypatch.delenv("PRINTPLAY_LANG", raising=False)
    monkeypatch.delenv("LC_ALL", raising=False)
    monkeypatch.delenv("LC_MESSAGES", raising=False)
    monkeypatch.setenv("LANG", "de_DE.UTF-8")
    monkeypatch.setattr(
        "printplay.i18n.subprocess.run",
        lambda *args, **kwargs: _Result("", returncode=1),
    )
    assert detect_lang() == "en"
