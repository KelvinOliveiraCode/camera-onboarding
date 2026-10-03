"""Log de onboarding em markdown.

Markdown onboarding log.

Resume um lote de onboarding: uma tabela com o estado de cada camera, a
contagem de OK e de falhas, e a lista de falhas com o motivo de cada uma.
"""

from __future__ import annotations

import os

# Colunas canonicas da tabela de cameras.
COLUNAS = ["nome", "ip", "andar", "vlan", "estado"]

# Estados considerados no relatorio.
ESTADO_OK = "ok"

# Chave onde uma camera falha guarda o motivo.
CHAVE_MOTIVO = "motivo"

MOTIVO_PADRAO = "sem motivo informado"


def _estado(entrada: dict) -> str:
    """O estado normalizado (minusculas, sem espacos) de uma camera.

    The normalized state of a camera in the batch.
    """
    return str(entrada.get("estado", "")).strip().lower()


def _colunas(resultados: list[dict]) -> list[str]:
    """As colunas canonicas presentes em pelo menos um resultado.

    Canonical columns present in at least one result.
    """
    vistas = set()
    for resultado in resultados:
        vistas.update(resultado.keys())
    return [coluna for coluna in COLUNAS if coluna in vistas] or list(COLUNAS)


def gerar(resultados: list[dict]) -> str:
    """Gera o log de onboarding de um lote em markdown.

    Build the markdown onboarding log for a batch.

    Args:
        resultados: Um dict por camera processada, com o `estado` ("ok" ou
            "falha") e, nas falhas, o `motivo`.

    Returns:
        O log em markdown, com tabela por camera, contagens de ok e falha,
        e a lista de falhas com o motivo.
    """
    if not resultados:
        return (
            "# Log de Onboarding\n"
            "\n"
            "Nada foi processado neste lote.\n"
        )
    falhas = [r for r in resultados if _estado(r) != ESTADO_OK]
    ok = len(resultados) - len(falhas)
    colunas = _colunas(resultados)
    linhas = [
        "# Log de Onboarding",
        "",
        "## Resumo",
        "",
        f"- Processadas: {len(resultados)}",
        f"- OK: {ok}",
        f"- Falhas: {len(falhas)}",
        "",
        "## Cameras",
        "",
        "| " + " | ".join(colunas) + " |",
        "| " + " | ".join("---" for _ in colunas) + " |",
    ]
    for resultado in resultados:
        linhas.append(
            "| "
            + " | ".join(str(resultado.get(c, "")).strip() for c in colunas)
            + " |"
        )
    linhas += ["", "## Falhas", ""]
    if falhas:
        for falha in falhas:
            motivo = str(falha.get(CHAVE_MOTIVO, "")).strip() or MOTIVO_PADRAO
            linhas.append(
                f"- {str(falha.get('nome', '?')).strip()}: {motivo}"
            )
    else:
        linhas.append("Sem falhas neste lote.")
    return "\n".join(linhas) + "\n"


def salvar(texto: str, caminho: str) -> None:
    """Grava o log em UTF-8.

    Write the log as UTF-8.

    Args:
        texto: O log markdown gerado.
        caminho: Caminho do arquivo de destino.
    """
    diretorio = os.path.dirname(caminho)
    if diretorio:
        os.makedirs(diretorio, exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as arquivo:
        arquivo.write(texto)
