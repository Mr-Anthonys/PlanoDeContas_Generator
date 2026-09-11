from src.services import criar_base_service
from src.services.criar_base_service import (
    AlvoParametros, NovaBaseConfig, ParametrosClienteConfig, PlanoProvisionamento, ProgressEvent, TabelaExtra,
)
from src.services.db_connection_service import ConnectionSettings
from tests.conftest import FakeConnection, FakeCursor

MODELO_CS = ConnectionSettings(servidor="prod-host", usuario="user_modelo", senha="x")
DESTINO_CS = ConnectionSettings(servidor="prod-host", usuario="user_destino", senha="y")  # mesmo servidor do modelo
DESTINO_OUTRO_SERVIDOR_CS = ConnectionSettings(servidor="outro-host", usuario="user_destino", senha="y")
PP_CS = ConnectionSettings(servidor="100.77.102.1,1435", usuario="user_pp", senha="z")


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
    )


def _parametros_cfg() -> ParametrosClienteConfig:
    return ParametrosClienteConfig(
        nome="INR - Gestor_SP_Teste",
        servidor="100.77.102.1,1435",
        banco="Gestor_SP_Teste",
        usuario="user_teste",
        senha="senha123",
        diretorio_arquivo="C:\\ProPackages\\Arquivos\\Gestor_SP_Teste\\",
        odbc="DSN=ODBC_GF_INR;UID=user_teste;PWD=senha123;",
        browser_dashboard="CHROME",
        url_dashboard="https://dashboard-frontend-masterr.herokuapp.com/",
        url_dashboard_token="https://dashboard-frontend-masterr.herokuapp.com/",
        diretorio_mensalistas="C:\\ProPackages\\Mensalistas\\Propackage.Gestor.UI.exe",
        url_validacao="",
        url_gestor_clientes="https://gestor-clientes-git-main-propackages-projects.vercel.app/api/notaries/",
    )


def _plano(modelo_cs=MODELO_CS, destino_cs=DESTINO_CS, tabelas_extras=None, parametros_alvos=None, cart_interino=False):
    if parametros_alvos is None:
        parametros_alvos = [AlvoParametros("destino", "servidor de destino", destino_cs)]
    return PlanoProvisionamento(
        modelo_cs=modelo_cs,
        destino_cs=destino_cs,
        cfg=_config(cart_interino=cart_interino),
        tabelas_extras=tabelas_extras or [],
        parametros_cfg=_parametros_cfg(),
        parametros_alvos=parametros_alvos,
    )


def _patch_connect(monkeypatch, cursores_por_servidor=None):
    """Substitui db_connection_service.connect (visto de dentro de
    criar_base_service) por uma versão que devolve conexões falsas por
    servidor, registrando qual ConnectionSettings foi usada em cada chamada."""
    cursores_por_servidor = cursores_por_servidor or {}
    chamadas = []
    conexoes = {}

    def _fake_connect(cs, autocommit=False):
        chamadas.append(cs)
        chave = cs.servidor.strip().lower()
        if chave not in conexoes:
            cursor = cursores_por_servidor.get(chave, FakeCursor())
            conexoes[chave] = FakeConnection(cursor)
        return conexoes[chave]

    monkeypatch.setattr(criar_base_service.dbc, "connect", _fake_connect)
    return chamadas, conexoes


def test_happy_path_sem_interino_sem_tabelas_extras(monkeypatch):
    chamadas, conexoes = _patch_connect(monkeypatch)
    eventos = []

    resultado = criar_base_service.executar_criacao_base(_plano(), eventos.append)

    assert resultado.sucesso is True
    assert resultado.passos_concluidos == ["schema", "usuario", "dados", "cartorio", "cartorio_id", "parametros_destino"]
    assert conexoes["prod-host"].closed is True
    assert any(e.kind == "all_done" for e in eventos)


def test_reaproveita_uma_unica_conexao_quando_servidores_sao_iguais(monkeypatch):
    # modelo, destino e o alvo de parametros "destino" apontam pro mesmo host
    # ("prod-host") -> só deve abrir UMA conexão de verdade.
    chamadas, conexoes = _patch_connect(monkeypatch)
    criar_base_service.executar_criacao_base(_plano(), lambda e: None)
    assert len(chamadas) == 1
    assert chamadas[0].servidor == "prod-host"


def test_interino_roda_passo_extra(monkeypatch):
    _patch_connect(monkeypatch)
    resultado = criar_base_service.executar_criacao_base(_plano(cart_interino=True), lambda e: None)

    assert resultado.sucesso is True
    assert resultado.passos_concluidos == [
        "schema", "usuario", "dados", "cartorio", "cartorio_id", "interino", "parametros_destino",
    ]


def test_para_no_primeiro_erro_e_nao_registra_parametros(monkeypatch):
    cursor_falho = FakeCursor(fail_on_substring="DadosCartorio set")
    _patch_connect(monkeypatch, {"prod-host": cursor_falho})
    eventos = []

    resultado = criar_base_service.executar_criacao_base(_plano(), eventos.append)

    assert resultado.sucesso is False
    assert resultado.passo_falho == "cartorio"
    assert resultado.passos_concluidos == ["schema", "usuario", "dados"]
    assert "parametros_destino" not in resultado.passos_concluidos
    assert any(e.kind == "step_error" and e.step_name == "cartorio" for e in eventos)


def test_falha_de_conexao_reporta_erro(monkeypatch):
    def _fake_connect(cs, autocommit=False):
        raise RuntimeError("servidor inacessível")

    monkeypatch.setattr(criar_base_service.dbc, "connect", _fake_connect)
    eventos = []

    resultado = criar_base_service.executar_criacao_base(_plano(), eventos.append)

    assert resultado.sucesso is False
    assert resultado.passo_falho == "conexao"
    assert resultado.passos_concluidos == []


def test_copia_dados_linha_a_linha_quando_servidores_sao_diferentes(monkeypatch):
    cursor_modelo = FakeCursor(rows=[("valor1", "valor2")])
    cursor_destino = FakeCursor()
    _patch_connect(monkeypatch, {"prod-host": cursor_modelo, "outro-host": cursor_destino})
    eventos = []
    plano = _plano(
        destino_cs=DESTINO_OUTRO_SERVIDOR_CS,
        parametros_alvos=[AlvoParametros("destino", "servidor de destino", DESTINO_OUTRO_SERVIDOR_CS)],
    )

    resultado = criar_base_service.executar_criacao_base(plano, eventos.append)

    assert resultado.sucesso is True
    assert "dados" in resultado.passos_concluidos
    assert any(e.kind == "step_done" and e.step_name == "dados" for e in eventos)
    # SELECT roda no cursor do servidor modelo, totalmente qualificado.
    assert any("FROM [Gestor_SP_Modelo].dbo.[Contas]" in sql for sql in cursor_modelo.executed)
    # INSERT roda no cursor do servidor de destino, sem qualificação de base
    # (já em USE [Gestor_SP_Teste], feito explicitamente antes da cópia).
    assert any(sql.startswith("USE [Gestor_SP_Teste]") for sql in cursor_destino.executed)
    assert any(sql.startswith("INSERT INTO [Contas]") for sql, _ in cursor_destino.executed_many)
    # As 4 tabelas transacionais continuam sendo zeradas antes da cópia.
    assert any(sql == "DELETE FROM [Resumo];" for sql in cursor_destino.executed)


def test_copia_tabelas_extras_linha_a_linha_quando_servidores_sao_diferentes(monkeypatch):
    cursor_modelo = FakeCursor(rows=[("1", "Banco Teste")])
    cursor_destino = FakeCursor()
    _patch_connect(monkeypatch, {"prod-host": cursor_modelo, "outro-host": cursor_destino})
    plano = _plano(
        destino_cs=DESTINO_OUTRO_SERVIDOR_CS,
        tabelas_extras=[TabelaExtra("Bancos", ["Codigo", "Nome"])],
        parametros_alvos=[AlvoParametros("destino", "servidor de destino", DESTINO_OUTRO_SERVIDOR_CS)],
    )

    resultado = criar_base_service.executar_criacao_base(plano, lambda e: None)

    assert resultado.sucesso is True
    assert "tabelas_extras" in resultado.passos_concluidos
    assert any("FROM [Gestor_SP_Modelo].dbo.[Bancos]" in sql for sql in cursor_modelo.executed)
    assert any(sql.startswith("INSERT INTO [Bancos]") for sql, _ in cursor_destino.executed_many)


def test_falha_na_copia_cross_server_reporta_passo_dados(monkeypatch):
    cursor_modelo = FakeCursor(fail_on_substring="[GrupoContábil]")
    cursor_destino = FakeCursor()
    _patch_connect(monkeypatch, {"prod-host": cursor_modelo, "outro-host": cursor_destino})
    eventos = []
    plano = _plano(
        destino_cs=DESTINO_OUTRO_SERVIDOR_CS,
        parametros_alvos=[AlvoParametros("destino", "servidor de destino", DESTINO_OUTRO_SERVIDOR_CS)],
    )

    resultado = criar_base_service.executar_criacao_base(plano, eventos.append)

    assert resultado.sucesso is False
    assert resultado.passo_falho == "dados"
    assert "dados" not in resultado.passos_concluidos
    assert any(e.kind == "step_error" and e.step_name == "dados" for e in eventos)


def test_copia_tabelas_extras_quando_mesmo_servidor(monkeypatch):
    cursor = FakeCursor()
    _patch_connect(monkeypatch, {"prod-host": cursor})
    plano = _plano(tabelas_extras=[TabelaExtra("Bancos", ["Codigo", "Nome"])])

    resultado = criar_base_service.executar_criacao_base(plano, lambda e: None)

    assert resultado.sucesso is True
    assert "tabelas_extras" in resultado.passos_concluidos
    assert any("INSERT INTO [Gestor_SP_Teste].dbo.[Bancos]" in sql for sql in cursor.executed)


def test_registra_parametros_em_multiplos_servidores_distintos(monkeypatch):
    cursor_modelo = FakeCursor()
    cursor_pp = FakeCursor()
    _patch_connect(monkeypatch, {"prod-host": cursor_modelo, "100.77.102.1,1435": cursor_pp})
    plano = _plano(parametros_alvos=[
        AlvoParametros("modelo", "servidor da base modelo", MODELO_CS),
        AlvoParametros("servidorpp", "ServidorPP (nosso)", PP_CS),
    ])

    resultado = criar_base_service.executar_criacao_base(plano, lambda e: None)

    assert resultado.sucesso is True
    assert resultado.passos_concluidos[-2:] == ["parametros_modelo", "parametros_servidorpp"]
    assert any("USE [Gestor_Parametros]" in sql for sql in cursor_modelo.executed)
    assert any("INSERT INTO [dbo].[Parametros_Clientes]" in sql for sql in cursor_pp.executed)


def test_montar_insert_parametros_cliente_inclui_todas_as_13_colunas():
    sql = criar_base_service.montar_insert_parametros_cliente(_parametros_cfg())
    for coluna in criar_base_service.PARAMETROS_CLIENTE_COLUNAS:
        assert f"[{coluna}]" in sql
    assert "N'INR - Gestor_SP_Teste'" in sql
    assert "N'https://gestor-clientes-git-main-propackages-projects.vercel.app/api/notaries/'" in sql
