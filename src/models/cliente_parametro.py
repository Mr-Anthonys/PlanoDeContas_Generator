"""Uma linha de Gestor_Parametros.Parametros_Clientes: os dados de conexão
de um cliente cadastrados centralmente (mesma tabela que o Gestor Financeiro
VB6 usa para popular a tela de seleção de base)."""

from dataclasses import dataclass


@dataclass
class ClienteParametro:
    nome: str
    servidor: str
    banco: str
    usuario: str
    senha: str
    diretorio_arquivo: str = ""
    odbc: str = ""
    browser_dashboard: str = ""
    url_dashboard: str = ""
    url_dashboard_token: str = ""
    diretorio_mensalistas: str = ""
    url_validacao: str = ""
