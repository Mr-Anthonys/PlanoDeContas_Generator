"""Painel "Criação de Base": reproduz o fluxo do CriaBase (provisionar a
base de um cliente novo do Gestor Financeiro) dentro do próprio app, como um
assistente de várias etapas (a quantidade de campos não cabe numa tela só):

1. Servidores e base modelo — servidor da base modelo e servidor de destino
   (onde a base nova será criada) podem ser o mesmo (checkbox) ou diferentes.
2. Nova base e cartório — dados da base nova e do cartório.
3. Tabelas adicionais (opcional) — além das ~15 tabelas fixas que
   03_dados.sql já copia, permite escolher tabelas/colunas extras do banco
   modelo pra copiar pra base nova.
4. Registro em Parametros_Clientes — os 13 campos de
   Gestor_Parametros.Parametros_Clientes, com a mesma linha registrada em
   1+ servidores escolhidos (base modelo / destino / os dois), sempre
   também no ServidorPP (nosso, 100.77.102.1,1435).
5. Confirmação e execução.
"""

import random
import string
import tkinter as tk
import unicodedata
from tkinter import messagebox, ttk

from src.gui.scrollable_area import ScrollableArea
from src.models.session import SessionContext
from src.services import db_connection_service as dbc
from src.services import schema_service, settings_service
from src.services.criar_base_service import (
    AlvoParametros, NovaBaseConfig, ParametrosClienteConfig, PlanoProvisionamento, ProgressEvent, TabelaExtra,
)
from src.utils.constants import SERVIDOR_PP

PLACEHOLDER_COLOR = "#9a9a9a"

PARAM_DEFAULT_BROWSER_DASHBOARD = "CHROME"
PARAM_DEFAULT_URL_DASHBOARD = "https://dashboard-frontend-masterr.herokuapp.com/"
PARAM_DEFAULT_URL_DASHBOARD_TOKEN = "https://dashboard-frontend-masterr.herokuapp.com/"
PARAM_DEFAULT_DIRETORIO_MENSALISTAS = r"C:\ProPackages\Mensalistas\Propackage.Gestor.UI.exe"
PARAM_DEFAULT_URL_VALIDACAO = ""
PARAM_DEFAULT_URL_GESTOR_CLIENTES = "https://gestor-clientes-git-main-propackages-projects.vercel.app/api/notaries/"

# Tabelas que ficam pré-selecionadas na etapa 3 (Tabelas adicionais) mas SEM
# nenhuma coluna marcada, ou seja, sem dado nenhum copiado: Resumo já é
# coberto pela cópia fixa (03_dados.sql) — copiar de novo aqui duplicaria
# linhas —, e Lançamentos/Lanca_exclui/InterfaceDataArq são tabelas
# transacionais que 03_dados.sql já limpa (DELETE) e deliberadamente não
# repopula numa base nova.
TABELAS_SEM_COPIA_PADRAO = ["Resumo", "Lançamentos", "Lanca_exclui", "InterfaceDataArq"]
TABELAS_SEM_COPIA_PADRAO_LOWER = {t.lower() for t in TABELAS_SEM_COPIA_PADRAO}

ETAPAS = [
    ("servidores", "1. Servidores e base modelo"),
    ("nova_base", "2. Nova base e cartório"),
    ("tabelas_extras", "3. Tabelas adicionais"),
    ("parametros", "4. Registro em Parametros_Clientes"),
    ("execucao", "5. Confirmação e execução"),
]


def _slug(texto: str) -> str:
    """Remove acentos/espaços para compor nomes de base/DSN a partir de
    texto livre (cidade, etc.)."""
    sem_acento = unicodedata.normalize("NFKD", texto or "").encode("ascii", "ignore").decode("ascii")
    return "".join(ch for ch in sem_acento if ch.isalnum())


class CriarBasePanel(ttk.Frame):
    def __init__(self, master, session: SessionContext, on_provisionar=None, **kwargs):
        super().__init__(master, **kwargs)
        self.session = session
        self.on_provisionar = on_provisionar or (lambda plano: None)
        self._auto_editado_manualmente = {
            "odbc_dsn": False, "diretorio": False,
            "param_banco": False, "param_usuario": False, "param_senha": False,
            "param_diretorio": False, "param_odbc": False,
        }
        self._tabelas_estado = {}  # nome_tabela -> {"var": BooleanVar, "frame": Frame|None, "colunas": {col: BooleanVar}}
        self._colunas_cache = {}  # nome_tabela -> [colunas]

        self._build()
        self._wire_autosuggest()
        self._carregar_ultimos_servidor()
        self._ir_para_etapa(0)

    # ------------------------------------------------------------------
    # Estrutura geral: indicador de etapas + área rolável + navegação fixa
    # ------------------------------------------------------------------
    def _build(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self._build_indicador_etapas()

        self.area = ScrollableArea(self)
        self.area.grid(row=1, column=0, sticky="nsew", pady=(8, 0))

        self._etapa_frames = {}
        self._etapa_frames["servidores"] = self._build_etapa_servidores(self.area.interior)
        self._etapa_frames["nova_base"] = self._build_etapa_nova_base(self.area.interior)
        self._etapa_frames["tabelas_extras"] = self._build_etapa_tabelas_extras(self.area.interior)
        self._etapa_frames["parametros"] = self._build_etapa_parametros(self.area.interior)
        self._etapa_frames["execucao"] = self._build_etapa_execucao(self.area.interior)
        for frame in self._etapa_frames.values():
            frame.grid(row=0, column=0, sticky="nsew")
        self.area.interior.columnconfigure(0, weight=1)

        self._build_navegacao()

    def _build_indicador_etapas(self):
        barra = ttk.Frame(self)
        barra.grid(row=0, column=0, sticky="ew")
        self._labels_etapas = {}
        for i, (chave, titulo) in enumerate(ETAPAS):
            lbl = tk.Label(
                barra, text=titulo, font=("Segoe UI", 10, "bold"), foreground="#8c8c8c", cursor="hand2",
            )
            lbl.pack(side="left", padx=(0 if i == 0 else 12, 0))
            lbl.bind("<Button-1>", lambda _e, idx=i: self._ir_para_etapa(idx))
            self._labels_etapas[chave] = lbl

    def _build_navegacao(self):
        barra = ttk.Frame(self)
        barra.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        self.btn_voltar = ttk.Button(barra, text="◀ Voltar", command=self._etapa_anterior)
        self.btn_voltar.pack(side="left")
        self.btn_avancar = ttk.Button(barra, text="Avançar ▶", command=self._proxima_etapa)
        self.btn_avancar.pack(side="right")

    def _ir_para_etapa(self, indice: int):
        self._etapa_atual = max(0, min(indice, len(ETAPAS) - 1))
        chave, _ = ETAPAS[self._etapa_atual]
        self._etapa_frames[chave].tkraise()
        for i, (k, _titulo) in enumerate(ETAPAS):
            self._labels_etapas[k].configure(foreground="#000000" if i == self._etapa_atual else "#8c8c8c")
        self.btn_voltar.configure(state="disabled" if self._etapa_atual == 0 else "normal")
        self.btn_avancar.configure(state="disabled" if self._etapa_atual == len(ETAPAS) - 1 else "normal")
        if chave == "execucao":
            self._atualizar_resumo_execucao()
        self.area.scroll_to_top()

    def _etapa_anterior(self):
        self._ir_para_etapa(self._etapa_atual - 1)

    def _proxima_etapa(self):
        self._ir_para_etapa(self._etapa_atual + 1)

    # ------------------------------------------------------------------
    # Etapa 1: servidores e base modelo
    # ------------------------------------------------------------------
    def _build_etapa_servidores(self, parent):
        frame = ttk.Frame(parent, padding=(0, 8))
        frame.columnconfigure(0, weight=1, uniform="col")
        frame.columnconfigure(1, weight=1, uniform="col")

        grupo_modelo = ttk.LabelFrame(frame, text="Servidor da base modelo (obrigatório)", padding=10)
        grupo_modelo.grid(row=0, column=0, sticky="new", padx=(0, 8))
        grupo_modelo.columnconfigure(1, weight=1)

        self.var_modelo_servidor = tk.StringVar(value="")
        self.var_modelo_usuario = tk.StringVar(value="")
        self.var_modelo_senha = tk.StringVar(value="")

        ttk.Label(grupo_modelo, text="Servidor:").grid(row=0, column=0, sticky="w", pady=2)
        ttk.Entry(grupo_modelo, textvariable=self.var_modelo_servidor).grid(row=0, column=1, sticky="we", pady=2)
        ttk.Label(grupo_modelo, text="Usuário:").grid(row=1, column=0, sticky="w", pady=2)
        ttk.Entry(grupo_modelo, textvariable=self.var_modelo_usuario).grid(row=1, column=1, sticky="we", pady=2)
        ttk.Label(grupo_modelo, text="Senha:").grid(row=2, column=0, sticky="w", pady=2)
        ttk.Entry(grupo_modelo, textvariable=self.var_modelo_senha, show="*").grid(row=2, column=1, sticky="we", pady=2)

        linha = ttk.Frame(grupo_modelo)
        linha.grid(row=3, column=0, columnspan=2, sticky="we", pady=(6, 0))
        linha.columnconfigure(0, weight=1)
        self.var_base_modelo = tk.StringVar(value="")
        self.combo_base_modelo = ttk.Combobox(linha, textvariable=self.var_base_modelo, state="disabled")
        self.combo_base_modelo.grid(row=0, column=0, sticky="we")
        ttk.Button(linha, text="Buscar bases", command=self.refresh_bases_modelo).grid(row=0, column=1, padx=(6, 0))
        self.lbl_bases_modelo_status = ttk.Label(grupo_modelo, text="", foreground="#555", wraplength=320)
        self.lbl_bases_modelo_status.grid(row=4, column=0, columnspan=2, sticky="w", pady=(6, 0))

        grupo_destino = ttk.LabelFrame(frame, text="Servidor de destino (onde a base nova será criada)", padding=10)
        grupo_destino.grid(row=0, column=1, sticky="new")
        grupo_destino.columnconfigure(1, weight=1)

        self.var_mesmo_servidor = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            grupo_destino, text="É o mesmo servidor da base modelo",
            variable=self.var_mesmo_servidor, command=self._on_mesmo_servidor_changed,
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))

        self.var_destino_servidor = tk.StringVar(value="")
        self.var_destino_usuario = tk.StringVar(value="")
        self.var_destino_senha = tk.StringVar(value="")

        ttk.Label(grupo_destino, text="Servidor:").grid(row=1, column=0, sticky="w", pady=2)
        self.entry_destino_servidor = ttk.Entry(grupo_destino, textvariable=self.var_destino_servidor)
        self.entry_destino_servidor.grid(row=1, column=1, sticky="we", pady=2)
        ttk.Label(grupo_destino, text="Usuário:").grid(row=2, column=0, sticky="w", pady=2)
        self.entry_destino_usuario = ttk.Entry(grupo_destino, textvariable=self.var_destino_usuario)
        self.entry_destino_usuario.grid(row=2, column=1, sticky="we", pady=2)
        ttk.Label(grupo_destino, text="Senha:").grid(row=3, column=0, sticky="w", pady=2)
        self.entry_destino_senha = ttk.Entry(grupo_destino, textvariable=self.var_destino_senha, show="*")
        self.entry_destino_senha.grid(row=3, column=1, sticky="we", pady=2)

        ttk.Label(
            grupo_destino,
            text="Se os dois servidores forem o mesmo, a cópia de dados da base modelo roda direto no servidor "
            "(rápida). Se forem diferentes, a cópia (dados fixos e tabelas adicionais da etapa 3) é feita "
            "linha a linha pela aplicação — funciona, só que mais devagar, já que não depende de linked "
            "server.",
            foreground="#555", wraplength=320,
        ).grid(row=4, column=0, columnspan=2, sticky="w", pady=(8, 0))

        return frame

    def _on_mesmo_servidor_changed(self):
        estado = "disabled" if self.var_mesmo_servidor.get() else "normal"
        for entry in (self.entry_destino_servidor, self.entry_destino_usuario, self.entry_destino_senha):
            entry.configure(state=estado)
        if self.var_mesmo_servidor.get():
            self.var_destino_servidor.set(self.var_modelo_servidor.get())
            self.var_destino_usuario.set(self.var_modelo_usuario.get())
            self.var_destino_senha.set(self.var_modelo_senha.get())

    # ------------------------------------------------------------------
    # Etapa 2: nova base e cartório
    # ------------------------------------------------------------------
    def _build_etapa_nova_base(self, parent):
        frame = ttk.Frame(parent, padding=(0, 8))
        frame.columnconfigure(0, weight=1, uniform="col")
        frame.columnconfigure(1, weight=1, uniform="col")

        self._build_nova_base(frame)
        self._build_dados_cartorio(frame)
        return frame

    def _build_nova_base(self, parent):
        grupo = ttk.LabelFrame(parent, text="Nova base", padding=10)
        grupo.grid(row=0, column=0, sticky="new", padx=(0, 8))
        grupo.columnconfigure(1, weight=1)

        self.var_base_nova = tk.StringVar(value="")
        self.var_base_usuario = tk.StringVar(value="")
        self.var_base_senha = tk.StringVar(value="")
        self.var_odbc_dsn = tk.StringVar(value="")
        self.var_diretorio = tk.StringVar(value="")
        self.var_interino = tk.BooleanVar(value=False)

        campos = [
            ("Nome da base nova:", self.var_base_nova),
            ("Usuário da base:", self.var_base_usuario),
        ]
        for i, (rotulo, var) in enumerate(campos):
            ttk.Label(grupo, text=rotulo).grid(row=i, column=0, sticky="w", pady=2)
            ttk.Entry(grupo, textvariable=var).grid(row=i, column=1, sticky="we", pady=2)

        ttk.Label(grupo, text="Senha da base:").grid(row=2, column=0, sticky="w", pady=2)
        senha_frame = ttk.Frame(grupo)
        senha_frame.grid(row=2, column=1, sticky="we", pady=2)
        senha_frame.columnconfigure(0, weight=1)
        ttk.Entry(senha_frame, textvariable=self.var_base_senha, show="*").grid(row=0, column=0, sticky="we")
        ttk.Button(senha_frame, text="Gerar", command=self._gerar_senha).grid(row=0, column=1, padx=(4, 0))

        ttk.Label(grupo, text="DSN ODBC:").grid(row=3, column=0, sticky="w", pady=2)
        ttk.Entry(grupo, textvariable=self.var_odbc_dsn).grid(row=3, column=1, sticky="we", pady=2)

        ttk.Label(grupo, text="Diretório de arquivos:").grid(row=4, column=0, sticky="w", pady=2)
        ttk.Entry(grupo, textvariable=self.var_diretorio).grid(row=4, column=1, sticky="we", pady=2)

        ttk.Label(
            grupo, text="DSN ODBC e diretório são sugeridos a partir do nome da base nova (edite à vontade).",
            foreground="#555", wraplength=280,
        ).grid(row=5, column=0, columnspan=2, sticky="w", pady=(0, 2))

        ttk.Checkbutton(grupo, text="Responsável interino", variable=self.var_interino).grid(
            row=6, column=0, columnspan=2, sticky="w", pady=(8, 0)
        )

    def _build_dados_cartorio(self, parent):
        grupo = ttk.LabelFrame(parent, text="Dados do cartório", padding=10)
        grupo.grid(row=0, column=1, sticky="new")
        grupo.columnconfigure(1, weight=1)

        self.var_cart_id = tk.StringVar(value="")
        self.var_cart_nome = tk.StringVar(value="")
        self.var_cart_cns = tk.StringVar(value="")
        self.var_cart_endereco = tk.StringVar(value="")
        self.var_cart_bairro = tk.StringVar(value="")
        self.var_cart_cep = tk.StringVar(value="")
        self.var_cidade = tk.StringVar(value="")
        self.var_uf = tk.StringVar(value="")
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
            ("Cidade:", self.var_cidade),
            ("UF:", self.var_uf),
            ("Responsável (nome):", self.var_cart_resp_nome),
            ("Responsável (CPF):", self.var_cart_resp_cpf),
            ("Início do responsável (aaaa-mm-dd):", self.var_cart_inicio),
            ("CNPJ:", self.var_cart_cnpj),
        ]
        for i, (rotulo, var) in enumerate(campos):
            ttk.Label(grupo, text=rotulo).grid(row=i, column=0, sticky="w", pady=2)
            ttk.Entry(grupo, textvariable=var).grid(row=i, column=1, sticky="we", pady=2)

    # ------------------------------------------------------------------
    # Etapa 3: tabelas adicionais
    # ------------------------------------------------------------------
    def _build_etapa_tabelas_extras(self, parent):
        frame = ttk.Frame(parent, padding=(0, 8))
        frame.columnconfigure(0, weight=1)

        ttk.Label(
            frame,
            text="Além das ~15 tabelas que a cópia padrão já cobre (Contas, GrupoContábil, InterfaceArq "
            "etc.), escolha aqui tabelas e colunas extras do banco modelo pra copiar pra base nova. Ao "
            "buscar, todas as tabelas já vêm pré-selecionadas com todas as colunas — exceto "
            f"{', '.join(TABELAS_SEM_COPIA_PADRAO)}, que ficam selecionadas mas sem coluna nenhuma marcada "
            "(ou seja, sem dado copiado: Resumo já é coberto pela cópia padrão, e as outras três são "
            "tabelas transacionais que devem começar vazias). Desmarque/marque à vontade. Funciona mesmo "
            "quando o servidor da base modelo e o de destino são diferentes (etapa 1) — nesse caso a cópia "
            "é feita linha a linha pela aplicação, mais devagar.",
            foreground="#555", wraplength=900,
        ).grid(row=0, column=0, sticky="w", pady=(0, 8))

        barra = ttk.Frame(frame)
        barra.grid(row=1, column=0, sticky="w", pady=(0, 8))
        ttk.Button(barra, text="Buscar tabelas da base modelo", command=self._buscar_tabelas).pack(side="left")
        self.lbl_tabelas_status = ttk.Label(barra, text="", foreground="#555")
        self.lbl_tabelas_status.pack(side="left", padx=(10, 0))

        self.frame_tabelas = ttk.Frame(frame)
        self.frame_tabelas.grid(row=2, column=0, sticky="nsew")
        frame.rowconfigure(2, weight=1)

        return frame

    def _buscar_tabelas(self):
        servidor = self.var_modelo_servidor.get().strip()
        usuario = self.var_modelo_usuario.get().strip()
        base = self.var_base_modelo.get().strip()
        if not servidor or not usuario or not base:
            messagebox.showwarning(
                "Tabelas adicionais", "Escolha a base modelo (etapa 1) antes de buscar as tabelas.",
            )
            return

        cs = dbc.ConnectionSettings(servidor=servidor, usuario=usuario, senha=self.var_modelo_senha.get())
        try:
            conn = dbc.connect(cs)
            tabelas = schema_service.listar_tabelas(conn, base)
            # Busca as colunas de TODAS as tabelas de uma vez (uma única
            # consulta) já aqui, porque todas vêm pré-selecionadas e
            # pré-expandidas (ver _popular_tabelas) — evitar isso seria uma
            # consulta por tabela na hora de montar a tela.
            self._colunas_cache = schema_service.listar_colunas_de_varias_tabelas(conn, base, tabelas)
            dbc.close(conn)
        except Exception as exc:
            messagebox.showerror("Tabelas adicionais", f"Falha ao listar tabelas: {exc}")
            return

        self._popular_tabelas(tabelas)
        self.lbl_tabelas_status.configure(
            text=(
                f"{len(tabelas)} tabela(s) encontrada(s), todas pré-selecionadas com todas as colunas — "
                f"exceto {', '.join(sorted(TABELAS_SEM_COPIA_PADRAO))}, que ficam selecionadas mas sem dados "
                "(desmarque/marque colunas à vontade)."
            ),
            foreground="#1b7a1b",
        )

    def _popular_tabelas(self, tabelas: list):
        for widget in self.frame_tabelas.winfo_children():
            widget.destroy()
        self._tabelas_estado = {}
        self.frame_tabelas.columnconfigure(0, weight=1)

        for i, tabela in enumerate(tabelas):
            secao = ttk.Frame(self.frame_tabelas)
            secao.grid(row=i, column=0, sticky="ew", pady=1)
            secao.columnconfigure(1, weight=1)

            var_tabela = tk.BooleanVar(value=True)
            estado = {"var": var_tabela, "frame_colunas": None, "colunas": {}}
            self._tabelas_estado[tabela] = estado

            ttk.Checkbutton(
                secao, text=tabela, variable=var_tabela,
                command=lambda t=tabela: self._on_tabela_toggle(t),
            ).grid(row=0, column=0, sticky="w")

            self._renderizar_colunas(tabela, secao, estado)

    def _on_tabela_toggle(self, tabela: str):
        estado = self._tabelas_estado[tabela]
        indice = list(self._tabelas_estado.keys()).index(tabela)
        secao = self.frame_tabelas.grid_slaves(row=indice, column=0)[0]

        if not estado["var"].get():
            if estado["frame_colunas"] is not None:
                estado["frame_colunas"].destroy()
                estado["frame_colunas"] = None
            return

        self._renderizar_colunas(tabela, secao, estado)

    def _renderizar_colunas(self, tabela: str, secao, estado: dict):
        """Busca (com cache) e desenha os checkboxes de coluna de `tabela`
        dentro de `secao`. Colunas de tabelas em TABELAS_SEM_COPIA_PADRAO
        começam desmarcadas (nenhum dado copiado); as demais, todas
        marcadas — ver _tabelas_extras_selecionadas."""
        if tabela not in self._colunas_cache:
            cs = dbc.ConnectionSettings(
                servidor=self.var_modelo_servidor.get().strip(),
                usuario=self.var_modelo_usuario.get().strip(),
                senha=self.var_modelo_senha.get(),
            )
            try:
                conn = dbc.connect(cs)
                self._colunas_cache[tabela] = schema_service.listar_colunas(conn, self.var_base_modelo.get(), tabela)
                dbc.close(conn)
            except Exception as exc:
                messagebox.showerror("Tabelas adicionais", f"Falha ao listar colunas de '{tabela}': {exc}")
                estado["var"].set(False)
                return

        colunas = self._colunas_cache[tabela]
        marcar_por_padrao = tabela.strip().lower() not in TABELAS_SEM_COPIA_PADRAO_LOWER

        frame_colunas = ttk.Frame(secao)
        frame_colunas.grid(row=1, column=0, columnspan=2, sticky="w", padx=(20, 0))
        estado["frame_colunas"] = frame_colunas
        estado["colunas"] = {}
        for j, coluna in enumerate(colunas):
            var_col = tk.BooleanVar(value=marcar_por_padrao)
            estado["colunas"][coluna] = var_col
            ttk.Checkbutton(frame_colunas, text=coluna, variable=var_col).grid(
                row=j // 4, column=j % 4, sticky="w", padx=(0, 12)
            )

    def _tabelas_extras_selecionadas(self) -> list:
        resultado = []
        for tabela, estado in self._tabelas_estado.items():
            if not estado["var"].get():
                continue
            colunas = [col for col, var in estado["colunas"].items() if var.get()]
            if colunas:
                resultado.append(TabelaExtra(tabela=tabela, colunas=colunas))
        return resultado

    # ------------------------------------------------------------------
    # Etapa 4: registro em Parametros_Clientes
    # ------------------------------------------------------------------
    def _build_etapa_parametros(self, parent):
        frame = ttk.Frame(parent, padding=(0, 8))
        frame.columnconfigure(0, weight=1, uniform="col")
        frame.columnconfigure(1, weight=1, uniform="col")

        grupo_hosting = ttk.LabelFrame(frame, text="Onde a base nova está hospedada", padding=10)
        grupo_hosting.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))

        self.var_pp_hosting = tk.StringVar(value="servidorpp")
        ttk.Radiobutton(
            grupo_hosting, text=f"ServidorPP (nosso) — {SERVIDOR_PP}", value="servidorpp",
            variable=self.var_pp_hosting, command=self._on_hosting_changed,
        ).pack(anchor="w")
        ttk.Radiobutton(
            grupo_hosting, text="Servidor do cliente", value="cliente",
            variable=self.var_pp_hosting, command=self._on_hosting_changed,
        ).pack(anchor="w")

        grupo_campos = ttk.LabelFrame(frame, text="Dados do registro (Parametros_Clientes)", padding=10)
        grupo_campos.grid(row=1, column=0, sticky="new", padx=(0, 8))
        grupo_campos.columnconfigure(1, weight=1)

        self.var_param_nome = tk.StringVar(value="")
        self.var_param_servidor = tk.StringVar(value=SERVIDOR_PP)
        self.var_param_banco = tk.StringVar(value="")
        self.var_param_usuario = tk.StringVar(value="")
        self.var_param_senha = tk.StringVar(value="")
        self.var_param_diretorio = tk.StringVar(value="")
        self.var_param_odbc = tk.StringVar(value="")

        campos = [
            ("Nome:", self.var_param_nome, {}),
            ("Servidor:", self.var_param_servidor, {}),
            ("Banco:", self.var_param_banco, {}),
            ("Usuario:", self.var_param_usuario, {}),
            ("Senha:", self.var_param_senha, {"show": "*"}),
            ("DiretorioArquivo:", self.var_param_diretorio, {}),
            ("Odbc:", self.var_param_odbc, {}),
        ]
        for i, (rotulo, var, opcoes) in enumerate(campos):
            ttk.Label(grupo_campos, text=rotulo).grid(row=i, column=0, sticky="w", pady=2)
            ttk.Entry(grupo_campos, textvariable=var, **opcoes).grid(row=i, column=1, sticky="we", pady=2)
        self.entry_param_servidor = grupo_campos.grid_slaves(row=1, column=1)[0]

        grupo_extras = ttk.LabelFrame(frame, text="Dashboard / mensalistas / validação", padding=10)
        grupo_extras.grid(row=1, column=1, sticky="new")
        grupo_extras.columnconfigure(1, weight=1)

        self.var_param_browser_dashboard = tk.StringVar(value=PARAM_DEFAULT_BROWSER_DASHBOARD)
        self.var_param_url_dashboard = tk.StringVar(value=PARAM_DEFAULT_URL_DASHBOARD)
        self.var_param_url_dashboard_token = tk.StringVar(value=PARAM_DEFAULT_URL_DASHBOARD_TOKEN)
        self.var_param_diretorio_mensalistas = tk.StringVar(value=PARAM_DEFAULT_DIRETORIO_MENSALISTAS)
        self.var_param_url_validacao = tk.StringVar(value=PARAM_DEFAULT_URL_VALIDACAO)
        self.var_param_url_gestor_clientes = tk.StringVar(value=PARAM_DEFAULT_URL_GESTOR_CLIENTES)

        campos_extras = [
            ("BrowserDashboard:", self.var_param_browser_dashboard),
            ("UrlDashboard:", self.var_param_url_dashboard),
            ("UrlDashboardToken:", self.var_param_url_dashboard_token),
            ("DiretorioMensalistas:", self.var_param_diretorio_mensalistas),
            ("UrlValidacao:", self.var_param_url_validacao),
            ("UrlGestorClientes:", self.var_param_url_gestor_clientes),
        ]
        for i, (rotulo, var) in enumerate(campos_extras):
            ttk.Label(grupo_extras, text=rotulo).grid(row=i, column=0, sticky="w", pady=2)
            ttk.Entry(grupo_extras, textvariable=var).grid(row=i, column=1, sticky="we", pady=2)

        grupo_alvos = ttk.LabelFrame(frame, text="Onde registrar (além do ServidorPP, que é sempre incluído)", padding=10)
        grupo_alvos.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(8, 0))

        self.var_alvo_parametros = tk.StringVar(value="ambos")
        ttk.Radiobutton(
            grupo_alvos, text="Somente no servidor da base modelo", value="modelo", variable=self.var_alvo_parametros,
        ).pack(anchor="w")
        ttk.Radiobutton(
            grupo_alvos, text="Somente no servidor de destino", value="destino", variable=self.var_alvo_parametros,
        ).pack(anchor="w")
        ttk.Radiobutton(
            grupo_alvos, text="Nos dois (base modelo e destino)", value="ambos", variable=self.var_alvo_parametros,
        ).pack(anchor="w")

        grupo_pp_cred = ttk.LabelFrame(frame, text="Credenciais do ServidorPP (nosso)", padding=10)
        grupo_pp_cred.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        grupo_pp_cred.columnconfigure(1, weight=1)

        self.var_pp_usuario = tk.StringVar(value="")
        self.var_pp_senha = tk.StringVar(value="")
        ttk.Label(grupo_pp_cred, text=f"Servidor: {SERVIDOR_PP} (fixo)", foreground="#555").grid(
            row=0, column=0, columnspan=2, sticky="w"
        )
        ttk.Label(grupo_pp_cred, text="Usuário:").grid(row=1, column=0, sticky="w", pady=2)
        ttk.Entry(grupo_pp_cred, textvariable=self.var_pp_usuario).grid(row=1, column=1, sticky="we", pady=2)
        ttk.Label(grupo_pp_cred, text="Senha:").grid(row=2, column=0, sticky="w", pady=2)
        ttk.Entry(grupo_pp_cred, textvariable=self.var_pp_senha, show="*").grid(row=2, column=1, sticky="we", pady=2)
        ttk.Label(
            grupo_pp_cred,
            text="Usadas só se o ServidorPP não for um dos servidores já informados na etapa 1 (nesse caso as "
            "credenciais de lá são reaproveitadas).",
            foreground="#555", wraplength=700,
        ).grid(row=3, column=0, columnspan=2, sticky="w", pady=(4, 0))

        return frame

    def _on_hosting_changed(self):
        if self.var_pp_hosting.get() == "servidorpp":
            self.entry_param_servidor.configure(state="disabled")
            self.var_param_servidor.set(SERVIDOR_PP)
        else:
            self.entry_param_servidor.configure(state="normal")
            self.var_param_servidor.set(self.var_destino_servidor.get())

    # ------------------------------------------------------------------
    # Etapa 5: confirmação e execução
    # ------------------------------------------------------------------
    def _build_etapa_execucao(self, parent):
        grupo = ttk.Frame(parent, padding=(0, 8))
        grupo.columnconfigure(0, weight=1)

        grupo_resumo = ttk.LabelFrame(grupo, text="Resumo do provisionamento", padding=10)
        grupo_resumo.grid(row=0, column=0, sticky="nsew", pady=(0, 8))
        grupo_resumo.columnconfigure(0, weight=1)
        grupo.rowconfigure(0, weight=1)

        self.txt_resumo = tk.Text(
            grupo_resumo, height=16, state="disabled", background="#ffffff", wrap="word", relief="flat",
        )
        self.txt_resumo.grid(row=0, column=0, sticky="nsew")
        grupo_resumo.rowconfigure(0, weight=1)

        barra_progresso = ttk.Frame(grupo)
        barra_progresso.grid(row=1, column=0, sticky="ew", pady=(0, 2))
        barra_progresso.columnconfigure(0, weight=1)
        self.progress = ttk.Progressbar(barra_progresso, mode="determinate", maximum=1)
        self.progress.grid(row=0, column=0, sticky="we")
        self.lbl_progresso = ttk.Label(barra_progresso, text="", width=12, anchor="e")
        self.lbl_progresso.grid(row=0, column=1, padx=(8, 0))

        self.txt_log = tk.Text(grupo, height=10, state="disabled", background="#f7f7f7")
        self.txt_log.grid(row=2, column=0, sticky="nsew", pady=(6, 0))

        self.btn_provisionar = ttk.Button(grupo, text="Confirmar e provisionar", command=self._confirmar_e_provisionar)
        self.btn_provisionar.grid(row=3, column=0, sticky="e", pady=(8, 0))

        return grupo

    def _atualizar_resumo_execucao(self):
        mesmo_servidor = (
            self.var_modelo_servidor.get().strip().lower() == self.var_destino_servidor.get().strip().lower()
        )
        tabelas_extras = self._tabelas_extras_selecionadas()
        alvos = self._montar_alvos_parametros()
        param_cfg = self._montar_parametros_cfg()

        def _ou_vazio(valor: str) -> str:
            return valor if valor.strip() else "(não preenchido)"

        linhas = [
            f"Base nova: {_ou_vazio(self.var_base_nova.get())}",
            f"   → será criada no servidor de destino: {_ou_vazio(self.var_destino_servidor.get())}",
            "",
            f"Base modelo: {_ou_vazio(self.var_base_modelo.get())}",
            f"   → servidor da base modelo: {_ou_vazio(self.var_modelo_servidor.get())}",
            "",
        ]
        if mesmo_servidor:
            texto_dados = "Cópia de dados: SIM (mesmo servidor, direto no SQL) — inclui a cópia padrão (~15 tabelas fixas)"
        else:
            texto_dados = "Cópia de dados: SIM (servidores diferentes, linha a linha pela aplicação) — inclui a cópia padrão (~15 tabelas fixas)"
        if tabelas_extras:
            texto_dados += f" + {len(tabelas_extras)} tabela(s) adicional(is) selecionada(s)"
        linhas.append(texto_dados)
        linhas.append("")
        linhas.append(f"Cartório: {_ou_vazio(self.var_cart_nome.get())} ({self.var_cidade.get()}/{self.var_uf.get()})")
        linhas.append(f"Responsável interino: {'Sim' if self.var_interino.get() else 'Não'}")
        linhas.append("")
        linhas.append(f"Registro em Gestor_Parametros.Parametros_Clientes em {len(alvos)} servidor(es):")
        for alvo in alvos:
            linhas.append(f"   • {alvo.titulo} — {alvo.connection_settings.servidor}")
        linhas.append("")
        linhas.append("Exemplo dos dados que serão gravados (a mesma linha, em todos os servidores acima):")
        senha_mascarada = "•" * len(param_cfg.senha) if param_cfg.senha else "(não preenchido)"
        linhas.append(f"   Nome: {_ou_vazio(param_cfg.nome)}")
        linhas.append(f"   Servidor: {_ou_vazio(param_cfg.servidor)}")
        linhas.append(f"   Banco: {_ou_vazio(param_cfg.banco)}")
        linhas.append(f"   Usuario: {_ou_vazio(param_cfg.usuario)}")
        linhas.append(f"   Senha: {senha_mascarada}")
        linhas.append(f"   DiretorioArquivo: {_ou_vazio(param_cfg.diretorio_arquivo)}")
        linhas.append(f"   Odbc: {_ou_vazio(param_cfg.odbc)}")

        self.txt_resumo.configure(state="normal")
        self.txt_resumo.delete("1.0", "end")
        self.txt_resumo.insert("1.0", "\n".join(linhas))
        self.txt_resumo.configure(state="disabled")

    def _contar_passos_estimados(self) -> int:
        """Quantidade de passos esperados nesta execução, pra calibrar a
        barra de progresso (0 a 100%) antes de começar — varia conforme o
        que foi escolhido nas etapas anteriores."""
        total = 3  # schema, usuario, dados (sempre roda, mesmo com servidores diferentes)
        if self._tabelas_extras_selecionadas():
            total += 1
        total += 2  # cartorio, cartorio_id
        if self.var_interino.get():
            total += 1
        total += len(self._montar_alvos_parametros())
        return max(total, 1)

    # ------------------------------------------------------------------
    # Auto-sugestão
    # ------------------------------------------------------------------
    def _wire_autosuggest(self):
        self.var_odbc_dsn.trace_add("write", lambda *_: self._marcar_editado_manualmente("odbc_dsn"))
        self.var_diretorio.trace_add("write", lambda *_: self._marcar_editado_manualmente("diretorio"))
        self.var_base_nova.trace_add("write", lambda *_: self._atualizar_sugestoes())

        # Espelha modelo -> destino enquanto "mesmo servidor" estiver marcado.
        for var in (self.var_modelo_servidor, self.var_modelo_usuario, self.var_modelo_senha):
            var.trace_add("write", lambda *_: self._espelhar_destino_se_mesmo_servidor())

        # Etapa 4: Banco/Usuario/Senha/DiretorioArquivo sugeridos a partir da
        # etapa 2, e Odbc calculado a partir de Nome/Usuario/Senha da própria
        # etapa 4 — todos só enquanto o usuário não editar manualmente.
        self.var_param_banco.trace_add("write", lambda *_: self._marcar_editado_manualmente("param_banco"))
        self.var_param_usuario.trace_add("write", lambda *_: self._marcar_editado_manualmente("param_usuario"))
        self.var_param_senha.trace_add("write", lambda *_: self._marcar_editado_manualmente("param_senha"))
        self.var_param_diretorio.trace_add("write", lambda *_: self._marcar_editado_manualmente("param_diretorio"))
        self.var_param_odbc.trace_add("write", lambda *_: self._marcar_editado_manualmente("param_odbc"))

        self.var_base_nova.trace_add("write", lambda *_: self._atualizar_sugestoes_parametros())
        self.var_base_usuario.trace_add("write", lambda *_: self._atualizar_sugestoes_parametros())
        self.var_base_senha.trace_add("write", lambda *_: self._atualizar_sugestoes_parametros())
        self.var_diretorio.trace_add("write", lambda *_: self._atualizar_sugestoes_parametros())
        for var in (self.var_param_nome, self.var_param_usuario, self.var_param_senha):
            var.trace_add("write", lambda *_: self._atualizar_odbc_parametros())

    def _marcar_editado_manualmente(self, campo):
        if getattr(self, "_nivel_auto_atualizacao", 0) > 0:
            return
        self._auto_editado_manualmente[campo] = True

    def _iniciar_auto_atualizacao(self):
        # Contador (não booleano) porque estas três funções de auto-sugestão
        # se chamam em cascata (ex.: _atualizar_sugestoes dispara, via trace
        # de var_base_nova, _atualizar_sugestoes_parametros) — um booleano
        # simples faria o `finally` da chamada aninhada desarmar a guarda
        # cedo demais, deixando a chamada externa ainda em andamento marcar
        # campos como "editados manualmente" por engano.
        self._nivel_auto_atualizacao = getattr(self, "_nivel_auto_atualizacao", 0) + 1

    def _finalizar_auto_atualizacao(self):
        self._nivel_auto_atualizacao -= 1

    def _atualizar_sugestoes(self):
        base_nova = self.var_base_nova.get().strip()
        if not base_nova:
            return
        self._iniciar_auto_atualizacao()
        try:
            if not self._auto_editado_manualmente["odbc_dsn"]:
                self.var_odbc_dsn.set(f"ODBC_GF_{_slug(base_nova)[:24]}")
            if not self._auto_editado_manualmente["diretorio"]:
                self.var_diretorio.set(f"C:\\ProPackages\\Arquivos\\{base_nova}\\")
        finally:
            self._finalizar_auto_atualizacao()

    def _atualizar_sugestoes_parametros(self):
        self._iniciar_auto_atualizacao()
        try:
            if not self._auto_editado_manualmente["param_banco"]:
                self.var_param_banco.set(self.var_base_nova.get())
            if not self._auto_editado_manualmente["param_usuario"]:
                self.var_param_usuario.set(self.var_base_usuario.get())
            if not self._auto_editado_manualmente["param_senha"]:
                self.var_param_senha.set(self.var_base_senha.get())
            if not self._auto_editado_manualmente["param_diretorio"]:
                self.var_param_diretorio.set(self.var_diretorio.get())
        finally:
            self._finalizar_auto_atualizacao()

    def _atualizar_odbc_parametros(self):
        if self._auto_editado_manualmente["param_odbc"]:
            return
        self._iniciar_auto_atualizacao()
        try:
            nome = self.var_param_nome.get()
            usuario = self.var_param_usuario.get()
            senha = self.var_param_senha.get()
            self.var_param_odbc.set(f"DSN=ODBC_GF_{nome};UID={usuario};PWD={senha};")
        finally:
            self._finalizar_auto_atualizacao()

    def _espelhar_destino_se_mesmo_servidor(self):
        if not self.var_mesmo_servidor.get():
            return
        self.var_destino_servidor.set(self.var_modelo_servidor.get())
        self.var_destino_usuario.set(self.var_modelo_usuario.get())
        self.var_destino_senha.set(self.var_modelo_senha.get())

    def _gerar_senha(self):
        alfabeto = string.ascii_letters + string.digits
        self.var_base_senha.set("".join(random.choices(alfabeto, k=16)))

    # ------------------------------------------------------------------
    # Dados auxiliares
    # ------------------------------------------------------------------
    def refresh_bases_modelo(self):
        servidor = self.var_modelo_servidor.get().strip()
        usuario = self.var_modelo_usuario.get().strip()
        if not servidor or not usuario:
            messagebox.showwarning(
                "Base modelo", "Informe servidor e usuário da base modelo antes de buscar as bases."
            )
            return

        cs = dbc.ConnectionSettings(servidor=servidor, usuario=usuario, senha=self.var_modelo_senha.get())
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
        self.var_modelo_servidor.set(dados.get("modelo_servidor", "") or self.session.connection_settings.servidor)
        self.var_modelo_usuario.set(dados.get("modelo_usuario", "") or self.session.connection_settings.usuario)
        self.var_modelo_senha.set(self.session.connection_settings.senha)

        self.var_mesmo_servidor.set(dados.get("mesmo_servidor", True))
        if self.var_mesmo_servidor.get():
            self._on_mesmo_servidor_changed()
        else:
            self.var_destino_servidor.set(dados.get("destino_servidor", ""))
            self.var_destino_usuario.set(dados.get("destino_usuario", ""))
            self._on_mesmo_servidor_changed()  # só ajusta o estado (disabled/normal) dos campos

        self.var_pp_usuario.set(dados.get("pp_usuario", ""))

    # ------------------------------------------------------------------
    # Validação / execução
    # ------------------------------------------------------------------
    def _campos_obrigatorios_faltando(self) -> list:
        obrigatorios = [
            ("Servidor da base modelo", self.var_modelo_servidor.get()),
            ("Usuário da base modelo", self.var_modelo_usuario.get()),
            ("Senha da base modelo", self.var_modelo_senha.get()),
            ("Base modelo", self.var_base_modelo.get()),
            ("Servidor de destino", self.var_destino_servidor.get()),
            ("Usuário de destino", self.var_destino_usuario.get()),
            ("Senha de destino", self.var_destino_senha.get()),
            ("Nome da base nova", self.var_base_nova.get()),
            ("Usuário da base", self.var_base_usuario.get()),
            ("Senha da base", self.var_base_senha.get()),
            ("Nome do cartório", self.var_cart_nome.get()),
            ("Cidade", self.var_cidade.get()),
            ("UF", self.var_uf.get()),
            ("Cart ID", self.var_cart_id.get()),
            ("Nome (Parametros_Clientes)", self.var_param_nome.get()),
            ("Servidor (Parametros_Clientes)", self.var_param_servidor.get()),
        ]
        if not self._pp_ja_coberto():
            obrigatorios.append(("Usuário do ServidorPP", self.var_pp_usuario.get()))
            obrigatorios.append(("Senha do ServidorPP", self.var_pp_senha.get()))
        return [nome for nome, valor in obrigatorios if not valor.strip()]

    def _pp_ja_coberto(self) -> bool:
        """True quando o ServidorPP já é o servidor de destino ou o da base
        modelo — nesse caso reaproveita as credenciais já informadas, sem
        precisar de um usuário/senha extra do ServidorPP."""
        return (
            self.var_destino_servidor.get().strip() == SERVIDOR_PP
            or self.var_modelo_servidor.get().strip() == SERVIDOR_PP
        )

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
        )

    def _montar_parametros_cfg(self) -> ParametrosClienteConfig:
        return ParametrosClienteConfig(
            nome=self.var_param_nome.get(),
            servidor=self.var_param_servidor.get(),
            banco=self.var_param_banco.get(),
            usuario=self.var_param_usuario.get(),
            senha=self.var_param_senha.get(),
            diretorio_arquivo=self.var_param_diretorio.get(),
            odbc=self.var_param_odbc.get(),
            browser_dashboard=self.var_param_browser_dashboard.get(),
            url_dashboard=self.var_param_url_dashboard.get(),
            url_dashboard_token=self.var_param_url_dashboard_token.get(),
            diretorio_mensalistas=self.var_param_diretorio_mensalistas.get(),
            url_validacao=self.var_param_url_validacao.get(),
            url_gestor_clientes=self.var_param_url_gestor_clientes.get(),
        )

    def _montar_modelo_cs(self) -> dbc.ConnectionSettings:
        return dbc.ConnectionSettings(
            servidor=self.var_modelo_servidor.get(), usuario=self.var_modelo_usuario.get(),
            senha=self.var_modelo_senha.get(),
        )

    def _montar_destino_cs(self) -> dbc.ConnectionSettings:
        return dbc.ConnectionSettings(
            servidor=self.var_destino_servidor.get(), usuario=self.var_destino_usuario.get(),
            senha=self.var_destino_senha.get(),
        )

    def _montar_pp_cs(self) -> dbc.ConnectionSettings:
        if self.var_destino_servidor.get().strip() == SERVIDOR_PP:
            return self._montar_destino_cs()
        if self.var_modelo_servidor.get().strip() == SERVIDOR_PP:
            return self._montar_modelo_cs()
        return dbc.ConnectionSettings(
            servidor=SERVIDOR_PP, usuario=self.var_pp_usuario.get(), senha=self.var_pp_senha.get(),
        )

    def _montar_alvos_parametros(self) -> list:
        modelo_cs = self._montar_modelo_cs()
        destino_cs = self._montar_destino_cs()
        pp_cs = self._montar_pp_cs()

        candidatos = []
        escolha = self.var_alvo_parametros.get()
        if escolha in ("modelo", "ambos"):
            candidatos.append(AlvoParametros("modelo", "servidor da base modelo", modelo_cs))
        if escolha in ("destino", "ambos"):
            candidatos.append(AlvoParametros("destino", "servidor de destino", destino_cs))
        candidatos.append(AlvoParametros("servidorpp", "ServidorPP (nosso)", pp_cs))

        # Dedup por servidor: se dois alvos apontam pro mesmo servidor físico,
        # só um INSERT é necessário (senão o segundo falharia por duplicidade
        # ou, na melhor das hipóteses, seria redundante).
        vistos = set()
        alvos = []
        for alvo in candidatos:
            chave_servidor = alvo.connection_settings.servidor.strip().lower()
            if chave_servidor in vistos:
                continue
            vistos.add(chave_servidor)
            alvos.append(alvo)
        return alvos

    def _confirmar_e_provisionar(self):
        faltando = self._campos_obrigatorios_faltando()
        if faltando:
            messagebox.showwarning("Criação de base", "Preencha os campos obrigatórios:\n\n" + "\n".join(faltando))
            return

        cfg = self._montar_config()
        tabelas_extras = self._tabelas_extras_selecionadas()
        parametros_cfg = self._montar_parametros_cfg()
        parametros_alvos = self._montar_alvos_parametros()

        resumo_alvos = "\n".join(f"- {a.titulo} ({a.connection_settings.servidor})" for a in parametros_alvos)
        resumo_tabelas = f"\n{len(tabelas_extras)} tabela(s) adicional(is) selecionada(s)." if tabelas_extras else ""
        resumo = (
            f"Isto vai CRIAR o banco '{cfg.base_nova}' no servidor de destino, copiar dados de "
            f"'{cfg.base_modelo}'{resumo_tabelas} e registrar o cliente '{cfg.cart_nome}' em "
            f"Parametros_Clientes:\n\n{resumo_alvos}\n\nEsta ação não é reversível automaticamente.\n\n"
            f"Deseja continuar?"
        )
        if not messagebox.askyesno("Confirmar provisionamento", resumo, icon="warning"):
            return

        settings_service.save_last_criar_base_settings({
            "modelo_servidor": self.var_modelo_servidor.get(),
            "modelo_usuario": self.var_modelo_usuario.get(),
            "destino_servidor": self.var_destino_servidor.get(),
            "destino_usuario": self.var_destino_usuario.get(),
            "mesmo_servidor": self.var_mesmo_servidor.get(),
            "pp_usuario": self.var_pp_usuario.get(),
        })

        plano = PlanoProvisionamento(
            modelo_cs=self._montar_modelo_cs(),
            destino_cs=self._montar_destino_cs(),
            cfg=cfg,
            tabelas_extras=tabelas_extras,
            parametros_cfg=parametros_cfg,
            parametros_alvos=parametros_alvos,
        )
        self.on_provisionar(plano)

    # ------------------------------------------------------------------
    # Progresso (chamado pela MainWindow via fila thread-safe)
    # ------------------------------------------------------------------
    def set_busy(self, ocupado: bool):
        self.btn_provisionar.configure(state="disabled" if ocupado else "normal")
        if not ocupado:
            return
        self.progress.configure(maximum=self._contar_passos_estimados())
        self.progress["value"] = 0
        self._atualizar_label_progresso()
        self.txt_log.configure(state="normal")
        self.txt_log.delete("1.0", "end")
        self.txt_log.configure(state="disabled")

    def _atualizar_label_progresso(self):
        maximo = self.progress["maximum"] or 1
        atual = self.progress["value"]
        percentual = int(round(100 * atual / maximo))
        self.lbl_progresso.configure(text=f"{percentual}% ({int(atual)}/{int(maximo)})")

    def append_log(self, evento: ProgressEvent):
        linha = None
        if evento.kind == "step_start":
            linha = f"» {evento.message}..."
        elif evento.kind == "step_done":
            linha = f"✓ {evento.message}"
            self.progress["value"] += 1
            self._atualizar_label_progresso()
        elif evento.kind == "step_skipped":
            linha = f"⚠ {evento.step_name}: {evento.message}"
        elif evento.kind == "step_error":
            linha = f"✗ ERRO em '{evento.step_name}': {evento.message}"
        elif evento.kind == "all_done":
            linha = f"✓ {evento.message}"
            self.progress["value"] = self.progress["maximum"]
            self._atualizar_label_progresso()

        if linha is None:
            return
        self.txt_log.configure(state="normal")
        self.txt_log.insert("end", linha + "\n")
        self.txt_log.see("end")
        self.txt_log.configure(state="disabled")
