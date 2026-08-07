import openpyxl
import pytest


def _save_workbook(path, headers, rows):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(headers)
    for row in rows:
        ws.append(row)
    wb.save(path)
    return path


@pytest.fixture
def make_workbook(tmp_path):
    """Fixture que cria um .xlsx temporário com cabeçalhos e linhas arbitrárias."""

    def _make(headers, rows, filename="planilha.xlsx"):
        caminho = tmp_path / filename
        return str(_save_workbook(caminho, headers, rows))

    return _make
