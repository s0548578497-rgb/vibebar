"""Full Windows frontend over the unchanged VibeBar implementation."""

from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk

from vibebar_modular.compositions import get_composition
from vibebar_modular.contracts import CommandResult
from vibebar_modular.achievements import MarkdownAchievementSocket, PendingAchievementCapture

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
    assemble_bluetooth_devices,
    assemble_windows,
    default_environment,
    rebuild_command_entry,
)
from .clipboard_watcher import ClipboardWatcher
from .category_panel import CategoryPanel
from vibebar_modular.language import LanguageController
from .tray import TrayController
from .view_model import ActivityItem, VibeBarView
from vibebar_voice.controller import VoiceController
from vibebar_voice.diagnostics import text_fingerprint
from .journal_events import WindowsJournalChangeListener
from .bluetooth_panel import BluetoothDevicePanel
from .app_layout import WindowLayoutMixin


class VibeBarWindow(WindowLayoutMixin):
    def __init__(self, repository: Path) -> None:
        self.repository = repository
        self._assemble_services()
        self._create_window_state()
        self._create_runtime_controllers()
        self._configure_window()
        self._build()
        self._start_background_services()

    def _assemble_services(self) -> None:
        """Create business adapters before any UI or background thread exists."""
        repository = self.repository
        environment = default_environment(repository)
        self.sockets = assemble_windows(repository, environment, allow_deletion=True)
        journal = Path(environment["VIBEBAR_FILE"])
        self.task_timer = assemble_task_timer(journal, self.sockets.clock)
        self.achievements = MarkdownAchievementSocket(journal, self.sockets.clock)
        self.achievement_capture = PendingAchievementCapture(self.achievements)
        self.diagnostics = assemble_diagnostics(repository, self.sockets.clock)
        category_sockets = assemble_categories(repository, journal, self.sockets.clock)
        self.categories = category_sockets.service
        self.category_reports = category_sockets.reports
        commands = assemble_commands(repository, self.sockets.entry)
        self.command_store = commands.repository
        self.entry = commands.entry
        self.view_socket = assemble_menu_view(repository, environment, self.sockets.clock)
        self.composition = get_composition("windows")

    def _create_window_state(self) -> None:
        """Create Tk-owned state on the main thread."""
        repository = self.repository
        self.language = LanguageController(repository / "resources" / "locales", repository / "windows" / "settings.json")
        self.root = tk.Tk()
        self.text = tk.StringVar()
        self.current = tk.StringVar(value="—")
        self.status = tk.StringVar()
        self.trees: dict[str, ttk.Treeview] = {}

    def _create_runtime_controllers(self) -> None:
        """Wire controllers without starting threads; startup order is explicit below."""
        repository = self.repository
        self.journal_listener = WindowsJournalChangeListener(lambda: self.root.after(0, self.refresh))
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
        bluetooth = assemble_bluetooth_devices(repository)
        self.bluetooth_panel = BluetoothDevicePanel(bluetooth.provider, bluetooth.store, self.t)

    def _start_background_services(self) -> None:
        """Start observers only after every callback and widget has been constructed."""
        self._start_tray()
        self.hotkey.start()
        self.refresh()
        self._start_timer()
        self.journal_listener.start()
        self.diagnostics.event("app_ready")

    def t(self, key: str) -> str:
        return self.language.catalog.text(key)
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
        self._fill_activity("achievements", tuple(ActivityItem(x.time, x.text) for x in self.achievements.load_today()))
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

    def capture_achievement(self) -> None:
        self.achievement_capture.arm()
        self.voice.request_command()

    def _submit_voice(self, text: str) -> None:
        self.diagnostics.event("voice_text_received", characters=len(text), fingerprint=text_fingerprint(text))
        result = self.achievement_capture.submit_if_armed(text) or self.entry.submit(text)
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
