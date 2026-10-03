"""Registro idempotente do inventario de cameras em CSV.

Idempotent camera inventory registry in CSV.

O arquivo segue o cabecalho `nome, ip, andar, usuario, senha, vlan, ntp,
estado`. `nome` e a chave do registro: registrar o mesmo nome duas vezes
atualiza a linha existente em vez de criar uma segunda linha.
"""

from __future__ import annotations

import csv
import os

# Colunas canonicas do inventario, na ordem do cabecalho inicial.
CAMPOS_PADRAO = ["nome", "ip", "andar", "usuario", "senha", "vlan", "ntp", "estado"]

# Chave que identifica uma camera no inventario.
CHAVE = "nome"


def _limpar(valor) -> str:
    """Normaliza um valor de celula para texto sem espacos nas pontas.

    Normalize a cell value to stripped text.
    """
    if valor is None:
        return ""
    return str(valor).strip()


def carregar(caminho: str) -> list[dict]:
    """Le o inventario CSV e devolve uma lista de dicts.

    Load the CSV inventory as a list of dicts.

    Args:
        caminho: Caminho do arquivo CSV com o cabecalho do inventario.

    Returns:
        Uma lista de dicts, uma por camera; vazia se o arquivo nao existir
        ou nao tiver linhas de dados.
    """
    if not os.path.exists(caminho):
        return []
    with open(caminho, newline="", encoding="utf-8") as arquivo:
        leitor = csv.DictReader(arquivo)
        entradas = []
        for linha in leitor:
            entrada = {}
            for campo, valor in linha.items():
                if campo is None:
                    continue
                entrada[str(campo).strip()] = _limpar(valor)
            entradas.append(entrada)
        return entradas


def _campos(entradas: list[dict]) -> list[str]:
    """Ordem das colunas a gravar no cabecalho.

    Column order to write in the header.

    A chave vem primeiro, depois as colunas encontradas nos dicts na ordem
    de aparecimento, e por ultimo as colunas canonicas que faltarem.
    """
    ordem = [CHAVE]
    for entrada in entradas:
        for campo in entrada:
            if campo not in ordem:
                ordem.append(campo)
    for campo in CAMPOS_PADRAO:
        if campo not in ordem:
            ordem.append(campo)
    return ordem


def salvar(caminho: str, entradas: list[dict]) -> None:
    """Grava o inventario completo no CSV.

    Write the full inventory to CSV.

    Args:
        caminho: Caminho do arquivo CSV de destino.
        entradas: A lista de dicts a gravar, na ordem dada.
    """
    campos = _campos(entradas)
    with open(caminho, "w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos, extrasaction="ignore")
        escritor.writeheader()
        for entrada in entradas:
            escritor.writerow(
                {campo: _limpar(entrada.get(campo, "")) for campo in campos}
            )


def registrar(caminho: str, entrada: dict) -> list[dict]:
    """Acrescenta ou atualiza uma camera pelo nome, sem duplicar.

    Add or update a camera by name, keeping exactly one row per name.

    Registar de novo o mesmo nome atualiza a linha existente (o estado novo
    vira o estado da camera) em vez de criar uma segunda linha.

    Args:
        caminho: Caminho do CSV do inventario.
        entrada: Dict com a camera; o campo `nome` e obrigatoria.

    Returns:
        A lista completa de entradas apos o registro.

    Raises:
        ValueError: Se a entrada nao tiver um nome nao vazio.
    """
    nome = _limpar(entrada.get(CHAVE, ""))
    if not nome:
        raise ValueError("entrada sem o campo 'nome'")
    entrada = dict(entrada)
    entrada[CHAVE] = nome
    entradas = carregar(caminho)
    for indice, existente in enumerate(entradas):
        if _limpar(existente.get(CHAVE, "")) == nome:
            atualizada = dict(existente)
            for campo, valor in entrada.items():
                atualizada[campo] = _limpar(valor)
            entradas[indice] = atualizada
            salvar(caminho, entradas)
            return entradas
    entradas.append(entrada)
    salvar(caminho, entradas)
    return entradas
