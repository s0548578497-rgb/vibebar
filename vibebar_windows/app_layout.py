"""Tk layout for the Windows window, separate from application behaviour."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable

from vibebar_modular.compositions import Action


class WindowLayoutMixin:
    """Build widgets while delegating every action to the application class."""

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
        self._button(row, Action.VOICE_INPUT, self.t("what_achieved"), self.capture_achievement)
        entry.focus_set()

    def _build_tabs(self, parent: ttk.Frame) -> None:
        notebook = ttk.Notebook(parent)
        notebook.pack(fill="both", expand=True)
        for key in ("tasks", "ideas", "achievements", "todos", "breaks"):
            self._activity_tab(notebook, key)
        self._clipboard_tab(notebook)
        self._reports_tab(notebook)
        self.category_panel.build(notebook)
        self.bluetooth_panel.build(notebook)
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

    def _activity_tab(self, notebook: ttk.Notebook, key: str) -> None:
        frame = ttk.Frame(notebook, padding=8)
        notebook.add(frame, text=self.t(key))
        tree = ttk.Treeview(frame, columns=("time", "text"), show="headings")
        tree.heading("time", text=self.t("break_start") if key == "breaks" else "⏱")
        tree.heading("text", text=self.t(key))
        tree.column("time", width=150 if key == "breaks" else 80, anchor="center", stretch=False)
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
