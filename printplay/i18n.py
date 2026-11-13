"""Small, dependency-free CLI localization."""

from __future__ import annotations

import os
import re
import subprocess
from typing import Any

MESSAGES: dict[str, dict[str, str]] = {
    "en": {
        "app_title": "PrintPlay — print-and-play game templates for thermal printers",
        "menu_title": "What do you want to print?",
        "menu_sudoku": "1) Sudoku",
        "menu_battleship": "2) Battleship",
        "menu_scan": "3) Scan for printers",
        "menu_models": "4) List printer models",
        "menu_exit": "0) Exit",
        "menu_choice": "Choice: ",
        "menu_invalid": "Invalid choice.",
        "sudoku_difficulty_prompt": "Difficulty 1-5 [3]: ",
        "sudoku_count_prompt": "How many puzzles [1]: ",
        "battleship_menu_hint": "Each player gets one fragment: own fleet with ships already placed + empty enemy waters.",
        "battleship_players_prompt": "Number of players (1-2) [2]: ",
        "sudoku_title": "SUDOKU",
        "sudoku_number": "No. {number}",
        "sudoku_level_1": "very easy",
        "sudoku_level_2": "easy",
        "sudoku_level_3": "medium",
        "sudoku_level_4": "hard",
        "sudoku_level_5": "expert",
        "battleship_title": "BATTLESHIP",
        "battleship_player": "Player {player}",
        "battleship_own": "Your fleet — ships are pre-placed",
        "battleship_enemy": "Enemy waters — mark your shots",
        "battleship_fleet": "Fleet",
        "battleship_page_label": "Player {player} — {role}",
        "battleship_pair_label": "Player {player} — own fleet + enemy waters",
        "battleship_own_short": "your fleet",
        "battleship_enemy_short": "enemy waters",
        "plan_title": "Print plan",
        "plan_printer": "Printer: {name} ({model}, profile {profile})",
        "plan_paper": "Paper: {paper} · {width} px · {dpi} dpi",
        "plan_pages": "Pages: {count}",
        "plan_pause": "Pause between fragments: {seconds} s",
        "plan_page": "{index}. {label}",
        "printing_page": "Printing {index}/{total}: {label}",
        "printed_page": "Done: {label}",
        "tear_off": "Tear off the fragment. Next page in {seconds} s...",
        "tear_off_short": "tear off",
        "tear_off_last": "Tear off the fragment.",
        "done": "All pages printed.",
        "dry_run_done": "Dry run: nothing was printed.",
        "confirm": "Print now? [Y/n]: ",
        "cancelled": "Cancelled.",
        "no_printer": "No supported printer found. Check that it is awake and paired, then try --scan or --bluetooth NAME.",
        "no_printer_fallback": "No printer found; using the v5x profile for preview.",
        "printer_not_ready": "Printer is not ready: {reasons}. {detail}",
        "scan_title": "Nearby printers:",
        "scan_none": "No supported printers found.",
        "scan_failure": "Scan warning ({transport}): {error}",
        "models_title": "Supported printer models:",
        "error": "Error: {message}",
        "cancelled_interrupt": "Cancelled.",
    },
    "ru": {
        "app_title": "PrintPlay — печатай и играй: шаблоны игр для термопринтера",
        "menu_title": "Что печатаем?",
        "menu_sudoku": "1) Судоку",
        "menu_battleship": "2) Морской бой",
        "menu_scan": "3) Найти принтер",
        "menu_models": "4) Список моделей принтеров",
        "menu_exit": "0) Выход",
        "menu_choice": "Выбор: ",
        "menu_invalid": "Неверный выбор.",
        "sudoku_difficulty_prompt": "Сложность 1-5 [3]: ",
        "sudoku_count_prompt": "Сколько головоломок [1]: ",
        "battleship_menu_hint": "Каждому игроку — один фрагмент: свой флот с уже расставленными кораблями + пустое поле противника.",
        "battleship_players_prompt": "Сколько игроков (1-2) [2]: ",
        "sudoku_title": "СУДОКУ",
        "sudoku_number": "№{number}",
        "sudoku_level_1": "очень легко",
        "sudoku_level_2": "легко",
        "sudoku_level_3": "средне",
        "sudoku_level_4": "сложно",
        "sudoku_level_5": "эксперт",
        "battleship_title": "МОРСКОЙ БОЙ",
        "battleship_player": "Игрок {player}",
        "battleship_own": "Твой флот — корабли уже расставлены",
        "battleship_enemy": "Поле противника — отмечай попадания",
        "battleship_fleet": "Флот",
        "battleship_page_label": "Игрок {player} — {role}",
        "battleship_pair_label": "Игрок {player} — свой флот + поле противника",
        "battleship_own_short": "твой флот",
        "battleship_enemy_short": "поле противника",
        "plan_title": "План печати",
        "plan_printer": "Принтер: {name} ({model}, профиль {profile})",
        "plan_paper": "Бумага: {paper} · {width} px · {dpi} dpi",
        "plan_pages": "Страниц: {count}",
        "plan_pause": "Пауза между фрагментами: {seconds} с",
        "plan_page": "{index}. {label}",
        "printing_page": "Печатаю {index}/{total}: {label}",
        "printed_page": "Готово: {label}",
        "tear_off": "Оторви фрагмент. Следующая страница через {seconds} с...",
        "tear_off_short": "оторвать",
        "tear_off_last": "Оторви фрагмент.",
        "done": "Все страницы напечатаны.",
        "dry_run_done": "Пробный запуск: ничего не напечатано.",
        "confirm": "Печатать? [Y/n]: ",
        "cancelled": "Отменено.",
        "no_printer": "Поддерживаемый принтер не найден. Проверь, что он включён и в паре, затем попробуй --scan или --bluetooth NAME.",
        "no_printer_fallback": "Принтер не найден; для превью используется профиль v5x.",
        "printer_not_ready": "Принтер не готов: {reasons}. {detail}",
        "scan_title": "Принтеры рядом:",
        "scan_none": "Поддерживаемые принтеры не найдены.",
        "scan_failure": "Предупреждение сканирования ({transport}): {error}",
        "models_title": "Поддерживаемые модели принтеров:",
        "error": "Ошибка: {message}",
        "cancelled_interrupt": "Отменено.",
    },
}

SUPPORTED_LANGS = tuple(MESSAGES)


def _macos_languages() -> list[str]:
    """Return the macOS preferred-language list without importing PyObjC."""
    try:
        result = subprocess.run(
            ["defaults", "read", "-g", "AppleLanguages"],
            capture_output=True,
            text=True,
            timeout=2,
        )
    except Exception:
        return []
    if result.returncode != 0:
        return []
    return re.findall(r'"([^"]+)"', result.stdout)


def _language_from_tag(tag: str) -> str | None:
    language = tag.replace("_", "-").split("-", 1)[0].lower()
    return language if language in MESSAGES else None


def detect_lang(explicit: str | None = None) -> str:
    """Pick a language from an explicit value, the OS, or the locale.

    macOS keeps the system language in AppleLanguages even when the terminal
    exports LANG=en_US.UTF-8, so it takes priority over shell locale variables.
    """
    if explicit in MESSAGES:
        return explicit

    env_choice = os.environ.get("PRINTPLAY_LANG")
    if env_choice in MESSAGES:
        return env_choice

    for tag in _macos_languages():
        language = _language_from_tag(tag)
        if language:
            return language

    env = (
        os.environ.get("LC_ALL")
        or os.environ.get("LC_MESSAGES")
        or os.environ.get("LANG")
        or ""
    )
    language = _language_from_tag(env)
    if language:
        return language

    try:
        import locale

        locale_name = locale.getlocale()[0] or ""
    except Exception:
        locale_name = ""
    language = _language_from_tag(locale_name)
    return language or "en"


class Translator:
    def __init__(self, lang: str | None = None) -> None:
        self.lang = detect_lang(lang)

    def __call__(self, key: str, **kwargs: Any) -> str:
        template = MESSAGES[self.lang].get(key) or MESSAGES["en"].get(key) or key
        if not kwargs:
            return template
        return template.format(**kwargs)

    def level(self, number: int) -> str:
        return self(f"sudoku_level_{number}")


__all__ = ["MESSAGES", "SUPPORTED_LANGS", "Translator", "detect_lang"]
