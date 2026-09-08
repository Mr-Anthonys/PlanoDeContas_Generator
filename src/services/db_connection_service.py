"""Conexão com o SQL Server via pyodbc.

Usado tanto pela tela de login (conectar + escolher a "base ativa") quanto
pela Criação de Base (conectar aos servidores de produção/dev para
provisionar um cliente novo). `listar_bases_gestor` é a mesma função nos
dois casos — só muda a conexão/servidor usado para chamá-la.
"""

from dataclasses import dataclass

import pyodbc

from src.utils.constants import GESTOR_DB_PREFIX


@dataclass
class ConnectionSettings:
    servidor: str
    usuario: str
    senha: str
    database: str = "master"
    timeout: int = 5


def driver_disponivel() -> str | None:
    """Retorna o nome do driver ODBC do SQL Server mais recente instalado,
    ou None se nenhum estiver disponível."""
    candidatos = [d for d in pyodbc.drivers() if "ODBC Driver" in d and "SQL Server" in d]
    return sorted(candidatos, reverse=True)[0] if candidatos else None


def _quote(valor: str) -> str:
    """Embrulha um valor de atributo ODBC entre chaves, dobrando `}` internos.

    Necessário porque servidor/usuário/senha vêm de fontes externas (linha de
    Parametros_Clientes, digitação manual) que podem conter `;`, `=`, `{` ou
    `}` — sem as chaves, esses caracteres quebram o parser da connection
    string e o driver retorna 'Invalid connection string attribute (0)'."""
    return "{" + str(valor).replace("}", "}}") + "}"


def build_connection_string(cs: ConnectionSettings, driver: str) -> str:
    return (
        f"DRIVER={{{driver}}};SERVER={_quote(cs.servidor)};DATABASE={_quote(cs.database)};"
        f"UID={_quote(cs.usuario)};PWD={_quote(cs.senha)};"
        f"Encrypt=yes;TrustServerCertificate=yes;Connection Timeout={cs.timeout}"
    )


def connect(cs: ConnectionSettings, autocommit: bool = False) -> pyodbc.Connection:
    driver = driver_disponivel()
    if driver is None:
        raise RuntimeError(
            "Nenhum driver ODBC do SQL Server encontrado nesta máquina. "
            "Instale o 'ODBC Driver 17' ou '18 for SQL Server' da Microsoft."
        )
    return pyodbc.connect(build_connection_string(cs, driver), autocommit=autocommit)


def test_connection(cs: ConnectionSettings) -> tuple[bool, str]:
    try:
        conn = connect(cs)
        conn.close()
        return True, "Conexão bem-sucedida."
    except Exception as exc:
        return False, str(exc)


def listar_bases_gestor(conn: pyodbc.Connection, prefixo: str = GESTOR_DB_PREFIX) -> list[str]:
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sys.databases WHERE name LIKE ? ORDER BY name", f"{prefixo}%")
    return [row[0] for row in cursor.fetchall()]


def close(conn: pyodbc.Connection | None) -> None:
    if conn is None:
        return
    try:
        conn.close()
    except Exception:
        pass
