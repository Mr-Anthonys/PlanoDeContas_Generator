from src.services import parametros_service
from src.services.db_connection_service import ConnectionSettings
from tests.conftest import FakeConnection, FakeCursor

COLUNAS = [
    "Nome", "Servidor", "Banco", "Usuario", "Senha", "DiretorioArquivo", "Odbc",
    "BrowserDashBoard", "UrlDashboard", "UrlDashboardToken", "DiretorioMensalistas", "UrlValidacao",
]


def _linha(nome, servidor="srv-1", banco=None):
    banco = banco or f"Gestor_{nome}"
    return (nome, servidor, banco, f"user_{nome}", "senha123", "C:\\Arq\\", "ODBC_X", "", "", "", "", "")


def test_servidor_parametros_le_variavel_de_ambiente(monkeypatch):
    monkeypatch.setenv("GESTOR_PARAM", "srv-parametros")
    assert parametros_service.servidor_parametros() == "srv-parametros"


def test_servidor_parametros_none_quando_variavel_ausente(monkeypatch):
    monkeypatch.delenv("GESTOR_PARAM", raising=False)
    assert parametros_service.servidor_parametros() is None


def test_servidor_parametros_none_quando_variavel_em_branco(monkeypatch):
    monkeypatch.setenv("GESTOR_PARAM", "   ")
    assert parametros_service.servidor_parametros() is None


def test_conectar_banco_parametros_usa_login_fixo(monkeypatch):
    capturado = {}

    def _fake_connect(cs, autocommit=False):
        capturado["cs"] = cs
        return FakeConnection()

    monkeypatch.setattr(parametros_service.dbc, "connect", _fake_connect)
    parametros_service.conectar_banco_parametros("srv-parametros")

    cs = capturado["cs"]
    assert cs.servidor == "srv-parametros"
    assert cs.usuario == "Gestor_Parametros_Login"
    assert cs.database == "Gestor_Parametros"


def test_listar_clientes_mapeia_colunas_para_cliente_parametro():
    cursor = FakeCursor(columns=COLUNAS, rows=[_linha("CONCHAS"), _linha("SP_MODELO")])
    conn = FakeConnection(cursor)

    clientes = parametros_service.listar_clientes(conn)

    assert [c.nome for c in clientes] == ["CONCHAS", "SP_MODELO"]
    assert clientes[0].servidor == "srv-1"
    assert clientes[0].banco == "Gestor_CONCHAS"
    assert clientes[0].usuario == "user_CONCHAS"
    assert clientes[0].senha == "senha123"
    assert "ORDER BY Nome" in cursor.executed[0]


def test_listar_clientes_remove_espacos_em_branco_das_credenciais():
    """Regressão: usuário/senha digitados à mão em SSMS às vezes carregam um
    espaço em branco no fim, o que faz o SQL Server rejeitar o login mesmo
    com a senha 'certa' visualmente."""
    linha = ("CONCHAS", "srv-1 ", "Gestor_CONCHAS", " user_CONCHAS", "senha123 ", "", "", "", "", "", "", "")
    cursor = FakeCursor(columns=COLUNAS, rows=[linha])
    conn = FakeConnection(cursor)

    cliente = parametros_service.listar_clientes(conn)[0]

    assert cliente.servidor == "srv-1"
    assert cliente.usuario == "user_CONCHAS"
    assert cliente.senha == "senha123"


def test_listar_clientes_filtra_por_nome_quando_informado():
    cursor = FakeCursor(columns=COLUNAS, rows=[_linha("CONCHAS")])
    conn = FakeConnection(cursor)

    clientes = parametros_service.listar_clientes(conn, nome="CONCHAS")

    assert len(clientes) == 1
    assert "WHERE Nome = ?" in cursor.executed[0]


def test_conexao_para_cliente_usa_dados_da_linha():
    cliente = parametros_service._linha_para_cliente(COLUNAS, _linha("CONCHAS", servidor="srv-conchas"))

    cs = parametros_service.conexao_para_cliente(cliente)

    assert cs == ConnectionSettings(
        servidor="srv-conchas", usuario="user_CONCHAS", senha="senha123", database="Gestor_CONCHAS",
    )
