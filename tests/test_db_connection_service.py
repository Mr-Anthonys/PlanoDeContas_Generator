from src.services import db_connection_service as dbc

DRIVER = "ODBC Driver 18 for SQL Server"


def test_build_connection_string_com_valores_simples():
    cs = dbc.ConnectionSettings(servidor="srv-1", usuario="user1", senha="senha123", database="Gestor_X")
    connection_string = dbc.build_connection_string(cs, DRIVER)

    assert connection_string == (
        f"DRIVER={{{DRIVER}}};SERVER={{srv-1}};DATABASE={{Gestor_X}};"
        "UID={user1};PWD={senha123};"
        "Encrypt=yes;TrustServerCertificate=yes;Connection Timeout=5"
    )


def test_build_connection_string_escapa_valores_com_ponto_e_virgula():
    """Reproduz o bug reportado: um valor (aqui, a senha) contendo ';' sem
    estar entre chaves quebra o parser da connection string e o driver
    retorna 'Invalid connection string attribute (0)'."""
    cs = dbc.ConnectionSettings(servidor="srv-1", usuario="user1", senha="a;b=c", database="Gestor_X")
    connection_string = dbc.build_connection_string(cs, DRIVER)

    assert "PWD={a;b=c}" in connection_string


def test_build_connection_string_escapa_chaves_internas():
    cs = dbc.ConnectionSettings(servidor="srv-1", usuario="user1", senha="a}b", database="Gestor_X")
    connection_string = dbc.build_connection_string(cs, DRIVER)

    assert "PWD={a}}b}" in connection_string
