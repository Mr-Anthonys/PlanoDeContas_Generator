"""Execução de scripts T-SQL com separadores 'GO', como o SSMS/SMO fazem.

pyodbc (e DB-API em geral) não entende 'GO' — não é um comando SQL, é uma
convenção de cliente (sqlcmd/SSMS/SMO) para separar lotes. Esse módulo faz
essa divisão manualmente antes de executar cada lote com o cursor.
"""

import re
from dataclasses import dataclass
from typing import Callable, Optional

_GO_PATTERN = re.compile(r"^[ \t]*GO[ \t]*$", re.IGNORECASE | re.MULTILINE)
_PLACEHOLDER_PATTERN = re.compile(r"\$[A-Z_]+")
_LINE_COMMENT_PATTERN = re.compile(r"--.*$", re.MULTILINE)


def split_batches(script_text: str) -> list[str]:
    """Divide um script T-SQL em lotes: uma linha contendo só 'GO'
    (case-insensitive, espaços ao redor permitidos) separa lotes — mesma
    convenção usada pelo SSMS/SMO. Scripts sem nenhum 'GO' viram um único
    lote."""
    normalizado = script_text.replace("\r\n", "\n")
    partes = _GO_PATTERN.split(normalizado)
    return [p.strip() for p in partes if p.strip()]


def substitute_placeholders(text: str, valores: dict) -> str:
    """Troca cada `$PLACEHOLDER` pelo valor correspondente. Ordena as
    chaves da mais longa para a mais curta para evitar que um placeholder
    prefixo de outro (ex.: $BASE_NOVA vs $BASE_USUARIO não colidem, mas
    $CART_ID vs um futuro $CART_IDADE colidiria) seja substituído parcial."""
    for chave in sorted(valores, key=len, reverse=True):
        text = text.replace(chave, str(valores[chave]))
    return text


def find_unresolved_placeholders(text: str) -> list:
    """Detecta tokens '$ALGO' que sobraram após a substituição — indica um
    placeholder ausente do dicionário passado (evita enviar o literal
    '$BASE_NOVA' ao servidor por engano). Ignora comentários de linha
    ('-- ...'): alguns templates trazem exemplos comentados que citam
    placeholders (ex.: $USER, $NOME_DEV) que não fazem parte do lote
    realmente executado."""
    sem_comentarios = _LINE_COMMENT_PATTERN.sub("", text)
    return sorted(set(_PLACEHOLDER_PATTERN.findall(sem_comentarios)))


@dataclass
class BatchProgress:
    step_name: str
    batch_index: int
    total_batches: int
    sql_preview: str


class SqlStepError(Exception):
    def __init__(self, step_name: str, batch_index: int, total_batches: int, original: Exception):
        super().__init__(f"Falha em '{step_name}' (lote {batch_index}/{total_batches}): {original}")
        self.step_name = step_name
        self.batch_index = batch_index
        self.total_batches = total_batches
        self.original = original


def run_sql_script(
    cursor,
    template_path: str,
    placeholders: dict,
    step_name: str,
    on_batch: Optional[Callable[[BatchProgress], None]] = None,
) -> int:
    """Lê um template .sql, substitui os placeholders, divide em lotes e
    executa lote a lote. Levanta SqlStepError no primeiro lote que falhar
    (nenhum lote seguinte é executado) — implementa "parar imediatamente
    no primeiro erro"."""
    with open(template_path, "r", encoding="utf-8-sig") as f:
        raw = f.read()

    texto = substitute_placeholders(raw, placeholders)
    faltando = find_unresolved_placeholders(texto)
    if faltando:
        raise SqlStepError(step_name, 0, 0, ValueError(f"Placeholders não resolvidos: {faltando}"))

    lotes = split_batches(texto)
    for i, lote in enumerate(lotes, start=1):
        if on_batch:
            on_batch(BatchProgress(step_name, i, len(lotes), lote[:120]))
        try:
            cursor.execute(lote)
        except Exception as exc:
            raise SqlStepError(step_name, i, len(lotes), exc) from exc
    return len(lotes)
