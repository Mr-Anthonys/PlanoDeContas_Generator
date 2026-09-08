"""Painel "Criação de Base": reproduz o fluxo do CriaBase (provisionar a
base de um cliente novo do Gestor Financeiro) dentro do próprio app, com a
base modelo obrigatória e o restante dos campos auto-sugeridos sempre que
possível, para reduzir digitação manual.
"""

import random
import string
import tkinter as tk
import unicodedata
from tkinter import messagebox, ttk

from src.models.session import SessionContext
from src.services import db_connection_service as dbc
from src.services import settings_service
from src.services.criar_base_service import NovaBaseConfig, ProgressEvent

PLACEHOLDER_COLOR = "#9a9a9a"


def _slug(texto: str) -> str:
    """Remove acentos/espaços para compor nomes de base/DSN a partir de
    texto livre (cidade, etc.)."""
    sem_acento = unicodedata.normalize("NFKD", texto or "").encode("ascii", "ignore").decode("ascii")
    return "".join(ch for ch in sem_acento if ch.isalnum())


class CriarBasePanel(ttk.Frame):
    def __init__(self, master, session: SessionContext, on_provisionar=None, **kwargs):
        super().__init__(master, **kwargs)
        self.session = session
        self.on_provisionar = on_provisionar or (lambda cfg, prod_cs, dev_cs: None)
        self._auto_editado_manualmente = {"base_nova": False, "odbc_dsn": False, "diretorio": False}

        self._build()
        self._wire_autosuggest()
        self._carregar_ultimos_servidor()
        # Não busca as bases automaticamente aqui: isso conecta ao SQL Server
        # de forma síncrona ainda durante a construção da MainWindow (antes
        # da janela maximizar), então qualquer lentidão/erro de conexão
        # travava a inicialização inteira do app atrás de um messagebox
        # bloqueante. O usuário busca manualmente com o botão "Buscar bases".

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------
    def _build(self):
        self.columnconfigure(0, weight=1, uniform="col")
        self.columnconfigure(1, weight=1, uniform="col")
        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=0)

        self._build_base_modelo(self)
        self._build_dados_cartorio(self)
        self._build_nova_base(self)
        self._build_regime_dev(self)
        self._build_execucao(self)

    def _build_base_modelo(self, parent):
        grupo = ttk.LabelFrame(parent, text="Base modelo (obrigatório)", padding=10)
        grupo.grid(row=0, column=0, sticky="new", padx=(0, 8), pady=(0, 8))
        grupo.columnconfigure(1, weight=1)

        # Servidor onde a base nova será criada — independente do cliente em
        # que a sessão está logada (cada cliente pode estar em um servidor
        # diferente). A cópia de dados em 03_dados.sql referencia a base
        # modelo como [$BASE_MODELO].dbo.Tabela, sem linked server, então ela
        # precisa estar OBRIGATORIAMENTE no mesmo servidor da base nova.
        self.var_prod_servidor = tk.StringVar(value="")
        self.var_prod_usuario = tk.StringVar(value="")
        self.var_prod_senha = tk.StringVar(value="")

        ttk.Label(grupo, text="Servidor de produção:").grid(row=0, column=0, sticky="w", pady=2)
        ttk.Entry(grupo, textvariable=self.var_prod_servidor).grid(row=0, column=1, sticky="we", pady=2)
        ttk.Label(grupo, text="Usuário:").grid(row=1, column=0, sticky="w", pady=2)
        ttk.Entry(grupo, textvariable=self.var_prod_usuario).grid(row=1, column=1, sticky="we", pady=2)
        ttk.Label(grupo, text="Senha:").grid(row=2, column=0, sticky="w", pady=2)
        ttk.Entry(grupo, textvariable=self.var_prod_senha, show="*").grid(row=2, column=1, sticky="we", pady=2)

        ttk.Label(
            grupo,
            text="Servidor onde a base nova será criada. A base modelo precisa estar nesse mesmo "
            "servidor (a cópia de dados não usa linked server).",
            foreground="#555", wraplength=320,
        ).grid(row=3, column=0, columnspan=2, sticky="w", pady=(4, 8))

        linha = ttk.Frame(grupo)
        linha.grid(row=4, column=0, columnspan=2, sticky="we")
        linha.columnconfigure(0, weight=1)

        self.var_base_modelo = tk.StringVar(value="")
        self.combo_base_modelo = ttk.Combobox(linha, textvariable=self.var_base_modelo, state="disabled")
        self.combo_base_modelo.grid(row=0, column=0, sticky="we")
        ttk.Button(linha, text="Buscar bases", command=self.refresh_bases_modelo).grid(row=0, column=1, padx=(6, 0))

        self.lbl_bases_modelo_status = ttk.Label(grupo, text="", foreground="#555", wraplength=320)
        self.lbl_bases_modelo_status.grid(row=5, column=0, columnspan=2, sticky="w", pady=(6, 0))

    def _build_nova_base(self, parent):
        grupo = ttk.LabelFrame(parent, text="Nova base", padding=10)
        grupo.grid(row=1, column=0, sticky="new", padx=(0, 8))
        grupo.columnconfigure(1, weight=1)

        self.var_cidade = tk.StringVar(value="")
        self.var_uf = tk.StringVar(value="")
        self.var_base_nova = tk.StringVar(value="")
        self.var_base_usuario = tk.StringVar(value="")
        self.var_base_senha = tk.StringVar(value="")
        self.var_odbc_dsn = tk.StringVar(value="")
        self.var_diretorio = tk.StringVar(value="")

        campos = [
            ("Cidade:", self.var_cidade), ("UF:", self.var_uf),
            ("Nome da base nova:", self.var_base_nova),
            ("Usuário da base:", self.var_base_usuario),
        ]
        for i, (rotulo, var) in enumerate(campos):
            ttk.Label(grupo, text=rotulo).grid(row=i, column=0, sticky="w", pady=2)
            ttk.Entry(grupo, textvariable=var).grid(row=i, column=1, sticky="we", pady=2)

        ttk.Label(grupo, text="Senha da base:").grid(row=4, column=0, sticky="w", pady=2)
        senha_frame = ttk.Frame(grupo)
        senha_frame.grid(row=4, column=1, sticky="we", pady=2)
        senha_frame.columnconfigure(0, weight=1)
        ttk.Entry(senha_frame, textvariable=self.var_base_senha, show="*").grid(row=0, column=0, sticky="we")
        ttk.Button(senha_frame, text="Gerar", command=self._gerar_senha).grid(row=0, column=1, padx=(4, 0))

        ttk.Label(grupo, text="DSN ODBC:").grid(row=5, column=0, sticky="w", pady=2)
        ttk.Entry(grupo, textvariable=self.var_odbc_dsn).grid(row=5, column=1, sticky="we", pady=2)

        ttk.Label(grupo, text="Diretório de arquivos:").grid(row=6, column=0, sticky="w", pady=2)
        ttk.Entry(grupo, textvariable=self.var_diretorio).grid(row=6, column=1, sticky="we", pady=2)

    def _build_dados_cartorio(self, parent):
        grupo = ttk.LabelFrame(parent, text="Dados do cartório", padding=10)
        grupo.grid(row=0, column=1, rowspan=2, sticky="new")
        grupo.columnconfigure(1, weight=1)

        self.var_cart_id = tk.StringVar(value="")
        self.var_cart_nome = tk.StringVar(value="")
        self.var_cart_cns = tk.StringVar(value="")
        self.var_cart_endereco = tk.StringVar(value="")
        self.var_cart_bairro = tk.StringVar(value="")
        self.var_cart_cep = tk.StringVar(value="")
        self.var_cart_resp_nome = tk.StringVar(value="")
        self.var_cart_resp_cpf = tk.StringVar(value="")
        self.var_cart_inicio = tk.StringVar(value="")
        self.var_cart_cnpj = tk.StringVar(value="")

        campos = [
            ("Cart ID:", self.var_cart_id),
            ("Nome do cartório:", self.var_cart_nome),
            ("CNS:", self.var_cart_cns),
            ("Endereço:", self.var_cart_endereco),
            ("Bairro:", self.var_cart_bairro),
            ("CEP:", self.var_cart_cep),
            ("Responsável (nome):", self.var_cart_resp_nome),
            ("Responsável (CPF):", self.var_cart_resp_cpf),
            ("Início do responsável (aaaa-mm-dd):", self.var_cart_inicio),
            ("CNPJ:", self.var_cart_cnpj),
        ]
        for i, (rotulo, var) in enumerate(campos):
            ttk.Label(grupo, text=rotulo).grid(row=i, column=0, sticky="w", pady=2)
            ttk.Entry(grupo, textvariable=var).grid(row=i, column=1, sticky="we", pady=2)

        ttk.Label(
            grupo, text="Cidade/UF do cartório vêm do quadro 'Nova base' ao lado.",
            foreground="#555", wraplength=280,
        ).grid(row=len(campos), column=0, columnspan=2, sticky="w", pady=(6, 0))

    def _build_regime_dev(self, parent):
        grupo = ttk.LabelFrame(parent, text="Regime e registro para a equipe (Pro-Packages)", padding=10)
        grupo.grid(row=2, column=0, columnspan=2, sticky="we", pady=(8, 0))
        for col in range(4):
            grupo.columnconfigure(col, weight=1, uniform="dev_col")

        self.var_interino = tk.BooleanVar(value=False)
        ttk.Checkbutton(grupo, text="Responsável interino", variable=self.var_interino).grid(
            row=0, column=0, columnspan=4, sticky="w", pady=(0, 8)
        )

        self.var_dev_servidor = tk.StringVar(value="")
        self.var_dev_usuario = tk.StringVar(value="")
        self.var_dev_senha = tk.StringVar(value="")
        self.var_nome_dev = tk.StringVar(value="")
        self.var_diretorio_dev = tk.StringVar(value="")

        ttk.Label(grupo, text="Servidor dev:").grid(row=1, column=0, sticky="w")
        ttk.Entry(grupo, textvariable=self.var_dev_servidor).grid(row=2, column=0, sticky="we", padx=(0, 8))
        ttk.Label(grupo, text="Usuário dev:").grid(row=1, column=1, sticky="w")
        ttk.Entry(grupo, textvariable=self.var_dev_usuario).grid(row=2, column=1, sticky="we", padx=(0, 8))
        ttk.Label(grupo, text="Senha dev:").grid(row=1, column=2, sticky="w")
        ttk.Entry(grupo, textvariable=self.var_dev_senha, show="*").grid(row=2, column=2, sticky="we", padx=(0, 8))
        ttk.Label(grupo, text="Nome de exibição (dev):").grid(row=3, column=0, sticky="w", pady=(6, 0))
        ttk.Entry(grupo, textvariable=self.var_nome_dev).grid(row=4, column=0, sticky="we", padx=(0, 8))
        ttk.Label(grupo, text="Diretório dev:").grid(row=3, column=1, columnspan=2, sticky="w", pady=(6, 0))
        ttk.Entry(grupo, textvariable=self.var_diretorio_dev).grid(row=4, column=1, columnspan=2, sticky="we", padx=(0, 8))

    def _build_execucao(self, parent):
        grupo = ttk.Frame(parent)
        grupo.grid(row=3, column=0, columnspan=2, sticky="nsew", pady=(8, 0))
        grupo.columnconfigure(0, weight=1)
        parent.rowconfigure(3, weight=1)

        passos_visiveis = [
            "schema", "usuario", "dados", "cartorio", "cartorio_id",
            "parametros_prod", "parametros_dev", "interino",
        ]
        self.progress = ttk.Progressbar(grupo, mode="determinate", maximum=len(passos_visiveis))
        self.progress.grid(row=0, column=0, sticky="we", pady=(0, 6))

        self.txt_log = tk.Text(grupo, height=8, state="disabled", background="#f7f7f7")
        self.txt_log.grid(row=1, column=0, sticky="nsew")
        grupo.rowconfigure(1, weight=1)

        self.btn_provisionar = ttk.Button(grupo, text="Provisionar base", command=self._confirmar_e_provisionar)
        self.btn_provisionar.grid(row=2, column=0, sticky="e", pady=(8, 0))

    # ------------------------------------------------------------------
    # Auto-sugestão
    # ------------------------------------------------------------------
    def _wire_autosuggest(self):
        self.var_base_nova.trace_add("write", lambda *_: self._marcar_editado_manualmente("base_nova"))
        self.var_odbc_dsn.trace_add("write", lambda *_: self._marcar_editado_manualmente("odbc_dsn"))
        self.var_diretorio.trace_add("write", lambda *_: self._marcar_editado_manualmente("diretorio"))
        self.var_cidade.trace_add("write", lambda *_: self._atualizar_sugestoes())
        self.var_uf.trace_add("write", lambda *_: self._atualizar_sugestoes())

    def _marcar_editado_manualmente(self, campo):
        # Só marca como "manual" se o valor não veio da própria auto-sugestão
        # (evita marcar quando é o _atualizar_sugestoes escrevendo).
        if getattr(self, "_atualizando_sugestao", False):
            return
        self._auto_editado_manualmente[campo] = True

    def _atualizar_sugestoes(self):
        cidade = _slug(self.var_cidade.get())
        uf = self.var_uf.get().strip().upper()[:2]
        if not cidade or not uf:
            return
        self._atualizando_sugestao = True
        try:
            if not self._auto_editado_manualmente["base_nova"]:
                self.var_base_nova.set(f"Gestor_{uf}_{cidade}")
            if not self._auto_editado_manualmente["odbc_dsn"]:
                self.var_odbc_dsn.set(f"ODBC_GF_{uf}_{cidade[:20]}")
            if not self._auto_editado_manualmente["diretorio"]:
                base_nome = self.var_base_nova.get() or f"Gestor_{uf}_{cidade}"
                self.var_diretorio.set(f"C:\\ProPackages\\Arquivos\\{base_nome}\\")
        finally:
            self._atualizando_sugestao = False

    def _gerar_senha(self):
        alfabeto = string.ascii_letters + string.digits
        self.var_base_senha.set("".join(random.choices(alfabeto, k=16)))

    # ------------------------------------------------------------------
    # Dados auxiliares
    # ------------------------------------------------------------------
    def refresh_bases_modelo(self):
        servidor = self.var_prod_servidor.get().strip()
        usuario = self.var_prod_usuario.get().strip()
        if not servidor or not usuario:
            messagebox.showwarning(
                "Base modelo", "Informe servidor e usuário de produção antes de buscar as bases."
            )
            return

        cs = dbc.ConnectionSettings(servidor=servidor, usuario=usuario, senha=self.var_prod_senha.get())
        try:
            conn = dbc.connect(cs)
            bases = dbc.listar_bases_gestor(conn)
            dbc.close(conn)
        except Exception as exc:
            messagebox.showerror("Base modelo", f"Falha ao listar bases: {exc}")
            self.combo_base_modelo.configure(state="disabled")
            self.combo_base_modelo["values"] = []
            self.lbl_bases_modelo_status.configure(text="")
            return

        self.combo_base_modelo.configure(state="readonly" if bases else "disabled")
        self.combo_base_modelo["values"] = bases
        if bases:
            self.lbl_bases_modelo_status.configure(text=f"{len(bases)} base(s) encontrada(s).", foreground="#1b7a1b")
        else:
            self.var_base_modelo.set("")
            self.lbl_bases_modelo_status.configure(
                text="Conexão ok, mas nenhuma base 'Gestor_*' foi encontrada nesse servidor.",
                foreground="#b00020",
            )

    def _carregar_ultimos_servidor(self):
        dados = settings_service.load_last_criar_base_settings()
        # Servidor/usuário de produção: usa o último valor salvo ou, na
        # ausência dele, a sessão logada como sugestão inicial (frequentemente
        # é o mesmo servidor, mas sempre editável — ver nota em
        # _build_base_modelo sobre por que isso não pode ficar implícito).
        self.var_prod_servidor.set(dados.get("prod_servidor", "") or self.session.connection_settings.servidor)
        self.var_prod_usuario.set(dados.get("prod_usuario", "") or self.session.connection_settings.usuario)
        self.var_prod_senha.set(self.session.connection_settings.senha)

        self.var_dev_servidor.set(dados.get("dev_servidor", ""))
        self.var_dev_usuario.set(dados.get("dev_usuario", ""))
        self.var_nome_dev.set(dados.get("nome_dev", ""))
        self.var_diretorio_dev.set(dados.get("diretorio_dev", ""))

    # ------------------------------------------------------------------
    # Validação / execução
    # ------------------------------------------------------------------
    def _campos_obrigatorios_faltando(self) -> list:
        obrigatorios = [
            ("Servidor de produção", self.var_prod_servidor.get()),
            ("Usuário de produção", self.var_prod_usuario.get()),
            ("Senha de produção", self.var_prod_senha.get()),
            ("Base modelo", self.var_base_modelo.get()),
            ("Nome da base nova", self.var_base_nova.get()),
            ("Usuário da base", self.var_base_usuario.get()),
            ("Senha da base", self.var_base_senha.get()),
            ("Nome do cartório", self.var_cart_nome.get()),
            ("Cidade", self.var_cidade.get()),
            ("UF", self.var_uf.get()),
            ("Cart ID", self.var_cart_id.get()),
            ("Servidor dev", self.var_dev_servidor.get()),
            ("Usuário dev", self.var_dev_usuario.get()),
            ("Senha dev", self.var_dev_senha.get()),
            ("Nome de exibição (dev)", self.var_nome_dev.get()),
        ]
        return [nome for nome, valor in obrigatorios if not valor.strip()]

    def _montar_config(self) -> NovaBaseConfig:
        return NovaBaseConfig(
            base_modelo=self.var_base_modelo.get(),
            base_nova=self.var_base_nova.get(),
            base_usuario=self.var_base_usuario.get(),
            base_senha=self.var_base_senha.get(),
            cart_interino=self.var_interino.get(),
            cart_id=self.var_cart_id.get(),
            cart_nome=self.var_cart_nome.get(),
            cart_cns=self.var_cart_cns.get(),
            cart_cidade=self.var_cidade.get(),
            cart_estado=self.var_uf.get(),
            cart_endereco=self.var_cart_endereco.get(),
            cart_bairro=self.var_cart_bairro.get(),
            cart_cep=self.var_cart_cep.get(),
            cart_resp_nome=self.var_cart_resp_nome.get(),
            cart_resp_cpf=self.var_cart_resp_cpf.get(),
            cart_inicio=self.var_cart_inicio.get(),
            cart_cnpj=self.var_cart_cnpj.get(),
            diretorio=self.var_diretorio.get(),
            odbc_dsn=self.var_odbc_dsn.get(),
            nome_dev=self.var_nome_dev.get(),
            diretorio_dev=self.var_diretorio_dev.get(),
        )

    def _montar_prod_cs(self) -> dbc.ConnectionSettings:
        return dbc.ConnectionSettings(
            servidor=self.var_prod_servidor.get(),
            usuario=self.var_prod_usuario.get(),
            senha=self.var_prod_senha.get(),
        )

    def _montar_dev_cs(self) -> dbc.ConnectionSettings:
        return dbc.ConnectionSettings(
            servidor=self.var_dev_servidor.get(),
            usuario=self.var_dev_usuario.get(),
            senha=self.var_dev_senha.get(),
        )

    def _confirmar_e_provisionar(self):
        faltando = self._campos_obrigatorios_faltando()
        if faltando:
            messagebox.showwarning("Criação de base", "Preencha os campos obrigatórios:\n\n" + "\n".join(faltando))
            return

        cfg = self._montar_config()
        resumo = (
            f"Isto vai CRIAR o banco '{cfg.base_nova}' no servidor de produção, copiar dados de "
            f"'{cfg.base_modelo}' e registrar o cliente '{cfg.cart_nome}' no Gestor_Parametros "
            f"(produção e dev).\n\nEsta ação não é reversível automaticamente.\n\nDeseja continuar?"
        )
        if not messagebox.askyesno("Confirmar provisionamento", resumo, icon="warning"):
            return

        settings_service.save_last_criar_base_settings({
            "prod_servidor": self.var_prod_servidor.get(),
            "prod_usuario": self.var_prod_usuario.get(),
            "dev_servidor": self.var_dev_servidor.get(),
            "dev_usuario": self.var_dev_usuario.get(),
            "nome_dev": cfg.nome_dev,
            "diretorio_dev": cfg.diretorio_dev,
        })

        self.on_provisionar(cfg, self._montar_prod_cs(), self._montar_dev_cs())

    # ------------------------------------------------------------------
    # Progresso (chamado pela MainWindow via fila thread-safe)
    # ------------------------------------------------------------------
    def set_busy(self, ocupado: bool):
        self.btn_provisionar.configure(state="disabled" if ocupado else "normal")
        if not ocupado:
            return
        self.progress["value"] = 0
        self.txt_log.configure(state="normal")
        self.txt_log.delete("1.0", "end")
        self.txt_log.configure(state="disabled")

    def append_log(self, evento: ProgressEvent):
        linha = None
        if evento.kind == "step_start":
            linha = f"» {evento.message}..."
        elif evento.kind == "step_done":
            linha = f"✓ {evento.message}"
            self.progress["value"] += 1
        elif evento.kind == "step_error":
            linha = f"✗ ERRO em '{evento.step_name}': {evento.message}"
        elif evento.kind == "all_done":
            linha = f"✓ {evento.message}"

        if linha is None:
            return
        self.txt_log.configure(state="normal")
        self.txt_log.insert("end", linha + "\n")
        self.txt_log.see("end")
        self.txt_log.configure(state="disabled")
