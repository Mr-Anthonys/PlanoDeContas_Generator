from src.services import criar_base_service
from src.services.criar_base_service import NovaBaseConfig, ProgressEvent
from src.services.db_connection_service import ConnectionSettings
from tests.conftest import FakeConnection, FakeCursor

PROD_CS = ConnectionSettings(servidor="prod-host", usuario="user_prod", senha="x")
DEV_CS = ConnectionSettings(servidor="dev-host", usuario="user_dev", senha="y")


def _config(cart_interino=False) -> NovaBaseConfig:
    return NovaBaseConfig(
        base_modelo="Gestor_SP_Modelo",
        base_nova="Gestor_SP_Teste",
        base_usuario="user_teste",
        base_senha="senha123",
        cart_interino=cart_interino,
        cart_id="1",
        cart_nome="CARTORIO TESTE",
        cart_cns="00.000-0",
        cart_cidade="TESTE",
        cart_estado="SP",
        cart_endereco="RUA X",
        cart_bairro="CENTRO",
        cart_cep="00000-000",
        cart_resp_nome="FULANO DE TAL",
        cart_resp_cpf="00000000000",
        cart_inicio="2026-01-01",
        cart_cnpj="00.000.000/0000-00",
        diretorio="C:\\ProPackages\\Arquivos\\Gestor_SP_Teste\\",
        odbc_dsn="ODBC_GF_SP_Teste",
        nome_dev="INR - Gestor_SP_Teste",
        diretorio_dev="C:\\ProPackages\\Clientes\\INR\\Arquivos\\Gestor_SP_Teste\\",
    )


def _patch_connect(monkeypatch, cursor_prod=None, cursor_dev=None):
    """Substitui db_connection_service.connect (visto de dentro de
    criar_base_service) por uma versão que devolve conexões falsas,
    registrando qual ConnectionSettings foi usada em cada chamada."""
    chamadas = []
    conn_prod = FakeConnection(cursor_prod or FakeCursor())
    conn_dev = FakeConnection(cursor_dev or FakeCursor())

    def _fake_connect(cs, autocommit=False):
        chamadas.append(cs)
        return conn_dev if cs is DEV_CS else conn_prod

    monkeypatch.setattr(criar_base_service.dbc, "connect", _fake_connect)
    return chamadas, conn_prod, conn_dev


def test_executar_criacao_base_happy_path_sem_interino(monkeypatch):
    chamadas, conn_prod, conn_dev = _patch_connect(monkeypatch)
    eventos = []

    resultado = criar_base_service.executar_criacao_base(PROD_CS, DEV_CS, _config(), eventos.append)

    assert resultado.sucesso is True
    assert resultado.passos_concluidos == [
        "schema", "usuario", "dados", "cartorio", "cartorio_id", "parametros_prod", "parametros_dev",
    ]
    assert chamadas == [PROD_CS, DEV_CS]
    assert conn_prod.closed is True
    assert conn_dev.closed is True
    assert any(e.kind == "all_done" for e in eventos)


def test_executar_criacao_base_interino_roda_passo_extra(monkeypatch):
    _patch_connect(monkeypatch)
    resultado = criar_base_service.executar_criacao_base(PROD_CS, DEV_CS, _config(cart_interino=True), lambda e: None)

    assert resultado.sucesso is True
    assert resultado.passos_concluidos == [
        "schema", "usuario", "dados", "cartorio", "cartorio_id",
        "parametros_prod", "interino", "parametros_dev",
    ]


def test_executar_criacao_base_para_no_primeiro_erro_e_nao_registra_dev(monkeypatch):
    # Falha simulada no lote de "04_cartorio.sql" (update DadosCartorio set),
    # depois de schema/usuario/dados já terem rodado com sucesso.
    cursor_prod = FakeCursor(fail_on_substring="DadosCartorio set")
    chamadas, conn_prod, conn_dev = _patch_connect(monkeypatch, cursor_prod=cursor_prod)
    eventos = []

    resultado = criar_base_service.executar_criacao_base(PROD_CS, DEV_CS, _config(), eventos.append)

    assert resultado.sucesso is False
    assert resultado.passo_falho == "cartorio"
    assert resultado.passos_concluidos == ["schema", "usuario", "dados"]
    assert "cartorio_id" not in resultado.passos_concluidos
    assert "parametros_prod" not in resultado.passos_concluidos
    assert "parametros_dev" not in resultado.passos_concluidos
    # A conexão de dev nunca deveria ter sido aberta: o registro em dev não
    # roda quando um passo de produção falha.
    assert DEV_CS not in chamadas
    assert conn_prod.closed is True
    # A conexão de dev nunca foi de fato aberta pelo serviço (só existe no
    # fixture do teste) — nunca chegou a ser fechada.
    assert conn_dev.closed is False
    assert any(e.kind == "step_error" and e.step_name == "cartorio" for e in eventos)


def test_executar_criacao_base_falha_de_conexao_reporta_erro(monkeypatch):
    def _fake_connect(cs, autocommit=False):
        raise RuntimeError("servidor inacessível")

    monkeypatch.setattr(criar_base_service.dbc, "connect", _fake_connect)
    eventos = []

    resultado = criar_base_service.executar_criacao_base(PROD_CS, DEV_CS, _config(), eventos.append)

    assert resultado.sucesso is False
    assert resultado.passo_falho == "conexao"
    assert resultado.passos_concluidos == []
