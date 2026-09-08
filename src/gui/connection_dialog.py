"""Diálogo de login exibido antes da janela principal: conectar ao SQL
Server e escolher a "base ativa" (o banco do cliente atual, usado por
Criar Contas/Excluir Contas para executar ao vivo pelo resto da sessão).

Modo automático (padrão quando a variável de ambiente GESTOR_PARAM está
definida nesta máquina): conecta ao banco central Gestor_Parametros com o
login fixo do sistema, lista os clientes de Parametros_Clientes e usa o
Servidor/Usuário/Senha/Banco daquela linha para abrir a sessão — o mesmo
fluxo que o Gestor Financeiro VB6 usa (ver modBancoDeParametros.bas). Se a
variável não estiver definida, ou a conexão ao banco central falhar, cai
para o modo manual (servidor/usuário/senha digitados à mão). O usuário pode
alternar entre os dois modos a qualquer momento pelo link no rodapé.

Não confundir com a "base modelo" escolhida depois, dentro da aba Criação
de Base — são seleções independentes, com propósitos diferentes.
"""

import tkinter as tk
from tkinter import messagebox, ttk

from src.models.session import SessionContext
from src.services import db_connection_service as dbc
from src.services import parametros_service
from src.services import settings_service


class ConnectionDialog(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Conectar ao servidor")
        self.resizable(False, False)
        self.result: SessionContext | None = None
        self._conexao_testada = None  # ConnectionSettings da última conexão manual bem-sucedida
        self._clientes: dict[str, parametros_service.ClienteParametro] = {}

        self._servidor_param = parametros_service.servidor_parametros()
        self._modo = "auto" if self._servidor_param else "manual"

        self._build_shell()
        self._trocar_modo(self._modo, tentar_auto_primeiro=True)
        self.protocol("WM_DELETE_WINDOW", self._cancelar)
        # Sem self.transient(master): com o root escondido (withdraw()) no
        # app.py, marcar este Toplevel como transient dele impede o Windows
        # de criar uma janela nativa visível para o diálogo (bug observado
        # nesta versão do Tk/Windows). grab_set() já garante a modalidade.
        self.grab_set()

    # -- estrutura fixa (campos variam por modo dentro de self.campos) -----

    def _build_shell(self):
        frame = ttk.Frame(self, padding=16)
        frame.pack(fill="both", expand=True)

        self.campos = ttk.Frame(frame)
        self.campos.grid(row=0, column=0, sticky="we")

        self.lbl_status = ttk.Label(frame, text="", foreground="#555", wraplength=340)
        self.lbl_status.grid(row=1, column=0, sticky="w", pady=(8, 0))

        self.lnk_alternar = ttk.Label(frame, text="", foreground="#0563c1", cursor="hand2")
        self.lnk_alternar.grid(row=2, column=0, sticky="w", pady=(8, 0))
        self.lnk_alternar.bind("<Button-1>", lambda _e: self._alternar_modo())

        botoes = ttk.Frame(frame)
        botoes.grid(row=3, column=0, sticky="e", pady=(12, 0))
        ttk.Button(botoes, text="Cancelar", command=self._cancelar).pack(side="right", padx=(6, 0))
        self.btn_conectar = ttk.Button(botoes, text="Conectar", command=self._conectar, state="disabled")
        self.btn_conectar.pack(side="right")

    def _alternar_modo(self):
        self._trocar_modo("manual" if self._modo == "auto" else "auto")

    def _trocar_modo(self, modo: str, tentar_auto_primeiro: bool = False):
        self._modo = modo
        self.lbl_status.configure(text="")
        self.btn_conectar.configure(state="disabled")
        for widget in self.campos.winfo_children():
            widget.destroy()

        if modo == "auto":
            self._build_campos_auto()
            self.lnk_alternar.configure(text="Usar conexão manual")
            if tentar_auto_primeiro or not self._clientes:
                self._carregar_clientes_automatico()
        else:
            self._build_campos_manual()
            if self._servidor_param:
                self.lnk_alternar.configure(text="Voltar para conexão automática (GESTOR_PARAM)")
            else:
                self.lnk_alternar.configure(text="")

    # -- modo automático (GESTOR_PARAM -> Parametros_Clientes) -------------

    def _build_campos_auto(self):
        c = self.campos
        ttk.Label(c, text="Servidor de parâmetros (GESTOR_PARAM):").grid(row=0, column=0, sticky="w")
        ttk.Label(c, text=self._servidor_param or "", foreground="#555").grid(row=0, column=1, sticky="w", padx=(6, 0))

        ttk.Label(c, text="Cliente:").grid(row=1, column=0, sticky="w", pady=(8, 0))
        self.var_cliente = tk.StringVar(value="")
        self.combo_cliente = ttk.Combobox(c, textvariable=self.var_cliente, state="disabled", width=34)
        self.combo_cliente.grid(row=1, column=1, sticky="we", pady=(8, 0))
        self.combo_cliente.bind("<<ComboboxSelected>>", lambda _e: self._atualizar_botao_conectar())

        ttk.Button(c, text="Atualizar lista", command=self._carregar_clientes_automatico).grid(
            row=2, column=1, sticky="w", pady=(6, 0)
        )

    def _carregar_clientes_automatico(self):
        if not self._servidor_param:
            return
        self.lbl_status.configure(text="Consultando Gestor_Parametros...", foreground="#555")
        self.update_idletasks()

        try:
            conn = parametros_service.conectar_banco_parametros(self._servidor_param)
            clientes = parametros_service.listar_clientes(conn)
            dbc.close(conn)
        except Exception as exc:
            self.lbl_status.configure(text=f"Falha ao consultar Gestor_Parametros: {exc}", foreground="#b00020")
            self.combo_cliente.configure(state="disabled")
            self.combo_cliente["values"] = []
            return

        self._clientes = {cliente.nome: cliente for cliente in clientes}
        nomes = list(self._clientes.keys())
        self.combo_cliente.configure(state="readonly" if nomes else "disabled")
        self.combo_cliente["values"] = nomes
        if nomes:
            ultimo = settings_service.load_last_connection().get("ultimo_cliente_parametros", "")
            self.var_cliente.set(ultimo if ultimo in self._clientes else nomes[0])
            self.lbl_status.configure(text=f"{len(nomes)} cliente(s) encontrado(s).", foreground="#1b7a1b")
        else:
            self.var_cliente.set("")
            self.lbl_status.configure(text="Nenhum cliente cadastrado em Parametros_Clientes.", foreground="#b00020")
        self._atualizar_botao_conectar()

    # -- modo manual (servidor/usuário/senha digitados) ---------------------

    def _build_campos_manual(self):
        c = self.campos
        ultimos = settings_service.load_last_connection()

        self.var_servidor = tk.StringVar(value=ultimos.get("ultimo_servidor", ""))
        self.var_usuario = tk.StringVar(value=ultimos.get("ultimo_usuario", ""))
        self.var_senha = tk.StringVar(value="")
        self.var_base = tk.StringVar(value="")

        ttk.Label(c, text="Servidor:").grid(row=0, column=0, sticky="w", pady=(0, 4))
        ttk.Entry(c, textvariable=self.var_servidor, width=36).grid(row=0, column=1, columnspan=2, sticky="we", pady=(0, 4))

        ttk.Label(c, text="Usuário:").grid(row=1, column=0, sticky="w", pady=(0, 4))
        ttk.Entry(c, textvariable=self.var_usuario, width=36).grid(row=1, column=1, columnspan=2, sticky="we", pady=(0, 4))

        ttk.Label(c, text="Senha:").grid(row=2, column=0, sticky="w", pady=(0, 4))
        ttk.Entry(c, textvariable=self.var_senha, show="*", width=36).grid(row=2, column=1, columnspan=2, sticky="we", pady=(0, 4))

        self.btn_testar = ttk.Button(c, text="Testar conexão", command=self._testar_conexao)
        self.btn_testar.grid(row=3, column=0, columnspan=3, sticky="we", pady=(4, 8))

        ttk.Label(c, text="Base ativa (Gestor):").grid(row=4, column=0, sticky="w", pady=(4, 4))
        self.combo_base = ttk.Combobox(c, textvariable=self.var_base, state="disabled", width=34)
        self.combo_base.grid(row=4, column=1, columnspan=2, sticky="we", pady=(4, 4))
        self.combo_base.bind("<<ComboboxSelected>>", lambda _e: self._atualizar_botao_conectar())

        for var in (self.var_servidor, self.var_usuario, self.var_senha):
            var.trace_add("write", lambda *_: self._invalidar_teste())

    def _invalidar_teste(self):
        self._conexao_testada = None
        self.combo_base.configure(state="disabled")
        self.combo_base["values"] = []
        self.var_base.set("")
        self._atualizar_botao_conectar()
        self.lbl_status.configure(text="")

    def _cs_atual(self) -> dbc.ConnectionSettings:
        return dbc.ConnectionSettings(
            servidor=self.var_servidor.get().strip(),
            usuario=self.var_usuario.get().strip(),
            senha=self.var_senha.get(),
        )

    def _testar_conexao(self):
        cs = self._cs_atual()
        if not cs.servidor or not cs.usuario:
            messagebox.showwarning("Conectar", "Informe servidor e usuário.")
            return
        self.lbl_status.configure(text="Testando conexão...", foreground="#555")
        self.update_idletasks()

        ok, mensagem = dbc.test_connection(cs)
        if not ok:
            self.lbl_status.configure(text=f"Falha: {mensagem}", foreground="#b00020")
            return

        try:
            conn = dbc.connect(cs)
            bases = dbc.listar_bases_gestor(conn)
            dbc.close(conn)
        except Exception as exc:
            self.lbl_status.configure(text=f"Falha ao listar bases: {exc}", foreground="#b00020")
            return

        self._conexao_testada = cs
        self.lbl_status.configure(text="Conexão bem-sucedida.", foreground="#1b7a1b")
        self.combo_base.configure(state="readonly" if bases else "disabled")
        self.combo_base["values"] = bases
        if not bases:
            self.lbl_status.configure(
                text="Conexão ok, mas nenhuma base 'Gestor_*' foi encontrada neste servidor.",
                foreground="#b00020",
            )
        self._atualizar_botao_conectar()

    # -- comum aos dois modos ------------------------------------------------

    def _atualizar_botao_conectar(self):
        if self._modo == "auto":
            pode_conectar = bool(self.var_cliente.get()) and self.var_cliente.get() in self._clientes
        else:
            pode_conectar = self._conexao_testada is not None and bool(self.var_base.get())
        self.btn_conectar.configure(state="normal" if pode_conectar else "disabled")

    def _conectar(self):
        if self._modo == "auto":
            self._conectar_automatico()
        else:
            self._conectar_manual()

    def _conectar_automatico(self):
        cliente = self._clientes.get(self.var_cliente.get())
        if cliente is None:
            return
        cs = parametros_service.conexao_para_cliente(cliente)
        try:
            conn = dbc.connect(cs, autocommit=True)
        except Exception as exc:
            messagebox.showerror("Conectar", f"Falha ao abrir a sessão do cliente '{cliente.nome}':\n{exc}")
            return

        settings_service.save_last_connection(cs.servidor, cs.usuario, ultimo_cliente_parametros=cliente.nome)
        # connection_settings guarda servidor/usuário/senha sem fixar o
        # "Banco" do cliente (mesmo padrão do modo manual: a base ativa da
        # sessão fica em base_ativa/connection; connection_settings é
        # reaproveitado depois como login "de servidor" pela aba Criação de
        # Base, ver main_window._worker_provisionar).
        cs_admin = dbc.ConnectionSettings(servidor=cs.servidor, usuario=cs.usuario, senha=cs.senha)
        self.result = SessionContext(connection_settings=cs_admin, connection=conn, base_ativa=cs.database)
        self.destroy()

    def _conectar_manual(self):
        cs = self._conexao_testada
        base = self.var_base.get()
        if cs is None or not base:
            return
        cs_sessao = dbc.ConnectionSettings(servidor=cs.servidor, usuario=cs.usuario, senha=cs.senha, database=base)
        try:
            conn = dbc.connect(cs_sessao, autocommit=True)
        except Exception as exc:
            messagebox.showerror("Conectar", f"Falha ao abrir a sessão na base '{base}':\n{exc}")
            return

        settings_service.save_last_connection(cs.servidor, cs.usuario)
        self.result = SessionContext(connection_settings=cs, connection=conn, base_ativa=base)
        self.destroy()

    def _cancelar(self):
        self.result = None
        self.destroy()


def show_connection_dialog(root: tk.Tk) -> SessionContext | None:
    dialog = ConnectionDialog(root)
    root.wait_window(dialog)
    return dialog.result
