"""TiMini-Print integration: discovery, paper geometry, and printing."""

from __future__ import annotations

import asyncio
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional, Sequence

from ._paths import ensure_timiniprint_path
from .i18n import Translator
from .rendering import Page

ensure_timiniprint_path()


@dataclass(frozen=True)
class PrintOptions:
    model: Optional[str] = None
    bluetooth: Optional[str] = None
    paper: Optional[str] = None
    image_mode: str = "atkinson"
    darkness: int = 5
    pause: float = 2.0
    dry_run: bool = False
    keep_png: Optional[str] = None
    yes: bool = False
    verbose: bool = False


@dataclass(frozen=True)
class PrinterInfo:
    display_name: str
    model_key: str
    profile_key: str
    paper_key: str
    width: int
    dpi: int
    address: str


PageBuilder = Callable[[int], Sequence[Page]]


def _load_catalog() -> Any:
    try:
        from timiniprint.devices import PrinterCatalog
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "TiMini-Print not found. Set TIMINIPRINT_ROOT or clone it next to PrintPlay."
        ) from exc

    return PrinterCatalog.load()


def printer_info(device: Any, paper_key: Optional[str] = None) -> PrinterInfo:
    from timiniprint.printing.paper import resolve_paper
    from timiniprint.printing.settings import PrintSettings

    key = paper_key or device.profile.default_paper_preset.key
    paper = resolve_paper(device, PrintSettings(paper_preset_key=key))
    return PrinterInfo(
        display_name=device.display_name or device.profile_key,
        model_key=device.model_key or "",
        profile_key=device.profile_key,
        paper_key=key,
        width=paper.render_width_px,
        dpi=device.profile.dev_dpi,
        address=device.address,
    )


def build_settings(info: PrinterInfo, options: PrintOptions) -> Any:
    from timiniprint.printing.settings import ImageMode, PrintSettings

    return PrintSettings(
        paper_preset_key=info.paper_key,
        image_mode=ImageMode(options.image_mode),
        blackening=options.darkness,
        trim_side_margins=False,
        trim_top_bottom_margins=False,
        text_mode=False,
    )


async def _resolve_device(catalog: Any, discovery: Any, options: PrintOptions) -> Any:
    if options.model:
        target = None
        display_name = None
        if options.bluetooth:
            scanned = await discovery.resolve_device(options.bluetooth)
            target = scanned.transport_target
            display_name = scanned.display_name
        elif not options.dry_run:
            try:
                resolved = await discovery.resolve_transport_target(None)
                target = resolved.transport_target
                display_name = resolved.display_name
            except Exception:
                pass
        return catalog.device_from_model(
            options.model,
            transport_target=target,
            display_name=display_name,
        )

    if options.bluetooth:
        return await discovery.resolve_device(options.bluetooth)

    devices = await discovery.scan_devices()
    if not devices:
        raise RuntimeError("no supported printer found")
    return devices[0]


def _save_page(image: Any, keep_dir: Optional[str], index: int) -> tuple[str, bool]:
    if keep_dir:
        directory = Path(keep_dir).expanduser()
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"page_{index:02d}.png"
        image.save(path, format="PNG")
        return str(path), False

    handle = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    path = handle.name
    handle.close()
    image.save(path, format="PNG")
    return path, True


def _print_plan(info: PrinterInfo, pages: Sequence[Page], options: PrintOptions, t: Translator) -> None:
    print()
    print(t("plan_title"))
    print(
        t(
            "plan_printer",
            name=info.display_name,
            model=info.model_key or "?",
            profile=info.profile_key,
        )
    )
    print(t("plan_paper", paper=info.paper_key, width=info.width, dpi=info.dpi))
    print(t("plan_pages", count=len(pages)))
    if len(pages) > 1:
        print(t("plan_pause", seconds=options.pause))
    for index, page in enumerate(pages, 1):
        print(t("plan_page", index=index, label=page.label))
        if page.ascii_preview:
            print(page.ascii_preview)
    print()


def _confirm(t: Translator, options: PrintOptions) -> bool:
    if options.dry_run or options.yes:
        return True
    try:
        answer = input(t("confirm")).strip().lower()
    except EOFError:
        return False
    return answer in ("", "y", "yes", "д", "да")


async def run_print(
    build_pages: PageBuilder,
    options: PrintOptions,
    t: Translator,
) -> int:
    from timiniprint.printing.connected import connect_printer
    from timiniprint.transport.bluetooth import BleakBluetoothConnector, BluetoothDiscovery

    catalog = _load_catalog()
    discovery = BluetoothDiscovery(catalog)

    if options.dry_run:
        try:
            device = await _resolve_device(catalog, discovery, options)
        except Exception:
            device = catalog.device_from_model("v5x", display_name="v5x (preview)")
            print(t("no_printer_fallback"))
        info = printer_info(device, options.paper)
        pages = list(build_pages(info.width))
        _print_plan(info, pages, options, t)
        print(t("dry_run_done"))
        return 0

    device = await _resolve_device(catalog, discovery, options)
    async with await connect_printer(device, BleakBluetoothConnector()) as printer:
        resolved = printer.printer_device()
        info = printer_info(resolved, options.paper)
        pages = list(build_pages(info.width))
        _print_plan(info, pages, options, t)

        if not _confirm(t, options):
            print(t("cancelled"))
            return 0

        settings = build_settings(info, options)
        if options.verbose:
            pipeline = settings.resolve_image_pipeline(
                resolved,
                runtime_capabilities=printer.print_capabilities(),
            )
            print(
                f"[debug] image_mode={options.image_mode} darkness={settings.blackening} "
                f"encoding={pipeline.encoding.value} format={pipeline.default_format.value}",
                flush=True,
            )
        total = len(pages)
        for index, page in enumerate(pages, 1):
            print(
                t("printing_page", index=index, total=total, label=page.label),
                flush=True,
            )
            path, temporary = _save_page(page.image, options.keep_png, index)
            try:
                await printer.print_file(path, settings=settings)
            finally:
                if temporary:
                    try:
                        os.unlink(path)
                    except OSError:
                        pass
            print(t("printed_page", label=page.label), flush=True)
            if page.pause_after and options.pause > 0:
                if index < total:
                    print(t("tear_off", seconds=options.pause), flush=True)
                    await asyncio.sleep(options.pause)
                elif page.tear_off:
                    print(t("tear_off_last"), flush=True)

    print(t("done"))
    return 0


async def scan_printers(t: Translator) -> int:
    from timiniprint.transport.bluetooth import BluetoothDiscovery

    catalog = _load_catalog()
    discovery = BluetoothDiscovery(catalog)
    result = await discovery.scan_report()

    print(t("scan_title"))
    if not result.devices:
        print(t("scan_none"))
    for device in result.devices:
        badge = f" {device.transport_badge}" if device.transport_badge else ""
        print(
            f"{device.display_name or device.address} "
            f"[{device.profile_key}] {device.address}{badge}"
        )
    for failure in result.failures:
        transport = getattr(failure.transport, "value", failure.transport)
        print(t("scan_failure", transport=transport, error=failure.error))
    return 0


def list_models(t: Translator) -> int:
    catalog = _load_catalog()
    print(t("models_title"))
    for model in sorted(catalog.models, key=lambda item: item.model_key):
        names = ", ".join(model.names[:3])
        print(f"{model.model_key:24} {model.profile_key:12} {names}")
    return 0
