"""Painel de importação da planilha e pré-visualização das contas."""

import os
import tkinter as tk
from tkinter import filedialog, ttk


class ImportPanel(ttk.LabelFrame):
    def __init__(self, master, on_load=None, on_clear=None, initial_dir="", **kwargs):
        super().__init__(master, text="Importação da planilha", padding=10, **kwargs)
        self.on_load = on_load or (lambda path: None)
        self.on_clear = on_clear or (lambda: None)
        self.initial_dir = initial_dir or os.path.expanduser("~")
        self.caminho_arquivo = ""

        self._build()

    def _build(self):
        top = ttk.Frame(self)
        top.pack(fill="x")

        ttk.Button(top, text="Selecionar planilha", command=self._selecionar).pack(side="left")
        self.lbl_caminho = ttk.Label(top, text="Nenhum arquivo selecionado.", foreground="#555")
        self.lbl_caminho.pack(side="left", padx=10)

        ttk.Button(top, text="Carregar", command=self._carregar).pack(side="right", padx=(4, 0))
        ttk.Button(top, text="Limpar", command=self._limpar).pack(side="right")

        colunas = ("linha", "nome", "grupo", "conta_origem", "situacao")
        self.tree = ttk.Treeview(self, columns=colunas, show="headings", height=10)
        self.tree.heading("linha", text="Linha")
        self.tree.heading("nome", text="Nome da conta")
        self.tree.heading("grupo", text="Grupo")
        self.tree.heading("conta_origem", text="ContaOrigem")
        self.tree.heading("situacao", text="Situação")
        self.tree.column("linha", width=50, anchor="center")
        self.tree.column("nome", width=340)
        self.tree.column("grupo", width=180)
        self.tree.column("conta_origem", width=90, anchor="center")
        self.tree.column("situacao", width=260)

        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True, pady=(10, 0))
        scrollbar.pack(side="left", fill="y", pady=(10, 0))

        self.tree.tag_configure("invalido", background="#fdecea")
        self.tree.tag_configure("valido", background="")

    def _selecionar(self):
        caminho = filedialog.askopenfilename(
            title="Selecionar planilha de importação",
            initialdir=self.initial_dir,
            filetypes=[("Planilhas Excel", "*.xlsx")],
        )
        if caminho:
            self.caminho_arquivo = caminho
            self.lbl_caminho.configure(text=caminho)

    def _carregar(self):
        if not self.caminho_arquivo:
            tk.messagebox.showwarning("Selecionar planilha", "Selecione um arquivo .xlsx antes de carregar.")
            return
        self.on_load(self.caminho_arquivo)

    def _limpar(self):
        self.caminho_arquivo = ""
        self.lbl_caminho.configure(text="Nenhum arquivo selecionado.")
        self.show_accounts([])
        self.on_clear()

    def show_accounts(self, accounts):
        self.tree.delete(*self.tree.get_children())
        for a in accounts:
            tag = "valido" if a.valido else "invalido"
            self.tree.insert(
                "", "end",
                values=(a.linha, a.nome, a.grupo_normalizado, a.conta_origem, a.situacao),
                tags=(tag,),
            )
