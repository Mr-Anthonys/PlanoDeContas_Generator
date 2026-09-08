"""Validações de negócio sobre as contas importadas e sobre as configurações
gerais informadas pelo usuário (regime, histórico, TipoArq etc.).

Nenhuma geração de SQL é bloqueada silenciosamente: cada inconsistência gera
uma mensagem de erro específica, associada à linha correspondente sempre que
possível.
"""

import re

from src.models.account import Account
from src.utils.constants import MARCADOR


def build_accounts(raw_rows) -> list:
    """Converte RawRow em Account e aplica as validações de campo/linha
    (nome vazio, grupo vazio, ContaOrigem vazia ou com formato inválido)."""
    accounts = []
    for raw in raw_rows:
        account = Account(
            linha=raw.linha,
            nome=raw.nome.strip(),
            grupo=raw.grupo.strip(),
            conta_origem=raw.conta_origem.strip(),
        )
        if not account.nome:
            account.erros.append("Nome da conta vazio")
        if not account.grupo:
            account.erros.append("Grupo vazio")
        if not account.conta_origem:
            account.erros.append("ContaOrigem vazia")
        elif re.search(r"\s", account.conta_origem):
            account.erros.append("ContaOrigem contém espaços internos")
        accounts.append(account)
    return accounts


def apply_duplicate_checks(accounts: list) -> None:
    """Marca duplicidade de Nome+Grupo (comparação sem diferenciar maiúsculas/minúsculas,
    pois o SQL Server usa collation case-insensitive por padrão) e de ContaOrigem.

    Mesmo nome em grupos diferentes não é duplicidade: cada grupo tem sua
    própria conta, então essas linhas geram normalmente."""
    por_nome_grupo = {}
    por_codigo = {}
    for account in accounts:
        if account.nome and account.grupo:
            chave = (account.nome.strip().lower(), account.grupo.strip().lower())
            por_nome_grupo.setdefault(chave, []).append(account)
        if account.conta_origem:
            por_codigo.setdefault(account.conta_origem, []).append(account)

    for chave, grupo in por_nome_grupo.items():
        if len(grupo) > 1:
            linhas = ", ".join(str(a.linha) for a in grupo)
            for account in grupo:
                account.erros.append(f"Nome duplicado no mesmo grupo (linhas {linhas})")

    for codigo, grupo in por_codigo.items():
        if len(grupo) > 1:
            linhas = ", ".join(str(a.linha) for a in grupo)
            for account in grupo:
                account.erros.append(f"ContaOrigem '{codigo}' duplicado (linhas {linhas})")


def validate_accounts(raw_rows) -> list:
    """Função de conveniência: constrói as contas e aplica todas as validações
    de linha, retornando a lista de Account (cada uma com sua lista de erros)."""
    accounts = build_accounts(raw_rows)
    apply_duplicate_checks(accounts)
    return accounts


def validate_settings(settings, reference) -> list:
    """Valida as configurações gerais (regime, tipo de conta, TipoArq, histórico).

    Retorna uma lista de mensagens de erro (vazia quando tudo está correto).
    """
    erros = []

    if settings.regime not in ("Interino", "Titular"):
        erros.append("Regime deve ser 'Interino' ou 'Titular'.")

    if not settings.tipo_conta or not settings.tipo_conta.strip():
        erros.append("Tipo de Conta é obrigatório.")

    if not settings.tipo_arq or not settings.tipo_arq.strip():
        erros.append("TipoArq é obrigatório.")

    if not settings.interface_comum or not settings.interface_comum.strip():
        erros.append("InterfaceComum é obrigatório.")

    if not settings.interface_forma_pgto or not settings.interface_forma_pgto.strip():
        erros.append("InterfaceFormaPgto é obrigatório.")

    erros.extend(validate_historico(settings))

    return erros


def validate_historico(settings) -> list:
    """Valida a regra do histórico: quantidade de marcadores @, obrigatoriedade
    de Historico1/Historico2 conforme a quantidade escolhida."""
    erros = []
    qtd_marcadores = settings.qtd_marcadores
    texto = settings.historico_texto or ""
    qtd_arrobas = texto.count(MARCADOR)

    if qtd_marcadores not in (1, 2, 3):
        erros.append("Quantidade de marcadores deve ser 1, 2 ou 3.")
        return erros

    if not texto.strip():
        erros.append("Texto do histórico não pode ser vazio.")
    elif qtd_arrobas != qtd_marcadores:
        erros.append(
            f"O texto do histórico contém {qtd_arrobas} marcador(es) '@', "
            f"mas a quantidade selecionada foi {qtd_marcadores}."
        )

    if qtd_marcadores >= 1 and not (settings.historico1 or "").strip():
        erros.append("Historico1 é obrigatório quando há pelo menos um marcador '@'.")

    if qtd_marcadores >= 2 and not (settings.historico2 or "").strip():
        erros.append("Historico2 é obrigatório quando há dois ou mais marcadores '@'.")

    if qtd_marcadores < 2 and (settings.historico2 or "").strip():
        erros.append("Historico2 deve permanecer vazio quando há menos de dois marcadores '@'.")

    if qtd_marcadores >= 3 and not (settings.historico3 or "").strip():
        erros.append("Historico3 é obrigatório quando há três marcadores '@'.")

    if qtd_marcadores < 3 and (settings.historico3 or "").strip():
        erros.append("Historico3 deve permanecer vazio quando há menos de três marcadores '@'.")

    return erros


def has_blocking_errors(accounts: list, erros_gerais: list) -> bool:
    return bool(erros_gerais) or any(not a.valido for a in accounts)
