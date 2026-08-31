"""Full Windows frontend over the unchanged VibeBar implementation."""

from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable

from vibebar_modular.compositions import Action, get_composition
from vibebar_modular.contracts import CommandResult

from .assembly import assemble_windows, default_environment
from .clipboard_watcher import ClipboardWatcher
from .language import LanguageController
from .paths import discover
from .runner import WindowsBashRunner
from .tray import TrayController
from .view_model import ActivityItem, LegacyMenuViewSocket, VibeBarView
from .voice import VoiceController


class VibeBarWindow:
    def __init__(self, repository: Path) -> None:
        self.repository = repository
        environment = default_environment(repository)
        self.sockets = assemble_windows(repository, environment, allow_deletion=True)
        runner = WindowsBashRunner(discover(repository), environment)
        self.view_socket = LegacyMenuViewSocket(repository, runner)
        self.composition = get_composition("windows")
        self.language = LanguageController(repository / "windows" / "locales", repository / "windows" / "settings.json")
        self.root = tk.Tk()
        self.text = tk.StringVar()
        self.current = tk.StringVar(value="—")
        self.status = tk.StringVar()
        self.trees: dict[str, ttk.Treeview] = {}
        self.watcher = ClipboardWatcher(self.root, self.sockets.clipboard, self.refresh)
        self.voice = VoiceController(self.voice_text_from_thread, self.voice_status_from_thread)
        self.tray = TrayController(self.show_from_tray, self.quit_from_tray)
        self._configure_window()
        self._build()
        self._start_tray()
        self.refresh()
        self._schedule_refresh()

    def t(self, key: str) -> str:
        return self.language.catalog.text(key)

    def _configure_window(self) -> None:
        self.root.geometry("760x620")
        self.root.minsize(650, 500)
        self.root.protocol("WM_DELETE_WINDOW", self.hide)

    def _build(self) -> None:
        self.root.title(self.t("app_title"))
        self.status.set(self.t("ready"))
        for child in self.root.winfo_children():
            child.destroy()
        outer = ttk.Frame(self.root, padding=14)
        outer.pack(fill="both", expand=True)
        self._build_header(outer)
        self._build_input(outer)
        self._build_tabs(outer)
        self._build_footer(outer)

    def _build_header(self, parent: ttk.Frame) -> None:
        header = ttk.LabelFrame(parent, text=self.t("current"), padding=10)
        header.pack(fill="x", pady=(0, 10))
        ttk.Label(header, textvariable=self.current, font=("Segoe UI", 15, "bold"), anchor="e").pack(fill="x")

    def _build_input(self, parent: ttk.Frame) -> None:
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=(0, 10))
        entry = ttk.Entry(row, textvariable=self.text, justify="right", font=("Segoe UI", 11))
        entry.pack(side="right", fill="x", expand=True, padx=(8, 0))
        entry.bind("<Return>", self._submit_event)
        self._button(row, Action.ADD_ENTRY, self.t("submit"), self.submit)
        entry.focus_set()

    def _build_tabs(self, parent: ttk.Frame) -> None:
        notebook = ttk.Notebook(parent)
        notebook.pack(fill="both", expand=True)
        self._activity_tab(notebook, "tasks")
        self._activity_tab(notebook, "ideas")
        self._activity_tab(notebook, "todos")
        self._clipboard_tab(notebook)
        self._reports_tab(notebook)

    def _activity_tab(self, notebook: ttk.Notebook, key: str) -> None:
        frame = ttk.Frame(notebook, padding=8)
        notebook.add(frame, text=self.t(key))
        tree = ttk.Treeview(frame, columns=("time", "text"), show="headings")
        tree.heading("time", text="⏱")
        tree.heading("text", text=self.t(key))
        tree.column("time", width=80, anchor="center", stretch=False)
        tree.column("text", width=500, anchor="e")
        tree.pack(fill="both", expand=True)
        self.trees[key] = tree

    def _clipboard_tab(self, notebook: ttk.Notebook) -> None:
        frame = ttk.Frame(notebook, padding=8)
        notebook.add(frame, text=self.t("clipboard"))
        tree = ttk.Treeview(frame, columns=("number", "preview"), show="headings")
        tree.heading("number", text="#")
        tree.heading("preview", text=self.t("clipboard"))
        tree.column("number", width=50, anchor="center", stretch=False)
        tree.column("preview", width=530, anchor="e")
        tree.pack(fill="both", expand=True)
        self.trees["clipboard"] = tree
        buttons = ttk.Frame(frame)
        buttons.pack(fill="x", pady=(8, 0))
        self._button(buttons, Action.CAPTURE_CLIPBOARD, self.t("capture_clipboard"), self.capture_clipboard)
        self._button(buttons, Action.COPY_CLIPBOARD, self.t("copy"), self.copy_clipboard)
        self._button(buttons, Action.DELETE_CLIPBOARD, self.t("delete"), self.delete_clipboard)
        self._button(buttons, Action.CLEAR_CLIPBOARD, self.t("clear"), self.clear_clipboard)

    def _reports_tab(self, notebook: ttk.Notebook) -> None:
        frame = ttk.Frame(notebook, padding=18)
        notebook.add(frame, text=self.t("reports"))
        self._wide_button(frame, Action.DAILY_DIGEST, self.t("daily_digest"), self.daily_digest)
        self._wide_button(frame, Action.DAILY_DIGEST, self.t("rebuild_digest"), self.rebuild_digest)
        self._wide_button(frame, Action.WEEKLY_DIGEST, self.t("weekly_digest"), self.weekly_digest)
        self._wide_button(frame, Action.PUBLISH_DIGEST, self.t("publish_digest"), self.publish_digest)
        self._wide_button(frame, Action.OPEN_JOURNAL, self.t("edit_journal"), self.open_journal)

    def _build_footer(self, parent: ttk.Frame) -> None:
        footer = ttk.Frame(parent)
        footer.pack(fill="x", pady=(10, 0))
        ttk.Label(footer, textvariable=self.status).pack(side="left")
        ttk.Button(footer, text=self.t("hide_window"), command=self.hide).pack(side="right", padx=3)
        ttk.Button(footer, text=self.t("language"), command=self.switch_language).pack(side="right", padx=3)
        watcher_key = "watcher_on" if self.watcher.enabled else "watcher_off"
        ttk.Button(footer, text=self.t(watcher_key), command=self.toggle_watcher).pack(side="right", padx=3)
        voice_key = "voice_on" if self.voice.enabled else "voice_off"
        self._button(footer, Action.VOICE_INPUT, self.t(voice_key), self.toggle_voice)

    def _button(self, parent: ttk.Frame, action: Action, label: str, command: Callable[[], None]) -> None:
        if self.composition.contains(action):
            ttk.Button(parent, text=label, command=command).pack(side="right", padx=3)

    def _wide_button(self, parent: ttk.Frame, action: Action, label: str, command: Callable[[], None]) -> None:
        if self.composition.contains(action):
            ttk.Button(parent, text=label, command=command).pack(fill="x", pady=4)

    def refresh(self) -> None:
        try:
            view = self.view_socket.load()
        except RuntimeError as error:
            self.status.set(str(error))
            return
        self.current.set(view.current)
        self._fill_activity("tasks", view.tasks)
        self._fill_activity("ideas", view.ideas)
        self._fill_activity("todos", view.todos)
        self._fill_clipboard(view)

    def _fill_activity(self, key: str, items: tuple[ActivityItem, ...]) -> None:
        tree = self.trees[key]
        tree.delete(*tree.get_children())
        for item in items:
            tree.insert("", "end", values=(item.time, item.text))

    def _fill_clipboard(self, view: VibeBarView) -> None:
        tree = self.trees["clipboard"]
        tree.delete(*tree.get_children())
        for item in view.clipboard:
            tree.insert("", "end", iid=str(item.source_index), values=(item.display_index, item.preview))

    def _submit_event(self, _event: tk.Event[tk.Misc]) -> None:
        self.submit()

    def submit(self) -> None:
        text = self.text.get().strip()
        if text:
            result = self.sockets.entry.submit(text)
            self._result(result, "saved")
            if result.succeeded:
                self.text.set("")
                self.refresh()

    def capture_clipboard(self) -> None:
        result = self.sockets.clipboard.add_current()
        self._result(result, "clipboard_saved")
        self.refresh()

    def copy_clipboard(self) -> None:
        index = self._selected_clipboard_index()
        if index is None:
            return
        result = self.sockets.clipboard.copy(index)
        self.watcher.mark_current_seen()
        self._result(result, "copied")

    def delete_clipboard(self) -> None:
        index = self._selected_clipboard_index()
        if index is None:
            return
        result = self.sockets.recycle_bin.delete_clipboard_item(index)
        self._result(result, "deleted")
        self.refresh()

    def clear_clipboard(self) -> None:
        if messagebox.askyesno(self.t("clear"), self.t("confirm_clear")):
            result = self.sockets.recycle_bin.clear_clipboard()
            self._result(result, "cleared")
            self.refresh()

    def _selected_clipboard_index(self) -> int | None:
        selected = self.trees["clipboard"].selection()
        if not selected:
            self.status.set(self.t("no_selection"))
            return None
        return int(selected[0])

    def daily_digest(self) -> None:
        self._result(self.sockets.digest.build_day(), "daily_digest")

    def rebuild_digest(self) -> None:
        self._result(self.sockets.digest.build_day(rebuild=True), "rebuild_digest")

    def weekly_digest(self) -> None:
        self._result(self.sockets.digest.build_week(), "weekly_digest")

    def publish_digest(self) -> None:
        self._result(self.sockets.digest.publish_day(), "publish_digest")

    def open_journal(self) -> None:
        path = Path(default_environment(self.repository)["VIBEBAR_FILE"])
        self._result(self.sockets.opener.open(path), "edit_journal")

    def toggle_watcher(self) -> None:
        self.watcher.toggle()
        self._build()
        self.refresh()

    def switch_language(self) -> None:
        self.language.switch()
        self._build()
        self.tray.restart(self.t("show_window"), self.t("quit"))
        self.refresh()

    def toggle_voice(self) -> None:
        self.voice.toggle()
        self._build()
        self.refresh()

    def voice_text_from_thread(self, text: str) -> None:
        self.root.after(0, lambda: self._submit_voice(text))

    def _submit_voice(self, text: str) -> None:
        result = self.sockets.entry.submit(text)
        self._result(result, "saved")
        self.refresh()

    def voice_status_from_thread(self, key: str) -> None:
        self.root.after(0, lambda: self.status.set(self.t(key)))

    def _result(self, result: CommandResult, success_key: str) -> None:
        message = self.t(success_key) if result.succeeded else (result.stderr.strip() or self.t("failed"))
        self.status.set(message)

    def _schedule_refresh(self) -> None:
        self.root.after(3000, self._refresh_tick)

    def _refresh_tick(self) -> None:
        self.refresh()
        self._schedule_refresh()

    def _start_tray(self) -> None:
        try:
            self.tray.start(self.t("show_window"), self.t("quit"))
        except ImportError:
            self.status.set("pystray/Pillow missing")

    def hide(self) -> None:
        self.root.withdraw()

    def show_from_tray(self) -> None:
        self.root.after(0, self.show)

    def show(self) -> None:
        self.root.deiconify()
        self.root.lift()

    def quit_from_tray(self) -> None:
        self.root.after(0, self.quit)

    def quit(self) -> None:
        self.watcher.stop()
        self.voice.stop()
        self.tray.stop()
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    repository = Path(__file__).resolve().parents[1]
    VibeBarWindow(repository).run()


if __name__ == "__main__":
    main()
