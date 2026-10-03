"""A linha de comando do onboarding.

The onboarding command line.

Um comando: `executar` processa o inventario inteiro - configura cada camera,
registra no inventario sem duplicar, e escreve o log. Falha individual vira
linha no relatorio, nunca aborta o lote: uma camera com problema nao pode
parar as outras 23.

## Idempotencia

Rodar duas vezes nao duplica entrada no inventario nem gera erro. O registro
e por nome: se a camera ja esta la, a entrada e atualizada. E o criterio de
aceite passa por aqui - 24 cameras em 2 execucoes, sem duplicata.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

from . import configurador as modulo_configurador
from . import inventario as modulo_inventario
from . import relatorio as modulo_relatorio

SAIDA_OK = 0
SAIDA_FALHA = 1
SAIDA_ERRO = 2


def _constroi_parser() -> argparse.ArgumentParser:
    """Monta o parser de argumentos.

    Build the argument parser.

    Returns:
        O parser pronto.
    """
    parser = argparse.ArgumentParser(
        prog="onboarding",
        description=(
            "Onboarding automatico e idempotente de cameras. / "
            "Automatic, idempotent camera onboarding."
        ),
    )
    sub = parser.add_subparsers(dest="comando", required=True)

    p_exe = sub.add_parser("executar", help="processa o inventario inteiro")
    p_exe.add_argument("--faixa", required=True, help="o YAML da faixa-alvo")
    p_exe.add_argument("--inventario", required=True, help="o CSV de inventario")
    p_exe.add_argument("--log", required=True, help="onde gravar o relatorio")

    return parser


def _faixa_de(caminho: str | Path) -> tuple[str, str, str]:
    """Le a faixa-alvo do disco.

    Read the target range from disk.

    Args:
        caminho: O YAML.

    Returns:
        O trio `(faixa, ntp, senha_padrao)`.
    """
    documento = yaml.safe_load(Path(caminho).read_text(encoding="utf-8")) or {}
    return (
        str(documento.get("faixa", "")),
        str(documento.get("ntp", "")),
        str(documento.get("senha_padrao", "")),
    )


def _cmd_executar(args: argparse.Namespace, destino) -> int:
    """Executa `executar`.

    Run `executar`.

    Args:
        args: Os argumentos.
        destino: Onde imprimir.

    Returns:
        O codigo de saida.
    """
    faixa, ntp, _ = _faixa_de(args.faixa)
    try:
        entradas = modulo_inventario.carregar(args.inventario)
    except Exception as erro:
        print(f"erro de inventario: {erro}", file=sys.stderr)
        return SAIDA_ERRO

    resultados = []
    for entrada in entradas:
        config = modulo_configurador.Configuracao(
            vlan=str(entrada.get("vlan", "30")),
            ntp=ntp or str(entrada.get("ntp", "")),
            usuario=str(entrada.get("usuario", "admin")),
            senha_nova="Nova" + str(entrada.get("nome", ""))[-3:],
        )
        resultado = modulo_configurador.configurar(
            str(entrada.get("nome", "")),
            str(entrada.get("ip", "")),
            config,
            faixa=faixa or None,
        )
        resultados.append(resultado)
        if resultado.ok:
            modulo_inventario.registrar(
                args.inventario,
                {**entrada, "estado": "configurada"},
            )

    texto = modulo_relatorio.gerar([
        {
            "nome": r.nome,
            "estado": "ok" if r.ok else "falha",
            "motivo": r.erro or "",
            "etapas": list(r.etapas),
        }
        for r in resultados
    ])
    modulo_relatorio.salvar(texto, args.log)

    oks = sum(1 for r in resultados if r.ok)
    print(f"cameras processadas: {len(resultados)}", file=destino)
    print(f"configuradas: {oks}  com falha: {len(resultados) - oks}", file=destino)
    print(f"log gravado em {args.log}", file=destino)
    return SAIDA_OK if oks == len(resultados) else SAIDA_FALHA


def main(argv: list[str] | None = None) -> int:
    """O ponto de entrada.

    The entry point.

    Args:
        argv: Os argumentos, sem `argv[0]`.

    Returns:
        O codigo de saida.
    """
    parser = _constroi_parser()
    args = parser.parse_args(argv)
    if args.comando == "executar":
        return _cmd_executar(args, sys.stdout)
    parser.error(f"comando desconhecido: {args.comando}")
    return SAIDA_ERRO


if __name__ == "__main__":
    main()