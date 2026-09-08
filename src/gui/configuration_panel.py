"""Painel de configurações gerais (Regime, Tipo de Conta, TipoArq,
InterfaceComum, InterfaceFormaPgto, marcadores e histórico).

Layout replica o protótipo Figma ("Plano de Contas - Generator"): Tipo de
Conta é um combobox de seleção múltipla (checkboxes para cada opção, texto
das opções escolhidas unidas por "e"); TipoArq, InterfaceComum e
InterfaceFormaPgto são campos de texto totalmente livre — qualquer valor
digitado é aceito, sem exigir correspondência com os modelos de
config.json (ver reference_loader.ReferenceData._modelo, que cai num modelo
padrão de preenchimento quando o texto não bate com nenhum conhecido); e
Historico1/Historico2/Historico3 são campos de texto livre onde o usuário
escreve o nome da coluna que vai para o histórico.
"""

import tkinter as tk
from tkinter import ttk

from src.models.account import GenerationSettings

PLACEHOLDER_COLOR = "#9a9a9a"
TEXT_COLOR = "#000000"


class _PlaceholderEntry(ttk.Entry):
    """Entry de texto livre que mostra um texto de exemplo (placeholder) em
    cinza quando vazia, replicando o campo "Escreva" do protótipo."""

    def __init__(self, master, textvariable, placeholder="Escreva", **kwargs):
        super().__init__(master, textvariable=textvariable, **kwargs)
        self._var = textvariable
        self._placeholder = placeholder
        self._showing_placeholder = False

        self.bind("<FocusIn>", self._on_focus_in)
        self.bind("<FocusOut>", self._on_focus_out)
        self._apply_placeholder_if_empty()

    def _apply_placeholder_if_empty(self):
        if not self._var.get():
            self._showing_placeholder = True
            self.configure(foreground=PLACEHOLDER_COLOR)
            self._var.set(self._placeholder)

    def _on_focus_in(self, _event):
        if self._showing_placeholder:
            self._showing_placeholder = False
            self.configure(foreground=TEXT_COLOR)
            self._var.set("")

    def _on_focus_out(self, _event):
        self._apply_placeholder_if_empty()

    def get_value(self) -> str:
        return "" if self._showing_placeholder else self._var.get()

    def set_value(self, valor: str):
        valor = valor or ""
        if valor:
            self._showing_placeholder = False
            self.configure(foreground=TEXT_COLOR)
            self._var.set(valor)
        else:
            self._var.set("")
            self._apply_placeholder_if_empty()


class _MultiSelectCombo(ttk.Frame):
    """Combobox de seleção múltipla por checkboxes, replicando o campo
    "Tipo de Conta" do protótipo Figma: uma caixa fechada mostrando as
    opções escolhidas unidas por "e" (ex.: "Recebimento e Pagamento"), que
    abre um painel com um checkbox por opção ao ser clicada."""

    def __init__(self, master, options, on_change=None, **kwargs):
        super().__init__(master, **kwargs)
        self.options = list(options)
        self.on_change = on_change or (lambda: None)
        self.vars = {opt: tk.BooleanVar(value=False) for opt in self.options}
        self._popup = None

        self.box = tk.Frame(self, relief="solid", borderwidth=1, background="#F4F4F4", cursor="hand2")
        self.box.pack(fill="x")
        self.lbl_texto = tk.Label(
            self.box, text="Selecione...", background="#F4F4F4", foreground=PLACEHOLDER_COLOR,
            anchor="w", padx=6, pady=3,
        )
        self.lbl_texto.pack(side="left", fill="x", expand=True)
        self.lbl_seta = tk.Label(self.box, text="▾", background="#F4F4F4", padx=6)
        self.lbl_seta.pack(side="right")

        for widget in (self.box, self.lbl_texto, self.lbl_seta):
            widget.bind("<Button-1>", self._toggle_popup)

    def _toggle_popup(self, _event=None):
        if self._popup is not None:
            self._close_popup()
        else:
            self._open_popup()

    def _open_popup(self):
        self._popup = tk.Toplevel(self)
        self._popup.wm_overrideredirect(True)
        self._popup.wm_attributes("-topmost", True)
        x = self.box.winfo_rootx()
        y = self.box.winfo_rooty() + self.box.winfo_height()
        self._popup.wm_geometry(f"+{x}+{y}")

        frame = tk.Frame(self._popup, relief="solid", borderwidth=1, background="#ffffff", padx=6, pady=4)
        frame.pack()
        for opt in self.options:
            ttk.Checkbutton(
                frame, text=opt, variable=self.vars[opt], command=self._on_toggle,
            ).pack(anchor="w")

        self._outside_click_id = self.winfo_toplevel().bind_all("<Button-1>", self._maybe_close, add="+")

    def _maybe_close(self, event):
        if self._popup is None:
            return
        widget = event.widget
        while widget is not None:
            if widget is self or widget is self._popup:
                return
            widget = getattr(widget, "master", None)
        self._close_popup()

    def _close_popup(self):
        if self._popup is not None:
            self.winfo_toplevel().unbind_all("<Button-1>")
            self._popup.destroy()
            self._popup = None

    def _on_toggle(self):
        self._update_display()
        self.on_change()

    def _update_display(self):
        selecionados = self.get_selected()
        if selecionados:
            self.lbl_texto.configure(text=" e ".join(selecionados), foreground=TEXT_COLOR)
        else:
            self.lbl_texto.configure(text="Selecione...", foreground=PLACEHOLDER_COLOR)

    def get_selected(self) -> list:
        return [opt for opt in self.options if self.vars[opt].get()]

    def set_selected(self, selecionados):
        selecionados = set(selecionados or [])
        for opt in self.options:
            self.vars[opt].set(opt in selecionados)
        self._update_display()


class ConfigurationPanel(ttk.LabelFrame):
    def __init__(self, master, reference, on_change=None, **kwargs):
        super().__init__(master, text="Configurações gerais", padding=10, **kwargs)
        self.reference = reference
        self.on_change = on_change or (lambda: None)

        self.var_regime = tk.StringVar(value="Titular")
        self.var_tipo_arq = tk.StringVar(value="Emolumentos")
        self.var_interface_comum = tk.StringVar(value="Emolumentos")
        self.var_interface_forma_pgto = tk.StringVar(value="Emolumentos")
        self.var_qtd_marcadores = tk.IntVar(value=1)
        self.var_historico_texto = tk.StringVar(value="")
        self.var_historico1 = tk.StringVar(value="")
        self.var_historico2 = tk.StringVar(value="")
        self.var_historico3 = tk.StringVar(value="")

        self._build()
        self._wire_events()
        self._atualizar_estado_historico()

    def _build(self):
        for col in range(4):
            self.columnconfigure(col, weight=1, uniform="config_col")

        col1 = ttk.Frame(self)
        col1.grid(row=0, column=0, sticky="nwe", padx=(0, 16))
        col2 = ttk.Frame(self)
        col2.grid(row=0, column=1, sticky="nwe", padx=(0, 16))
        col3 = ttk.Frame(self)
        col3.grid(row=0, column=2, sticky="nwe", padx=(0, 16))
        col4 = ttk.Frame(self)
        col4.grid(row=0, column=3, sticky="nwe")
        for col in (col1, col2, col3, col4):
            col.columnconfigure(0, weight=1)

        # --- Regime / Tipo de Conta -------------------------------------
        ttk.Label(col1, text="Regime:", font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Radiobutton(col1, text="Interino", value="Interino", variable=self.var_regime).grid(row=1, column=0, sticky="w")
        ttk.Radiobutton(col1, text="Titular", value="Titular", variable=self.var_regime).grid(row=2, column=0, sticky="w")
        ttk.Label(col1, text="Regra: Interino = L_IRRF:0 | Titular = L_IRRF: 1", foreground="#555").grid(
            row=3, column=0, sticky="w", pady=(2, 8)
        )

        ttk.Label(col1, text="Tipo de Conta:", font=("Segoe UI", 9, "bold")).grid(row=4, column=0, sticky="w")
        self.multi_tipo_conta = _MultiSelectCombo(
            col1, self.reference.tipos_conta, on_change=lambda: self.on_change()
        )
        self.multi_tipo_conta.grid(row=5, column=0, sticky="we", pady=(0, 8))

        # --- TipoArq / Interfaces (texto livre) --------------------------
        ttk.Label(col2, text="TipoArq:", font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="w")
        self.entry_tipo_arq = ttk.Entry(col2, textvariable=self.var_tipo_arq)
        self.entry_tipo_arq.grid(row=1, column=0, sticky="we", pady=(0, 8))

        ttk.Label(col2, text="InterfaceComum:", font=("Segoe UI", 9, "bold")).grid(row=2, column=0, sticky="w")
        self.entry_interface_comum = ttk.Entry(col2, textvariable=self.var_interface_comum)
        self.entry_interface_comum.grid(row=3, column=0, sticky="we", pady=(0, 8))

        ttk.Label(col2, text="InterfaceFormaPgto:", font=("Segoe UI", 9, "bold")).grid(row=4, column=0, sticky="w")
        self.entry_interface_forma_pgto = ttk.Entry(col2, textvariable=self.var_interface_forma_pgto)
        self.entry_interface_forma_pgto.grid(row=5, column=0, sticky="we", pady=(0, 8))

        # --- Marcadores / Texto do histórico -----------------------------
        ttk.Label(col3, text="Marcadores '@' no histórico:", font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Radiobutton(col3, text="Um marcador (@)", value=1, variable=self.var_qtd_marcadores).grid(row=1, column=0, sticky="w")
        ttk.Radiobutton(col3, text="Dois marcadores (@ @)", value=2, variable=self.var_qtd_marcadores).grid(row=2, column=0, sticky="w")
        ttk.Radiobutton(col3, text="Três marcadores (@ @ @)", value=3, variable=self.var_qtd_marcadores).grid(row=3, column=0, sticky="w")

        ttk.Label(col3, text="Texto do histórico:", font=("Segoe UI", 9, "bold")).grid(row=4, column=0, sticky="w", pady=(8, 0))
        self.entry_historico_texto = ttk.Entry(col3, textvariable=self.var_historico_texto)
        self.entry_historico_texto.grid(row=5, column=0, sticky="we", pady=(0, 8))

        # --- Historico1 / Historico2 / Historico3 (texto livre) ----------
        ttk.Label(col4, text="Historico1:", font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="w")
        self.entry_historico1 = _PlaceholderEntry(col4, self.var_historico1)
        self.entry_historico1.grid(row=1, column=0, sticky="we", pady=(0, 8))

        ttk.Label(col4, text="Historico2:", font=("Segoe UI", 9, "bold")).grid(row=2, column=0, sticky="w")
        self.entry_historico2 = _PlaceholderEntry(col4, self.var_historico2)
        self.entry_historico2.grid(row=3, column=0, sticky="we", pady=(0, 8))

        ttk.Label(col4, text="Historico3:", font=("Segoe UI", 9, "bold")).grid(row=4, column=0, sticky="w")
        self.entry_historico3 = _PlaceholderEntry(col4, self.var_historico3)
        self.entry_historico3.grid(row=5, column=0, sticky="we", pady=(0, 8))

    def _wire_events(self):
        self.var_qtd_marcadores.trace_add("write", lambda *_: self._atualizar_estado_historico())
        for var in (
            self.var_regime, self.var_tipo_arq, self.var_interface_comum,
            self.var_interface_forma_pgto, self.var_historico_texto,
            self.var_historico1, self.var_historico2, self.var_historico3,
        ):
            var.trace_add("write", lambda *_: self.on_change())

    def _atualizar_estado_historico(self):
        qtd = self.var_qtd_marcadores.get()
        self.entry_historico2.configure(state="normal" if qtd >= 2 else "disabled")
        self.entry_historico3.configure(state="normal" if qtd >= 3 else "disabled")
        if qtd < 2:
            self.entry_historico2.set_value("")
        if qtd < 3:
            self.entry_historico3.set_value("")
        self.on_change()

    def get_settings(self) -> GenerationSettings:
        qtd = self.var_qtd_marcadores.get()
        return GenerationSettings(
            regime=self.var_regime.get(),
            tipo_conta=" e ".join(self.multi_tipo_conta.get_selected()),
            tipo_arq=self.var_tipo_arq.get(),
            interface_comum=self.var_interface_comum.get(),
            interface_forma_pgto=self.var_interface_forma_pgto.get(),
            qtd_marcadores=qtd,
            historico_texto=self.var_historico_texto.get(),
            historico1=self.entry_historico1.get_value(),
            historico2=self.entry_historico2.get_value() if qtd >= 2 else "",
            historico3=self.entry_historico3.get_value() if qtd >= 3 else "",
        )

    def set_from_dict(self, dados: dict):
        self.var_regime.set(dados.get("ultimo_regime", "Titular"))
        selecionados = [
            opt for opt in self.reference.tipos_conta
            if opt in dados.get("ultimo_tipo_conta", "Recebimento").split(" e ")
        ]
        if not selecionados and self.reference.tipos_conta:
            selecionados = [self.reference.tipos_conta[0]]
        self.multi_tipo_conta.set_selected(selecionados)
        self.var_tipo_arq.set(dados.get("ultimo_tipo_arq", "Emolumentos"))
        self.var_interface_comum.set(dados.get("ultimo_interface_comum", "Emolumentos"))
        self.var_interface_forma_pgto.set(dados.get("ultimo_interface_forma_pgto", "Emolumentos"))
        self.var_qtd_marcadores.set(dados.get("ultima_qtd_marcadores", 1))
        self.entry_historico1.set_value(dados.get("ultimo_historico1", ""))
        self.entry_historico2.set_value(dados.get("ultimo_historico2", ""))
        self.entry_historico3.set_value(dados.get("ultimo_historico3", ""))
        self._atualizar_estado_historico()
