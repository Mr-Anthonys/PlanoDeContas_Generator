"""Painel de configurações gerais (Regime, Tipo de Conta, TipoArq,
InterfaceComum, InterfaceFormaPgto, marcadores e histórico)."""

import tkinter as tk
from tkinter import ttk

from src.models.account import GenerationSettings


class ConfigurationPanel(ttk.LabelFrame):
    def __init__(self, master, reference, on_change=None, **kwargs):
        super().__init__(master, text="Configurações gerais", padding=10, **kwargs)
        self.reference = reference
        self.on_change = on_change or (lambda: None)

        self.var_regime = tk.StringVar(value="Titular")
        self.var_tipo_conta = tk.StringVar(value="Recebimento")
        self.var_tipo_arq = tk.StringVar(value="Emolumentos")
        self.var_interface_comum = tk.StringVar(value="Emolumentos")
        self.var_interface_forma_pgto = tk.StringVar(value="Emolumentos")
        self.var_qtd_marcadores = tk.IntVar(value=1)
        self.var_historico_texto = tk.StringVar(value="")
        self.var_historico1 = tk.StringVar(value="")
        self.var_historico2 = tk.StringVar(value="")

        self._build()
        self._wire_events()
        self._atualizar_estado_historico2()

    def _build(self):
        col1 = ttk.Frame(self)
        col1.grid(row=0, column=0, sticky="nw", padx=(0, 24))
        col2 = ttk.Frame(self)
        col2.grid(row=0, column=1, sticky="nw", padx=(0, 24))
        col3 = ttk.Frame(self)
        col3.grid(row=0, column=2, sticky="nw")

        # --- Regime -----------------------------------------------------
        ttk.Label(col1, text="Regime:", font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Radiobutton(col1, text="Interino", value="Interino", variable=self.var_regime).grid(row=1, column=0, sticky="w")
        ttk.Radiobutton(col1, text="Titular", value="Titular", variable=self.var_regime).grid(row=2, column=0, sticky="w")
        ttk.Label(col1, text="Regra: Interino = L_IRRF 0  |  Titular = L_IRRF 1", foreground="#555").grid(
            row=3, column=0, sticky="w", pady=(2, 8)
        )

        ttk.Label(col1, text="Tipo de Conta:", font=("Segoe UI", 9, "bold")).grid(row=4, column=0, sticky="w")
        self.combo_tipo_conta = ttk.Combobox(
            col1, textvariable=self.var_tipo_conta, values=self.reference.tipos_conta, width=22
        )
        self.combo_tipo_conta.grid(row=5, column=0, sticky="w", pady=(0, 8))

        # --- TipoArq / Interfaces ----------------------------------------
        ttk.Label(col2, text="TipoArq:", font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="w")
        self.combo_tipo_arq = ttk.Combobox(
            col2, textvariable=self.var_tipo_arq, values=self.reference.tipos_arquivo, state="readonly", width=22
        )
        self.combo_tipo_arq.grid(row=1, column=0, sticky="w", pady=(0, 8))

        ttk.Label(col2, text="InterfaceComum:", font=("Segoe UI", 9, "bold")).grid(row=2, column=0, sticky="w")
        self.combo_interface_comum = ttk.Combobox(
            col2, textvariable=self.var_interface_comum, values=self.reference.tipos_arquivo, state="readonly", width=22
        )
        self.combo_interface_comum.grid(row=3, column=0, sticky="w", pady=(0, 8))

        ttk.Label(col2, text="InterfaceFormaPgto:", font=("Segoe UI", 9, "bold")).grid(row=4, column=0, sticky="w")
        self.combo_interface_forma_pgto = ttk.Combobox(
            col2, textvariable=self.var_interface_forma_pgto, values=self.reference.tipos_arquivo, state="readonly", width=22
        )
        self.combo_interface_forma_pgto.grid(row=5, column=0, sticky="w", pady=(0, 8))

        # --- Histórico -----------------------------------------------------
        ttk.Label(col3, text="Marcadores '@' no histórico:", font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Radiobutton(col3, text="Um marcador (@)", value=1, variable=self.var_qtd_marcadores).grid(row=1, column=0, sticky="w")
        ttk.Radiobutton(col3, text="Dois marcadores (@ @)", value=2, variable=self.var_qtd_marcadores).grid(row=2, column=0, sticky="w")

        ttk.Label(col3, text="Texto do histórico:").grid(row=3, column=0, sticky="w", pady=(8, 0))
        self.entry_historico_texto = ttk.Entry(col3, textvariable=self.var_historico_texto, width=48)
        self.entry_historico_texto.grid(row=4, column=0, sticky="we", pady=(0, 8))

        ttk.Label(col3, text="Historico1 (1º @):").grid(row=5, column=0, sticky="w")
        self.combo_historico1 = ttk.Combobox(
            col3, textvariable=self.var_historico1, values=self.reference.opcoes_historico, state="readonly", width=22
        )
        self.combo_historico1.grid(row=6, column=0, sticky="w", pady=(0, 8))

        ttk.Label(col3, text="Historico2 (2º @):").grid(row=7, column=0, sticky="w")
        self.combo_historico2 = ttk.Combobox(
            col3, textvariable=self.var_historico2, values=self.reference.opcoes_historico, state="readonly", width=22
        )
        self.combo_historico2.grid(row=8, column=0, sticky="w")

    def _wire_events(self):
        self.var_tipo_arq.trace_add("write", self._on_tipo_arq_changed)
        self.var_qtd_marcadores.trace_add("write", lambda *_: self._atualizar_estado_historico2())
        for var in (
            self.var_regime, self.var_tipo_conta, self.var_interface_comum,
            self.var_interface_forma_pgto, self.var_historico_texto,
            self.var_historico1, self.var_historico2,
        ):
            var.trace_add("write", lambda *_: self.on_change())

    def _on_tipo_arq_changed(self, *_):
        tipo = self.var_tipo_arq.get()
        if tipo in self.reference.tipos_arquivo:
            self.var_interface_comum.set(tipo)
            self.var_interface_forma_pgto.set(tipo)
        self.on_change()

    def _atualizar_estado_historico2(self):
        if self.var_qtd_marcadores.get() == 1:
            self.var_historico2.set("")
            self.combo_historico2.configure(state="disabled")
        else:
            self.combo_historico2.configure(state="readonly")
        self.on_change()

    def get_settings(self) -> GenerationSettings:
        return GenerationSettings(
            regime=self.var_regime.get(),
            tipo_conta=self.var_tipo_conta.get(),
            tipo_arq=self.var_tipo_arq.get(),
            interface_comum=self.var_interface_comum.get(),
            interface_forma_pgto=self.var_interface_forma_pgto.get(),
            qtd_marcadores=self.var_qtd_marcadores.get(),
            historico_texto=self.var_historico_texto.get(),
            historico1=self.var_historico1.get(),
            historico2=self.var_historico2.get() if self.var_qtd_marcadores.get() == 2 else "",
        )

    def set_from_dict(self, dados: dict):
        self.var_regime.set(dados.get("ultimo_regime", "Titular"))
        self.var_tipo_conta.set(dados.get("ultimo_tipo_conta", "Recebimento"))
        self.var_tipo_arq.set(dados.get("ultimo_tipo_arq", "Emolumentos"))
        self.var_interface_comum.set(dados.get("ultimo_interface_comum", "Emolumentos"))
        self.var_interface_forma_pgto.set(dados.get("ultimo_interface_forma_pgto", "Emolumentos"))
        self.var_qtd_marcadores.set(dados.get("ultima_qtd_marcadores", 1))
        self.var_historico1.set(dados.get("ultimo_historico1", ""))
        self.var_historico2.set(dados.get("ultimo_historico2", ""))
