# PrintPlay

[English](README.md) | **Русский**

Печатай и играй: шаблоны игр для термопринтера.

PrintPlay генерирует готовые к заполнению игровые листы и печатает их на
Bluetooth-термопринтерах, совместимых с TiMini-Print. В качестве движка
используется [TiMini-Print](https://github.com/Dejniel/TiMini-Print): он
отвечает за поиск принтера, геометрию бумаги, протокол и отправку растра.

## Игры

- **Судоку** — сложность 1–5, единственное решение, одна или несколько
  головоломок за запуск.
- **Морской бой** — поля 10×10, стандартный русский флот, авторасстановка на
  своём поле каждого игрока, пустое поле противника для отметок.

Каждый запуск создаёт новую головоломку или новую расстановку кораблей. Ответов
нет: чтобы получить новую игру, просто напечатайте ещё раз.

## Требования

- Python 3.10+
- Локальный клон [TiMini-Print](https://github.com/Dejniel/TiMini-Print)
- Поддерживаемый Bluetooth-термопринтер (проверено на **MXW-W5**, 384 px, 203 dpi)
- Pillow (уже установлен в virtualenv TiMini-Print)

PrintPlay не копирует и не вендорит исходники TiMini-Print. Пакет импортируется
из локального клона.

## Быстрый старт

PrintPlay — тонкая надстройка над TiMini-Print, поэтому нужны оба репозитория.
PrintPlay **не создаёт virtualenv автоматически**: он использует окружение из
клона TiMini-Print.

### 1. Клонируйте оба репозитория рядом

```bash
mkdir -p ~/projects
cd ~/projects

git clone https://github.com/Dejniel/TiMini-Print.git timini-print
git clone https://github.com/MarioForte/printplay.git printplay
```

### 2. Создайте virtualenv TiMini-Print и установите зависимости

```bash
cd ~/projects/timini-print
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
```

Если используешь [`uv`](https://docs.astral.sh/uv/):

```bash
uv venv .venv -p 3.13
uv pip install --python .venv/bin/python -r requirements.txt
```

### 3. Запустите PrintPlay

```bash
cd ~/projects/printplay
./run.sh
```

`run.sh` использует `../timini-print/.venv/bin/python` и добавляет клон
TiMini-Print в `PYTHONPATH`. Если TiMini-Print лежит в другом месте:

```bash
TIMINIPRINT_ROOT=/path/to/timini-print ./run.sh
```

### 4. Опционально: установите команды `printplay` и `pnp`

```bash
cd ~/projects/printplay
python3 -m pip install -e ".[dev]"
printplay --version
pnp --version
```

Установленным командам всё равно нужен TiMini-Print. PrintPlay сам находит
`../timini-print` или использует `TIMINIPRINT_ROOT`.

### Если принтер не найден

- Убедись, что принтер включён и находится в паре.
- На macOS разреши доступ к Bluetooth, когда система спросит.
- Запусти `./run.sh scan`.
- Попробуй `./run.sh sudoku --bluetooth MXW-W5` или `./run.sh sudoku --model v5x`.

### Зависимости на GitHub

- Pillow объявлен в `pyproject.toml`, поэтому GitHub dependency graph может его
  показать, а Dependabot — обновлять.
- TiMini-Print не является pip-пакетом. Он клонируется отдельно и не попадает
  в Python dependency graph.
- `.github/dependabot.yml` обновляет Python- и GitHub Actions-зависимости.

## Использование

```bash
# Интерактивное меню
./run.sh
# Язык интерфейса определяется по системе. Принудительно: --lang en|ru
# или PRINTPLAY_LANG=en|ru.

# Судоку, сложность 1-5
./run.sh sudoku --difficulty 3
./run.sh sudoku --difficulty 5 --count 2

# Морской бой: два комплекта, итого четыре поля
./run.sh battleship --players 2

# Показать план и ASCII-превью без печати
./run.sh sudoku --difficulty 3 --dry-run

# Найти принтер
./run.sh scan

# Список известных моделей принтеров
./run.sh models
```

Короткий алиас работает и локально:

```bash
./pnp sudoku --difficulty 3
./pnp battleship --players 2
```

### Раскладка морского боя

Для двух игроков PrintPlay печатает четыре поля, по два на игрока:

1. Игрок 1 — свой флот, корабли уже расставлены;
2. Игрок 1 — поле противника, пустая сетка;
3. Игрок 2 — свой флот, корабли уже расставлены;
4. Игрок 2 — поле противника, пустая сетка.

По умолчанию флот каждого игрока уже расставлен. Передай `--no-auto-ships`,
чтобы напечатать оба поля пустыми, или ответь соответствующим образом в меню.
В интерактивном меню морской бой спрашивает количество игроков и нужно ли
расставлять корабли автоматически. Пауза — это продвинутая опция CLI
(`--pause`), по умолчанию две секунды между фрагментами.

Если корабли расставляются автоматически, в плане печати дополнительно
показывается расстановка каждого игрока ASCII-схемой, а поле противника
остаётся пустым.

Два поля одного игрока печатаются одним фрагментом. Пара развёрнута на 90°:
оторви фрагмент, поверни бумагу — и свой флот окажется слева, а пустое поле
противника справа. Легенда флота печатается под каждым полем. Линия отрыва и
пауза появляются только после пары, поэтому два поля не нужно разрывать. Затем
PrintPlay печатает пару следующего игрока. Пауза меняется через `--pause`.

### Раскладка судоку

Каждая головоломка печатается на отдельном фрагменте на всю ширину печати.
На бумаге 384 px / 203 dpi клетка получается около 5 мм. Сложность 1 — самая
простая, 5 — самая сложная; у каждой головоломки ровно одно решение.
Количество подсказок используется только для выбора сложности и на лист не
печатается.

## Определение принтера

PrintPlay просит TiMini-Print просканировать Bluetooth и определить модель,
профиль, пресет бумаги, ширину и DPI. Ничего не привязано жёстко к одному
принтеру.

Для MXW-W5 движок выбирает профиль `v5x` и бумагу `plain_384r`
(384 px, 203 dpi). Если автоопределение не сработало, можно переопределить:

```bash
./run.sh sudoku --difficulty 3 --bluetooth MXW-W5
./run.sh sudoku --difficulty 3 --model v5x
./run.sh sudoku --difficulty 3 --paper tag_384r
```

По умолчанию используются `--image-mode atkinson` и `--darkness 5`.
На MXW-W5 режим grayscale печатает бледно, а 1-битный Atkinson — темно.
Для чистых контуров можно попробовать `--image-mode threshold`, а плотность
меняется через `--darkness 1-5`.

## Опции

```text
--lang en|ru          Язык интерфейса (или PRINTPLAY_LANG)
--model KEY           Переопределить модель принтера
--bluetooth NAME      Имя или адрес Bluetooth-принтера
--paper KEY           Переопределить пресет бумаги
--image-mode MODE     atkinson, threshold, floyd_steinberg, bayer_4, bayer_8, grayscale
--darkness 1-5        Плотность печати (по умолчанию: 5)
--auto-ships / --no-auto-ships
                      Авторасстановка кораблей на своих полях (по умолчанию: да)
--pause SECONDS       Пауза между фрагментами (по умолчанию: 2.0)
--dry-run             Показать план и ASCII-превью, не печатать
--keep-png DIR        Сохранить страницы в DIR для отладки
--yes                 Не спрашивать подтверждение (по умолчанию PrintPlay спрашивает)
```

## Разработка

```bash
cd printplay
PYTHONPATH=".:../timini-print" ../timini-print/.venv/bin/python -m pytest -q
```

При желании можно установить команды `printplay` и `pnp` локально:

```bash
python -m pip install -e ".[dev]"
printplay --version
```

PrintPlay сам находит `../timini-print`; если клон лежит в другом месте,
задай `TIMINIPRINT_ROOT`.

Генераторы и рендереры игр не импортируют TiMini-Print, поэтому их тесты
работают без Bluetooth и принтера. GitHub Actions запускает те же тесты
против upstream-клона TiMini-Print.

## Лицензия

MIT. См. [LICENSE](LICENSE).

PrintPlay использует [TiMini-Print](https://github.com/Dejniel/TiMini-Print) как
внешнюю зависимость. TiMini-Print распространяется по лицензии Apache-2.0.
Его исходный код в этот репозиторий не включён.
