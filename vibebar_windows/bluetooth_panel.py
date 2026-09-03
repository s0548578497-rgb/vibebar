"""Tk presentation adapter for selecting the proximity marker device."""

from __future__ import annotations

from tkinter import ttk
from typing import Callable

from bluetooth_proximity.devices import BluetoothDevice, BluetoothDeviceProvider, SelectedDeviceStore


class BluetoothDevicePanel:
    def __init__(
        self, provider: BluetoothDeviceProvider, store: SelectedDeviceStore, translate: Callable[[str], str]
    ) -> None:
        self.provider = provider
        self.store = store
        self.t = translate
        self.choice: ttk.Combobox | None = None
        self.status: ttk.Label | None = None
        self.items: dict[str, BluetoothDevice] = {}

    def build(self, notebook: ttk.Notebook) -> None:
        frame = ttk.Frame(notebook, padding=16)
        notebook.add(frame, text=self.t("bluetooth_device"))
        self.choice = ttk.Combobox(frame, state="readonly")
        self.choice.pack(fill="x", pady=8)
        buttons = ttk.Frame(frame)
        buttons.pack(fill="x")
        ttk.Button(buttons, text=self.t("refresh_devices"), command=self.refresh).pack(side="right", padx=4)
        ttk.Button(buttons, text=self.t("use_marker_device"), command=self.save).pack(side="right", padx=4)
        self.status = ttk.Label(frame, anchor="e")
        self.status.pack(fill="x", pady=12)
        self.refresh()

    def refresh(self) -> None:
        devices = self.provider.devices()
        self.items = {self._label(device): device for device in devices}
        if self.choice is not None:
            self.choice.configure(values=tuple(self.items))
            selected = self.store.load()
            match = next((label for label, item in self.items.items() if item.identifier == getattr(selected, "identifier", "")), "")
            if match:
                self.choice.set(match)
        self._set_status("device_scan_empty" if not devices else "ready")

    def save(self) -> None:
        if self.choice is None or self.choice.get() not in self.items:
            self._set_status("no_device_selected")
            return
        self.store.save(self.items[self.choice.get()])
        self._set_status("marker_device_saved")

    def _label(self, device: BluetoothDevice) -> str:
        state = self.t("connected") if device.connected else self.t("known_device")
        return f"{device.name} — {state}"

    def _set_status(self, key: str) -> None:
        if self.status is not None:
            self.status.configure(text=self.t(key))
