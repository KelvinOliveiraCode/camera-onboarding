"""Prova de aceite do onboarding.

onboarding acceptance proof.

O criterio de aceite tem tres partes:

1. **24 cameras processadas em 2 execucoes**, sem duplicata no inventario.
   Rodar duas vezes e parte do criterio, nao detalhe: idempotencia so existe
   se for exercitada.
2. **Sem duplicata.** A segunda execucao nao acrescenta linha nenhuma.
3. **Falhas individuais registradas sem abortar o lote.** A camera com IP
   fora da faixa aparece no log com o motivo, e as outras 23 passam.
"""

from __future__ import annotations

import contextlib
import io
import shutil
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from onboarding.cli import main as cli_main  # noqa: E402

FAIXA = RAIZ / "dados" / "faixa-alvo.yaml"
INVENTARIO = RAIZ / "dados" / "inventario-inicial.csv"

TOTAL_ESPERADO = 24
FALHA_ESPERADA = "CLI-SEGUNDO-CAM-013"


class Falha(Exception):
    """Uma condicao de aceite nao foi satisfeita."""


def checar(condicao: bool, mensagem: str) -> None:
    """Falha se a condicao e falsa.

    Args:
        condicao: A condicao.
        mensagem: O que deu errado.

    Raises:
        Falha: Se a condicao for falsa.
    """
    if not condicao:
        raise Falha(mensagem)


def _roda(inventario: Path, log: Path) -> tuple[int, str]:
    """Roda o CLI capturando a saida.

    Args:
        inventario: O CSV de trabalho.
        log: Onde gravar o relatorio.

    Returns:
        O par `(codigo, saida)`.
    """
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        codigo = cli_main([
            "executar", "--faixa", str(FAIXA),
            "--inventario", str(inventario),
            "--log", str(log),
        ])
    return codigo, buffer.getvalue()


def _linhas(inventario: Path) -> int:
    """Quantas linhas de dados tem o CSV.

    Args:
        inventario: O CSV.

    Returns:
        O numero de linhas menos o cabecalho.
    """
    return len(inventario.read_text(encoding="utf-8").strip().splitlines()) - 1


def principal() -> int:
    """Roda a prova de aceite.

    Returns:
        0 se tudo passar, 1 se alguma condicao falhar.
    """
    try:
        with tempfile.TemporaryDirectory() as tmp:
            trabalho = Path(tmp) / "inv.csv"
            shutil.copy(INVENTARIO, trabalho)

            codigo1, saida1 = _roda(trabalho, Path(tmp) / "log1.md")
            checar("24" in saida1, "a primeira execucao nao processou 24")
            checar(_linhas(trabalho) == TOTAL_ESPERADO, "inventario mudou de tamanho")
            print("1) primeira execucao processa as 24 cameras")

            codigo2, _ = _roda(trabalho, Path(tmp) / "log2.md")
            checar(
                _linhas(trabalho) == TOTAL_ESPERADO,
                "a segunda execucao duplicou entrada",
            )
            print("2) segunda execucao nao duplica nada")

            log = Path(tmp) / "log2.md"
            texto = log.read_text(encoding="utf-8")
            checar(FALHA_ESPERADA in texto, "a falha individual nao esta no log")
            checar("faixa-alvo" in texto, "o motivo da falha nao esta no log")
            checar(codigo2 == 1, f"codigo de saida {codigo2}, esperado 1")
            print("3) falha individual registrada com motivo, lote nao abortou")
    except Falha as erro:
        print("\nACEITE FALHOU:")
        print(f"  - {erro}")
        return 1

    print("\nok: 24 em 2 execucoes, sem duplicata, falha registrada")
    return 0


if __name__ == "__main__":
    raise SystemExit(principal())