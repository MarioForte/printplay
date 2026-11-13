# PrintPlay

**English** | [Русский](README.ru.md)

Print-and-play game templates for thermal printers.

PrintPlay generates ready-to-fill game sheets and prints them on TiMini-compatible
Bluetooth thermal printers. It uses [TiMini-Print](https://github.com/Dejniel/TiMini-Print)
as an external engine for printer discovery, paper geometry, protocol handling,
and raster sending.

## Games

- **Sudoku** — difficulty 1–5, unique solution, one or more puzzles per run.
- **Battleship** — 10×10 fields, standard Russian fleet, automatic placement on
  each player's own field, empty enemy waters for marking shots.

Every run generates a new puzzle or fleet. There is no answer key: print again
for a fresh game.

## Requirements

- Python 3.10+
- [TiMini-Print](https://github.com/Dejniel/TiMini-Print) checkout
- A supported Bluetooth thermal printer (tested with **MXW-W5**, 384 px, 203 dpi)
- Pillow (installed in the TiMini-Print virtualenv)

PrintPlay does not copy or vendor TiMini-Print source code. It imports the
package from a local checkout.

## Quick start

Clone both repositories side by side:

```text
projects/
  timini-print/
  printplay/
```

Then run:

```bash
cd printplay
./run.sh
```

`run.sh` uses `../timini-print/.venv/bin/python` and adds the TiMini-Print
checkout to `PYTHONPATH`. If TiMini-Print lives elsewhere:

```bash
TIMINIPRINT_ROOT=/path/to/timini-print ./run.sh
```

## Usage

```bash
# Interactive menu
./run.sh

# Sudoku, difficulty 1-5
./run.sh sudoku --difficulty 3
./run.sh sudoku --difficulty 5 --count 2

# Battleship: two player sets, four fields total
./run.sh battleship --players 2

# Show the plan and ASCII preview without printing
./run.sh sudoku --difficulty 3 --dry-run

# Scan for printers
./run.sh scan

# List known printer models
./run.sh models
```

The short alias works locally too:

```bash
./pnp sudoku --difficulty 3
./pnp battleship --players 2
```

### Battleship layout

For two players PrintPlay prints four separate fields:

1. Player 1 — own fleet, ships already placed;
2. Player 1 — enemy waters, empty grid;
3. Player 2 — own fleet, ships already placed;
4. Player 2 — enemy waters, empty grid.

Each field is a separate fragment. PrintPlay pauses for two seconds between
fields so you can tear off the previous one. Change the pause with `--pause`.

### Sudoku layout

Each puzzle is printed on its own fragment at the full printable width. The grid
uses a 5 mm cell on 384 px / 203 dpi paper. Difficulty 1 is the easiest and 5 is
the hardest; every puzzle has exactly one solution.

## Printer detection

PrintPlay asks TiMini-Print to scan Bluetooth and resolve the printer model,
profile, paper preset, width, and DPI. Nothing is hard-coded to one printer.

For the MXW-W5 the engine selects the `v5x` profile and `plain_384r` paper
(384 px, 203 dpi). If automatic detection fails, override it:

```bash
./run.sh sudoku --difficulty 3 --bluetooth MXW-W5
./run.sh sudoku --difficulty 3 --model v5x
./run.sh sudoku --difficulty 3 --paper tag_384r
```

The default print settings are `--image-mode atkinson` and `--darkness 5`.
On the MXW-W5 the grayscale pipeline prints faint; the 1-bit Atkinson pipeline
prints dark. Use `--image-mode threshold` for crisp line art or `--darkness 1-5`
to adjust density.

## Options

```text
--lang en|ru          Interface language (also PRINTPLAY_LANG)
--model KEY           Printer model override
--bluetooth NAME      Bluetooth name or address
--paper KEY           Paper preset override
--image-mode MODE     atkinson, threshold, floyd_steinberg, bayer_4, bayer_8, grayscale
--darkness 1-5        Print density (default: 5)
--pause SECONDS       Pause between fragments (default: 2.0)
--dry-run             Show the plan and ASCII preview, do not print
--keep-png DIR        Save generated pages to DIR for debugging
--yes                 Skip the confirmation prompt
```

## Development

```bash
cd printplay
PYTHONPATH=".:../timini-print" ../timini-print/.venv/bin/python -m pytest -q
```

The game generators and renderers do not import TiMini-Print, so their tests run
without Bluetooth or printer hardware.

## License

MIT. See [LICENSE](LICENSE).

PrintPlay uses [TiMini-Print](https://github.com/Dejniel/TiMini-Print) as an
external dependency. TiMini-Print is licensed under Apache-2.0. Its source code
is not included in this repository.
