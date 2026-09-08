"""Painel "Excluir contas": consulta no banco do Gestor conectado quais
registros já existem para os processos cobertos pela geração de scripts
(Contas, GrupoContábil, InterfaceContas, InterfaceArq, InterfaceComum,
InterfaceFormaPgto, InterfaceHistorico), deixando o usuário marcar quais
linhas quer excluir antes de rodar os DELETEs no banco.

Reaproveita a planilha e as Configurações gerais já carregadas na aba
"Criar contas" (ver MainWindow._consultar_exclusoes) — esta tela não tem
carregamento de planilha próprio.
"""

import tkinter as tk
from tkinter import ttk

from src.gui.scrollable_area import ScrollableArea

MARCA_VAZIA = "☐"
MARCA_SELECIONADA = "☑"


class _SecaoTabela(ttk.LabelFrame):
    """Uma seção da tela: título (+ aviso quando a tabela é configuração
    compartilhada por TipoArq) + treeview com uma coluna "Excluir" que
    alterna ☐/☑ ao clicar na linha."""

    def __init__(self, master, resultado, on_selecao_mudou=None, **kwargs):
        super().__init__(master, text=resultado.consulta.titulo, padding=8, **kwargs)
        self.resultado = resultado
        self.on_selecao_mudou = on_selecao_mudou or (lambda: None)
        self.selecionados = set()
        self.tree = None
        self._build()

    def _build(self):
        if self.resultado.consulta.compartilhada:
            ttk.Label(
                self,
                text="⚠ Configuração compartilhada por TipoArq — excluir aqui pode afetar outras contas/clientes que usam o mesmo TipoArq.",
                foreground="#b00020", wraplength=900,
            ).pack(fill="x", pady=(0, 6))

        if self.resultado.erro:
            ttk.Label(
                self, text=f"Falha ao consultar: {self.resultado.erro}", foreground="#b00020", wraplength=900,
            ).pack(fill="x")
            return

        if not self.resultado.linhas:
            ttk.Label(self, text="Nenhum registro encontrado.", foreground="#555").pack(fill="x")
            return

        barra = ttk.Frame(self)
        barra.pack(fill="x", pady=(0, 4))
        ttk.Label(
            barra, text=f"{len(self.resultado.linhas)} registro(s) encontrado(s).", font=("Segoe UI", 9, "bold"),
        ).pack(side="left")
        ttk.Button(barra, text="Selecionar todos", command=self._selecionar_todos).pack(side="right")
        ttk.Button(barra, text="Limpar seleção", command=self._limpar_selecao).pack(side="right", padx=(0, 6))

        container = ttk.Frame(self)
        container.pack(fill="both", expand=True)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(0, weight=1)

        colunas = ("__sel__",) + tuple(self.resultado.colunas)
        altura = max(2, min(8, len(self.resultado.linhas)))
        self.tree = ttk.Treeview(container, columns=colunas, show="headings", height=altura)
        self.tree.heading("__sel__", text="Excluir")
        self.tree.column("__sel__", width=60, anchor="center", stretch=False)
        for col in self.resultado.colunas:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=140)

        scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        for i, linha in enumerate(self.resultado.linhas):
            valores = (MARCA_VAZIA,) + tuple(self._formatar(linha.get(c)) for c in self.resultado.colunas)
            self.tree.insert("", "end", iid=str(i), values=valores)

        self.tree.bind("<Button-1>", self._on_click)

    @staticmethod
    def _formatar(valor):
        return "" if valor is None else str(valor)

    def _on_click(self, event):
        if self.tree.identify_region(event.x, event.y) != "cell":
            return
        if self.tree.identify_column(event.x) != "#1":  # só a coluna "Excluir" alterna seleção
            return
        iid = self.tree.identify_row(event.y)
        if iid:
            self._alternar(iid)

    def _alternar(self, iid):
        idx = int(iid)
        if idx in self.selecionados:
            self.selecionados.discard(idx)
            marca = MARCA_VAZIA
        else:
            self.selecionados.add(idx)
            marca = MARCA_SELECIONADA
        valores = list(self.tree.item(iid, "values"))
        valores[0] = marca
        self.tree.item(iid, values=valores)
        self.on_selecao_mudou()

    def _selecionar_todos(self):
        for iid in self.tree.get_children():
            if int(iid) not in self.selecionados:
                self._alternar(iid)

    def _limpar_selecao(self):
        for iid in list(self.tree.get_children()):
            if int(iid) in self.selecionados:
                self._alternar(iid)

    def itens_selecionados(self):
        """[(titulo, tabela, colunas_chave, linha_dict), ...] das linhas marcadas."""
        consulta = self.resultado.consulta
        return [
            (consulta.titulo, consulta.tabela, consulta.colunas_chave, self.resultado.linhas[idx])
            for idx in sorted(self.selecionados)
        ]

    def total_selecionados(self):
        return len(self.selecionados)


class ExcluirContasPanel(ttk.Frame):
    def __init__(self, master, on_consultar=None, on_excluir=None, **kwargs):
        super().__init__(master, **kwargs)
        self.on_consultar = on_consultar or (lambda: None)
        self.on_excluir = on_excluir or (lambda itens: None)
        self._secoes = []
        self._build()

    def _build(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        topo = ttk.Frame(self)
        topo.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        ttk.Button(topo, text="Consultar", command=self.on_consultar).pack(side="left")
        self.lbl_status = ttk.Label(
            topo,
            text="Consulte para ver, no banco conectado, as contas e registros que já existem para as "
            "Configurações gerais e a planilha carregadas em \"Criar contas\".",
            foreground="#555", wraplength=900,
        )
        self.lbl_status.pack(side="left", padx=(10, 0))

        self.area = ScrollableArea(self)
        self.area.grid(row=1, column=0, sticky="nsew")

        rodape = ttk.Frame(self)
        rodape.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        self.lbl_selecionados = ttk.Label(rodape, text="")
        self.lbl_selecionados.pack(side="left")
        self.btn_excluir = ttk.Button(
            rodape, text="Excluir selecionados", command=self._on_excluir_clicked, state="disabled",
        )
        self.btn_excluir.pack(side="right")

    def mostrar_resultados(self, resultados):
        for widget in self.area.interior.winfo_children():
            widget.destroy()
        self._secoes = []

        total_encontrado = 0
        for resultado in resultados:
            secao = _SecaoTabela(self.area.interior, resultado, on_selecao_mudou=self._atualizar_contagem)
            secao.pack(fill="x", pady=(0, 8), padx=(0, 4))
            self._secoes.append(secao)
            total_encontrado += len(resultado.linhas)

        self.lbl_status.configure(
            text=f"{total_encontrado} registro(s) encontrado(s) no total, em {len(resultados)} tabela(s)."
        )
        self._atualizar_contagem()

    def _atualizar_contagem(self):
        total = sum(s.total_selecionados() for s in self._secoes)
        self.lbl_selecionados.configure(text=f"{total} selecionado(s)." if total else "")
        self.btn_excluir.configure(state="normal" if total else "disabled")

    def _on_excluir_clicked(self):
        itens = []
        for secao in self._secoes:
            itens.extend(secao.itens_selecionados())
        if itens:
            self.on_excluir(itens)
