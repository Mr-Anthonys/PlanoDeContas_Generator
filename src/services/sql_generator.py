"""Geração dos scripts SQL Server para os 8 processos de cadastro.

Cada função retorna um `SqlProcessResult` com o SQL pronto para copiar/colar,
já com:
  * escape de apóstrofos (dobrando-os) e uso de strings Unicode N'...';
  * proteção contra duplicidade (IF NOT EXISTS) em TODAS as tabelas — no
    processo manual original, apenas a tabela Contas possuía essa proteção;
    as demais foram corrigidas aqui (ver README, seção "Correções realizadas");
  * transação BEGIN TRY/CATCH com ROLLBACK, para permitir a execução segura e
    independente de cada processo;
  * quebras de linha estilo Windows (\\r\\n).

Os nomes de tabelas/colunas usados são os confirmados nas planilhas de
referência (ver src/utils/constants.py).
"""

from dataclasses import dataclass

from src.utils import constants as C
from src.utils.sql_escape import sql_string


@dataclass
class SqlProcessResult:
    titulo: str
    descricao: str
    sql: str
    quantidade: int


def _nl(texto: str) -> str:
    """Normaliza quebras de linha para o padrão Windows (CRLF)."""
    return texto.replace("\r\n", "\n").replace("\n", "\r\n")


def _wrap_transaction(corpo: str) -> str:
    if not corpo.strip():
        return "-- Nenhum comando gerado para este processo.\r\n"
    return _nl(
        "BEGIN TRY\n"
        "    BEGIN TRANSACTION;\n\n"
        f"{corpo}\n"
        "    COMMIT;\n"
        "END TRY\n"
        "BEGIN CATCH\n"
        "    IF @@TRANCOUNT > 0\n"
        "        ROLLBACK;\n\n"
        "    THROW;\n"
        "END CATCH;\n"
    )


def _indent(linhas: list) -> str:
    return "\n".join(f"    {linha}" for linha in linhas)


def _grupos_distintos(accounts) -> list:
    """Retorna os grupos distintos realmente usados pelas contas válidas,
    na ordem de primeira ocorrência (maiúsculas, sem espaços)."""
    vistos = []
    for account in accounts:
        grupo = account.grupo_normalizado
        if grupo and grupo not in vistos:
            vistos.append(grupo)
    return vistos


# ---------------------------------------------------------------------------
# 1. Contas
# ---------------------------------------------------------------------------
def generate_contas(accounts, settings) -> SqlProcessResult:
    colunas = ", ".join(f"[{c}]" for c in C.COLUNAS_CONTAS)
    p = C.CONTAS_PADRAO
    linhas = []
    for a in accounts:
        valores = ", ".join([
            sql_string(a.nome),
            sql_string(a.grupo_normalizado),
            sql_string(settings.historico_texto),
            sql_string(settings.tipo_conta),
            sql_string(p["forma_transacao"]),
            str(p["l_oficial"]),
            str(p["l_gerencial"]),
            str(p["l_contabil"]),
            str(p["l_dinheiro"]),
            str(p["l_particular"]),
            str(settings.l_previo),
            str(p["l_portal"]),
            sql_string(a.grupo_normalizado),
            str(settings.l_irrf),
            str(p["pdf"]),
            str(p["ativa"]),
        ])
        linhas.append(
            f"IF NOT EXISTS (SELECT 1 FROM {C.TABELA_CONTAS} WHERE Nome = {sql_string(a.nome)})\n"
            f"    INSERT INTO {C.TABELA_CONTAS} ({colunas})\n"
            f"    VALUES ({valores});"
        )
    corpo = _indent(linhas)
    sql = _wrap_transaction(corpo)
    return SqlProcessResult(
        "1. Contas",
        "Cria uma conta do plano de contas para cada linha importada, evitando duplicidade pelo Nome.",
        sql,
        len(accounts),
    )


# ---------------------------------------------------------------------------
# 2. GrupoPortal
# ---------------------------------------------------------------------------
def generate_grupo_portal(accounts) -> SqlProcessResult:
    grupos = _grupos_distintos(accounts)
    colunas = ", ".join(f"[{c}]" for c in C.COLUNAS_GRUPO_PORTAL)
    linhas = []
    for grupo in grupos:
        linhas.append(
            f"IF NOT EXISTS (SELECT 1 FROM {C.TABELA_GRUPO_PORTAL} WHERE NomeGrupo = {sql_string(grupo)})\n"
            f"    INSERT INTO {C.TABELA_GRUPO_PORTAL} ({colunas})\n"
            f"    VALUES ({sql_string(grupo)}, {C.GRUPO_PORTAL_TIPO_GRUPO_PADRAO});"
        )
    corpo = _indent(linhas)
    sql = _wrap_transaction(corpo)
    return SqlProcessResult(
        "2. GrupoPortal",
        "Cria somente os grupos de portal efetivamente usados pelas contas importadas (um registro por grupo distinto).",
        sql,
        len(grupos),
    )


# ---------------------------------------------------------------------------
# 3. GrupoContábil
# ---------------------------------------------------------------------------
def generate_grupo_contabil(accounts) -> SqlProcessResult:
    grupos = _grupos_distintos(accounts)
    colunas = ", ".join(f"[{c}]" for c in C.COLUNAS_GRUPO_CONTABIL)
    linhas = []
    for grupo in grupos:
        linhas.append(
            f"IF NOT EXISTS (SELECT 1 FROM {C.TABELA_GRUPO_CONTABIL} WHERE Nome = {sql_string(grupo)})\n"
            f"    INSERT INTO {C.TABELA_GRUPO_CONTABIL} ({colunas})\n"
            f"    VALUES ({sql_string(grupo)});"
        )
    corpo = _indent(linhas)
    sql = _wrap_transaction(corpo)
    return SqlProcessResult(
        "3. GrupoContábil",
        "Cria somente os grupos contábeis efetivamente usados pelas contas importadas (um registro por grupo distinto).",
        sql,
        len(grupos),
    )


# ---------------------------------------------------------------------------
# 4. InterfaceContas
# ---------------------------------------------------------------------------
def generate_interface_contas(accounts, settings) -> SqlProcessResult:
    colunas = ", ".join(f"[{c}]" for c in C.COLUNAS_INTERFACE_CONTAS)
    linhas = []
    for a in accounts:
        linhas.append(
            f"IF NOT EXISTS (\n"
            f"    SELECT 1 FROM {C.TABELA_INTERFACE_CONTAS}\n"
            f"    WHERE ContaOrigem = {sql_string(a.conta_origem)} AND TipoArq = {sql_string(settings.tipo_arq)}\n"
            f")\n"
            f"    INSERT INTO {C.TABELA_INTERFACE_CONTAS} ({colunas})\n"
            f"    VALUES ({sql_string(a.nome)}, {sql_string(a.conta_origem)}, {sql_string(settings.tipo_arq)});"
        )
    corpo = _indent(linhas)
    sql = _wrap_transaction(corpo)
    return SqlProcessResult(
        "4. InterfaceContas",
        "Vincula o código ContaOrigem informado na planilha (usado exatamente como digitado, sem geração ou consulta de identidade) ao nome da conta no SGF.",
        sql,
        len(accounts),
    )


# ---------------------------------------------------------------------------
# 5. InterfaceHistorico
# ---------------------------------------------------------------------------
def generate_interface_historico(accounts, settings) -> SqlProcessResult:
    colunas = ", ".join(f"[{c}]" for c in C.COLUNAS_INTERFACE_HISTORICO)
    valores_fixos_numericos = ", ".join("0" for _ in C.COLUNAS_INTERFACE_HISTORICO_FIXAS_NUMERICAS)
    valores_fixos_texto = ", ".join(sql_string("") for _ in C.COLUNAS_INTERFACE_HISTORICO_FIXAS_TEXTO)

    linhas = []
    for a in accounts:
        valores_dinamicos = ", ".join([
            sql_string(a.conta_origem),
            sql_string(settings.historico1),
            sql_string(settings.historico2 if settings.qtd_marcadores >= 2 else ""),
            sql_string(settings.historico3 if settings.qtd_marcadores >= 3 else ""),
            sql_string(settings.tipo_arq),
        ])
        valores = ", ".join([valores_dinamicos, valores_fixos_numericos, valores_fixos_texto])
        linhas.append(
            f"IF NOT EXISTS (\n"
            f"    SELECT 1 FROM {C.TABELA_INTERFACE_HISTORICO}\n"
            f"    WHERE ContaOrigem = {sql_string(a.conta_origem)} AND TipoArq = {sql_string(settings.tipo_arq)}\n"
            f")\n"
            f"    INSERT INTO {C.TABELA_INTERFACE_HISTORICO} ({colunas})\n"
            f"    VALUES ({valores});"
        )
    corpo = _indent(linhas)
    sql = _wrap_transaction(corpo)
    return SqlProcessResult(
        "5. InterfaceHistorico",
        "Define, para cada conta, as colunas do arquivo de origem que substituirão os marcadores '@' de Contas.Histórico "
        "(Historico1 para o primeiro '@', Historico2 para o segundo, Historico3 para o terceiro, quando existirem). "
        "Os demais 37 campos da tabela permanecem com o valor fixo observado no processo manual atual (0 ou vazio).",
        sql,
        len(accounts),
    )


# ---------------------------------------------------------------------------
# 6. InterfaceArq
# ---------------------------------------------------------------------------
def generate_interface_arq(settings, reference) -> SqlProcessResult:
    dados = reference.interface_arq(settings.tipo_arq)
    colunas = ", ".join(f"[{c}]" for c in C.COLUNAS_INTERFACE_ARQ)
    valores = []
    for coluna in C.COLUNAS_INTERFACE_ARQ:
        if coluna == "NomeTipo":
            valor = settings.tipo_arq
        else:
            chave = C.CAMPOS_INTERFACE_ARQ_CONFIG[coluna]
            valor = dados[chave]
        if coluna in C.INTERFACE_ARQ_COLUNAS_TEXTO:
            valores.append(sql_string(valor))
        else:
            valores.append(str(valor))
    valores_txt = ", ".join(valores)
    corpo = _indent([
        f"IF NOT EXISTS (SELECT 1 FROM {C.TABELA_INTERFACE_ARQ} WHERE NomeTipo = {sql_string(settings.tipo_arq)})\n"
        f"    INSERT INTO {C.TABELA_INTERFACE_ARQ} ({colunas})\n"
        f"    VALUES ({valores_txt});"
    ])
    sql = _wrap_transaction(corpo)
    return SqlProcessResult(
        "6. InterfaceArq",
        f"Define os parâmetros de leitura do arquivo para o TipoArq selecionado ('{settings.tipo_arq}').",
        sql,
        1,
    )


# ---------------------------------------------------------------------------
# 7. InterfaceComum
# ---------------------------------------------------------------------------
def generate_interface_comum(settings, reference) -> SqlProcessResult:
    dados = reference.interface_comum(settings.interface_comum)
    colunas = ", ".join(f"[{c}]" for c in C.COLUNAS_INTERFACE_COMUM)
    valores = []
    for coluna in C.COLUNAS_INTERFACE_COMUM:
        if coluna == "TipoArq":
            valores.append(sql_string(settings.tipo_arq))
        else:
            valores.append(sql_string(dados[coluna]))
    valores_txt = ", ".join(valores)
    corpo = _indent([
        f"IF NOT EXISTS (SELECT 1 FROM {C.TABELA_INTERFACE_COMUM} WHERE TipoArq = {sql_string(settings.tipo_arq)})\n"
        f"    INSERT INTO {C.TABELA_INTERFACE_COMUM} ({colunas})\n"
        f"    VALUES ({valores_txt});"
    ])
    sql = _wrap_transaction(corpo)
    return SqlProcessResult(
        "7. InterfaceComum",
        f"Mapeia os cabeçalhos do arquivo de origem para os campos lógicos do sistema, conforme o modelo '{settings.interface_comum}'.",
        sql,
        1,
    )


# ---------------------------------------------------------------------------
# 8. InterfaceFormaPgto
# ---------------------------------------------------------------------------
def generate_interface_forma_pgto(settings, reference) -> SqlProcessResult:
    dados = reference.interface_forma_pgto(settings.interface_forma_pgto)
    colunas = ", ".join(f"[{c}]" for c in C.COLUNAS_INTERFACE_FORMA_PGTO)
    valores = []
    for coluna in C.COLUNAS_INTERFACE_FORMA_PGTO:
        if coluna == "TipoArq":
            valores.append(sql_string(settings.tipo_arq))
        elif coluna in C.INTERFACE_FORMA_PGTO_COLUNAS_TEXTO:
            valores.append(sql_string(dados[coluna]))
        else:
            valores.append(str(dados[coluna]))
    valores_txt = ", ".join(valores)
    corpo = _indent([
        f"IF NOT EXISTS (\n"
        f"    SELECT 1 FROM {C.TABELA_INTERFACE_FORMA_PGTO}\n"
        f"    WHERE TipoArq = {sql_string(settings.tipo_arq)} AND FormaSist = {sql_string(dados['FormaSist'])}\n"
        f")\n"
        f"    INSERT INTO {C.TABELA_INTERFACE_FORMA_PGTO} ({colunas})\n"
        f"    VALUES ({valores_txt});"
    ])
    sql = _wrap_transaction(corpo)
    return SqlProcessResult(
        "8. InterfaceFormaPgto",
        f"Converte a forma de pagamento do arquivo de origem para a forma usada pelo SGF, conforme o modelo '{settings.interface_forma_pgto}'.",
        sql,
        1,
    )


# ---------------------------------------------------------------------------
# Script completo
# ---------------------------------------------------------------------------
def generate_all(accounts, settings, reference) -> list:
    """Gera os 8 processos na ordem dos painéis (igual à lista de PROCESSOS SEPARADOS)."""
    return [
        generate_contas(accounts, settings),
        generate_grupo_portal(accounts),
        generate_grupo_contabil(accounts),
        generate_interface_contas(accounts, settings),
        generate_interface_historico(accounts, settings),
        generate_interface_arq(settings, reference),
        generate_interface_comum(settings, reference),
        generate_interface_forma_pgto(settings, reference),
    ]


def generate_full_script(accounts, settings, reference) -> str:
    """Monta o script completo na ORDEM LÓGICA DE EXECUÇÃO recomendada pela
    documentação (seção 8): GrupoPortal/GrupoContábil -> Contas ->
    InterfaceArq/InterfaceComum/InterfaceFormaPgto -> InterfaceContas ->
    InterfaceHistorico. Essa ordem respeita eventuais chaves estrangeiras
    entre grupos, contas e tabelas de interface."""
    ordem_logica = [
        generate_grupo_portal(accounts),
        generate_grupo_contabil(accounts),
        generate_contas(accounts, settings),
        generate_interface_arq(settings, reference),
        generate_interface_comum(settings, reference),
        generate_interface_forma_pgto(settings, reference),
        generate_interface_contas(accounts, settings),
        generate_interface_historico(accounts, settings),
    ]
    partes = []
    for i, resultado in enumerate(ordem_logica, start=1):
        separador = "=" * 50
        partes.append(
            f"-- {separador}\n"
            f"-- {i}. {resultado.titulo.split('. ', 1)[-1].upper()}\n"
            f"-- {resultado.descricao}\n"
            f"-- {separador}\n\n"
            f"{resultado.sql}"
        )
    return _nl("\n".join(partes))
