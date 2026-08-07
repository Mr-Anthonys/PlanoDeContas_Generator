"""Carrega os valores de referência (TipoArq, InterfaceComum, InterfaceFormaPgto)
a partir do config.json — fonte única de verdade, extraída originalmente da aba
"Interface" da planilha "PLANO DE CONTAS - RECEITAS.xlsx".

Nenhuma regra de negócio SQL é duplicada em outro lugar do código: os módulos de
geração de SQL (sql_generator.py) sempre consultam estes dados através deste
módulo.
"""

import json
import os

from src.utils.constants import CONFIG_PATH


class ReferenceData:
    def __init__(self, config: dict):
        self._config = config

    @property
    def tipos_conta(self):
        return list(self._config.get("tipos_conta", ["Recebimento"]))

    @property
    def opcoes_historico(self):
        return list(self._config.get("opcoes_historico", []))

    @property
    def tipos_arquivo(self):
        """Lista dos nomes de TipoArq disponíveis (ex.: Emolumentos)."""
        return list(self._config.get("tipos_arquivo", {}).keys())

    def interface_arq(self, tipo_arq: str) -> dict:
        return self._config["tipos_arquivo"][tipo_arq]["interface_arq"]

    def interface_comum(self, nome: str) -> dict:
        return self._config["tipos_arquivo"][nome]["interface_comum"]

    def interface_forma_pgto(self, nome: str) -> dict:
        return self._config["tipos_arquivo"][nome]["interface_forma_pgto"]


def load_reference_data(caminho: str = None) -> ReferenceData:
    caminho = caminho or CONFIG_PATH
    if not os.path.exists(caminho):
        raise FileNotFoundError(
            f"Arquivo de configuração não encontrado: {caminho}. "
            "Reinstale a aplicação ou restaure o config.json padrão."
        )
    with open(caminho, "r", encoding="utf-8") as f:
        config = json.load(f)
    return ReferenceData(config)
