"""Command-line interface for PrintPlay."""

from __future__ import annotations

import argparse
import asyncio
import sys
from typing import Optional, Sequence

from . import __version__
from .games.battleship import build_battleship_pages
from .games.sudoku import build_sudoku_pages
from .i18n import Translator
from .printer import PrintOptions, list_models, run_print, scan_printers


def _common_options() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--lang", choices=("en", "ru"), default=argparse.SUPPRESS)
    parser.add_argument("--model", help="Printer model key (default: auto-detect)")
    parser.add_argument("--bluetooth", help="Bluetooth printer name or address")
    parser.add_argument("--paper", help="Paper preset key (default: printer profile default)")
    parser.add_argument(
        "--image-mode",
        choices=("atkinson", "threshold", "floyd_steinberg", "bayer_4", "bayer_8", "grayscale"),
        default="atkinson",
        help="Image conversion mode (default: atkinson)",
    )
    parser.add_argument(
        "--darkness",
        type=int,
        choices=range(1, 6),
        default=5,
        help="Print darkness 1-5 (default: 5)",
    )
    parser.add_argument(
        "--pause",
        type=float,
        default=2.0,
        help="Pause between fragments in seconds (default: 2.0)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Show the plan and ASCII preview, do not print")
    parser.add_argument("--keep-png", metavar="DIR", help="Save generated pages to DIR (debug)")
    parser.add_argument("--yes", "-y", action="store_true", help="Do not ask for confirmation")
    parser.add_argument("-v", "--verbose", action="count", default=argparse.SUPPRESS)
    return parser


def build_parser() -> argparse.ArgumentParser:
    common = _common_options()
    parser = argparse.ArgumentParser(
        prog="printplay",
        description="Print-and-play game templates for thermal printers.",
    )
    parser.add_argument("--version", action="version", version=f"PrintPlay {__version__}")
    parser.add_argument("--lang", choices=("en", "ru"), default=argparse.SUPPRESS)
    parser.add_argument("-v", "--verbose", action="count", default=argparse.SUPPRESS)
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("menu", parents=[common], help="Interactive menu")
    sudoku = subparsers.add_parser("sudoku", parents=[common], help="Print sudoku puzzles")
    sudoku.add_argument(
        "--difficulty",
        type=int,
        choices=range(1, 6),
        default=3,
        help="Difficulty 1-5 (default: 3)",
    )
    sudoku.add_argument("--count", type=int, default=1, help="Number of puzzles (default: 1)")

    battleship = subparsers.add_parser(
        "battleship",
        parents=[common],
        help="Print battleship fields",
    )
    battleship.add_argument(
        "--players",
        type=int,
        choices=(1, 2),
        default=2,
        help="Number of player sets, each with own fleet and enemy waters (default: 2)",
    )
    battleship.add_argument(
        "--auto-ships",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Auto-place ships on each own field (default: yes)",
    )

    subparsers.add_parser("scan", parents=[common], help="Scan for supported printers")
    subparsers.add_parser("models", parents=[common], help="List supported printer models")
    return parser


def _options_from_args(args: argparse.Namespace) -> PrintOptions:
    return PrintOptions(
        model=getattr(args, "model", None),
        bluetooth=getattr(args, "bluetooth", None),
        paper=getattr(args, "paper", None),
        image_mode=getattr(args, "image_mode", "atkinson"),
        darkness=getattr(args, "darkness", 5),
        pause=getattr(args, "pause", 2.0),
        dry_run=getattr(args, "dry_run", False),
        keep_png=getattr(args, "keep_png", None),
        yes=getattr(args, "yes", False),
        verbose=bool(getattr(args, "verbose", 0)),
    )


def _ask_int(t: Translator, prompt: str, minimum: int, maximum: int, default: int) -> int:
    while True:
        try:
            raw = input(prompt).strip()
        except EOFError:
            return default
        if not raw:
            return default
        try:
            value = int(raw)
        except ValueError:
            print(t("menu_invalid"))
            continue
        if minimum <= value <= maximum:
            return value
        print(t("menu_invalid"))


def _ask_yes_no(t: Translator, prompt: str, default: bool) -> bool:
    while True:
        try:
            raw = input(prompt).strip().lower()
        except EOFError:
            return default
        if not raw:
            return default
        if raw in ("y", "yes", "д", "да"):
            return True
        if raw in ("n", "no", "н", "нет"):
            return False
        print(t("menu_invalid"))


def _run_sudoku(level: int, count: int, options: PrintOptions, t: Translator) -> int:
    return asyncio.run(
        run_print(
            lambda width: build_sudoku_pages(
                width=width,
                level=level,
                count=count,
                t=t,
            ),
            options,
            t,
        )
    )


def _run_battleship(
    players: int,
    auto_ships: bool,
    options: PrintOptions,
    t: Translator,
) -> int:
    return asyncio.run(
        run_print(
            lambda width: build_battleship_pages(
                width=width,
                players=players,
                auto_ships=auto_ships,
                t=t,
            ),
            options,
            t,
        )
    )


def run_menu(t: Translator) -> int:
    print(t("app_title"))
    while True:
        print()
        print(t("menu_title"))
        print(t("menu_sudoku"))
        print(t("menu_battleship"))
        print(t("menu_scan"))
        print(t("menu_models"))
        print(t("menu_exit"))
        try:
            choice = input(t("menu_choice")).strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0

        if choice in ("0", "q", "exit", "выход"):
            return 0
        if choice == "1":
            level = _ask_int(t, t("sudoku_difficulty_prompt"), 1, 5, 3)
            count = _ask_int(t, t("sudoku_count_prompt"), 1, 20, 1)
            _run_sudoku(level, count, PrintOptions(pause=2.0), t)
        elif choice == "2":
            print(t("battleship_menu_hint"))
            players = _ask_int(t, t("battleship_players_prompt"), 1, 2, 2)
            auto_ships = _ask_yes_no(t, t("battleship_auto_ships_prompt"), True)
            _run_battleship(players, auto_ships, PrintOptions(pause=2.0), t)
        elif choice == "3":
            asyncio.run(scan_printers(t))
        elif choice == "4":
            list_models(t)
        else:
            print(t("menu_invalid"))


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    lang = getattr(args, "lang", None)
    t = Translator(lang)
    command = args.command or "menu"

    try:
        if command == "menu":
            return run_menu(t)
        if command == "sudoku":
            if args.count < 1:
                raise ValueError("--count must be at least 1")
            return _run_sudoku(args.difficulty, args.count, _options_from_args(args), t)
        if command == "battleship":
            return _run_battleship(
                args.players,
                args.auto_ships,
                _options_from_args(args),
                t,
            )
        if command == "scan":
            return asyncio.run(scan_printers(t))
        if command == "models":
            return list_models(t)
        parser.print_help()
        return 0
    except KeyboardInterrupt:
        print()
        print(t("cancelled_interrupt"))
        return 130
    except Exception as exc:
        try:
            from timiniprint.printing.errors import PrinterNotReadyError
        except Exception:
            PrinterNotReadyError = ()  # type: ignore[assignment]
        if PrinterNotReadyError and isinstance(exc, PrinterNotReadyError):
            reasons = ", ".join(reason.value for reason in exc.reasons)
            print(t("printer_not_ready", reasons=reasons, detail=str(exc)), file=sys.stderr)
            return 2
        if getattr(args, "verbose", 0):
            raise
        print(t("error", message=str(exc)), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
