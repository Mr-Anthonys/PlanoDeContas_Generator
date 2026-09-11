"""Orquestração da criação de uma base nova do Gestor Financeiro para um
cliente, reproduzindo o fluxo do CriaBase (app C# separado) a partir dos
templates .sql copiados para resources/sql_templates/criar_base/, mais:

- cópia de tabelas/colunas extras escolhidas pelo usuário (além das ~15
  tabelas fixas de 03_dados.sql — ver `schema_service.py`);
- registro em Gestor_Parametros.Parametros_Clientes em 1 ou mais servidores
  escolhidos pelo usuário (servidor da base modelo / servidor de destino /
  ServidorPP), sempre com a MESMA linha de valores em cada um.

Diferenças deliberadas em relação ao CriaBase original:
- "base modelo" é obrigatória aqui (lá era opcional).
- Para no primeiro erro (o CriaBase original só loga e segue em frente).
- Servidor da base modelo e servidor de destino podem ser diferentes (o
  CriaBase original exigia sempre o mesmo servidor). Quando são o mesmo, a
  cópia de dados usa INSERT...SELECT cross-database direto no servidor
  (rápido). Quando são diferentes, a cópia é feita linha a linha pela
  aplicação (lê da conexão do modelo, grava na conexão de destino) — mais
  lenta, mas não depende de linked server.
"""

import os
from dataclasses import dataclass, field
from typing import Callable, Optional

from src.services import db_connection_service as dbc
from src.services import schema_service
from src.services.schema_service import montar_copia_tabela
from src.services.sql_batch_executor import SqlStepError, run_sql_script
from src.utils.constants import GESTOR_PARAMETROS_DATABASE, SQL_TEMPLATES_DIR
from src.utils.sql_escape import quote_identifier, sql_string

PARAMETROS_CLIENTE_COLUNAS = [
    "Nome", "Servidor", "Banco", "Usuario", "Senha", "DiretorioArquivo", "Odbc",
    "BrowserDashboard", "UrlDashboard", "UrlDashboardToken", "DiretorioMensalistas",
    "UrlValidacao", "UrlGestorClientes",
]


@dataclass
class NovaBaseConfig:
    base_modelo: str  # obrigatório
    base_nova: str
    base_usuario: str
    base_senha: str
    cart_interino: bool
    cart_id: str
    cart_nome: str
    cart_cns: str
    cart_cidade: str
    cart_estado: str
    cart_endereco: str
    cart_bairro: str
    cart_cep: str
    cart_resp_nome: str
    cart_resp_cpf: str
    cart_inicio: str  # 'yyyy-MM-dd'
    cart_cnpj: str
    diretorio: str
    odbc_dsn: str


@dataclass
class ParametrosClienteConfig:
    """Uma linha de Gestor_Parametros.Parametros_Clientes — os mesmos 13
    valores são inseridos em cada servidor de `PlanoProvisionamento.parametros_alvos`."""
    nome: str
    servidor: str
    banco: str
    usuario: str
    senha: str
    diretorio_arquivo: str
    odbc: str
    browser_dashboard: str
    url_dashboard: str
    url_dashboard_token: str
    diretorio_mensalistas: str
    url_validacao: str
    url_gestor_clientes: str

    def valores(self) -> list:
        return [
            self.nome, self.servidor, self.banco, self.usuario, self.senha, self.diretorio_arquivo,
            self.odbc, self.browser_dashboard, self.url_dashboard, self.url_dashboard_token,
            self.diretorio_mensalistas, self.url_validacao, self.url_gestor_clientes,
        ]


@dataclass
class AlvoParametros:
    """Um servidor onde a mesma linha de Parametros_Clientes será inserida."""
    chave: str    # ex.: "modelo", "destino", "servidorpp" — vira sufixo do nome do passo
    titulo: str   # ex.: "servidor da base modelo" — usado nas mensagens de progresso
    connection_settings: object  # dbc.ConnectionSettings


@dataclass
class TabelaExtra:
    tabela: str
    colunas: list


@dataclass
class PlanoProvisionamento:
    modelo_cs: object     # dbc.ConnectionSettings — onde a base modelo está
    destino_cs: object    # dbc.ConnectionSettings — onde a base nova será criada
    cfg: NovaBaseConfig
    tabelas_extras: list             # list[TabelaExtra]
    parametros_cfg: ParametrosClienteConfig
    parametros_alvos: list           # list[AlvoParametros], já deduplicados por servidor


@dataclass
class ProgressEvent:
    kind: str  # "step_start" | "batch" | "step_done" | "step_skipped" | "step_error" | "all_done"
    step_name: str
    message: str = ""
    batch_index: Optional[int] = None
    total_batches: Optional[int] = None


@dataclass
class CriarBaseResultado:
    sucesso: bool
    passos_concluidos: list = field(default_factory=list)
    passo_falho: Optional[str] = None
    erro: Optional[str] = None


_PASSOS_BASE = [
    ("schema", "01_schema.sql", "Criando base nova"),
    ("usuario", "02_usuario.sql", "Criando usuário de acesso"),
    ("dados", "03_dados.sql", "Copiando dados da base modelo"),
    ("cartorio", "04_cartorio.sql", "Gravando dados do cartório"),
    ("cartorio_id", "05_cartorio_id.sql", "Gravando ID do cartório"),
]

CAMINHO_03_DADOS = os.path.join(SQL_TEMPLATES_DIR, "03_dados.sql")


def mesmo_servidor(a, b) -> bool:
    return a.servidor.strip().lower() == b.servidor.strip().lower()


def _placeholders_comuns(cfg: NovaBaseConfig) -> dict:
    return {
        "$BASE_NOVA": cfg.base_nova,
        "$BASE_USUARIO": cfg.base_usuario,
        "$BASE_MODELO": cfg.base_modelo,
        "$CART_NOME": cfg.cart_nome,
        "$CART_CNS": cfg.cart_cns,
        "$CART_CIDADE": cfg.cart_cidade,
        "$CART_ESTADO": cfg.cart_estado,
        "$CART_ENDERECO": cfg.cart_endereco,
        "$CART_BAIRRO": cfg.cart_bairro,
        "$CART_CEP": cfg.cart_cep,
        "$CART_RESP_NOME": cfg.cart_resp_nome,
        "$CART_RESP_CPF": cfg.cart_resp_cpf,
        "$CART_INICIO": cfg.cart_inicio,
        "$CART_CNPJ": cfg.cart_cnpj,
        "$CART_ID": cfg.cart_id,
    }


def montar_insert_parametros_cliente(cfg: ParametrosClienteConfig) -> str:
    colunas_sql = ", ".join(f"[{c}]" for c in PARAMETROS_CLIENTE_COLUNAS)
    valores_sql = ", ".join(sql_string(v) for v in cfg.valores())
    return f"INSERT INTO [dbo].[Parametros_Clientes] ({colunas_sql})\nVALUES ({valores_sql});"


def _copiar_linhas(cursor_modelo, cursor_destino, base_modelo: str, tabela_origem: str, tabela_destino: str, colunas: list):
    colunas_sql = ", ".join(quote_identifier(c) for c in colunas)
    cursor_modelo.execute(
        f"SELECT {colunas_sql} FROM {quote_identifier(base_modelo)}.dbo.{quote_identifier(tabela_origem)};"
    )
    linhas = [tuple(linha) for linha in cursor_modelo.fetchall()]
    if not linhas:
        return
    placeholders_sql = ", ".join("?" for _ in colunas)
    insert_sql = f"INSERT INTO {quote_identifier(tabela_destino)} ({colunas_sql}) VALUES ({placeholders_sql})"
    cursor_destino.executemany(insert_sql, linhas)


def _copiar_dados_cross_server(conn_modelo, cursor_destino, cfg: NovaBaseConfig):
    """Equivalente a rodar 03_dados.sql, mas linha a linha via Python — usado
    quando o servidor da base modelo é diferente do servidor de destino
    (sem linked server, então um único INSERT...SELECT cross-database não
    funciona). O plano de cópia (tabelas/colunas exatas, tabelas zeradas por
    DELETE) vem de `schema_service.analisar_copia_fixa_de_dados`, extraído
    do próprio 03_dados.sql — mesma fonte usada no caminho de mesmo servidor."""
    cursor_destino.execute(f"USE {quote_identifier(cfg.base_nova)};")
    plano = schema_service.analisar_copia_fixa_de_dados(CAMINHO_03_DADOS)
    for tabela in plano.tabelas_para_limpar:
        cursor_destino.execute(f"DELETE FROM {quote_identifier(tabela)};")

    cursor_modelo = conn_modelo.cursor()
    for copia in plano.tabelas:
        colunas = copia.colunas
        if colunas is None:
            colunas = schema_service.listar_colunas(conn_modelo, cfg.base_modelo, copia.tabela_origem)
        _copiar_linhas(cursor_modelo, cursor_destino, cfg.base_modelo, copia.tabela_origem, copia.tabela_destino, colunas)


def _copiar_tabelas_extras_cross_server(conn_modelo, cursor_destino, cfg: NovaBaseConfig, tabelas_extras: list):
    cursor_destino.execute(f"USE {quote_identifier(cfg.base_nova)};")
    cursor_modelo = conn_modelo.cursor()
    for extra in tabelas_extras:
        _copiar_linhas(cursor_modelo, cursor_destino, cfg.base_modelo, extra.tabela, extra.tabela, extra.colunas)


def executar_criacao_base(
    plano: PlanoProvisionamento, on_progress: Callable[[ProgressEvent], None],
) -> CriarBaseResultado:
    """Roda a sequência completa de provisionamento. Para imediatamente no
    primeiro passo que falhar — nenhum passo seguinte roda, incluindo os
    registros em Parametros_Clientes ainda não feitos."""
    passos_ok = []
    conexoes = {}  # servidor (lower, strip) -> connection já aberta, reaproveitada quando repete
    cfg = plano.cfg
    copia_via_sql_direto = mesmo_servidor(plano.modelo_cs, plano.destino_cs)

    def _conectar(cs):
        chave = cs.servidor.strip().lower()
        if chave not in conexoes:
            conexoes[chave] = dbc.connect(cs, autocommit=True)
        return conexoes[chave]

    def _rodar_ou_relatar(chave, func):
        try:
            func()
        except Exception as exc:
            raise SqlStepError(chave, 0, 0, exc) from exc

    try:
        conn_destino = _conectar(plano.destino_cs)
        cursor_destino = conn_destino.cursor()
        conn_modelo = _conectar(plano.modelo_cs)
        comuns = _placeholders_comuns(cfg)

        for chave, arquivo, titulo in _PASSOS_BASE:
            titulo_efetivo = titulo if chave != "dados" or copia_via_sql_direto else (
                f"{titulo} (servidores diferentes: copiando linha a linha via aplicação)"
            )
            on_progress(ProgressEvent("step_start", chave, titulo_efetivo))
            if chave == "dados" and not copia_via_sql_direto:
                _rodar_ou_relatar(chave, lambda: _copiar_dados_cross_server(conn_modelo, cursor_destino, cfg))
            else:
                caminho = os.path.join(SQL_TEMPLATES_DIR, arquivo)
                run_sql_script(
                    cursor_destino, caminho, comuns, chave,
                    on_batch=lambda p: on_progress(
                        ProgressEvent("batch", p.step_name, p.sql_preview, p.batch_index, p.total_batches)
                    ),
                )
            passos_ok.append(chave)
            on_progress(ProgressEvent("step_done", chave, titulo_efetivo))

        if plano.tabelas_extras:
            on_progress(ProgressEvent(
                "step_start", "tabelas_extras",
                f"Copiando {len(plano.tabelas_extras)} tabela(s) adicional(is) selecionada(s)",
            ))
            if copia_via_sql_direto:
                for extra in plano.tabelas_extras:
                    sql = montar_copia_tabela(cfg.base_nova, cfg.base_modelo, extra.tabela, extra.colunas)
                    cursor_destino.execute(sql)
            else:
                _rodar_ou_relatar(
                    "tabelas_extras",
                    lambda: _copiar_tabelas_extras_cross_server(conn_modelo, cursor_destino, cfg, plano.tabelas_extras),
                )
            passos_ok.append("tabelas_extras")
            on_progress(ProgressEvent("step_done", "tabelas_extras", "Tabelas adicionais copiadas"))

        if cfg.cart_interino:
            on_progress(ProgressEvent("step_start", "interino", "Ajustando IRRF para responsável interino"))
            caminho = os.path.join(SQL_TEMPLATES_DIR, "07_interino.sql")
            run_sql_script(cursor_destino, caminho, comuns, "interino")
            passos_ok.append("interino")
            on_progress(ProgressEvent("step_done", "interino", "Ajustado"))

        insert_sql = montar_insert_parametros_cliente(plano.parametros_cfg)
        for alvo in plano.parametros_alvos:
            chave = f"parametros_{alvo.chave}"
            on_progress(ProgressEvent("step_start", chave, f"Registrando cliente ({alvo.titulo})"))
            cursor_alvo = _conectar(alvo.connection_settings).cursor()
            cursor_alvo.execute(f"USE {quote_identifier(GESTOR_PARAMETROS_DATABASE)};")
            cursor_alvo.execute(insert_sql)
            passos_ok.append(chave)
            on_progress(ProgressEvent("step_done", chave, f"Registrado ({alvo.titulo})"))

        on_progress(ProgressEvent("all_done", "all", "Provisionamento concluído."))
        return CriarBaseResultado(sucesso=True, passos_concluidos=passos_ok)

    except SqlStepError as exc:
        on_progress(ProgressEvent("step_error", exc.step_name, str(exc)))
        return CriarBaseResultado(False, passos_ok, exc.step_name, str(exc))
    except Exception as exc:
        on_progress(ProgressEvent("step_error", "conexao", str(exc)))
        return CriarBaseResultado(False, passos_ok, "conexao", str(exc))
    finally:
        for conn in conexoes.values():
            dbc.close(conn)
