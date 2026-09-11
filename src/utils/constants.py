"""Constantes de negócio: nomes reais de tabelas/colunas e valores padrão.

Os nomes e a ordem das colunas foram confirmados por análise célula a célula das
planilhas de referência (PLANO DE CONTAS - RECEITAS.xlsx e Plano de Contas
Receitas - Conchas.xlsx). Ver README.md para o detalhamento das regras.
"""

import os
import sys

if getattr(sys, "frozen", False):
    # Executável gerado pelo PyInstaller: o config.json vive ao lado do .exe,
    # e não dentro do pacote temporário extraído em tempo de execução, para
    # que ele possa ser editado e persistido pelo usuário entre execuções.
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

CONFIG_PATH = os.path.join(BASE_DIR, "config.json")


def resource_path(*parts) -> str:
    """Caminho para recursos somente-leitura empacotados pelo PyInstaller
    (sys._MEIPASS quando congelado). Diferente de BASE_DIR: BASE_DIR é a
    pasta do .exe, editável pelo usuário (config.json); resource_path() é a
    pasta temporária de extração, read-only, para arquivos adicionados via
    --add-data (ex.: os templates .sql de Criação de Base)."""
    if getattr(sys, "frozen", False):
        base = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    else:
        base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base, *parts)


SQL_TEMPLATES_DIR = resource_path("resources", "sql_templates", "criar_base")
GESTOR_DB_PREFIX = "Gestor_"

# ---------------------------------------------------------------------------
# Banco central de parâmetros (Gestor_Parametros / Parametros_Clientes)
#
# Mesmo fluxo usado pelo Gestor Financeiro VB6 (modBancoDeParametros.bas):
# cada máquina tem uma variável de ambiente GESTOR_PARAM apontando para o
# servidor SQL do banco central; a conexão a esse banco usa sempre o mesmo
# login fixo (não é por usuário); a partir dele lista-se Parametros_Clientes
# para obter servidor/base/usuário/senha de cada cliente.
# ---------------------------------------------------------------------------
GESTOR_PARAM_ENV_VAR = "GESTOR_PARAM"
GESTOR_PARAMETROS_DATABASE = "Gestor_Parametros"
GESTOR_PARAMETROS_LOGIN = "Gestor_Parametros_Login"
GESTOR_PARAMETROS_SENHA = "OTqzUdjX8YNiXh71Rzv/gXx9q6o6OP3uRGsaCzJ5l2A="
TABELA_PARAMETROS_CLIENTES = "Parametros_Clientes"

# Servidor próprio da Pro-Packages ("ServidorPP") — endereço fixo oferecido
# como opção de hospedagem na Criação de Base (etapa Parametros_Clientes) e
# sempre um dos alvos possíveis de registro, independente de onde a base do
# cliente física está.
SERVIDOR_PP = "100.77.102.1,1435"

REGIME_INTERINO = "Interino"
REGIME_TITULAR = "Titular"
REGIMES = [REGIME_INTERINO, REGIME_TITULAR]

MARCADOR = "@"

# ---------------------------------------------------------------------------
# Contas
# ---------------------------------------------------------------------------
TABELA_CONTAS = "[dbo].[Contas]"
COLUNAS_CONTAS = [
    "Nome", "GrupoContábil", "Histórico", "Tipo de Conta", "Forma de Transação",
    "LOficial", "LGerencial", "LContábil", "LDinheiro", "LParticular",
    "LPrévio", "LPortal", "GrupoPortal", "L_IRRF", "PDF", "Ativa",
]

CONTAS_PADRAO = {
    "forma_transacao": "Vários",
    "l_oficial": 1,
    "l_gerencial": 0,
    "l_contabil": 0,
    "l_dinheiro": 0,
    "l_particular": 0,
    "l_portal": 1,
    "pdf": 0,
    "ativa": 1,
}

# ---------------------------------------------------------------------------
# GrupoPortal / GrupoContábil
# ---------------------------------------------------------------------------
TABELA_GRUPO_PORTAL = "[dbo].[GrupoPortal]"
COLUNAS_GRUPO_PORTAL = ["NomeGrupo", "TipoGrupo"]
GRUPO_PORTAL_TIPO_GRUPO_PADRAO = 0

TABELA_GRUPO_CONTABIL = "[dbo].[GrupoContábil]"
COLUNAS_GRUPO_CONTABIL = ["Nome"]

# ---------------------------------------------------------------------------
# InterfaceContas
# ---------------------------------------------------------------------------
TABELA_INTERFACE_CONTAS = "[dbo].[InterfaceContas]"
COLUNAS_INTERFACE_CONTAS = ["ContaSGF", "ContaOrigem", "TipoArq"]

# ---------------------------------------------------------------------------
# InterfaceHistorico
# ---------------------------------------------------------------------------
TABELA_INTERFACE_HISTORICO = "[dbo].[InterfaceHistorico]"

# As 5 colunas dinâmicas (variam por conta) + as 37 colunas fixas confirmadas
# na planilha real (sempre 0 ou '' no processo manual atual). Historico3 é
# dinâmica (e não fixa) para suportar o terceiro marcador '@' no histórico.
COLUNAS_INTERFACE_HISTORICO_DINAMICAS = ["ContaOrigem", "Historico1", "Historico2", "Historico3", "TipoArq"]

COLUNAS_INTERFACE_HISTORICO_FIXAS_NUMERICAS = [
    "HistIni1", "HistTam1", "HistFim1",
    "HistIni2", "HistTam2", "HistFim2",
    "HistIni3", "HistTam3", "HistFim3",
    "HistIni4", "HistTam4", "HistFim4",
    "HistIni5", "HistTam5", "HistFim5",
    "HistIni6", "HistTam6", "HistFim6",
    "HistIni7", "HistTam7", "HistFim7",
    "HistIni8", "HistTam8", "HistFim8",
]

COLUNAS_INTERFACE_HISTORICO_FIXAS_TEXTO = [
    "Precedente1", "Precedente2", "Precedente3",
    "Precedente4", "Historico4", "Precedente5", "Historico5",
    "Precedente6", "Historico6", "Precedente7", "Historico7",
    "Precedente8", "Historico8",
]

COLUNAS_INTERFACE_HISTORICO = (
    COLUNAS_INTERFACE_HISTORICO_DINAMICAS
    + COLUNAS_INTERFACE_HISTORICO_FIXAS_NUMERICAS
    + COLUNAS_INTERFACE_HISTORICO_FIXAS_TEXTO
)

# ---------------------------------------------------------------------------
# InterfaceArq
# ---------------------------------------------------------------------------
TABELA_INTERFACE_ARQ = "[dbo].[InterfaceArq]"
COLUNAS_INTERFACE_ARQ = [
    "NomeTipo", "Extensão", "FormaColunas", "LocalArquivos", "Linha1", "LinhaF",
    "LimpaCol", "Cab_Ult_Col", "Cab_Ult_Text", "Rod_Pri_Col", "Rod_Pri_Text",
    "InterfaceInicial", "Cab_Ult_Oco", "Rod_Pri_Oco", "InterfaceEntrManual",
]
# Mapeia nome da coluna SQL -> chave usada no config.json (ignora acentos)
CAMPOS_INTERFACE_ARQ_CONFIG = {
    "NomeTipo": "NomeTipo",
    "Extensão": "Extensao",
    "FormaColunas": "FormaColunas",
    "LocalArquivos": "LocalArquivos",
    "Linha1": "Linha1",
    "LinhaF": "LinhaF",
    "LimpaCol": "LimpaCol",
    "Cab_Ult_Col": "Cab_Ult_Col",
    "Cab_Ult_Text": "Cab_Ult_Text",
    "Rod_Pri_Col": "Rod_Pri_Col",
    "Rod_Pri_Text": "Rod_Pri_Text",
    "InterfaceInicial": "InterfaceInicial",
    "Cab_Ult_Oco": "Cab_Ult_Oco",
    "Rod_Pri_Oco": "Rod_Pri_Oco",
    "InterfaceEntrManual": "InterfaceEntrManual",
}
INTERFACE_ARQ_COLUNAS_TEXTO = {"NomeTipo", "Extensão", "FormaColunas", "LocalArquivos", "Cab_Ult_Text", "Rod_Pri_Text"}

# ---------------------------------------------------------------------------
# InterfaceComum
# ---------------------------------------------------------------------------
TABELA_INTERFACE_COMUM = "[dbo].[InterfaceComum]"
COLUNAS_INTERFACE_COMUM = [
    "LocalCodigo", "LocalDataMovimento", "LocalValor", "LocalForma", "LocalAtos",
    "LocalVlBruto", "LocalEstado", "LocalIPESP", "LocalStaCasa", "LocalRegCivil",
    "LocalTribunal", "TipoArq", "LocalISS", "LocalMP", "LocalEdital",
    "LocalIntimacao", "LocalTelegrama", "LocalProtocolo",
]

# ---------------------------------------------------------------------------
# InterfaceFormaPgto
# ---------------------------------------------------------------------------
TABELA_INTERFACE_FORMA_PGTO = "[dbo].[InterfaceFormaPgto]"
COLUNAS_INTERFACE_FORMA_PGTO = [
    "FormaSist", "FormaSGF", "BcoSGF", "CCNumSGF", "TipoArq",
    "ChequeSGF", "ChequeSGFIni", "ChequeSGFTam", "ChequeSGFFim",
]
INTERFACE_FORMA_PGTO_COLUNAS_TEXTO = {"FormaSist", "FormaSGF", "BcoSGF", "CCNumSGF", "TipoArq", "ChequeSGF"}

# ---------------------------------------------------------------------------
# Cabeçalhos aceitos na planilha de importação (normalizados para minúsculas
# sem espaços/acentos na comparação, ver excel_reader.py)
# ---------------------------------------------------------------------------
CABECALHOS_NOME = ["nome", "nome da conta", "conta", "nome do ato"]
CABECALHOS_GRUPO = ["grupo", "grupo contábil", "grupocontábil", "nomegrupo"]
CABECALHOS_CONTA_ORIGEM = [
    "contaorigem", "conta origem", "código", "codigo",
    "código da conta", "codigo da conta", "codconta",
]
