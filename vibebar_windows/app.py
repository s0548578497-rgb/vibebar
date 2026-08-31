"""Small native Windows UI over the socket assembly."""

from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import ttk
from typing import Callable

from vibebar_modular.compositions import Action, get_composition
from vibebar_modular.contracts import CommandResult

from .assembly import assemble_windows


class VibeBarWindow:
    def __init__(self, repository: Path) -> None:
        self.sockets = assemble_windows(repository)
        self.composition = get_composition("windows")
        self.root = tk.Tk()
        self.root.title("VibeBar — Windows")
        self.root.geometry("560x250")
        self.text = tk.StringVar()
        self.status = tk.StringVar(value="מוכן")
        self._build()

    def _build(self) -> None:
        frame = ttk.Frame(self.root, padding=18)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="מה אתה עושה עכשיו?", anchor="e").pack(fill="x")
        entry = ttk.Entry(frame, textvariable=self.text, justify="right")
        entry.pack(fill="x", pady=(6, 12))
        entry.bind("<Return>", self._submit_event)
        actions = ttk.Frame(frame)
        actions.pack(fill="x")
        self._add_button(actions, Action.ADD_ENTRY, "הוסף ליומן", self.submit)
        self._add_button(actions, Action.CAPTURE_CLIPBOARD, "שמור לוח העתקה", self.add_clipboard)
        self._add_button(actions, Action.DAILY_DIGEST, "דוח יומי", self.daily_digest)
        ttk.Label(frame, textvariable=self.status, anchor="e").pack(fill="x", pady=(20, 0))
        entry.focus_set()

    def _add_button(self, parent: ttk.Frame, action: Action, label: str, command: Callable[[], None]) -> None:
        if self.composition.contains(action):
            ttk.Button(parent, text=label, command=command).pack(side="right", padx=4)

    def _submit_event(self, _event: tk.Event[tk.Misc]) -> None:
        self.submit()

    def submit(self) -> None:
        text = self.text.get().strip()
        if not text:
            self.status.set("לא הוזן טקסט")
            return
        result = self.sockets.entry.submit(text)
        self._show_result(result, "נוסף ליומן")
        if result.succeeded:
            self.text.set("")

    def add_clipboard(self) -> None:
        result = self.sockets.clipboard.add_current()
        self._show_result(result, "לוח ההעתקה נשמר")

    def daily_digest(self) -> None:
        result = self.sockets.digest.build_day()
        self._show_result(result, "הדוח היומי נפתח")

    def _show_result(self, result: CommandResult, success: str) -> None:
        message = success if result.succeeded else (result.stderr.strip() or "הפעולה נכשלה")
        self.status.set(message)

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    repository = Path(__file__).resolve().parents[1]
    VibeBarWindow(repository).run()


if __name__ == "__main__":
    main()
