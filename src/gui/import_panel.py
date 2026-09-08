"""Painel de importação da planilha e pré-visualização das contas."""

import os
import tkinter as tk
from tkinter import filedialog, ttk


class ImportPanel(ttk.Frame):
    def __init__(self, master, on_load=None, on_clear=None, initial_dir="", **kwargs):
        super().__init__(master, **kwargs)
        self.on_load = on_load or (lambda path: None)
        self.on_clear = on_clear or (lambda: None)
        self.initial_dir = initial_dir or os.path.expanduser("~")
        self.caminho_arquivo = ""

        self._build()

    def _build(self):
        instrucoes = ttk.Label(
            self,
            text=(
                "A planilha (.xlsx) deve conter as colunas, nesta ordem: "
                "1) Nome  2) Grupo  3) ContaOrigem"
            ),
            foreground="#555555",
        )
        instrucoes.pack(fill="x", pady=(0, 6))

        top = ttk.Frame(self)
        top.pack(fill="x")

        ttk.Button(top, text="Selecionar planilha", command=self._selecionar).pack(side="left")
        self.lbl_caminho = ttk.Label(top, text="Nenhum arquivo selecionado.", foreground="#8c8c8c")
        self.lbl_caminho.pack(side="left", padx=10)

        ttk.Button(top, text="Carregar", command=self._carregar).pack(side="right", padx=(4, 0))
        ttk.Button(top, text="Limpar", command=self._limpar).pack(side="right")

        self.lbl_resumo = ttk.Label(self, text="", font=("Segoe UI", 10, "bold"))
        self.lbl_resumo.pack(fill="x", pady=(8, 0))

        self.problemas_container = ttk.Frame(self)
        self.txt_problemas = tk.Text(
            self.problemas_container, height=5, wrap="word",
            foreground="#c0392b", relief="solid", borderwidth=1, padx=6, pady=4,
        )
        problemas_scroll = ttk.Scrollbar(self.problemas_container, orient="vertical", command=self.txt_problemas.yview)
        self.txt_problemas.configure(yscrollcommand=problemas_scroll.set, state="disabled")
        self.txt_problemas.pack(side="left", fill="both", expand=True)
        problemas_scroll.pack(side="left", fill="y")

        self.tree_container = ttk.Frame(self)
        self.tree_container.pack(fill="both", expand=True, pady=(10, 0))
        self.tree_container.columnconfigure(0, weight=1)
        self.tree_container.rowconfigure(0, weight=1)

        colunas = ("linha", "nome", "codigo", "grupo", "situacao")
        self.tree = ttk.Treeview(self.tree_container, columns=colunas, show="headings", height=10)
        self.tree.heading("linha", text="Linha")
        self.tree.heading("nome", text="Nome da conta")
        self.tree.heading("codigo", text="Código")
        self.tree.heading("grupo", text="Grupo")
        self.tree.heading("situacao", text="Situação")
        self.tree.column("linha", width=60, anchor="center")
        self.tree.column("nome", width=320)
        self.tree.column("codigo", width=110, anchor="center")
        self.tree.column("grupo", width=200)
        self.tree.column("situacao", width=320)

        scrollbar = ttk.Scrollbar(self.tree_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

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
                values=(a.linha, a.nome, a.conta_origem, a.grupo_normalizado, a.situacao),
                tags=(tag,),
            )
        self._atualizar_resumo(accounts)

    def _atualizar_resumo(self, accounts):
        if not accounts:
            self.lbl_resumo.configure(text="")
            self.problemas_container.pack_forget()
            return

        invalidas = [a for a in accounts if not a.valido]
        total = len(accounts)
        if not invalidas:
            self.lbl_resumo.configure(
                text=f"✔ {total} conta(s) carregada(s) e validada(s). Pronto para gerar os scripts.",
                foreground="#1e7e34",
            )
            self.problemas_container.pack_forget()
        else:
            self.lbl_resumo.configure(
                text=(
                    f"✖ {total} conta(s) carregada(s), {len(invalidas)} com problema(s). "
                    "Corrija a planilha e carregue novamente antes de gerar os scripts."
                ),
                foreground="#c0392b",
            )
            detalhes = "\n".join(f"Linha {a.linha}: {a.situacao}" for a in invalidas)
            self.txt_problemas.configure(state="normal")
            self.txt_problemas.delete("1.0", "end")
            self.txt_problemas.insert("1.0", detalhes)
            self.txt_problemas.configure(state="disabled")
            self.problemas_container.pack(fill="x", pady=(6, 0), before=self.tree_container)
