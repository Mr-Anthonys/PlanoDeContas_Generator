"""Introspecção de schema (tabelas/colunas) do banco modelo, para a etapa
opcional de "Tabelas adicionais" na Criação de Base — cópia dinâmica de
tabelas/colunas escolhidas pelo usuário, além das ~15 tabelas fixas que
`resources/sql_templates/criar_base/03_dados.sql` já cobre (ver
criar_base_service.py). Só funciona quando a base modelo e a base nova
estão no MESMO servidor (sem linked server) — mesma limitação do
03_dados.sql.
"""

from src.utils.sql_escape import quote_identifier


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
