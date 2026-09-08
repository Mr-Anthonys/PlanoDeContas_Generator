"""Descoberta de clientes via o banco central Gestor_Parametros.

Replica o fluxo do Gestor Financeiro VB6 (`modBancoDeParametros.bas`): cada
máquina tem uma variável de ambiente GESTOR_PARAM com o endereço do servidor
SQL do banco central; a conexão a esse banco usa sempre o mesmo login fixo
(`Gestor_Parametros_Login`, não é por usuário); a partir dela lista-se
`Parametros_Clientes` para obter servidor/base/usuário/senha de cada cliente
e então conectar à base daquele cliente especificamente.
"""

import os

import pyodbc

from src.models.cliente_parametro import ClienteParametro
from src.services import db_connection_service as dbc
from src.services.db_connection_service import ConnectionSettings
from src.utils.constants import (
    GESTOR_PARAM_ENV_VAR,
    GESTOR_PARAMETROS_DATABASE,
    GESTOR_PARAMETROS_LOGIN,
    GESTOR_PARAMETROS_SENHA,
    TABELA_PARAMETROS_CLIENTES,
)

# Nome da coluna em Parametros_Clientes -> nome do campo em ClienteParametro.
_MAPA_COLUNAS = {
    "Nome": "nome",
    "Servidor": "servidor",
    "Banco": "banco",
    "Usuario": "usuario",
    "Senha": "senha",
    "DiretorioArquivo": "diretorio_arquivo",
    "Odbc": "odbc",
    "BrowserDashBoard": "browser_dashboard",
    "UrlDashboard": "url_dashboard",
    "UrlDashboardToken": "url_dashboard_token",
    "DiretorioMensalistas": "diretorio_mensalistas",
    "UrlValidacao": "url_validacao",
}


def servidor_parametros() -> str | None:
    """Servidor do banco central, lido da mesma variável de ambiente que o
    Gestor Financeiro VB6 usa (GESTOR_PARAM). None se não estiver definida
    nesta máquina."""
    valor = os.environ.get(GESTOR_PARAM_ENV_VAR, "").strip()
    return valor or None


def conectar_banco_parametros(servidor: str) -> pyodbc.Connection:
    """Abre conexão a Gestor_Parametros usando o login fixo do sistema
    (o mesmo usado pelo Gestor Financeiro VB6 — não é por usuário)."""
    cs = ConnectionSettings(
        servidor=servidor,
        usuario=GESTOR_PARAMETROS_LOGIN,
        senha=GESTOR_PARAMETROS_SENHA,
        database=GESTOR_PARAMETROS_DATABASE,
    )
    return dbc.connect(cs)


def _linha_para_cliente(colunas: list[str], valores) -> ClienteParametro:
    """Colunas são VARCHAR digitadas à mão por operadores em SSMS (via
    Script.txt / plano-contas-generator antigo); .strip() evita falha de
    login por espaço em branco invisível no fim do usuário/senha/servidor."""
    dados = {}
    for coluna, valor in zip(colunas, valores):
        campo = _MAPA_COLUNAS.get(coluna)
        if campo:
            dados[campo] = valor.strip() if isinstance(valor, str) else (valor or "")
    return ClienteParametro(**dados)


def listar_clientes(conn: pyodbc.Connection, nome: str | None = None) -> list[ClienteParametro]:
    """Lista os clientes cadastrados em Parametros_Clientes, ordenados por
    nome. Se `nome` for informado, filtra por esse cliente."""
    cursor = conn.cursor()
    sql = f"SELECT * FROM {TABELA_PARAMETROS_CLIENTES}"
    if nome:
        sql += " WHERE Nome = ?"
        cursor.execute(sql + " ORDER BY Nome", nome)
    else:
        cursor.execute(sql + " ORDER BY Nome")

    colunas = [coluna[0] for coluna in cursor.description]
    return [_linha_para_cliente(colunas, linha) for linha in cursor.fetchall()]


def conexao_para_cliente(cliente: ClienteParametro) -> ConnectionSettings:
    """Monta os dados de conexão à base do cliente a partir da linha de
    Parametros_Clientes (Servidor/Usuario/Senha/Banco daquele cliente)."""
    return ConnectionSettings(
        servidor=cliente.servidor,
        usuario=cliente.usuario,
        senha=cliente.senha,
        database=cliente.banco,
    )
