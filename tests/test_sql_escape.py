from src.utils.sql_escape import quote_identifier


def test_quote_identifier_simples():
    assert quote_identifier("Gestor_SP_Teste") == "[Gestor_SP_Teste]"


def test_quote_identifier_com_espaco():
    assert quote_identifier("Gestor SP Teste") == "[Gestor SP Teste]"


def test_quote_identifier_escapa_colchete_fechando_interno():
    assert quote_identifier("Gestor]Estranho") == "[Gestor]]Estranho]"
