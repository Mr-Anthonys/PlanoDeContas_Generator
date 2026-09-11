"""Modelos de dados usados pela aplicação."""
from dataclasses import dataclass, field


@dataclass
class Account:
    """Uma conta importada da planilha de entrada (Nome, Grupo, ContaOrigem)."""

    linha: int
    nome: str
    grupo: str
    conta_origem: str
    erros: list = field(default_factory=list)

    @property
    def valido(self) -> bool:
        return len(self.erros) == 0

    @property
    def situacao(self) -> str:
        return "Válido" if self.valido else "; ".join(self.erros)

    @property
    def grupo_normalizado(self) -> str:
        return self.grupo.strip().upper()


@dataclass
class GenerationSettings:
    """Configurações gerais informadas pelo usuário antes da geração dos scripts."""

    regime: str = "Titular"
    tipo_conta: str = "Recebimento"
    tipo_arq: str = "Emolumentos"
    interface_comum: str = "Emolumentos"
    interface_forma_pgto: str = "Emolumentos"
    qtd_marcadores: int = 1
    historico_texto: str = ""
    historico1: str = ""
    historico2: str = ""
    historico3: str = ""
    l_previo: int = 2

    @property
    def l_irrf(self) -> int:
        return 1 if self.regime == "Titular" else 0
