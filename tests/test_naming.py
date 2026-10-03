"""Testes da nomenclatura.

Naming tests.

O padrao e o contrato que todo o resto consome: descoberta, configurador,
inventario e relatorio leem nomes neste formato. Um nome fora do padrao que
passa aqui vira duas formas de dizer a mesma coisa la - e duas viram vinte.
"""

from __future__ import annotations

import pytest

from onboarding.naming import ErroDeNome, montar, proximo_numero, validar


class TestMontar:
    """A construcao."""

    def test_basico(self) -> None:
        assert montar("CLI", "TERREO", 1) == "CLI-TERREO-CAM-001"

    def test_tres_digitos(self) -> None:
        assert montar("CLI", "PATIO", 7) == "CLI-PATIO-CAM-007"

    def test_maiusculas_forcadas(self) -> None:
        assert montar("cli", "terreo", 1) == "CLI-TERREO-CAM-001"

    def test_numero_limite(self) -> None:
        assert montar("CLI", "PATIO", 999) == "CLI-PATIO-CAM-999"
        with pytest.raises(ErroDeNome):
            montar("CLI", "PATIO", 1000)
        with pytest.raises(ErroDeNome):
            montar("CLI", "PATIO", 0)

    def test_cliente_invalido(self) -> None:
        with pytest.raises(ErroDeNome):
            montar("C", "TERREO", 1)
        with pytest.raises(ErroDeNome):
            montar("CLIENTE-LONGO", "TERREO", 1)


class TestValidar:
    """A validacao e decomposicao."""

    def test_valido(self) -> None:
        assert validar("CLI-TERREO-CAM-001") == ("CLI", "TERREO", 1)

    def test_sem_cam(self) -> None:
        with pytest.raises(ErroDeNome):
            validar("CLI-TERREO-001")

    def test_sem_zero(self) -> None:
        with pytest.raises(ErroDeNome):
            validar("CLI-TERREO-CAM-1")

    def test_minusculas(self) -> None:
        with pytest.raises(ErroDeNome):
            validar("cli-terreo-cam-001")

    def test_sufixo(self) -> None:
        with pytest.raises(ErroDeNome):
            validar("CLI-TERREO-CAM-001-X")


class TestProximo:
    """O sequencial nunca reutiliza."""

    def test_proximo_livre(self) -> None:
        nomes = ["CLI-TERREO-CAM-001", "CLI-TERREO-CAM-003"]
        assert proximo_numero(nomes, "CLI", "TERREO") == 4

    def test_buraco_nao_reutiliza(self) -> None:
        # O 2 foi removido; o proximo continua sendo 4, nao 2. Numero
        # reutilizado mistura o historico de duas cameras.
        nomes = ["CLI-TERREO-CAM-001", "CLI-TERREO-CAM-003"]
        assert proximo_numero(nomes, "CLI", "TERREO") != 2

    def test_outro_andar_nao_conta(self) -> None:
        nomes = ["CLI-PRIMEIRO-CAM-005"]
        assert proximo_numero(nomes, "CLI", "TERREO") == 1

    def test_vazio_comeca_no_um(self) -> None:
        assert proximo_numero([], "CLI", "TERREO") == 1