"""Janela principal do Gerador de Plano de Contas."""

import datetime
import os
import tkinter as tk
import traceback
from tkinter import filedialog, messagebox, ttk

from src.gui.configuration_panel import ConfigurationPanel
from src.gui.import_panel import ImportPanel
from src.gui.sql_tabs import SqlTabs
from src.services import excel_reader, settings_service, sql_generator, validation_service
from src.services.excel_reader import ExcelReadError
from src.services.reference_loader import load_reference_data

APP_TITLE = "Gerador de Plano de Contas e Scripts SQL"


class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.minsize(1000, 700)

        self.reference = load_reference_data()
        self.ultimas_config = settings_service.load_last_settings()

        self.accounts = []
        self._erros_configuracao = []

        self._build_layout()
        self._center_window()

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------
    def _build_layout(self):
        container = ttk.Frame(self, padding=8)
        container.pack(fill="both", expand=True)

        self.import_panel = ImportPanel(
            container,
            on_load=self._carregar_planilha,
            on_clear=self._limpar,
            initial_dir=self.ultimas_config.get("ultimo_diretorio", ""),
        )
        self.import_panel.pack(fill="both", expand=False, pady=(0, 8))

        self.config_panel = ConfigurationPanel(container, self.reference)
        self.config_panel.set_from_dict(self.ultimas_config)
        self.config_panel.pack(fill="x", pady=(0, 8))

        acoes = ttk.Frame(container)
        acoes.pack(fill="x", pady=(0, 8))
        ttk.Button(acoes, text="Validar dados", command=self._validar_dados).pack(side="left")
        ttk.Button(acoes, text="Gerar scripts", command=self._gerar_scripts).pack(side="left", padx=6)
        ttk.Button(acoes, text="Copiar todos os scripts", command=self._copiar_tudo).pack(side="left", padx=6)
        ttk.Button(acoes, text="Salvar SQL em arquivo", command=self._salvar_arquivo).pack(side="left", padx=6)
        ttk.Button(acoes, text="Salvar cada processo separadamente", command=self._salvar_por_processo).pack(
            side="left", padx=6
        )
        ttk.Button(acoes, text="Restaurar padrões", command=self._restaurar_padroes).pack(side="right")

        self.sql_tabs = SqlTabs(container, copy_to_clipboard=self._copiar_texto)
        self.sql_tabs.pack(fill="both", expand=True)

        self.status_var = tk.StringVar(value="Pronto.")
        status_bar = ttk.Label(self, textvariable=self.status_var, relief="sunken", anchor="w", padding=4)
        status_bar.pack(fill="x", side="bottom")

    def _center_window(self):
        self.update_idletasks()
        largura, altura = 1200, 800
        x = (self.winfo_screenwidth() // 2) - (largura // 2)
        y = (self.winfo_screenheight() // 2) - (altura // 2)
        self.geometry(f"{largura}x{altura}+{x}+{y}")

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
        self.sql_tabs.clear()
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

    def _gerar_scripts(self):
        try:
            if not self._validar_dados():
                return
            settings = self.config_panel.get_settings()
            resultados = sql_generator.generate_all(self.accounts, settings, self.reference)
            script_completo = sql_generator.generate_full_script(self.accounts, settings, self.reference)
            self.sql_tabs.update_results(resultados, script_completo)
            settings_service.save_last_settings(settings, self.ultimas_config.get("ultimo_diretorio", ""))
            self._status("Scripts gerados com sucesso.")
        except Exception as exc:
            messagebox.showerror("Erro ao gerar scripts", f"Ocorreu um erro ao gerar os scripts SQL:\n{exc}")
            traceback.print_exc()
            self._status("Falha ao gerar scripts.")

    def _copiar_texto(self, texto: str):
        if not texto.strip():
            messagebox.showinfo("Copiar", "Não há SQL gerado para copiar. Clique em 'Gerar scripts' primeiro.")
            return
        self.clipboard_clear()
        self.clipboard_append(texto)
        self._status("SQL copiado para a área de transferência.")

    def _copiar_tudo(self):
        self._copiar_texto(self.sql_tabs.get_full_script())

    def _salvar_arquivo(self):
        script = self.sql_tabs.get_full_script()
        if not script.strip():
            messagebox.showinfo("Salvar SQL", "Não há SQL gerado para salvar. Clique em 'Gerar scripts' primeiro.")
            return
        nome_sugerido = f"PlanoContas_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
        caminho = filedialog.asksaveasfilename(
            title="Salvar script SQL",
            initialfile=nome_sugerido,
            defaultextension=".sql",
            filetypes=[("Script SQL", "*.sql")],
        )
        if not caminho:
            return
        with open(caminho, "w", encoding="utf-8-sig", newline="") as f:
            f.write(script)
        self._status(f"Script salvo em: {caminho}")

    def _salvar_por_processo(self):
        if not self.accounts:
            messagebox.showinfo("Salvar por processo", "Gere os scripts antes de salvar.")
            return
        script = self.sql_tabs.get_full_script()
        if not script.strip():
            messagebox.showinfo("Salvar por processo", "Não há SQL gerado para salvar. Clique em 'Gerar scripts' primeiro.")
            return
        pasta = filedialog.askdirectory(title="Selecionar pasta para salvar os scripts")
        if not pasta:
            return
        settings = self.config_panel.get_settings()
        resultados = sql_generator.generate_all(self.accounts, settings, self.reference)
        nomes_arquivo = [
            "01_Contas.sql", "02_GrupoPortal.sql", "03_GrupoContabil.sql", "04_InterfaceContas.sql",
            "05_InterfaceHistorico.sql", "06_InterfaceArq.sql", "07_InterfaceComum.sql", "08_InterfaceFormaPgto.sql",
        ]
        for nome_arquivo, resultado in zip(nomes_arquivo, resultados):
            caminho = os.path.join(pasta, nome_arquivo)
            with open(caminho, "w", encoding="utf-8-sig", newline="") as f:
                f.write(resultado.sql)
        self._status(f"Scripts individuais salvos em: {pasta}")

    def _restaurar_padroes(self):
        padroes = settings_service.restore_defaults()
        self.config_panel.set_from_dict(padroes)
        self._status("Configurações restauradas para o padrão.")

    def _status(self, texto: str):
        self.status_var.set(texto)
