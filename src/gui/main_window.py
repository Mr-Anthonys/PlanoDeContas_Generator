"""Janela principal do Gerador de Plano de Contas."""

import os
import queue
import threading
import tkinter as tk
import traceback
from tkinter import filedialog, messagebox, ttk

from src.gui.configuration_panel import ConfigurationPanel
from src.gui.criar_base_panel import CriarBasePanel
from src.gui.excluir_contas_panel import ExcluirContasPanel
from src.gui.import_panel import ImportPanel
from src.models.session import SessionContext
from src.services import (
    criar_base_service, delete_service, excel_reader, settings_service, sql_generator, validation_service,
)
from src.services.excel_reader import ExcelReadError
from src.services.reference_loader import load_reference_data
from src.utils.sql_escape import quote_identifier

APP_TITLE = "Gerador de Plano de Contas e Scripts SQL"

# Ordem dos 8 processos, igual à da lista retornada por sql_generator.generate_all().
PROCESS_KEYS = [
    "contas", "grupo_portal", "grupo_contabil", "interface_contas",
    "interface_historico", "interface_arq", "interface_comum", "interface_forma_pgto",
]

PROCESS_LABELS = {
    "contas": "Contas",
    "grupo_portal": "GrupoPortal",
    "grupo_contabil": "GrupoContábil",
    "interface_contas": "InterfaceContas",
    "interface_historico": "InterfaceHistorico",
    "interface_arq": "InterfaceArq",
    "interface_comum": "InterfaceComum",
    "interface_forma_pgto": "InterfaceFormaPgto",
}

NOMES_ARQUIVO = {
    "contas": "01_Contas.sql",
    "grupo_portal": "02_GrupoPortal.sql",
    "grupo_contabil": "03_GrupoContabil.sql",
    "interface_contas": "04_InterfaceContas.sql",
    "interface_historico": "05_InterfaceHistorico.sql",
    "interface_arq": "06_InterfaceArq.sql",
    "interface_comum": "07_InterfaceComum.sql",
    "interface_forma_pgto": "08_InterfaceFormaPgto.sql",
}

# Agrupamento visual dos checkboxes de geração, igual ao protótipo Figma
# (4 colunas de 2 processos cada, com "TODOS" ao lado da primeira linha).
CHECKBOX_COLUNAS = [
    ("contas", "grupo_portal"),
    ("grupo_contabil", "interface_contas"),
    ("interface_historico", "interface_arq"),
    ("interface_comum", "interface_forma_pgto"),
]


class MainWindow(tk.Tk):
    def __init__(self, session: SessionContext):
        super().__init__()
        self.title(f"{APP_TITLE} — {session.base_ativa}")
        self.minsize(1100, 720)

        self.session = session
        self.reference = load_reference_data()
        self.ultimas_config = settings_service.load_last_settings()

        self.accounts = []
        self._erros_configuracao = []

        self._build_layout()
        self._maximizar_janela()

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------
    def _build_layout(self):
        container = ttk.Frame(self, padding=8)
        container.pack(fill="both", expand=True)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(1, weight=1)

        self._build_top_tabs(container)

        content = ttk.Frame(container)
        content.grid(row=1, column=0, sticky="nsew")
        content.columnconfigure(0, weight=1)
        content.rowconfigure(0, weight=1)

        self.tab_frames = {
            "criar_contas": self._build_criar_contas_tab(content),
            "excluir_contas": self._build_excluir_contas_tab(content),
            "criacao_base": self._build_criacao_base_tab(content),
        }
        for frame in self.tab_frames.values():
            frame.grid(row=0, column=0, sticky="nsew")

        self._switch_tab("criar_contas")

        self.status_var = tk.StringVar(value="Pronto.")
        status_bar = ttk.Label(self, textvariable=self.status_var, relief="sunken", anchor="w", padding=4)
        status_bar.pack(fill="x", side="bottom")

    def _build_top_tabs(self, container):
        """Navegação superior (protótipo Figma), agora com troca real de
        aba: rótulo clicável muda de cor e traz o painel correspondente
        pra frente (tkraise)."""
        tabs = ttk.Frame(container)
        tabs.grid(row=0, column=0, sticky="ew", pady=(0, 8))

        self.tab_labels = {}
        rotulos = [
            ("criar_contas", "Criar contas"),
            ("excluir_contas", "Excluir contas"),
            ("criacao_base", "Criação de base"),
        ]
        for i, (chave, texto) in enumerate(rotulos):
            lbl = tk.Label(tabs, text=texto, font=("Segoe UI", 14, "bold"), foreground="#8c8c8c", cursor="hand2")
            lbl.pack(side="left", padx=(0 if i == 0 else 16, 0))
            lbl.bind("<Button-1>", lambda _e, k=chave: self._switch_tab(k))
            self.tab_labels[chave] = lbl

        self._build_status_conexao(tabs)

    def _build_status_conexao(self, container):
        """Indicador de conexão com o banco: bolinha verde/vermelha + qual
        servidor/base está ativa. Verificado agora e periodicamente com um
        'SELECT 1' leve, para refletir se a conexão caiu."""
        status = ttk.Frame(container)
        status.pack(side="right")

        self.status_conexao_bolinha = tk.Canvas(status, width=12, height=12, highlightthickness=0)
        self.status_conexao_bolinha.pack(side="left", padx=(0, 6))
        self._bolinha_id = self.status_conexao_bolinha.create_oval(1, 1, 11, 11, fill="#8c8c8c", outline="")

        self.status_conexao_label = ttk.Label(status, text="Verificando conexão...", foreground="#8c8c8c")
        self.status_conexao_label.pack(side="left")

        self._verificar_conexao()

    def _verificar_conexao(self):
        servidor = self.session.connection_settings.servidor
        base = self.session.base_ativa
        try:
            cursor = self.session.connection.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            self.status_conexao_bolinha.itemconfigure(self._bolinha_id, fill="#28a745")
            self.status_conexao_label.configure(
                text=f"Conectado: {servidor} — {base}", foreground="#1e7e34",
            )
        except Exception:
            self.status_conexao_bolinha.itemconfigure(self._bolinha_id, fill="#c0392b")
            self.status_conexao_label.configure(
                text=f"Desconectado: {servidor} — {base}", foreground="#c0392b",
            )
        self.after(30000, self._verificar_conexao)

    def _switch_tab(self, chave: str):
        self.tab_frames[chave].tkraise()
        for k, lbl in self.tab_labels.items():
            lbl.configure(foreground="#000000" if k == chave else "#8c8c8c")

    def _build_criar_contas_tab(self, parent) -> ttk.Frame:
        frame = ttk.Frame(parent)
        frame.columnconfigure(0, weight=1)
        # minsize garante que a caixinha de contas nunca fique espremida a
        # ponto de sumir da tela em resoluções menores, mesmo com o painel
        # de configurações e a barra inferior ocupando espaço fixo abaixo.
        frame.rowconfigure(0, weight=1, minsize=260)

        self.import_panel = ImportPanel(
            frame,
            on_load=self._carregar_planilha,
            on_clear=self._limpar,
            initial_dir=self.ultimas_config.get("ultimo_diretorio", ""),
        )
        self.import_panel.grid(row=0, column=0, sticky="nsew", pady=(0, 8))

        self.config_panel = ConfigurationPanel(frame, self.reference)
        self.config_panel.set_from_dict(self.ultimas_config)
        self.config_panel.grid(row=1, column=0, sticky="ew", pady=(0, 8))

        self._build_bottom_bar(frame)
        return frame

    def _build_excluir_contas_tab(self, parent) -> ttk.Frame:
        self.excluir_contas_panel = ExcluirContasPanel(
            parent, on_consultar=self._consultar_exclusoes, on_excluir=self._excluir_contas_selecionadas, padding=8,
        )
        return self.excluir_contas_panel

    def _build_criacao_base_tab(self, parent) -> ttk.Frame:
        self.criar_base_panel = CriarBasePanel(
            parent, session=self.session, on_provisionar=self._on_provisionar_base, padding=8,
        )
        return self.criar_base_panel

    def _build_bottom_bar(self, container):
        """Barra inferior (protótipo Figma): Validar Dados | checkboxes dos
        8 processos + TODOS | Executar no banco | Gerar."""
        barra = ttk.Frame(container)
        barra.grid(row=2, column=0, sticky="ew")

        ttk.Button(barra, text="Validar Dados", command=self._validar_dados).pack(side="left", padx=(0, 16))

        self.checkbox_vars = {key: tk.BooleanVar(value=False) for key in PROCESS_KEYS}
        self.var_todos = tk.BooleanVar(value=False)

        checkboxes_frame = ttk.Frame(barra)
        checkboxes_frame.pack(side="left", fill="x", expand=True)

        for col, (chave_topo, chave_baixo) in enumerate(CHECKBOX_COLUNAS):
            ttk.Checkbutton(
                checkboxes_frame, text=PROCESS_LABELS[chave_topo],
                variable=self.checkbox_vars[chave_topo], command=self._on_checkbox_changed,
            ).grid(row=0, column=col, sticky="w", padx=(0, 16))
            ttk.Checkbutton(
                checkboxes_frame, text=PROCESS_LABELS[chave_baixo],
                variable=self.checkbox_vars[chave_baixo], command=self._on_checkbox_changed,
            ).grid(row=1, column=col, sticky="w", padx=(0, 16))

        ttk.Checkbutton(
            checkboxes_frame, text="TODOS", variable=self.var_todos, command=self._on_todos_changed,
            style="Todos.TCheckbutton",
        ).grid(row=0, column=len(CHECKBOX_COLUNAS), sticky="w")
        ttk.Style(self).configure("Todos.TCheckbutton", font=("Segoe UI", 9, "bold"))

        self.var_arquivo_unico = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            barra, text="Gerar em arquivo único", variable=self.var_arquivo_unico,
        ).pack(side="right", padx=(0, 16))

        ttk.Button(barra, text="Gerar", command=self._gerar).pack(side="right")
        ttk.Button(barra, text="Executar no banco", command=self._executar_no_banco).pack(side="right", padx=(0, 8))

    def _maximizar_janela(self):
        """Torna a janela responsiva independente do tamanho da tela: abre
        maximizada e todo o layout usa grid/weight para se ajustar."""
        self.update_idletasks()
        try:
            self.state("zoomed")
        except tk.TclError:
            largura = self.winfo_screenwidth()
            altura = self.winfo_screenheight()
            self.geometry(f"{largura}x{altura}+0+0")

    # ------------------------------------------------------------------
    # Checkboxes de geração
    # ------------------------------------------------------------------
    def _on_checkbox_changed(self):
        self.var_todos.set(all(var.get() for var in self.checkbox_vars.values()))

    def _on_todos_changed(self):
        marcado = self.var_todos.get()
        for var in self.checkbox_vars.values():
            var.set(marcado)

    def _chaves_selecionadas(self) -> list:
        return [key for key in PROCESS_KEYS if self.checkbox_vars[key].get()]

    # ------------------------------------------------------------------
    # Ações
    # ------------------------------------------------------------------
    def _carregar_planilha(self, caminho: str):
        try:
            raw_rows = excel_reader.read_accounts(caminho)
            self.accounts = validation_service.validate_accounts(raw_rows)
            self.import_panel.show_accounts(self.accounts)
            self.ultimas_config["ultimo_diretorio"] = os.path.dirname(caminho)
            invalidas = sum(1 for a in self.accounts if not a.valido)
            if invalidas:
                self._status(f"{len(self.accounts)} conta(s) carregada(s), {invalidas} com problema(s). Corrija antes de gerar os scripts.")
            else:
                self._status(f"{len(self.accounts)} conta(s) carregada(s) com sucesso.")
        except ExcelReadError as exc:
            messagebox.showerror("Erro ao importar planilha", str(exc))
            self._status("Falha ao importar planilha.")
        except Exception as exc:  # nunca deixar a aplicação travar/fechar
            messagebox.showerror("Erro inesperado", f"Ocorreu um erro ao importar a planilha:\n{exc}")
            traceback.print_exc()
            self._status("Falha ao importar planilha.")

    def _limpar(self):
        self.accounts = []
        self._status("Dados limpos.")

    def _validar_dados(self) -> bool:
        if not self.accounts:
            messagebox.showwarning("Validar dados", "Nenhuma planilha carregada. Selecione e carregue uma planilha primeiro.")
            return False

        validation_service.apply_duplicate_checks(self.accounts)
        settings = self.config_panel.get_settings()
        self._erros_configuracao = validation_service.validate_settings(settings, self.reference)
        self.import_panel.show_accounts(self.accounts)

        bloqueado = validation_service.has_blocking_errors(self.accounts, self._erros_configuracao)
        if bloqueado:
            mensagens = list(self._erros_configuracao)
            for a in self.accounts:
                if not a.valido:
                    mensagens.append(f"Linha {a.linha}: {a.situacao}")
            messagebox.showerror(
                "Dados inválidos",
                "Corrija os problemas abaixo antes de gerar os scripts:\n\n" + "\n".join(mensagens[:30]),
            )
            self._status("Existem inconsistências. Geração de scripts bloqueada.")
            return False

        self._status("Dados validados com sucesso. Nenhuma inconsistência encontrada.")
        return True

    def _gerar(self):
        chaves = self._chaves_selecionadas()
        if not chaves:
            messagebox.showwarning("Gerar", "Selecione ao menos um script (ou 'TODOS') antes de gerar.")
            return
        if not self._validar_dados():
            return

        try:
            settings = self.config_panel.get_settings()
            resultados = dict(zip(PROCESS_KEYS, sql_generator.generate_all(self.accounts, settings, self.reference)))
            settings_service.save_last_settings(settings, self.ultimas_config.get("ultimo_diretorio", ""))

            if len(chaves) == 1:
                self._salvar_um_script(chaves[0], resultados[chaves[0]])
            elif self.var_arquivo_unico.get():
                self._salvar_arquivo_unico(chaves, resultados)
            else:
                self._salvar_varios_scripts(chaves, resultados)
        except Exception as exc:
            messagebox.showerror("Erro ao gerar scripts", f"Ocorreu um erro ao gerar os scripts SQL:\n{exc}")
            traceback.print_exc()
            self._status("Falha ao gerar scripts.")

    def _executar_no_banco(self):
        chaves = self._chaves_selecionadas()
        if not chaves:
            messagebox.showwarning("Executar no banco", "Selecione ao menos um script (ou 'TODOS') antes de executar.")
            return
        if not self._validar_dados():
            return

        try:
            settings = self.config_panel.get_settings()
            resultados = dict(zip(PROCESS_KEYS, sql_generator.generate_all(self.accounts, settings, self.reference)))
        except Exception as exc:
            messagebox.showerror("Erro ao gerar scripts", f"Ocorreu um erro ao gerar os scripts SQL:\n{exc}")
            traceback.print_exc()
            self._status("Falha ao gerar scripts.")
            return

        resumo = "\n".join(f"- {PROCESS_LABELS[chave]}" for chave in chaves)
        script_preview = self._montar_preview_execucao_no_banco(chaves, resultados)

        if not self._confirmar_execucao_sql(
            "Confirmar execução no banco",
            f"Isto vai executar {len(chaves)} script(s) diretamente na base ativa '{self.session.base_ativa}':",
            resumo,
            script_preview,
            texto_botao="Executar",
        ):
            return

        try:
            cursor = self.session.connection.cursor()
            cursor.execute(f"USE {quote_identifier(self.session.base_ativa)};")
            executados = []
            for chave in chaves:
                cursor.execute(resultados[chave].sql)
                executados.append(PROCESS_LABELS[chave])
            settings_service.save_last_settings(settings, self.ultimas_config.get("ultimo_diretorio", ""))
            self._status(f"Executado no banco '{self.session.base_ativa}': {', '.join(executados)}.")
            messagebox.showinfo("Executar no banco", f"Executado com sucesso na base '{self.session.base_ativa}'.")
        except Exception as exc:
            messagebox.showerror("Erro ao executar no banco", f"Falha ao executar no banco:\n{exc}")
            traceback.print_exc()
            self._status("Falha ao executar no banco.")

    def _montar_preview_execucao_no_banco(self, chaves: list, resultados: dict) -> str:
        """Monta o texto exato exibido na confirmação: um `USE [base]` no
        topo seguido de cada script selecionado, na mesma formatação usada
        ao salvar um arquivo único (ver _salvar_arquivo_unico) — cada script
        já é transacional por conta própria (BEGIN TRY/CATCH), então rodam
        como lotes separados (GO), exatamente como são executados abaixo."""
        blocos = [f"USE {quote_identifier(self.session.base_ativa)};"]
        for chave in chaves:
            cabecalho = f"-- ===== {NOMES_ARQUIVO[chave]} ({PROCESS_LABELS[chave]}) ====="
            blocos.append(f"{cabecalho}\n{resultados[chave].sql}")
        return "\n\nGO\n\n".join(blocos)

    # ------------------------------------------------------------------
    # Excluir contas (consulta + exclusão do que já existe no banco)
    # ------------------------------------------------------------------
    def _consultar_exclusoes(self):
        if not self.accounts:
            messagebox.showwarning(
                "Excluir contas",
                "Nenhuma planilha carregada. Selecione e carregue uma planilha na aba 'Criar contas' primeiro.",
            )
            return
        try:
            settings = self.config_panel.get_settings()
            consultas = delete_service.montar_consultas(self.accounts, settings)
            resultados = delete_service.executar_consultas(self.session.connection, consultas)
            self.excluir_contas_panel.mostrar_resultados(resultados)
            total = sum(len(r.linhas) for r in resultados)
            self._status(f"Consulta de exclusão concluída: {total} registro(s) encontrado(s).")
        except Exception as exc:
            messagebox.showerror("Excluir contas", f"Falha ao consultar o banco:\n{exc}")
            traceback.print_exc()
            self._status("Falha ao consultar contas para exclusão.")

    def _excluir_contas_selecionadas(self, itens: list):
        # itens: [(titulo, tabela, colunas_chave, linha_dict), ...]
        contagem = {}
        for titulo, _, _, _ in itens:
            contagem[titulo] = contagem.get(titulo, 0) + 1
        resumo = "\n".join(f"- {titulo}: {qtd}" for titulo, qtd in contagem.items())

        itens_delete = [(tabela, colunas_chave, linha) for _, tabela, colunas_chave, linha in itens]
        script = delete_service.montar_script_exclusao(itens_delete, self.session.base_ativa)

        if not self._confirmar_execucao_sql(
            "Confirmar exclusão",
            f"Isto vai excluir {len(itens)} registro(s) diretamente na base ativa '{self.session.base_ativa}':",
            resumo,
            script,
            texto_botao="Excluir",
        ):
            return

        try:
            delete_service.executar_script(self.session.connection, script)
            messagebox.showinfo("Excluir contas", f"{len(itens)} registro(s) excluído(s) com sucesso.")
            self._status(f"{len(itens)} registro(s) excluído(s) na base '{self.session.base_ativa}'.")
            self._consultar_exclusoes()
        except Exception as exc:
            messagebox.showerror("Excluir contas", f"Falha ao excluir os registros selecionados:\n{exc}")
            traceback.print_exc()
            self._status("Falha ao excluir registros.")

    def _confirmar_execucao_sql(
        self, titulo_janela: str, cabecalho: str, resumo: str, script: str, texto_botao: str = "Executar",
    ) -> bool:
        """Mostra numa janela o SQL exato (com o USE da base ativa no topo)
        que será executado, para o usuário revisar antes de confirmar — o
        mesmo texto é depois enviado ao banco, sem reconstrução. Usado tanto
        por 'Executar no banco' (Criar contas) quanto por 'Excluir
        selecionados' (Excluir contas)."""
        dialog = tk.Toplevel(self)
        dialog.title(titulo_janela)
        dialog.transient(self)
        dialog.grab_set()
        dialog.geometry("760x560")
        dialog.minsize(560, 400)
        dialog.columnconfigure(0, weight=1)
        dialog.rowconfigure(2, weight=1)

        ttk.Label(
            dialog, text=cabecalho, font=("Segoe UI", 10, "bold"), wraplength=720,
        ).grid(row=0, column=0, sticky="w", padx=10, pady=(10, 4))
        ttk.Label(dialog, text=resumo, wraplength=720).grid(row=1, column=0, sticky="w", padx=10)

        ttk.Label(
            dialog, text="SQL que será executado:", font=("Segoe UI", 9, "bold"),
        ).grid(row=2, column=0, sticky="nw", padx=10, pady=(10, 0))

        texto_frame = ttk.Frame(dialog)
        texto_frame.grid(row=3, column=0, sticky="nsew", padx=10)
        dialog.rowconfigure(3, weight=1)
        texto_frame.columnconfigure(0, weight=1)
        texto_frame.rowconfigure(0, weight=1)

        txt = tk.Text(texto_frame, wrap="none", font=("Consolas", 9))
        scroll_y = ttk.Scrollbar(texto_frame, orient="vertical", command=txt.yview)
        scroll_x = ttk.Scrollbar(texto_frame, orient="horizontal", command=txt.xview)
        txt.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        txt.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")
        txt.insert("1.0", script)
        txt.configure(state="disabled")

        ttk.Label(
            dialog,
            text="Esta ação grava direto no banco do cliente e não é reversível automaticamente.",
            foreground="#b00020",
        ).grid(row=4, column=0, sticky="w", padx=10, pady=(8, 0))

        resultado = {"confirmado": False}

        def confirmar():
            resultado["confirmado"] = True
            dialog.destroy()

        def cancelar():
            dialog.destroy()

        botoes = ttk.Frame(dialog)
        botoes.grid(row=5, column=0, sticky="ew", padx=10, pady=10)
        ttk.Button(botoes, text="Cancelar", command=cancelar).pack(side="right")
        ttk.Button(botoes, text=texto_botao, command=confirmar).pack(side="right", padx=(0, 8))

        dialog.protocol("WM_DELETE_WINDOW", cancelar)
        dialog.wait_window()
        return resultado["confirmado"]

    def _salvar_um_script(self, chave: str, resultado):
        caminho = filedialog.asksaveasfilename(
            title="Salvar script SQL",
            initialfile=NOMES_ARQUIVO[chave],
            defaultextension=".sql",
            filetypes=[("Script SQL", "*.sql")],
        )
        if not caminho:
            self._status("Geração cancelada.")
            return
        with open(caminho, "w", encoding="utf-8-sig", newline="") as f:
            f.write(resultado.sql)
        self._status(f"Script salvo em: {caminho}")

    def _salvar_varios_scripts(self, chaves: list, resultados: dict):
        pasta = filedialog.askdirectory(title="Selecionar pasta para salvar os scripts")
        if not pasta:
            self._status("Geração cancelada.")
            return
        for chave in chaves:
            caminho = os.path.join(pasta, NOMES_ARQUIVO[chave])
            with open(caminho, "w", encoding="utf-8-sig", newline="") as f:
                f.write(resultados[chave].sql)
        self._status(f"{len(chaves)} script(s) salvo(s) em: {pasta}")

    def _salvar_arquivo_unico(self, chaves: list, resultados: dict):
        caminho = filedialog.asksaveasfilename(
            title="Salvar scripts combinados",
            initialfile="Scripts_Combinados.sql",
            defaultextension=".sql",
            filetypes=[("Script SQL", "*.sql")],
        )
        if not caminho:
            self._status("Geração cancelada.")
            return

        blocos = []
        for chave in chaves:
            cabecalho = f"-- ===== {NOMES_ARQUIVO[chave]} ({PROCESS_LABELS[chave]}) ====="
            blocos.append(f"{cabecalho}\n{resultados[chave].sql}")
        conteudo = "\n\nGO\n\n".join(blocos)

        with open(caminho, "w", encoding="utf-8-sig", newline="") as f:
            f.write(conteudo)
        self._status(f"{len(chaves)} script(s) combinado(s) em: {caminho}")

    # ------------------------------------------------------------------
    # Criação de base (thread de trabalho + fila thread-safe -> GUI)
    # ------------------------------------------------------------------
    def _on_provisionar_base(self, cfg, prod_cs, dev_cs):
        self.criar_base_panel.set_busy(True)
        self._progress_queue = queue.Queue()
        thread = threading.Thread(target=self._worker_provisionar, args=(cfg, prod_cs, dev_cs), daemon=True)
        thread.start()
        self.after(100, self._poll_progress_queue)

    def _worker_provisionar(self, cfg, prod_cs, dev_cs):
        resultado = criar_base_service.executar_criacao_base(
            prod_cs, dev_cs, cfg,
            on_progress=self._progress_queue.put,
        )
        self._progress_queue.put(("__RESULTADO__", resultado))

    def _poll_progress_queue(self):
        try:
            while True:
                item = self._progress_queue.get_nowait()
                if isinstance(item, tuple) and item[0] == "__RESULTADO__":
                    self._finalizar_provisionamento(item[1])
                    return
                self.criar_base_panel.append_log(item)
        except queue.Empty:
            pass
        self.after(150, self._poll_progress_queue)

    def _finalizar_provisionamento(self, resultado):
        self.criar_base_panel.set_busy(False)
        if resultado.sucesso:
            messagebox.showinfo("Criação de base", "Base provisionada com sucesso.")
            self._status("Base provisionada com sucesso.")
        else:
            messagebox.showerror(
                "Criação de base",
                f"Falha na etapa '{resultado.passo_falho}':\n{resultado.erro}\n\n"
                f"Etapas concluídas antes da falha: {', '.join(resultado.passos_concluidos) or '(nenhuma)'}",
            )
            self._status(f"Falha na criação de base (etapa '{resultado.passo_falho}').")

    def _status(self, texto: str):
        self.status_var.set(texto)
