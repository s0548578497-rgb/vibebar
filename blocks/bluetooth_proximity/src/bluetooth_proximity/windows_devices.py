"""Windows Bluetooth device discovery adapter."""

from __future__ import annotations

import json
import subprocess
import winreg

from .devices import BluetoothDevice


class WindowsBluetoothDeviceProvider:
    def devices(self) -> tuple[BluetoothDevice, ...]:
        command = (
            "Get-PnpDevice -Class Bluetooth | Select-Object InstanceId,FriendlyName,Status | "
            "ConvertTo-Json -Compress"
        )
        flags = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
        result = subprocess.run(
            ("powershell", "-NoProfile", "-NonInteractive", "-Command", command),
            capture_output=True, text=True, encoding="utf-8", check=False, creationflags=flags,
        )
        detected = _parse_devices(result.stdout) if result.returncode == 0 else ()
        return detected or _registry_devices()


def _parse_devices(payload: str) -> tuple[BluetoothDevice, ...]:
    try:
        values = json.loads(payload or "[]")
    except json.JSONDecodeError:
        return ()
    rows = values if isinstance(values, list) else [values]
    devices = {
        str(row.get("InstanceId", "")): BluetoothDevice(
            str(row.get("InstanceId", "")), str(row.get("FriendlyName", "")), row.get("Status") == "OK"
        )
        for row in rows if row.get("InstanceId") and row.get("FriendlyName")
    }
    return tuple(sorted(devices.values(), key=lambda item: (not item.connected, item.name.casefold())))


def _registry_devices() -> tuple[BluetoothDevice, ...]:
    path = r"SYSTEM\CurrentControlSet\Services\BTHPORT\Parameters\Devices"
    rows: list[BluetoothDevice] = []
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path) as devices:
            for index in range(winreg.QueryInfoKey(devices)[0]):
                identifier = winreg.EnumKey(devices, index)
                with winreg.OpenKey(devices, identifier) as device:
                    raw = winreg.QueryValueEx(device, "Name")[0]
                name = bytes(raw).rstrip(b"\0").decode("utf-8", "replace").strip()
                if name:
                    rows.append(BluetoothDevice(identifier, name))
    except (OSError, ValueError):
        return ()
    return tuple(sorted(rows, key=lambda item: item.name.casefold()))
