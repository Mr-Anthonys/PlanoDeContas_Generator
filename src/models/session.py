"""Estado da sessão conectada: credenciais + conexão viva + base ativa."""

from dataclasses import dataclass

import pyodbc

from src.services.db_connection_service import ConnectionSettings


@dataclass
class SessionContext:
    connection_settings: ConnectionSettings
    connection: pyodbc.Connection
    base_ativa: str
