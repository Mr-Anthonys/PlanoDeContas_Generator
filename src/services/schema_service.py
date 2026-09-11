"""Introspecção de schema (tabelas/colunas) do banco modelo, para a etapa
opcional de "Tabelas adicionais" na Criação de Base — cópia dinâmica de
tabelas/colunas escolhidas pelo usuário, além das ~15 tabelas fixas que
`resources/sql_templates/criar_base/03_dados.sql` já cobre (ver
criar_base_service.py).

`montar_copia_tabela` (INSERT...SELECT cross-database) e a execução direta
de 03_dados.sql só funcionam quando a base modelo e a base nova estão no
MESMO servidor (sem linked server). Quando os servidores são diferentes,
criar_base_service copia os dados linha a linha via Python (lê da conexão
do modelo, grava na conexão de destino) — `analisar_copia_fixa_de_dados`
abaixo é o que descreve, pra esse caminho, quais tabelas/colunas copiar,
extraindo isso do próprio 03_dados.sql (fonte única da verdade) em vez de
duplicar a lista à mão.
"""

import re
from dataclasses import dataclass
from typing import Optional

from src.utils.sql_escape import quote_identifier

_LINE_COMMENT_PATTERN = re.compile(r"--.*$", re.MULTILINE)
_DELETE_PATTERN = re.compile(r"^delete\s+(\S+)\s*$", re.IGNORECASE | re.MULTILINE)
_INSERT_BLOCK_PATTERN = re.compile(
    r"insert\s+into\s+(?P<destino>\[[^\]]+\]|\w+)"
    r"\s*(?:\(\s*(?P<colunas>[\s\S]*?)\s*\))?"
    r"\s*select\s+(?:\*|[\s\S]*?)"
    r"\s*from\s+\[\$BASE_MODELO\]\.dbo\.(?P<origem>\[[^\]]+\]|\w+)",
    re.IGNORECASE,
)


@dataclass
class CopiaTabelaFixa:
    tabela_destino: str
    tabela_origem: str
    colunas: Optional[list]  # None = 03_dados.sql usa "select *" (todas as colunas)


@dataclass
class PlanoCopiaFixa:
    tabelas_para_limpar: list  # tabelas com DELETE antes da cópia (Resumo, Lançamentos, ...)
    tabelas: list  # list[CopiaTabelaFixa], na ordem em que aparecem no script


def _limpar_identificador(bruto: str) -> str:
    bruto = bruto.strip()
    if bruto.startswith("[") and bruto.endswith("]"):
        return bruto[1:-1]
    return bruto


def _parse_colunas(bruto: Optional[str]) -> Optional[list]:
    if bruto is None:
        return None
    achatado = re.sub(r"\s+", " ", bruto).strip()
    if not achatado:
        return None
    return [_limpar_identificador(c) for c in achatado.split(",") if c.strip()]


def analisar_copia_fixa_de_dados(caminho_sql: str) -> PlanoCopiaFixa:
    """Extrai do 03_dados.sql, sem duplicar a lista à mão, as tabelas fixas
    que a etapa 'dados' copia da base modelo (tabela/colunas exatas de cada
    INSERT...SELECT do script — 'select *' vira colunas=None) e as tabelas
    zeradas por DELETE antes da cópia."""
    with open(caminho_sql, "r", encoding="utf-8-sig") as f:
        bruto = f.read()
    texto = _LINE_COMMENT_PATTERN.sub("", bruto)

    tabelas_para_limpar = _DELETE_PATTERN.findall(texto)
    tabelas = [
        CopiaTabelaFixa(
            tabela_destino=_limpar_identificador(m.group("destino")),
            tabela_origem=_limpar_identificador(m.group("origem")),
            colunas=_parse_colunas(m.group("colunas")),
        )
        for m in _INSERT_BLOCK_PATTERN.finditer(texto)
    ]
    return PlanoCopiaFixa(tabelas_para_limpar=tabelas_para_limpar, tabelas=tabelas)


def listar_tabelas(connection, base: str) -> list:
    """Lista as tabelas de usuário (BASE TABLE) do banco `base`, em ordem alfabética."""
    cursor = connection.cursor()
    cursor.execute(
        f"SELECT TABLE_NAME FROM {quote_identifier(base)}.INFORMATION_SCHEMA.TABLES "
        f"WHERE TABLE_TYPE = 'BASE TABLE' ORDER BY TABLE_NAME"
    )
    return [row[0] for row in cursor.fetchall()]


def listar_colunas(connection, base: str, tabela: str) -> list:
    """Lista as colunas de `tabela` no banco `base`, na ordem física (ORDINAL_POSITION)."""
    cursor = connection.cursor()
    cursor.execute(
        f"SELECT COLUMN_NAME FROM {quote_identifier(base)}.INFORMATION_SCHEMA.COLUMNS "
        f"WHERE TABLE_NAME = ? ORDER BY ORDINAL_POSITION",
        (tabela,),
    )
    return [row[0] for row in cursor.fetchall()]


def listar_colunas_de_varias_tabelas(connection, base: str, tabelas: list) -> dict:
    """Lista as colunas de várias tabelas de uma vez só (uma única consulta,
    com `WHERE TABLE_NAME IN (...)`) — usado quando todas as tabelas do
    banco modelo precisam ter suas colunas pré-carregadas de uma vez (ver
    CriarBasePanel._buscar_tabelas), evitando uma consulta por tabela.
    Retorna {tabela: [colunas na ordem física]}; tabelas sem nenhuma coluna
    encontrada (nome que não existe) não aparecem no resultado."""
    if not tabelas:
        return {}
    placeholders = ", ".join("?" for _ in tabelas)
    cursor = connection.cursor()
    cursor.execute(
        f"SELECT TABLE_NAME, COLUMN_NAME FROM {quote_identifier(base)}.INFORMATION_SCHEMA.COLUMNS "
        f"WHERE TABLE_NAME IN ({placeholders}) ORDER BY TABLE_NAME, ORDINAL_POSITION",
        tuple(tabelas),
    )
    resultado = {}
    for tabela, coluna in cursor.fetchall():
        resultado.setdefault(tabela, []).append(coluna)
    return resultado


def montar_copia_tabela(base_destino: str, base_modelo: str, tabela: str, colunas: list) -> str:
    """Monta um INSERT INTO ... SELECT ... pra copiar `colunas` de `tabela`
    do banco modelo pro banco novo. As duas bases precisam estar no MESMO
    servidor (sem linked server) — mesma limitação do 03_dados.sql. O alvo
    é totalmente qualificado (não depende de qual banco está "ativo" na
    conexão no momento da execução)."""
    colunas_sql = ", ".join(quote_identifier(c) for c in colunas)
    tabela_sql = quote_identifier(tabela)
    return (
        f"INSERT INTO {quote_identifier(base_destino)}.dbo.{tabela_sql} ({colunas_sql})\n"
        f"SELECT {colunas_sql} FROM {quote_identifier(base_modelo)}.dbo.{tabela_sql};"
    )
