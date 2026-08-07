"""Leitura e normalização da planilha de importação (.xlsx).

A planilha de entrada deve conter apenas as colunas Nome, Grupo e ContaOrigem
(aceitando variações de cabeçalho). Este módulo não faz nenhuma validação de
regra de negócio (duplicidade, formato de código etc.) — isso é feito por
`validation_service`. Aqui apenas lemos e normalizamos os dados brutos.
"""

import unicodedata
import zipfile

import openpyxl
from openpyxl.utils.exceptions import InvalidFileException

from src.utils.constants import CABECALHOS_NOME, CABECALHOS_GRUPO, CABECALHOS_CONTA_ORIGEM


class ExcelReadError(Exception):
    """Erro amigável ao tentar ler a planilha de importação."""


class RawRow:
    """Uma linha bruta lida da planilha, já com espaços removidos."""

    def __init__(self, linha: int, nome: str, grupo: str, conta_origem: str):
        self.linha = linha
        self.nome = nome
        self.grupo = grupo
        self.conta_origem = conta_origem


def _normalize_header(texto: str) -> str:
    """Remove acentos, espaços extras e caixa para comparar cabeçalhos."""
    if texto is None:
        return ""
    texto = str(texto).strip().lower()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return texto


def _build_header_map(header_row):
    """Retorna um dict {'nome': col_index, 'grupo': col_index, 'conta_origem': col_index}."""
    aliases = {
        "nome": [_normalize_header(h) for h in CABECALHOS_NOME],
        "grupo": [_normalize_header(h) for h in CABECALHOS_GRUPO],
        "conta_origem": [_normalize_header(h) for h in CABECALHOS_CONTA_ORIGEM],
    }
    encontrados = {}
    for idx, cell_value in enumerate(header_row):
        normalizado = _normalize_header(cell_value)
        if not normalizado:
            continue
        for campo, lista in aliases.items():
            if normalizado in lista and campo not in encontrados:
                encontrados[campo] = idx
    return encontrados


def _cell_to_text(valor) -> str:
    """Converte o valor de uma célula para texto, preservando zeros à esquerda
    quando o valor já foi lido como string pelo openpyxl (célula formatada como
    Texto). Quando a célula é numérica, converte para string sem casas
    decimais desnecessárias (ex.: 1.0 -> '1')."""
    if valor is None:
        return ""
    if isinstance(valor, float):
        if valor.is_integer():
            return str(int(valor))
        return str(valor)
    return str(valor).strip()


def read_accounts(caminho_arquivo: str):
    """Lê a planilha de importação e retorna uma lista de RawRow.

    Lança ExcelReadError com mensagem amigável quando o arquivo não puder ser
    lido (corrompido, bloqueado/aberto por outro programa) ou quando as
    colunas obrigatórias não forem encontradas.
    """
    try:
        workbook = openpyxl.load_workbook(caminho_arquivo, data_only=True, read_only=True)
    except FileNotFoundError:
        raise ExcelReadError(f"Arquivo não encontrado: {caminho_arquivo}")
    except PermissionError:
        raise ExcelReadError(
            "Não foi possível abrir o arquivo. Verifique se ele não está aberto "
            "em outro programa (ex.: Excel) e tente novamente."
        )
    except (InvalidFileException, zipfile.BadZipFile, OSError, KeyError) as exc:
        raise ExcelReadError(f"O arquivo selecionado parece estar corrompido ou não é um .xlsx válido ({exc}).")

    try:
        sheet = workbook.active
        rows_iter = sheet.iter_rows(values_only=True)
        try:
            header_row = next(rows_iter)
        except StopIteration:
            raise ExcelReadError("A planilha está vazia.")

        header_map = _build_header_map(header_row)
        faltando = [campo for campo in ("nome", "grupo", "conta_origem") if campo not in header_map]
        if faltando:
            nomes_amigaveis = {"nome": "Nome", "grupo": "Grupo", "conta_origem": "ContaOrigem"}
            faltando_txt = ", ".join(nomes_amigaveis[f] for f in faltando)
            raise ExcelReadError(
                f"A planilha não possui a(s) coluna(s) obrigatória(s): {faltando_txt}. "
                "Verifique o cabeçalho e tente novamente."
            )

        linhas = []
        for numero_linha, row in enumerate(rows_iter, start=2):
            if row is None:
                continue
            if all(v is None or str(v).strip() == "" for v in row):
                continue

            def valor(campo):
                idx = header_map[campo]
                return row[idx] if idx < len(row) else None

            nome = _cell_to_text(valor("nome"))
            grupo = _cell_to_text(valor("grupo"))
            conta_origem = _cell_to_text(valor("conta_origem"))

            if nome == "" and grupo == "" and conta_origem == "":
                continue

            linhas.append(RawRow(numero_linha, nome, grupo, conta_origem))

        if not linhas:
            raise ExcelReadError("Não há contas válidas na planilha (nenhuma linha com dados foi encontrada).")

        return linhas
    finally:
        workbook.close()
