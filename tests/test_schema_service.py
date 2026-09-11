import os

from src.services import schema_service
from src.utils.constants import SQL_TEMPLATES_DIR


def test_listar_tabelas_monta_query_information_schema(fake_cursor, fake_connection):
    fake_cursor.description = [("TABLE_NAME",)]
    fake_cursor._rows = [("Contas",), ("GrupoContábil",)]

    tabelas = schema_service.listar_tabelas(fake_connection, "Gestor_Modelo")

    assert tabelas == ["Contas", "GrupoContábil"]
    assert "[Gestor_Modelo].INFORMATION_SCHEMA.TABLES" in fake_cursor.executed[0]
    assert "BASE TABLE" in fake_cursor.executed[0]


def test_listar_colunas_monta_query_information_schema(fake_cursor, fake_connection):
    fake_cursor.description = [("COLUMN_NAME",)]
    fake_cursor._rows = [("Nome",), ("GrupoContábil",)]

    colunas = schema_service.listar_colunas(fake_connection, "Gestor_Modelo", "Contas")

    assert colunas == ["Nome", "GrupoContábil"]
    assert "[Gestor_Modelo].INFORMATION_SCHEMA.COLUMNS" in fake_cursor.executed[0]
    assert "ORDINAL_POSITION" in fake_cursor.executed[0]


def test_listar_colunas_de_varias_tabelas_agrupa_por_tabela(fake_cursor, fake_connection):
    fake_cursor.description = [("TABLE_NAME",), ("COLUMN_NAME",)]
    fake_cursor._rows = [
        ("Bancos", "Codigo"), ("Bancos", "Nome"),
        ("Contas", "Nome"), ("Contas", "GrupoContábil"),
    ]

    resultado = schema_service.listar_colunas_de_varias_tabelas(fake_connection, "Gestor_Modelo", ["Bancos", "Contas"])

    assert resultado == {"Bancos": ["Codigo", "Nome"], "Contas": ["Nome", "GrupoContábil"]}
    assert "WHERE TABLE_NAME IN (?, ?)" in fake_cursor.executed[0]


def test_listar_colunas_de_varias_tabelas_lista_vazia_nao_executa(fake_cursor, fake_connection):
    resultado = schema_service.listar_colunas_de_varias_tabelas(fake_connection, "Gestor_Modelo", [])
    assert resultado == {}
    assert fake_cursor.executed == []


def test_montar_copia_tabela_gera_insert_select_qualificado():
    sql = schema_service.montar_copia_tabela("Gestor_Novo", "Gestor_Modelo", "Bancos", ["Codigo", "Nome"])

    assert "INSERT INTO [Gestor_Novo].dbo.[Bancos] ([Codigo], [Nome])" in sql
    assert "SELECT [Codigo], [Nome] FROM [Gestor_Modelo].dbo.[Bancos];" in sql


def test_montar_copia_tabela_escapa_colchete_no_nome_da_tabela():
    sql = schema_service.montar_copia_tabela("Gestor_Novo", "Gestor_Modelo", "Ta]bela", ["Col"])
    assert "[Ta]]bela]" in sql


def test_analisar_copia_fixa_de_dados_extrai_tabelas_e_colunas_do_script_real():
    caminho = os.path.join(SQL_TEMPLATES_DIR, "03_dados.sql")

    plano = schema_service.analisar_copia_fixa_de_dados(caminho)

    assert plano.tabelas_para_limpar == ["Resumo", "Lançamentos", "Lanca_exclui", "InterfaceDataArq"]
    por_destino = {t.tabela_destino: t for t in plano.tabelas}
    assert set(por_destino) == {
        "atualiza_redis_dash", "Bancos", "Contas", "DadosCartorio", "DadosIR", "DatabaseVersion",
        "Deducoes", "Flags", "GrupoContábil", "GrupoPortal", "InterfaceArq", "InterfaceComum",
        "InterfaceContas", "InterfaceFormaPgto", "InterfaceHistorico", "Relatório", "Resumo", "Usuário",
    }
    # "select * from Bancos" não enumera colunas -> colunas=None (fallback:
    # descobrir via listar_colunas em tempo de execução).
    assert por_destino["Bancos"].colunas is None
    assert por_destino["Bancos"].tabela_origem == "Bancos"
    # Coluna comentada ("--,Cartorio_id") não deve aparecer na lista.
    assert por_destino["Flags"].colunas == ["CampoI", "CampoV", "CampoU", "CampoB"]
    assert por_destino["Contas"].colunas == [
        "Nome", "GrupoContábil", "Histórico", "Tipo de Conta", "Forma de Transação", "LOficial",
        "LGerencial", "LContábil", "LDinheiro", "LParticular", "LPrévio", "LPortal", "L_IRRF", "PDF",
        "Ativa", "ContrProt", "CodGProt", "GrupoPortal", "CodAux",
    ]
