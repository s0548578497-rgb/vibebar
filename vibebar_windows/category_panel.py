"""Tk presentation adapter for post-hoc task categorization."""

from __future__ import annotations

from tkinter import ttk
from typing import Callable

from .categories import CategoryService


class CategoryPanel:
    def __init__(self, service: CategoryService, translate: Callable[[str], str], language: Callable[[], str]) -> None:
        self.service = service
        self.t = translate
        self.language = language
        self.tree: ttk.Treeview | None = None
        self.choice: ttk.Combobox | None = None

    def build(self, notebook: ttk.Notebook) -> None:
        frame = ttk.Frame(notebook, padding=8)
        notebook.add(frame, text=self.t("categories"))
        self.tree = ttk.Treeview(frame, columns=("time", "text", "category"), show="headings")
        for column, key in (("time", "time"), ("text", "tasks"), ("category", "category")):
            self.tree.heading(column, text=self.t(key))
        self.tree.pack(fill="both", expand=True)
        row = ttk.Frame(frame)
        row.pack(fill="x", pady=6)
        values = tuple(item.label(self.language()) for item in self.service.catalog)
        self.choice = ttk.Combobox(row, state="readonly", values=values)
        self.choice.pack(side="right", padx=4)
        ttk.Button(row, text=self.t("assign_category"), command=self.assign).pack(side="right")
        self.refresh()

    def refresh(self) -> None:
        if self.tree is None:
            return
        self.tree.delete(*self.tree.get_children())
        labels = {item.number: item.label(self.language()) for item in self.service.catalog}
        for task in self.service.tasks():
            self.tree.insert("", "end", iid=task.key, values=(task.time, task.text, labels.get(task.category, "—")))

    def assign(self) -> None:
        if self.tree is None or self.choice is None or not self.tree.selection() or not self.choice.get():
            return
        number = int(self.choice.get().split(" ", 1)[0])
        self.service.assign(self.tree.selection()[0], number)
        self.refresh()
