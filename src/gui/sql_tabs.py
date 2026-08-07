"""Abas de visualização dos scripts SQL gerados, uma por processo, mais a
aba "Script completo" reunindo todos na ordem lógica de execução."""

import tkinter as tk
from tkinter import ttk


class _ProcessTab(ttk.Frame):
    def __init__(self, master, titulo, descricao, on_copy, **kwargs):
        super().__init__(master, padding=10, **kwargs)
        self.on_copy = on_copy

        header = ttk.Frame(self)
        header.pack(fill="x")
        ttk.Label(header, text=titulo, font=("Segoe UI", 11, "bold")).pack(side="left")
        self.lbl_quantidade = ttk.Label(header, text="0 comando(s) gerado(s)")
        self.lbl_quantidade.pack(side="right")

        ttk.Label(self, text=descricao, wraplength=760, foreground="#444").pack(fill="x", pady=(2, 8))

        text_frame = ttk.Frame(self)
        text_frame.pack(fill="both", expand=True)
        self.text = tk.Text(text_frame, wrap="none", font=("Consolas", 10), state="disabled", height=18)
        y_scroll = ttk.Scrollbar(text_frame, orient="vertical", command=self.text.yview)
        x_scroll = ttk.Scrollbar(text_frame, orient="horizontal", command=self.text.xview)
        self.text.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        self.text.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="we")
        text_frame.rowconfigure(0, weight=1)
        text_frame.columnconfigure(0, weight=1)

        self.text.bind("<Control-a>", self._select_all)
        self.text.bind("<Control-A>", self._select_all)

        footer = ttk.Frame(self)
        footer.pack(fill="x", pady=(8, 0))
        ttk.Button(footer, text="Copiar", command=self._copiar).pack(side="left")

    def _select_all(self, _event):
        self.text.tag_add("sel", "1.0", "end")
        return "break"

    def _copiar(self):
        self.on_copy(self.text.get("1.0", "end-1c"))

    def set_content(self, sql: str, quantidade: int):
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.insert("1.0", sql)
        self.text.configure(state="disabled")
        self.lbl_quantidade.configure(text=f"{quantidade} comando(s) gerado(s)")


class SqlTabs(ttk.Frame):
    PROCESS_KEYS = [
        "contas", "grupo_portal", "grupo_contabil", "interface_contas",
        "interface_historico", "interface_arq", "interface_comum", "interface_forma_pgto",
    ]

    def __init__(self, master, copy_to_clipboard, **kwargs):
        super().__init__(master, **kwargs)
        self.copy_to_clipboard = copy_to_clipboard
        self._full_script = ""

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        self.tabs = {}
        titulos_iniciais = {
            "contas": "1. Contas",
            "grupo_portal": "2. GrupoPortal",
            "grupo_contabil": "3. GrupoContábil",
            "interface_contas": "4. InterfaceContas",
            "interface_historico": "5. InterfaceHistorico",
            "interface_arq": "6. InterfaceArq",
            "interface_comum": "7. InterfaceComum",
            "interface_forma_pgto": "8. InterfaceFormaPgto",
        }
        for key in self.PROCESS_KEYS:
            tab = _ProcessTab(self.notebook, titulos_iniciais[key], "", self.copy_to_clipboard)
            self.notebook.add(tab, text=titulos_iniciais[key])
            self.tabs[key] = tab

        self.tab_completo = _ProcessTab(
            self.notebook, "9. Script completo",
            "Reúne todos os processos, na ordem lógica recomendada de execução, com comentários separadores.",
            lambda _texto: self.copy_to_clipboard(self._full_script),
        )
        self.notebook.add(self.tab_completo, text="9. Script completo")

    def update_results(self, resultados: list, full_script: str):
        for resultado, key in zip(resultados, self.PROCESS_KEYS):
            tab = self.tabs[key]
            tab.set_content(resultado.sql, resultado.quantidade)
            self.notebook.tab(tab, text=resultado.titulo)

        self._full_script = full_script
        total = sum(r.quantidade for r in resultados)
        self.tab_completo.set_content(full_script, total)

    def clear(self):
        for tab in self.tabs.values():
            tab.set_content("", 0)
        self._full_script = ""
        self.tab_completo.set_content("", 0)

    def get_full_script(self) -> str:
        return self._full_script
