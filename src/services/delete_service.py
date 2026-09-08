"""Consulta e exclusão de registros já existentes no banco do Gestor, para
os mesmos 7 processos cobertos por sql_generator.py (todos exceto
GrupoPortal, que não tem tela de exclusão).

Diferente da geração de scripts (que insere uma linha por conta importada),
a consulta aqui é ampla: filtra pelas Configurações gerais atuais (Tipo de
Conta, TipoArq) e pelos grupos usados na planilha carregada, e devolve TODAS
as linhas já cadastradas que batem com esses critérios — não só as da
planilha atual — para o usuário revisar na tela e escolher o que excluir.

InterfaceArq, InterfaceComum e InterfaceFormaPgto guardam configuração
compartilhada por TipoArq (um registro serve todas as contas daquele tipo,
não uma por conta) — por isso vêm marcadas como `compartilhada=True`, para a
tela avisar que excluir ali pode afetar outras contas/clientes que usam o
mesmo TipoArq.
"""

from dataclasses import dataclass, field

from src.services.sql_generator import _indent, _wrap_transaction
from src.utils import constants as C
from src.utils.sql_escape import sql_string

FILTRO_REMUNERACAO = "REMUNERAÇÃO"


@dataclass
class ConsultaExclusao:
    chave: str
    titulo: str
    tabela: str
    sql: str
    parametros: tuple
    colunas_chave: tuple
    compartilhada: bool = False


@dataclass
class ResultadoExclusao:
    consulta: ConsultaExclusao
    colunas: list = field(default_factory=list)
    linhas: list = field(default_factory=list)
    erro: str = ""


def _grupos_distintos(accounts) -> list:
    vistos = []
    for a in accounts:
        grupo = a.grupo_normalizado
        if grupo and grupo not in vistos:
            vistos.append(grupo)
    return vistos


def montar_consultas(accounts, settings) -> list:
    """Monta as 7 consultas (sem executar), na ordem exibida na tela."""
    grupos = _grupos_distintos(accounts)

    consultas = [
        ConsultaExclusao(
            chave="contas", titulo="Contas", tabela=C.TABELA_CONTAS,
            sql=(
                f"SELECT * FROM {C.TABELA_CONTAS} "
                f"WHERE [Tipo de Conta] = ? AND Nome NOT LIKE ?"
            ),
            parametros=(settings.tipo_conta, f"%{FILTRO_REMUNERACAO}%"),
            colunas_chave=("Nome",),
        ),
    ]

    if grupos:
        placeholders = ", ".join("?" for _ in grupos)
        consultas.append(ConsultaExclusao(
            chave="grupo_contabil", titulo="GrupoContábil", tabela=C.TABELA_GRUPO_CONTABIL,
            sql=f"SELECT * FROM {C.TABELA_GRUPO_CONTABIL} WHERE Nome IN ({placeholders})",
            parametros=tuple(grupos),
            colunas_chave=("Nome",),
        ))
    else:
        consultas.append(ConsultaExclusao(
            chave="grupo_contabil", titulo="GrupoContábil", tabela=C.TABELA_GRUPO_CONTABIL,
            sql="", parametros=(), colunas_chave=("Nome",),
        ))

    consultas.append(ConsultaExclusao(
        chave="interface_contas", titulo="InterfaceContas", tabela=C.TABELA_INTERFACE_CONTAS,
        sql=f"SELECT * FROM {C.TABELA_INTERFACE_CONTAS} WHERE TipoArq = ?",
        parametros=(settings.tipo_arq,),
        colunas_chave=("ContaOrigem", "TipoArq"),
    ))

    consultas.append(ConsultaExclusao(
        chave="interface_arq", titulo="InterfaceArq", tabela=C.TABELA_INTERFACE_ARQ,
        sql=f"SELECT * FROM {C.TABELA_INTERFACE_ARQ} WHERE NomeTipo = ?",
        parametros=(settings.tipo_arq,),
        colunas_chave=("NomeTipo",),
        compartilhada=True,
    ))

    consultas.append(ConsultaExclusao(
        chave="interface_comum", titulo="InterfaceComum", tabela=C.TABELA_INTERFACE_COMUM,
        sql=f"SELECT * FROM {C.TABELA_INTERFACE_COMUM} WHERE TipoArq = ?",
        parametros=(settings.tipo_arq,),
        colunas_chave=("TipoArq",),
        compartilhada=True,
    ))

    consultas.append(ConsultaExclusao(
        chave="interface_forma_pgto", titulo="InterfaceFormaPgto", tabela=C.TABELA_INTERFACE_FORMA_PGTO,
        sql=f"SELECT * FROM {C.TABELA_INTERFACE_FORMA_PGTO} WHERE TipoArq = ?",
        parametros=(settings.tipo_arq,),
        colunas_chave=("TipoArq", "FormaSist"),
        compartilhada=True,
    ))

    consultas.append(ConsultaExclusao(
        chave="interface_historico", titulo="InterfaceHistorico", tabela=C.TABELA_INTERFACE_HISTORICO,
        sql=f"SELECT * FROM {C.TABELA_INTERFACE_HISTORICO} WHERE TipoArq = ?",
        parametros=(settings.tipo_arq,),
        colunas_chave=("ContaOrigem", "TipoArq"),
    ))

    return consultas


def executar_consultas(connection, consultas) -> list:
    """Executa cada consulta e devolve os resultados, na mesma ordem. Uma
    consulta que falha (ex.: tabela sem permissão) não interrompe as
    demais — o erro fica registrado em `ResultadoExclusao.erro`."""
    resultados = []
    for consulta in consultas:
        if not consulta.sql:
            resultados.append(ResultadoExclusao(consulta))
            continue
        try:
            cursor = connection.cursor()
            cursor.execute(consulta.sql, consulta.parametros)
            colunas = [d[0] for d in cursor.description]
            linhas = [dict(zip(colunas, row)) for row in cursor.fetchall()]
            resultados.append(ResultadoExclusao(consulta, colunas, linhas))
        except Exception as exc:
            resultados.append(ResultadoExclusao(consulta, erro=str(exc)))
    return resultados


def montar_script_exclusao(itens) -> str:
    """Monta um único script T-SQL com um DELETE por item selecionado,
    dentro de uma transação (BEGIN TRY/CATCH, igual aos scripts de
    geração) — ou tudo é excluído, ou nada é, em caso de erro.

    `itens`: lista de (tabela, colunas_chave, linha_dict).
    """
    linhas_sql = []
    for tabela, colunas_chave, linha in itens:
        condicoes = []
        for col in colunas_chave:
            valor = linha.get(col)
            if valor is None:
                condicoes.append(f"[{col}] IS NULL")
            else:
                condicoes.append(f"[{col}] = {sql_string(valor)}")
        linhas_sql.append(f"DELETE FROM {tabela} WHERE {' AND '.join(condicoes)};")
    corpo = _indent(linhas_sql)
    return _wrap_transaction(corpo)


def executar_exclusoes(connection, itens) -> int:
    """Executa o script de exclusão como um único lote (mesmo padrão do
    'Executar no banco' da aba Criar contas). Retorna a quantidade de itens
    que foram enviados para exclusão."""
    if not itens:
        return 0
    script = montar_script_exclusao(itens)
    cursor = connection.cursor()
    cursor.execute(script)
    return len(itens)
