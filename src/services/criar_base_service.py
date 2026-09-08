"""Orquestração da criação de uma base nova do Gestor Financeiro para um
cliente, reproduzindo o fluxo do CriaBase (app C# separado) a partir dos
templates .sql copiados para resources/sql_templates/criar_base/.

Diferenças deliberadas em relação ao CriaBase original:
- "base modelo" é obrigatória aqui (lá era opcional).
- Para no primeiro erro (o CriaBase original só loga e segue em frente).
  Como consequência, se qualquer passo em produção falhar, o registro no
  Gestor_Parametros de dev também não roda (lá sempre rodava por último,
  independente do resultado da produção).
"""

import os
from dataclasses import dataclass, field
from typing import Callable, Optional

from src.services import db_connection_service as dbc
from src.services.sql_batch_executor import SqlStepError, run_sql_script
from src.utils.constants import SQL_TEMPLATES_DIR


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
    nome_dev: str
    diretorio_dev: str


@dataclass
class ProgressEvent:
    kind: str  # "step_start" | "batch" | "step_done" | "step_error" | "all_done"
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


_PASSOS = [
    ("schema", "01_schema.sql", "Criando base nova"),
    ("usuario", "02_usuario.sql", "Criando usuário de acesso"),
    ("dados", "03_dados.sql", "Copiando dados da base modelo"),
    ("cartorio", "04_cartorio.sql", "Gravando dados do cartório"),
    ("cartorio_id", "05_cartorio_id.sql", "Gravando ID do cartório"),
    ("parametros_prod", "06_insere_parametros.sql", "Registrando cliente (produção)"),
    ("interino", "07_interino.sql", "Ajustando IRRF para responsável interino"),
]


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


def executar_criacao_base(
    prod_cs: dbc.ConnectionSettings,
    dev_cs: dbc.ConnectionSettings,
    cfg: NovaBaseConfig,
    on_progress: Callable[[ProgressEvent], None],
) -> CriarBaseResultado:
    """Roda a sequência completa de provisionamento. Para imediatamente no
    primeiro passo que falhar (SqlStepError), sem tentar os seguintes nem o
    registro em dev."""
    passos_ok = []
    conn_prod = None
    conn_dev = None
    try:
        conn_prod = dbc.connect(prod_cs, autocommit=True)
        cursor_prod = conn_prod.cursor()
        comuns = _placeholders_comuns(cfg)

        for chave, arquivo, titulo in _PASSOS:
            if chave == "interino" and not cfg.cart_interino:
                continue

            on_progress(ProgressEvent("step_start", chave, titulo))
            caminho = os.path.join(SQL_TEMPLATES_DIR, arquivo)
            placeholders = dict(comuns)
            if chave == "parametros_prod":
                placeholders.update({
                    "$NOME": cfg.base_nova,
                    "$HOST": prod_cs.servidor,
                    "$PASS": cfg.base_senha,
                    "$DIR": cfg.diretorio,
                    "$ODBC": cfg.odbc_dsn,
                })

            run_sql_script(
                cursor_prod, caminho, placeholders, chave,
                on_batch=lambda p: on_progress(
                    ProgressEvent("batch", p.step_name, p.sql_preview, p.batch_index, p.total_batches)
                ),
            )
            passos_ok.append(chave)
            on_progress(ProgressEvent("step_done", chave, titulo))

        # Registro no servidor/base de parâmetros de dev (Pro-Packages).
        # O endereço do servidor do cliente (`$HOST`) continua sendo o de
        # produção — é o mesmo banco físico nos dois registros; só a base
        # Gestor_Parametros de destino (produção x dev) e os metadados de
        # exibição/diretório mudam.
        on_progress(ProgressEvent("step_start", "parametros_dev", "Registrando cliente (dev/Pro-Packages)"))
        conn_dev = dbc.connect(dev_cs, autocommit=True)
        cursor_dev = conn_dev.cursor()
        placeholders_dev = dict(comuns)
        placeholders_dev.update({
            "$NOME": cfg.nome_dev,
            "$HOST": prod_cs.servidor,
            "$PASS": cfg.base_senha,
            "$DIR": cfg.diretorio_dev,
            "$ODBC": cfg.odbc_dsn,
        })
        run_sql_script(
            cursor_dev, os.path.join(SQL_TEMPLATES_DIR, "06_insere_parametros.sql"),
            placeholders_dev, "parametros_dev",
        )
        passos_ok.append("parametros_dev")
        on_progress(ProgressEvent("step_done", "parametros_dev", "Registrado"))

        on_progress(ProgressEvent("all_done", "all", "Provisionamento concluído."))
        return CriarBaseResultado(sucesso=True, passos_concluidos=passos_ok)

    except SqlStepError as exc:
        on_progress(ProgressEvent("step_error", exc.step_name, str(exc)))
        return CriarBaseResultado(False, passos_ok, exc.step_name, str(exc))
    except Exception as exc:
        on_progress(ProgressEvent("step_error", "conexao", str(exc)))
        return CriarBaseResultado(False, passos_ok, "conexao", str(exc))
    finally:
        dbc.close(conn_prod)
        dbc.close(conn_dev)
