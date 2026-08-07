import pytest

from src.services import excel_reader
from src.services.excel_reader import ExcelReadError


def test_planilha_valida(make_workbook):
    caminho = make_workbook(
        ["Nome", "Grupo", "ContaOrigem"],
        [
            ["RECONHECIMENTO DE FIRMA", "TABELIONATO DE NOTAS", 1],
            ["AUTENTICAÇÃO", "TABELIONATO DE NOTAS", 2],
        ],
    )
    linhas = excel_reader.read_accounts(caminho)
    assert len(linhas) == 2
    assert linhas[0].nome == "RECONHECIMENTO DE FIRMA"
    assert linhas[0].grupo == "TABELIONATO DE NOTAS"
    assert linhas[0].conta_origem == "1"
    assert linhas[0].linha == 2  # primeira linha de dados = linha 2 da planilha


def test_cabecalhos_alternativos(make_workbook):
    caminho = make_workbook(
        ["Nome do Ato", "GrupoContábil", "Código da Conta"],
        [["PROTESTO DE TÍTULO", "PROTESTO", 3]],
    )
    linhas = excel_reader.read_accounts(caminho)
    assert len(linhas) == 1
    assert linhas[0].nome == "PROTESTO DE TÍTULO"
    assert linhas[0].grupo == "PROTESTO"
    assert linhas[0].conta_origem == "3"


def test_linha_vazia_e_ignorada(make_workbook):
    caminho = make_workbook(
        ["Nome", "Grupo", "ContaOrigem"],
        [
            ["CONTA A", "GRUPO A", 1],
            [None, None, None],
            ["CONTA B", "GRUPO A", 2],
        ],
    )
    linhas = excel_reader.read_accounts(caminho)
    assert len(linhas) == 2
    assert [l.nome for l in linhas] == ["CONTA A", "CONTA B"]


def test_conta_sem_grupo_e_preservada_para_validacao(make_workbook):
    caminho = make_workbook(
        ["Nome", "Grupo", "ContaOrigem"],
        [["CONTA SEM GRUPO", "", 1]],
    )
    linhas = excel_reader.read_accounts(caminho)
    assert len(linhas) == 1
    assert linhas[0].grupo == ""


def test_conta_duplicada_nao_e_descartada_pelo_leitor(make_workbook):
    caminho = make_workbook(
        ["Nome", "Grupo", "ContaOrigem"],
        [
            ["CONTA REPETIDA", "GRUPO A", 1],
            ["CONTA REPETIDA", "GRUPO A", 2],
        ],
    )
    linhas = excel_reader.read_accounts(caminho)
    assert len(linhas) == 2  # o leitor não deve descartar duplicidades silenciosamente


def test_grupo_minusculo_preservado_no_bruto(make_workbook):
    caminho = make_workbook(
        ["Nome", "Grupo", "ContaOrigem"],
        [["CONTA X", "tabelionato de notas", 1]],
    )
    linhas = excel_reader.read_accounts(caminho)
    assert linhas[0].grupo == "tabelionato de notas"


def test_grupo_com_espacos_excedentes_e_removido(make_workbook):
    caminho = make_workbook(
        ["Nome", "Grupo", "ContaOrigem"],
        [["  CONTA Y  ", "  GRUPO A  ", "  10  "]],
    )
    linhas = excel_reader.read_accounts(caminho)
    assert linhas[0].nome == "CONTA Y"
    assert linhas[0].grupo == "GRUPO A"
    assert linhas[0].conta_origem == "10"


def test_falta_coluna_obrigatoria(make_workbook):
    caminho = make_workbook(
        ["Nome", "Grupo"],
        [["CONTA A", "GRUPO A"]],
    )
    with pytest.raises(ExcelReadError):
        excel_reader.read_accounts(caminho)


def test_arquivo_inexistente():
    with pytest.raises(ExcelReadError):
        excel_reader.read_accounts("caminho/que/nao/existe.xlsx")


def test_planilha_sem_contas_validas(make_workbook):
    caminho = make_workbook(["Nome", "Grupo", "ContaOrigem"], [])
    with pytest.raises(ExcelReadError):
        excel_reader.read_accounts(caminho)


def test_preserva_zero_a_esquerda_quando_texto(tmp_path):
    import openpyxl

    caminho = tmp_path / "codigos_texto.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["Nome", "Grupo", "ContaOrigem"])
    ws.append(["CONTA COM ZERO", "GRUPO A", "007"])
    ws["C2"].number_format = "@"  # célula formatada como texto
    wb.save(caminho)

    linhas = excel_reader.read_accounts(str(caminho))
    assert linhas[0].conta_origem == "007"
