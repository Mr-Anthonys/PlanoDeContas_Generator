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


class FakeCursor:
    """Cursor DB-API falso: registra cada SQL executado e pode ser
    configurado para falhar numa chamada específica (fail_on_call, 1-based)
    ou quando o texto do lote contém um determinado trecho
    (fail_on_substring) — usado para simular erro no meio de um script real
    sem depender do número exato de lotes do template."""

    def __init__(self, fail_on_call=None, fail_on_substring=None, columns=None, rows=None):
        self.executed = []
        self.executed_many = []  # [(sql, [params, ...]), ...] — chamadas via executemany
        self.fail_on_call = fail_on_call
        self.fail_on_substring = fail_on_substring
        self._call_count = 0
        # Suporte a SELECT: description no formato DB-API (lista de tuplas,
        # só o nome da coluna importa aqui) e as linhas a devolver.
        self.description = [(coluna,) for coluna in columns] if columns else []
        self._rows = rows if rows is not None else []

    def _registrar_e_verificar_falha(self, sql):
        self._call_count += 1
        self.executed.append(sql)
        if self.fail_on_call is not None and self._call_count == self.fail_on_call:
            raise RuntimeError(f"erro simulado na chamada {self._call_count}")
        if self.fail_on_substring is not None and self.fail_on_substring in sql:
            raise RuntimeError(f"erro simulado ao encontrar: {self.fail_on_substring!r}")

    def execute(self, sql, *params):
        self._registrar_e_verificar_falha(sql)

    def executemany(self, sql, seq_of_params):
        self._registrar_e_verificar_falha(sql)
        self.executed_many.append((sql, list(seq_of_params)))

    def fetchall(self):
        return self._rows


class FakeConnection:
    def __init__(self, cursor=None):
        self._cursor = cursor if cursor is not None else FakeCursor()
        self.closed = False

    def cursor(self):
        return self._cursor

    def close(self):
        self.closed = True


@pytest.fixture
def fake_cursor():
    return FakeCursor()


@pytest.fixture
def fake_connection(fake_cursor):
    return FakeConnection(fake_cursor)
