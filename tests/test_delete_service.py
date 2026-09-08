from src.models.account import Account, GenerationSettings
from src.services import delete_service


def _settings(**overrides):
    base = dict(
        regime="Titular", tipo_conta="Recebimento", tipo_arq="Emolumentos",
        interface_comum="Emolumentos", interface_forma_pgto="Emolumentos",
        qtd_marcadores=1, historico_texto="", historico1="", historico2="",
    )
    base.update(overrides)
    return GenerationSettings(**base)


def _contas():
    return [
        Account(linha=2, nome="CONTA A", grupo="TABELIONATO DE NOTAS", conta_origem="1"),
        Account(linha=3, nome="CONTA B", grupo="PROTESTO", conta_origem="2"),
    ]


def test_montar_consultas_gera_as_7_tabelas_na_ordem():
    consultas = delete_service.montar_consultas(_contas(), _settings())
    assert [c.chave for c in consultas] == [
        "contas", "grupo_contabil", "interface_contas", "interface_arq",
        "interface_comum", "interface_forma_pgto", "interface_historico",
    ]


def test_consulta_contas_filtra_por_tipo_de_conta_e_exclui_remuneracao():
    consulta = delete_service.montar_consultas(_contas(), _settings())[0]
    assert "[Tipo de Conta] = ?" in consulta.sql
    assert "Nome NOT LIKE ?" in consulta.sql
    assert consulta.parametros == ("Recebimento", "%REMUNERAÇÃO%")


def test_consulta_grupo_contabil_usa_grupos_distintos_da_planilha():
    consulta = delete_service.montar_consultas(_contas(), _settings())[1]
    assert "Nome IN (?, ?)" in consulta.sql
    assert consulta.parametros == ("TABELIONATO DE NOTAS", "PROTESTO")


def test_consulta_grupo_contabil_sem_contas_nao_gera_sql():
    consulta = delete_service.montar_consultas([], _settings())[1]
    assert consulta.sql == ""
    assert consulta.parametros == ()


def test_consultas_compartilhadas_marcadas():
    consultas = {c.chave: c for c in delete_service.montar_consultas(_contas(), _settings())}
    assert consultas["interface_arq"].compartilhada is True
    assert consultas["interface_comum"].compartilhada is True
    assert consultas["interface_forma_pgto"].compartilhada is True
    assert consultas["contas"].compartilhada is False
    assert consultas["interface_historico"].compartilhada is False


def test_executar_consultas_preenche_colunas_e_linhas(fake_cursor, fake_connection):
    fake_cursor.description = [("Nome",), ("GrupoContábil",)]
    fake_cursor._rows = [("CONTA A", "PROTESTO")]
    consultas = [delete_service.montar_consultas(_contas(), _settings())[0]]

    resultados = delete_service.executar_consultas(fake_connection, consultas)

    assert len(resultados) == 1
    assert resultados[0].colunas == ["Nome", "GrupoContábil"]
    assert resultados[0].linhas == [{"Nome": "CONTA A", "GrupoContábil": "PROTESTO"}]
    assert resultados[0].erro == ""


def test_executar_consultas_sem_sql_nao_executa_nada(fake_connection):
    consulta = delete_service.montar_consultas([], _settings())[1]  # grupo_contabil sem SQL
    resultados = delete_service.executar_consultas(fake_connection, [consulta])
    assert resultados[0].linhas == []
    assert resultados[0].erro == ""


def test_executar_consultas_registra_erro_sem_derrubar_as_outras(fake_connection):
    fake_connection._cursor.fail_on_call = 1
    consulta = delete_service.montar_consultas(_contas(), _settings())[0]
    resultados = delete_service.executar_consultas(fake_connection, [consulta])
    assert resultados[0].erro != ""
    assert resultados[0].linhas == []


def test_montar_script_exclusao_gera_um_delete_por_item_numa_transacao():
    itens = [
        ("[dbo].[Contas]", ("Nome",), {"Nome": "CONTA A"}),
        ("[dbo].[GrupoContábil]", ("Nome",), {"Nome": "PROTESTO"}),
    ]
    script = delete_service.montar_script_exclusao(itens)
    assert "BEGIN TRANSACTION" in script
    assert "COMMIT" in script
    assert "ROLLBACK" in script
    assert "DELETE FROM [dbo].[Contas] WHERE [Nome] = N'CONTA A';" in script
    assert "DELETE FROM [dbo].[GrupoContábil] WHERE [Nome] = N'PROTESTO';" in script


def test_montar_script_exclusao_combina_colunas_chave_compostas():
    itens = [("[dbo].[InterfaceContas]", ("ContaOrigem", "TipoArq"), {"ContaOrigem": "27", "TipoArq": "Emolumentos"})]
    script = delete_service.montar_script_exclusao(itens)
    assert "WHERE [ContaOrigem] = N'27' AND [TipoArq] = N'Emolumentos';" in script


def test_montar_script_exclusao_trata_valor_nulo():
    itens = [("[dbo].[Contas]", ("Nome",), {"Nome": None})]
    script = delete_service.montar_script_exclusao(itens)
    assert "[Nome] IS NULL" in script


def test_montar_script_exclusao_sem_base_ativa_nao_tem_use():
    itens = [("[dbo].[Contas]", ("Nome",), {"Nome": "CONTA A"})]
    script = delete_service.montar_script_exclusao(itens)
    assert "USE " not in script


def test_montar_script_exclusao_com_base_ativa_adiciona_use_no_topo():
    itens = [("[dbo].[Contas]", ("Nome",), {"Nome": "CONTA A"})]
    script = delete_service.montar_script_exclusao(itens, base_ativa="Gestor_SP_Teste")
    assert script.startswith("USE [Gestor_SP_Teste];")
    # o USE precisa vir antes do DELETE no texto
    assert script.index("USE [Gestor_SP_Teste]") < script.index("DELETE FROM")


def test_montar_script_exclusao_escapa_colchete_no_nome_da_base():
    itens = [("[dbo].[Contas]", ("Nome",), {"Nome": "CONTA A"})]
    script = delete_service.montar_script_exclusao(itens, base_ativa="Gestor]Estranho")
    assert "USE [Gestor]]Estranho];" in script


def test_executar_script_roda_o_texto_recebido_sem_alteracao(fake_cursor, fake_connection):
    delete_service.executar_script(fake_connection, "USE [Base];\nDELETE FROM X;")
    assert fake_cursor.executed == ["USE [Base];\nDELETE FROM X;"]


def test_executar_exclusoes_roda_o_script_como_um_unico_lote(fake_cursor, fake_connection):
    itens = [("[dbo].[Contas]", ("Nome",), {"Nome": "CONTA A"})]
    total = delete_service.executar_exclusoes(fake_connection, itens)
    assert total == 1
    assert len(fake_cursor.executed) == 1
    assert "DELETE FROM [dbo].[Contas]" in fake_cursor.executed[0]


def test_executar_exclusoes_com_base_ativa_inclui_use_no_lote_executado(fake_cursor, fake_connection):
    itens = [("[dbo].[Contas]", ("Nome",), {"Nome": "CONTA A"})]
    delete_service.executar_exclusoes(fake_connection, itens, base_ativa="Gestor_SP_Teste")
    assert fake_cursor.executed[0].startswith("USE [Gestor_SP_Teste];")


def test_executar_exclusoes_sem_itens_nao_executa(fake_cursor, fake_connection):
    total = delete_service.executar_exclusoes(fake_connection, [])
    assert total == 0
    assert fake_cursor.executed == []
