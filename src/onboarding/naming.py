"""Padrao de nomenclatura das cameras.

Camera naming standard.

O formato e `CLI-ANDAR-CAM-001`: cliente, andar, o literal `CAM` e o numero
sequencial com tres digitos. Cada parte existe por um motivo operacional, e
nenhuma e decoracao:

- **cliente** (`CLI`): quem e o dono. Numa prestadora com varios clientes no
  mesmo NVR, o nome sem dono obriga a abrir o cadastro para saber de quem e
  a camera que caiu.
- **andar** (`ANDAR`): onde fisicamente. O tecnico que sobe a escada com a
  escada precisa saber para onde ir sem abrir planta.
- **`CAM`**: o tipo. Distingue de `NVR`, `SW` e `SRV` no mesmo inventario.
- **numero** (`001`): ordem de cadastro, nao de instalacao. Numero nunca e
  reutilizado: uma camera removida deixa o buraco, e o buraco conta a
  historia de que ali ja houve uma camera.

## Por que tres digitos e maiusculas

Ordenacao lexicografica: `CAM-001` vem antes de `CAM-010` em qualquer
listagem, planilha ou `ls`. Com dois digitos, a camera 100 quebra a ordem;
com minusculas, `cam-1` e `CAM-01` viram duas cameras diferentes num
inventario que alguem edita a mao.

## O que o validador recusa

Nome fora do padrao nao e "quase certo": e outra coisa. `CLI-ANDAR-001` (sem
o `CAM`) e `CLI-ANDAR-CAM-1` (sem o zero) sao recusados, porque aceitar
"quase" cria duas formas de dizer a mesma coisa - e duas formas viram vinte
quando cada tecnico inventa a sua.
"""

from __future__ import annotations

import re

# O padrao completo, ancorado. Nada antes, nada depois: nome com sufixo e
# outro nome, nao variacao deste.
PADRAO = re.compile(r"^([A-Z]{2,6})-([A-Z]{2,10})-CAM-(\d{3})$")

# Partes minimas para montar um nome sem validacao parcial.
CLIENTE_PADRAO = "CLI"
TIPO_FIXO = "CAM"


class ErroDeNome(Exception):
    """O nome nao segue o padrao.

    The name does not follow the standard.
    """


def montar(cliente: str, andar: str, numero: int) -> str:
    """Monta um nome no padrao.

    Build a standard name.

    Args:
        cliente: A sigla do cliente, 2 a 6 letras maiusculas.
        andar: O andar, 2 a 10 letras maiusculas.
        numero: O sequencial, de 1 a 999.

    Returns:
        O nome montado.

    Raises:
        ErroDeNome: Se alguma parte violar o padrao.
    """
    cliente = str(cliente).strip().upper()
    andar = str(andar).strip().upper()
    if not re.fullmatch(r"[A-Z]{2,6}", cliente):
        raise ErroDeNome(
            f"cliente {cliente!r} fora do padrao: 2 a 6 letras maiusculas"
        )
    if not re.fullmatch(r"[A-Z]{2,10}", andar):
        raise ErroDeNome(
            f"andar {andar!r} fora do padrao: 2 a 10 letras maiusculas"
        )
    if not 1 <= int(numero) <= 999:
        raise ErroDeNome(f"numero {numero!r} fora de 1..999")
    return f"{cliente}-{andar}-{TIPO_FIXO}-{int(numero):03d}"


def validar(nome: str) -> tuple[str, str, int]:
    """Valida e decompoe um nome.

    Validate and decompose a name.

    Args:
        nome: O nome a validar.

    Returns:
        O trio `(cliente, andar, numero)`.

    Raises:
        ErroDeNome: Se o nome nao seguir o padrao.
    """
    correspondencia = PADRAO.match(str(nome).strip())
    if correspondencia is None:
        raise ErroDeNome(
            f"nome {nome!r} fora do padrao CLI-ANDAR-CAM-001 "
            "(cliente 2-6 letras, andar 2-10 letras, numero com 3 digitos)"
        )
    cliente, andar, numero = correspondencia.groups()
    return cliente, andar, int(numero)


def proximo_numero(nomes: list[str], cliente: str, andar: str) -> int:
    """O proximo sequencial livre para um par cliente/andar.

    The next free sequence for a client/floor pair.

    Numero nunca e reutilizado: o buraco de uma camera removida continua
    buraco. Reutilizar numero faria o historico de duas cameras se misturar
    no mesmo identificador.

    Args:
        nomes: Os nomes ja existentes.
        cliente: A sigla do cliente.
        andar: O andar.

    Returns:
        O menor numero acima do maior usado, ou 1 se nao houver nenhum.
    """
    usados = [
        validar(nome)[2]
        for nome in nomes
        if nome.startswith(f"{cliente}-{andar}-CAM-")
    ]
    return max(usados, default=0) + 1