from src.models.account import GenerationSettings
from src.services import validation_service
from src.services.excel_reader import RawRow
from src.services.reference_loader import load_reference_data


def _raw(linha, nome, grupo, conta_origem):
    return RawRow(linha, nome, grupo, conta_origem)


def test_nome_vazio_gera_erro():
    accounts = validation_service.validate_accounts([_raw(2, "", "GRUPO A", "1")])
    assert not accounts[0].valido
    assert "Nome" in accounts[0].situacao


def test_grupo_vazio_gera_erro():
    accounts = validation_service.validate_accounts([_raw(2, "CONTA A", "", "1")])
    assert not accounts[0].valido
    assert "Grupo" in accounts[0].situacao


def test_conta_origem_vazia_gera_erro():
    accounts = validation_service.validate_accounts([_raw(2, "CONTA A", "GRUPO A", "")])
    assert not accounts[0].valido
    assert "ContaOrigem" in accounts[0].situacao


def test_conta_origem_com_espaco_interno_invalida():
    accounts = validation_service.validate_accounts([_raw(2, "CONTA A", "GRUPO A", "1 2")])
    assert not accounts[0].valido


def test_nomes_duplicados_sao_marcados_e_nao_descartados():
    accounts = validation_service.validate_accounts([
        _raw(2, "CONTA X", "GRUPO A", "1"),
        _raw(3, "conta x", "GRUPO A", "2"),
    ])
    assert len(accounts) == 2
    assert not accounts[0].valido
    assert not accounts[1].valido
    assert "duplicado" in accounts[0].situacao.lower()


def test_nome_igual_em_grupos_diferentes_nao_e_duplicado():
    accounts = validation_service.validate_accounts([
        _raw(2, "CONTA X", "GRUPO A", "1"),
        _raw(3, "conta x", "GRUPO B", "2"),
    ])
    assert accounts[0].valido
    assert accounts[1].valido


def test_codigos_duplicados_sao_marcados():
    accounts = validation_service.validate_accounts([
        _raw(2, "CONTA A", "GRUPO A", "10"),
        _raw(3, "CONTA B", "GRUPO A", "10"),
    ])
    assert not accounts[0].valido
    assert not accounts[1].valido
    assert "ContaOrigem" in accounts[0].situacao


def test_duas_contas_distintas_mesmo_codigo_bloqueiam_geracao():
    accounts = validation_service.validate_accounts([
        _raw(2, "CONTA A", "GRUPO A", "5"),
        _raw(3, "CONTA B", "GRUPO B", "5"),
    ])
    assert validation_service.has_blocking_errors(accounts, [])


def test_conta_valida_nao_gera_erro():
    accounts = validation_service.validate_accounts([_raw(2, "CONTA A", "GRUPO A", "1")])
    assert accounts[0].valido
    assert accounts[0].situacao == "Válido"


def test_validate_settings_regime_invalido():
    reference = load_reference_data()
    settings = GenerationSettings(regime="Invalido", historico_texto="X @", historico1="Qtd")
    erros = validation_service.validate_settings(settings, reference)
    assert any("Regime" in e for e in erros)


def test_validate_settings_tipo_arq_vazio():
    reference = load_reference_data()
    settings = GenerationSettings(tipo_arq="", historico_texto="X @", historico1="Qtd")
    erros = validation_service.validate_settings(settings, reference)
    assert any("TipoArq" in e for e in erros)


def test_validate_settings_tipo_arq_fora_da_referencia_e_aceito():
    """TipoArq, InterfaceComum e InterfaceFormaPgto são texto livre: qualquer
    valor não vazio é aceito, mesmo sem corresponder a um modelo conhecido."""
    reference = load_reference_data()
    settings = GenerationSettings(
        tipo_arq="Modelo Personalizado", interface_comum="Modelo Personalizado",
        interface_forma_pgto="Modelo Personalizado", historico_texto="X @", historico1="Qtd",
    )
    erros = validation_service.validate_settings(settings, reference)
    assert erros == []


def test_validate_settings_ok():
    reference = load_reference_data()
    settings = GenerationSettings(
        regime="Titular", tipo_conta="Recebimento", tipo_arq="Emolumentos",
        interface_comum="Emolumentos", interface_forma_pgto="Emolumentos",
        qtd_marcadores=1, historico_texto="EMOLUMENTOS RECEBIDOS - QTD DE ATOS @", historico1="Qtd",
    )
    erros = validation_service.validate_settings(settings, reference)
    assert erros == []
