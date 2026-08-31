"""Optional system-tray controller using pystray and Pillow."""

from __future__ import annotations

from typing import Callable


class TrayController:
    def __init__(self, show: Callable[[], None], quit_app: Callable[[], None]) -> None:
        self.show = show
        self.quit_app = quit_app
        self.icon: object | None = None

    def start(self, show_label: str, quit_label: str) -> None:
        import pystray

        image = _icon_image()
        menu = pystray.Menu(
            pystray.MenuItem(show_label, self._show, default=True),
            pystray.MenuItem(quit_label, self._quit),
        )
        self.icon = pystray.Icon("VibeBar", image, "VibeBar", menu)
        self.icon.run_detached()

    def restart(self, show_label: str, quit_label: str) -> None:
        self.stop()
        self.start(show_label, quit_label)

    def stop(self) -> None:
        if self.icon is not None:
            self.icon.stop()
            self.icon = None

    def _show(self, _icon: object, _item: object) -> None:
        self.show()

    def _quit(self, _icon: object, _item: object) -> None:
        self.quit_app()


def _icon_image() -> object:
    from PIL import Image, ImageDraw

    image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((5, 5, 59, 59), radius=14, fill=(36, 99, 235, 255))
    draw.text((21, 17), "V", fill=(255, 255, 255, 255))
    return image
