"""Funções utilitárias para escapar e formatar valores em comandos SQL Server."""


def escape_sql_string(texto: str) -> str:
    """Escapa apóstrofos duplicando-os, conforme exigido pelo T-SQL.

    Exemplo: OFÍCIO D'ÁGUA -> OFÍCIO D''ÁGUA
    """
    if texto is None:
        return ""
    return str(texto).replace("'", "''")


def sql_string(texto: str) -> str:
    """Monta um literal string Unicode N'...' com apóstrofos escapados."""
    return f"N'{escape_sql_string(texto)}'"


def sql_string_ascii(texto: str) -> str:
    """Monta um literal string comum '...' (sem prefixo N) com apóstrofos escapados.

    Usado para valores de configuração que não exigem Unicode explícito, mantendo
    compatibilidade com o padrão observado nas planilhas de referência.
    """
    return f"'{escape_sql_string(texto)}'"


def sql_number(valor) -> str:
    """Formata um valor numérico para uso direto (sem aspas) no SQL."""
    return str(valor)


def quote_identifier(nome: str) -> str:
    """Coloca um identificador T-SQL (nome de tabela/base/coluna) entre
    colchetes, dobrando ']' internos — mesma regra de quoting de
    identificadores do SQL Server. Usado para montar `USE [base];` com o
    nome exato da base ativa da sessão."""
    return f"[{str(nome).replace(']', ']]')}]"
