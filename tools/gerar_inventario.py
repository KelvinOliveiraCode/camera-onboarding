"""Gera o inventario inicial com 24 cameras simuladas.

Generate the initial inventory with 24 simulated cameras.

Vinte e duas saudaveis e duas com problema individual: uma com senha padrao
ainda ativa (sera corrigida no onboarding) e uma com IP fora da faixa
(sera sinalizada, nao processada). O criterio de aceite exige falhas
individuais registradas sem abortar o lote, e e por isso que elas existem.
"""

from __future__ import annotations

import csv
import random
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DESTINO = RAIZ / "dados" / "inventario-inicial.csv"

SEMENTE = 20261003

CABECALHO = ("nome", "ip", "andar", "usuario", "senha", "vlan", "ntp", "estado")


def principal() -> int:
    """Gera o CSV.

    Generate the CSV.

    Returns:
        Sempre 0.
    """
    rng = random.Random(SEMENTE)
    andares = ["TERREO", "PRIMEIRO", "SEGUNDO", "COBERTURA"]
    linhas = [CABECALHO]
    for indice in range(1, 25):
        andar = andares[(indice - 1) // 6]
        senha = "admin123" if indice == 7 else "FICTICIA"
        ip = "10.99.99.99" if indice == 13 else f"192.168.30.{10 + indice}"
        linhas.append((
            f"CLI-{andar}-CAM-{indice:03d}",
            ip,
            andar,
            "admin",
            senha,
            "30",
            "192.168.30.1",
            "pendente",
        ))

    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    with open(DESTINO, "w", encoding="utf-8", newline="") as fh:
        escritor = csv.writer(fh)
        escritor.writerows(linhas)

    print(f"inventario gravado em {DESTINO.relative_to(RAIZ)}: 24 cameras")
    print("casos individuais: CAM-007 com senha padrao, CAM-013 com IP fora da faixa")
    return 0


if __name__ == "__main__":
    raise SystemExit(principal())