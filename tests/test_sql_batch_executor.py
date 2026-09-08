import pytest

from src.services.sql_batch_executor import (
    SqlStepError,
    find_unresolved_placeholders,
    run_sql_script,
    split_batches,
    substitute_placeholders,
)
from tests.conftest import FakeCursor


# ---------------------------------------------------------------------------
# split_batches
# ---------------------------------------------------------------------------
def test_split_batches_go_maiusculo():
    assert split_batches("SELECT 1\nGO\nSELECT 2") == ["SELECT 1", "SELECT 2"]


def test_split_batches_go_minusculo_e_misto():
    assert split_batches("SELECT 1\ngo\nSELECT 2\nGo\nSELECT 3") == ["SELECT 1", "SELECT 2", "SELECT 3"]


def test_split_batches_go_com_espacos_ao_redor():
    assert split_batches("SELECT 1\n  GO  \nSELECT 2") == ["SELECT 1", "SELECT 2"]


def test_split_batches_sem_go_vira_lote_unico():
    assert split_batches("SELECT 1\nSELECT 2") == ["SELECT 1\nSELECT 2"]


def test_split_batches_go_no_final_sem_lote_vazio_depois():
    assert split_batches("SELECT 1\nGO\n") == ["SELECT 1"]


def test_split_batches_script_vazio():
    assert split_batches("") == []


def test_split_batches_nao_confunde_go_dentro_de_palavra():
    # 'GOAL' não é uma linha 'GO' isolada — não deve separar lote.
    assert split_batches("SELECT 'GOAL'") == ["SELECT 'GOAL'"]


# ---------------------------------------------------------------------------
# substitute_placeholders / find_unresolved_placeholders
# ---------------------------------------------------------------------------
def test_substitute_placeholders_prefixos_sobrepostos():
    # $BASE_NOVA é prefixo de $BASE_NOVA_X; ordenar por tamanho decrescente
    # evita que a chave mais curta seja trocada primeiro e quebre a mais longa.
    texto = "$BASE_NOVA_X e $BASE_NOVA"
    valores = {"$BASE_NOVA": "abc", "$BASE_NOVA_X": "def"}
    resultado = substitute_placeholders(texto, valores)
    assert resultado == "def e abc"


def test_find_unresolved_placeholders_detecta_faltante():
    texto = "USE [$BASE_NOVA]; SELECT '$CART_NOME'"
    faltando = find_unresolved_placeholders(substitute_placeholders(texto, {"$BASE_NOVA": "X"}))
    assert faltando == ["$CART_NOME"]


def test_find_unresolved_placeholders_ignora_comentario_de_linha():
    texto = "SELECT 1\n-- exemplo: $USER $NOME_DEV\nSELECT 2"
    assert find_unresolved_placeholders(texto) == []


def test_find_unresolved_placeholders_nenhum_faltando():
    assert find_unresolved_placeholders("SELECT 1") == []


# ---------------------------------------------------------------------------
# run_sql_script
# ---------------------------------------------------------------------------
def test_run_sql_script_executa_todos_os_lotes(tmp_path):
    caminho = tmp_path / "template.sql"
    caminho.write_text("USE [$BASE_NOVA]\nGO\nSELECT 1\nGO\nSELECT 2", encoding="utf-8")

    cursor = FakeCursor()
    total = run_sql_script(cursor, str(caminho), {"$BASE_NOVA": "Teste"}, "passo_teste")

    assert total == 3
    assert cursor.executed == ["USE [Teste]", "SELECT 1", "SELECT 2"]


def test_run_sql_script_para_no_primeiro_erro(tmp_path):
    caminho = tmp_path / "template.sql"
    caminho.write_text("SELECT 1\nGO\nSELECT 2\nGO\nSELECT 3", encoding="utf-8")

    cursor = FakeCursor(fail_on_call=2)
    with pytest.raises(SqlStepError) as excinfo:
        run_sql_script(cursor, str(caminho), {}, "passo_teste")

    assert excinfo.value.step_name == "passo_teste"
    assert excinfo.value.batch_index == 2
    assert excinfo.value.total_batches == 3
    # O terceiro lote nunca deveria ter sido executado.
    assert cursor.executed == ["SELECT 1", "SELECT 2"]


def test_run_sql_script_placeholder_faltante_nao_executa_nada(tmp_path):
    caminho = tmp_path / "template.sql"
    caminho.write_text("SELECT '$ALGO_QUE_NAO_EXISTE'", encoding="utf-8")

    cursor = FakeCursor()
    with pytest.raises(SqlStepError):
        run_sql_script(cursor, str(caminho), {}, "passo_teste")

    assert cursor.executed == []
