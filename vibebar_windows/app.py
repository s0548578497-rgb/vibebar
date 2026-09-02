"""Full Windows frontend over the unchanged VibeBar implementation."""

from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable

from vibebar_modular.compositions import Action, get_composition
from vibebar_modular.contracts import CommandResult

from .assembly import (
    assemble_commands,
    assemble_categories,
    assemble_hotkey,
    assemble_menu_view,
    assemble_transcriber,
    assemble_task_timer,
    assemble_wakeword,
    assemble_audio_cue,
    assemble_diagnostics,
    assemble_windows,
    default_environment,
    rebuild_command_entry,
)
from .clipboard_watcher import ClipboardWatcher
from .category_panel import CategoryPanel
from .language import LanguageController
from .tray import TrayController
from .view_model import ActivityItem, VibeBarView
from .voice import VoiceController
from .diagnostics import text_fingerprint
from .journal_events import WindowsJournalChangeListener


class VibeBarWindow:
    def __init__(self, repository: Path) -> None:
        self.repository = repository
        environment = default_environment(repository)
        self.sockets = assemble_windows(repository, environment, allow_deletion=True)
        self.task_timer = assemble_task_timer(Path(environment["VIBEBAR_FILE"]), self.sockets.clock)
        self.diagnostics = assemble_diagnostics(repository, self.sockets.clock)
        category_sockets = assemble_categories(repository, Path(environment["VIBEBAR_FILE"]), self.sockets.clock)
        self.categories = category_sockets.service
        self.category_reports = category_sockets.reports
        commands = assemble_commands(repository, self.sockets.entry)
        self.command_store = commands.repository
        self.entry = commands.entry
        self.view_socket = assemble_menu_view(repository, environment, self.sockets.clock)
        self.composition = get_composition("windows")
        self.language = LanguageController(repository / "windows" / "locales", repository / "windows" / "settings.json")
        self.root = tk.Tk()
        self.journal_listener = WindowsJournalChangeListener(lambda: self.root.after(0, self.refresh))
        self.text = tk.StringVar()
        self.current = tk.StringVar(value="—")
        self.status = tk.StringVar()
        self.trees: dict[str, ttk.Treeview] = {}
        self.watcher = ClipboardWatcher(self.root, self.sockets.clipboard, self.refresh)
        self.voice = VoiceController(
            self.voice_text_from_thread,
            self.voice_status_from_thread,
            assemble_transcriber(repository),
            wakeword=assemble_wakeword(repository),
            cue=assemble_audio_cue(),
            diagnostics=self.diagnostics,
        )
        self.hotkey = assemble_hotkey(self.voice.request_command, self.hotkey_error_from_thread)
        self.tray = TrayController(self.show_from_tray, self.quit_from_tray)
        self.timer_state = self.task_timer.load()
        self.timer_job: str | None = None
        self.category_panel = CategoryPanel(self.categories, self.t, lambda: self.language.catalog.code)
        self._configure_window()
        self._build()
        self._start_tray()
        self.hotkey.start()
        self.refresh()
        self._start_timer()
        self.journal_listener.start()
        self.diagnostics.event("app_ready")

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
        self._activity_tab(notebook, "breaks")
        self._clipboard_tab(notebook)
        self._reports_tab(notebook)
        self.category_panel.build(notebook)
        self._commands_tab(notebook)
    def _commands_tab(self, notebook: ttk.Notebook) -> None:
        frame = ttk.Frame(notebook, padding=8)
        notebook.add(frame, text=self.t("custom_commands"))
        row = ttk.Frame(frame)
        row.pack(fill="x", pady=(0, 8))
        phrase = ttk.Entry(row, justify="right")
        phrase.pack(side="right", fill="x", expand=True, padx=4)
        kind = ttk.Combobox(row, state="readonly", values=("task", "idea", "todo", "pause"), width=12)
        kind.set("task")
        kind.pack(side="right", padx=4)
        ttk.Button(row, text=self.t("add_command"), command=lambda: self._add_command(phrase, kind)).pack(side="right")
        tree = ttk.Treeview(frame, columns=("phrase", "kind"), show="headings")
        tree.heading("phrase", text=self.t("command_phrase"))
        tree.heading("kind", text=self.t("command_kind"))
        tree.pack(fill="both", expand=True)
        for command in self.command_store.load():
            tree.insert("", "end", values=(command.phrase, command.kind))
        ttk.Button(frame, text=self.t("delete"), command=lambda: self._delete_command(tree)).pack(anchor="w", pady=6)
    def _add_command(self, phrase: ttk.Entry, kind: ttk.Combobox) -> None:
        self.command_store.add(phrase.get(), kind.get())
        self._reload_entry()
        self._build()
        self.refresh()
    def _delete_command(self, tree: ttk.Treeview) -> None:
        selected = tree.selection()
        if selected:
            self.command_store.delete(str(tree.item(selected[0], "values")[0]))
            self._reload_entry()
            self._build()
            self.refresh()
    def _reload_entry(self) -> None:
        self.entry = rebuild_command_entry(self.repository, self.sockets.entry, self.command_store)
    def _activity_tab(self, notebook: ttk.Notebook, key: str) -> None:
        frame = ttk.Frame(notebook, padding=8)
        notebook.add(frame, text=self.t(key))
        tree = ttk.Treeview(frame, columns=("time", "text"), show="headings")
        tree.heading("time", text=self.t("break_start") if key == "breaks" else "⏱")
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
        ttk.Label(footer, text=self.t("hotkey_hint")).pack(side="left", padx=8)
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
        self.timer_state = self.task_timer.load()
        self._update_timer_display()
        self._fill_activity("tasks", view.tasks)
        self._fill_activity("ideas", view.ideas)
        self._fill_activity("todos", view.todos)
        self._fill_activity("breaks", view.breaks)
        self._fill_clipboard(view)
        self.category_panel.refresh()

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
            result = self.entry.submit(text)
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
        self._categorized_digest(self.sockets.digest.build_day(), 1, "daily_digest", open_report=True)
    def rebuild_digest(self) -> None:
        self._categorized_digest(self.sockets.digest.build_day(rebuild=True), 1, "rebuild_digest", open_report=True)
    def weekly_digest(self) -> None:
        self._categorized_digest(self.sockets.digest.build_week(), 7, "weekly_digest")
    def _categorized_digest(
        self, result: CommandResult, days: int, success_key: str, open_report: bool = False
    ) -> None:
        if result.succeeded and result.stdout.strip():
            report = Path(result.stdout.strip().splitlines()[-1])
            summary = self.categories.summary(days, self.language.catalog.code)
            self.category_reports.enrich(report, summary)
            if open_report:
                opened = self.sockets.opener.open(report)
                if not opened.succeeded:
                    result = opened
        self._result(result, success_key)

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
        self.diagnostics.event("voice_text_received", characters=len(text), fingerprint=text_fingerprint(text))
        result = self.entry.submit(text)
        self.diagnostics.event("journal_submit_completed", exit_code=result.exit_code)
        self._result(result, "saved")
        self.refresh()

    def voice_status_from_thread(self, key: str) -> None:
        self.root.after(0, lambda: self.status.set(self.t(key)))

    def hotkey_error_from_thread(self, message: str) -> None:
        self.root.after(0, lambda: self.status.set(message))

    def _result(self, result: CommandResult, success_key: str) -> None:
        message = self.t(success_key) if result.succeeded else (result.stderr.strip() or self.t("failed"))
        self.status.set(message)

    def _start_timer(self) -> None:
        if self.timer_job is None:
            self.timer_job = self.root.after(1000, self._timer_tick)

    def _timer_tick(self) -> None:
        self.timer_job = None
        self._update_timer_display()
        if self.root.state() != "withdrawn":
            self._start_timer()

    def _update_timer_display(self) -> None:
        self.current.set(self.timer_state.display(self.sockets.clock.now()))

    def _stop_timer(self) -> None:
        if self.timer_job is not None:
            self.root.after_cancel(self.timer_job)
            self.timer_job = None

    def _start_tray(self) -> None:
        try:
            self.tray.start(self.t("show_window"), self.t("quit"))
        except ImportError:
            self.status.set("pystray/Pillow missing")

    def hide(self) -> None:
        self._stop_timer()
        self.root.withdraw()

    def show_from_tray(self) -> None:
        self.root.after(0, self.show)

    def show(self) -> None:
        self.root.deiconify()
        self.root.lift()
        self.refresh()
        self._start_timer()

    def quit_from_tray(self) -> None:
        self.root.after(0, self.quit)

    def quit(self) -> None:
        self._stop_timer()
        self.watcher.stop()
        self.voice.close()
        self.hotkey.close()
        self.tray.stop()
        self.journal_listener.close()
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    repository = Path(__file__).resolve().parents[1]
    VibeBarWindow(repository).run()


if __name__ == "__main__":
    main()
