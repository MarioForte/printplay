# Contributing

Thanks for taking a look at PrintPlay.

## Development setup

PrintPlay expects a TiMini-Print checkout next to this repository:

```text
projects/
  timini-print/
  printplay/
```

Run the tests with the TiMini-Print virtualenv:

```bash
cd printplay
PYTHONPATH=".:../timini-print" ../timini-print/.venv/bin/python -m pytest -q
```

## Guidelines

- Keep changes focused. One behavior per pull request.
- The game generators and renderers must not import TiMini-Print; keep them
  testable without Bluetooth or printer hardware.
- English documentation is the source of truth. Update `README.md` first and
  mirror user-facing changes in `README.ru.md`.
- Do not copy TiMini-Print source code into this repository. Use it as an
  external dependency and keep the attribution in the README.
- Add or update tests for behavior changes.

## License

By contributing you agree that your changes are licensed under the MIT License.
