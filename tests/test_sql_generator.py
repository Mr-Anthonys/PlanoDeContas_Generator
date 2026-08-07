import re

from src.models.account import Account, GenerationSettings
from src.services import sql_generator
from src.services.reference_loader import load_reference_data


def _settings(**overrides):
    base = dict(
        regime="Titular", tipo_conta="Recebimento", tipo_arq="Emolumentos",
        interface_comum="Emolumentos", interface_forma_pgto="Emolumentos",
        qtd_marcadores=1, historico_texto="EMOLUMENTOS RECEBIDOS - QTD DE ATOS @", historico1="Qtd", historico2="",
    )
    base.update(overrides)
    return GenerationSettings(**base)


def test_nome_com_apostrofo_e_escapado():
    conta = Account(linha=2, nome="OFÍCIO D'ÁGUA", grupo="GRUPO A", conta_origem="1")
    resultado = sql_generator.generate_contas([conta], _settings())
    assert "OFÍCIO D''ÁGUA" in resultado.sql
    assert "D'ÁGUA'," not in resultado.sql  # não pode haver aspa não escapada seguida de vírgula


def test_nome_com_acento_preservado():
    conta = Account(linha=2, nome="AUTENTICAÇÃO", grupo="GRUPO A", conta_origem="1")
    resultado = sql_generator.generate_contas([conta], _settings())
    assert "AUTENTICAÇÃO" in resultado.sql
    assert "N'AUTENTICAÇÃO'" in resultado.sql


def test_grupo_repetido_gera_um_unico_grupo_portal_e_contabil():
    contas = [
        Account(linha=2, nome="CONTA A", grupo="TABELIONATO DE NOTAS", conta_origem="1"),
        Account(linha=3, nome="CONTA B", grupo="TABELIONATO DE NOTAS", conta_origem="2"),
        Account(linha=4, nome="CONTA C", grupo="tabelionato de notas", conta_origem="3"),
    ]
    grupo_portal = sql_generator.generate_grupo_portal(contas)
    grupo_contabil = sql_generator.generate_grupo_contabil(contas)
    assert grupo_portal.quantidade == 1
    assert grupo_contabil.quantidade == 1
    assert grupo_portal.sql.count("INSERT INTO") == 1
    assert grupo_contabil.sql.count("INSERT INTO") == 1


def test_grupos_distintos_geram_registros_distintos():
    contas = [
        Account(linha=2, nome="CONTA A", grupo="TABELIONATO DE NOTAS", conta_origem="1"),
        Account(linha=3, nome="CONTA B", grupo="PROTESTO", conta_origem="2"),
    ]
    grupo_portal = sql_generator.generate_grupo_portal(contas)
    assert grupo_portal.quantidade == 2
    assert "TABELIONATO DE NOTAS" in grupo_portal.sql
    assert "PROTESTO" in grupo_portal.sql


def test_grupo_portal_bug_de_apostrofo_esta_corrigido():
    contas = [Account(linha=2, nome="CONTA A", grupo="TABELIONATO DE NOTAS", conta_origem="1")]
    resultado = sql_generator.generate_grupo_portal(contas)
    # O bug original gerava "...,0')" (apóstrofo indevido após o número). Confirmamos que não existe.
    assert not re.search(r",\s*0'\)", resultado.sql)
    assert ", 0)" in resultado.sql


def test_conta_origem_gerada_como_string_entre_aspas():
    conta = Account(linha=2, nome="CONTA A", grupo="GRUPO A", conta_origem="27")
    resultado = sql_generator.generate_interface_contas([conta], _settings())
    assert "N'27'" in resultado.sql


def test_conta_origem_preserva_zeros_a_esquerda():
    conta = Account(linha=2, nome="CONTA A", grupo="GRUPO A", conta_origem="007")
    resultado = sql_generator.generate_interface_contas([conta], _settings())
    assert "N'007'" in resultado.sql


def test_sem_virgula_final_invalida():
    conta = Account(linha=2, nome="CONTA A", grupo="GRUPO A", conta_origem="1")
    resultado = sql_generator.generate_contas([conta], _settings())
    assert ",)" not in resultado.sql
    assert ", )" not in resultado.sql


def test_sem_aspas_excedentes():
    conta = Account(linha=2, nome="CONTA A", grupo="GRUPO A", conta_origem="1")
    resultado = sql_generator.generate_contas([conta], _settings())
    # cada literal N'...' deve ter um número par de apóstrofos
    assert resultado.sql.count("'") % 2 == 0


def test_processos_sao_independentes_entre_si():
    """Cada processo deve poder ser executado isoladamente: não deve haver
    referência a variáveis @variavel declaradas fora do próprio script, nem
    dependência de IDENTITY/SCOPE_IDENTITY()."""
    conta = Account(linha=2, nome="CONTA A", grupo="GRUPO A", conta_origem="1")
    settings = _settings()
    reference = load_reference_data()
    resultados = sql_generator.generate_all([conta], settings, reference)
    for resultado in resultados:
        assert "DECLARE @" not in resultado.sql
        assert "SCOPE_IDENTITY" not in resultado.sql
        assert "IDENTITY" not in resultado.sql


def test_interface_contas_nao_usa_identity_nem_consulta_por_nome():
    conta = Account(linha=2, nome="CONTA A", grupo="GRUPO A", conta_origem="42")
    resultado = sql_generator.generate_interface_contas([conta], _settings())
    assert "SELECT Codigo" not in resultado.sql
    assert "N'42'" in resultado.sql


def test_script_completo_contem_todos_os_processos_com_separadores():
    conta = Account(linha=2, nome="CONTA A", grupo="GRUPO A", conta_origem="1")
    settings = _settings()
    reference = load_reference_data()
    script = sql_generator.generate_full_script([conta], settings, reference)
    for titulo in ["CONTAS", "GRUPOPORTAL", "GRUPOCONTÁBIL", "INTERFACECONTAS", "INTERFACEHISTORICO",
                   "INTERFACEARQ", "INTERFACECOMUM", "INTERFACEFORMAPGTO"]:
        assert titulo in script.upper()
    assert script.count("BEGIN TRY") == 8
