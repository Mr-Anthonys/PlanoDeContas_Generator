from src.models.account import Account, GenerationSettings
from src.services import sql_generator, validation_service


def _conta():
    return Account(linha=2, nome="CONTA TESTE", grupo="GRUPO A", conta_origem="1")


# ---------------------------------------------------------------------------
# Regime -> L_IRRF
# ---------------------------------------------------------------------------
def test_interino_gera_l_irrf_zero():
    settings = GenerationSettings(regime="Interino")
    assert settings.l_irrf == 0


def test_titular_gera_l_irrf_um():
    settings = GenerationSettings(regime="Titular")
    assert settings.l_irrf == 1


def test_l_irrf_no_sql_gerado_interino():
    settings = GenerationSettings(regime="Interino", historico_texto="TEXTO @", historico1="Qtd")
    resultado = sql_generator.generate_contas([_conta()], settings)
    assert ", 0, 0, 1)" in resultado.sql  # ...,L_IRRF=0,PDF=0,Ativa=1)


def test_l_irrf_no_sql_gerado_titular():
    settings = GenerationSettings(regime="Titular", historico_texto="TEXTO @", historico1="Qtd")
    resultado = sql_generator.generate_contas([_conta()], settings)
    assert ", 1, 0, 1)" in resultado.sql  # ...,L_IRRF=1,PDF=0,Ativa=1)


# ---------------------------------------------------------------------------
# Histórico: validação da quantidade de marcadores
# ---------------------------------------------------------------------------
def test_um_marcador_com_historico1_valido():
    settings = GenerationSettings(
        qtd_marcadores=1, historico_texto="EMOLUMENTOS RECEBIDOS - QTD DE ATOS @", historico1="Qtd", historico2=""
    )
    assert validation_service.validate_historico(settings) == []


def test_dois_marcadores_com_historico1_e_historico2_validos():
    settings = GenerationSettings(
        qtd_marcadores=2,
        historico_texto="EMOLUMENTOS RECEBIDOS - QTD DE ATOS @ PROTOCOLO: @",
        historico1="Qtd",
        historico2="LivroFolha",
    )
    assert validation_service.validate_historico(settings) == []


def test_bloqueio_quando_quantidade_de_marcadores_diverge():
    settings = GenerationSettings(qtd_marcadores=1, historico_texto="TEXTO @ @", historico1="Qtd")
    erros = validation_service.validate_historico(settings)
    assert any("marcador" in e.lower() for e in erros)


def test_bloqueio_historico2_vazio_com_dois_marcadores():
    settings = GenerationSettings(qtd_marcadores=2, historico_texto="TEXTO @ @", historico1="Qtd", historico2="")
    erros = validation_service.validate_historico(settings)
    assert any("Historico2" in e for e in erros)


def test_historico2_deve_ficar_vazio_com_um_marcador():
    settings = GenerationSettings(qtd_marcadores=1, historico_texto="TEXTO @", historico1="Qtd", historico2="LivroFolha")
    erros = validation_service.validate_historico(settings)
    assert any("Historico2" in e for e in erros)


def test_historico1_obrigatorio():
    settings = GenerationSettings(qtd_marcadores=1, historico_texto="TEXTO @", historico1="")
    erros = validation_service.validate_historico(settings)
    assert any("Historico1" in e for e in erros)


# ---------------------------------------------------------------------------
# Qtd/Protocolo/LivroFolha não substituem o @ em Contas.Histórico
# ---------------------------------------------------------------------------
def test_marcadores_nao_sao_substituidos_no_cadastro_de_contas():
    settings = GenerationSettings(
        qtd_marcadores=2,
        historico_texto="EMOLUMENTOS RECEBIDOS - QTD DE ATOS @ PROTOCOLO: @",
        historico1="Qtd",
        historico2="Protocolo",
    )
    resultado_contas = sql_generator.generate_contas([_conta()], settings)
    # O texto do histórico deve permanecer intacto, com os dois '@' literais.
    assert "EMOLUMENTOS RECEBIDOS - QTD DE ATOS @ PROTOCOLO: @" in resultado_contas.sql
    assert "Qtd" not in resultado_contas.sql
    assert "Protocolo" not in resultado_contas.sql

    resultado_historico = sql_generator.generate_interface_historico([_conta()], settings)
    # Já em InterfaceHistorico, Qtd/Protocolo aparecem como identificadores separados,
    # e o texto-base do histórico (com os marcadores '@') não é replicado aqui.
    assert "Qtd" in resultado_historico.sql
    assert "Protocolo" in resultado_historico.sql
    assert "EMOLUMENTOS RECEBIDOS - QTD DE ATOS @ PROTOCOLO: @" not in resultado_historico.sql
