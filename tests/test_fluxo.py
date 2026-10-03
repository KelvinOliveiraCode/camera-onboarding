"""Testes da descoberta, configurador, inventario, relatorio e CLI.

Discovery, configurator, inventory, report and CLI tests.

A propriedade que atravessa todos estes testes e a mesma do criterio de
aceite: falha individual nao aborta o lote, e o lote processado duas vezes
nao duplica nada. Cada teste prova um lado disso.
"""

from __future__ import annotations

import contextlib
import io
from pathlib import Path

import pytest

from onboarding import configurador, descoberta, inventario, relatorio
from onboarding.configurador import Configuracao

RAIZ = Path(__file__).resolve().parent.parent
FAIXA = RAIZ / "dados" / "faixa-alvo.yaml"
INVENTARIO = RAIZ / "dados" / "inventario-inicial.csv"


def _config() -> Configuracao:
    return Configuracao(
        vlan="30", ntp="192.168.30.1",
        usuario="admin", senha_nova="NovaFicticia1",
    )


class TestDescoberta:
    """A varredura simulada."""

    def test_recusa_faixa_publica(self) -> None:
        with pytest.raises(ValueError):
            descoberta.varrer("8.8.8.0/24", [554])

    def test_aceita_faixa_privada(self) -> None:
        assert len(descoberta.varrer("192.168.30.0/24", [554, 8554])) > 0

    def test_localhost_aceito(self) -> None:
        assert descoberta.varrer("127.0.0.1/32", [554]) is not None

    def test_sem_socket(self) -> None:
        import onboarding.descoberta as modulo

        assert "socket" not in dir(modulo)

    def test_identificar(self) -> None:
        achados = descoberta.varrer("192.168.30.0/24", [554])
        assert descoberta.identificar(achados[0]) in ("camera", "desconhecido")

    def test_cidr_invalido(self) -> None:
        with pytest.raises(ValueError):
            descoberta.varrer("nao-e-rede", [554])

    def test_ipv6_recusado(self) -> None:
        with pytest.raises(ValueError):
            descoberta.varrer("::1/128", [554])

    def test_prefixo_31_dois_hosts(self) -> None:
        import ipaddress

        hosts = list(descoberta._enderecos(ipaddress.ip_network("192.168.30.0/31")))
        assert hosts == ["192.168.30.0", "192.168.30.1"]

    def test_host_unico(self) -> None:
        import ipaddress

        assert list(descoberta._enderecos(
            ipaddress.ip_network("192.168.30.5/32")
        )) == ["192.168.30.5"]


class TestConfigurador:
    """Configura ou falha com motivo, nunca com excecao."""

    def test_senha_padrao_trocada(self) -> None:
        resultado = configurador.configurar(
            "CLI-TERREO-CAM-007", "192.168.30.17", _config()
        )
        assert resultado.ok is True
        assert len(resultado.etapas) == 4

    def test_nome_ruim_falha(self) -> None:
        resultado = configurador.configurar(
            "NOME-RUIM", "192.168.30.17", _config()
        )
        assert resultado.ok is False
        assert resultado.erro

    def test_ip_fora_da_faixa_falha(self) -> None:
        resultado = configurador.configurar(
            "CLI-TERREO-CAM-013", "10.99.99.99", _config(),
            faixa="192.168.30.0/24",
        )
        assert resultado.ok is False
        assert "faixa-alvo" in resultado.erro

    def test_ip_rfc1918_sem_faixa_passa(self) -> None:
        resultado = configurador.configurar(
            "CLI-TERREO-CAM-013", "10.99.99.99", _config()
        )
        assert resultado.ok is True


class TestInventario:
    """Registro idempotente."""

    def test_carrega_24(self) -> None:
        assert len(inventario.carregar(INVENTARIO)) == 24

    def test_registrar_duas_vezes(self, tmp_path: Path) -> None:
        destino = tmp_path / "inv.csv"
        destino.write_text("nome,ip,estado\n", encoding="utf-8")
        entrada = {"nome": "CLI-A-CAM-001", "ip": "10.0.0.1", "estado": "x"}
        inventario.registrar(str(destino), dict(entrada))
        inventario.registrar(str(destino), dict(entrada))
        linhas = destino.read_text(encoding="utf-8").strip().splitlines()
        assert len(linhas) == 2

    def test_atualizar_muda_estado(self, tmp_path: Path) -> None:
        destino = tmp_path / "inv.csv"
        destino.write_text("nome,ip,estado\n", encoding="utf-8")
        inventario.registrar(
            str(destino),
            {"nome": "CLI-A-CAM-001", "ip": "10.0.0.1", "estado": "pendente"},
        )
        inventario.registrar(
            str(destino),
            {"nome": "CLI-A-CAM-001", "ip": "10.0.0.1", "estado": "configurada"},
        )
        texto = destino.read_text(encoding="utf-8")
        assert "configurada" in texto
        assert len(texto.strip().splitlines()) == 2


class TestRelatorio:
    """O log mostra a falha com motivo."""

    def test_vazio(self) -> None:
        assert len(relatorio.gerar([])) > 0

    def test_falha_com_motivo(self) -> None:
        texto = relatorio.gerar([
            {"nome": "CLI-A-CAM-001", "estado": "ok", "motivo": "", "etapas": []},
            {"nome": "CLI-A-CAM-002", "estado": "falha",
             "motivo": "IP fora da faixa", "etapas": []},
        ])
        assert "CLI-A-CAM-002" in texto
        assert "IP fora da faixa" in texto

    def test_salvar(self, tmp_path: Path) -> None:
        destino = tmp_path / "log.md"
        relatorio.salvar("# teste", str(destino))
        assert destino.exists()


class TestCli:
    """O lote inteiro, duas vezes."""

    def _roda(self, argv):
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            from onboarding.cli import main as cli_main

            codigo = cli_main(argv)
        return codigo, buffer.getvalue()

    def _copia(self, tmp_path: Path) -> Path:
        destino = tmp_path / "inv.csv"
        destino.write_bytes(INVENTARIO.read_bytes())
        return destino

    def test_24_processadas_1_falha(self, tmp_path: Path) -> None:
        from onboarding.cli import main as cli_main

        inv = self._copia(tmp_path)
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            codigo = cli_main([
                "executar", "--faixa", str(FAIXA),
                "--inventario", str(inv),
                "--log", str(tmp_path / "log.md"),
            ])
        assert codigo == 1
        assert "24" in buffer.getvalue()

    def test_segunda_vez_sem_duplicata(self, tmp_path: Path) -> None:
        from onboarding.cli import main as cli_main

        inv = self._copia(tmp_path)
        argv = [
            "executar", "--faixa", str(FAIXA),
            "--inventario", str(inv),
            "--log", str(tmp_path / "log.md"),
        ]
        with contextlib.redirect_stdout(io.StringIO()):
            cli_main(argv)
        with contextlib.redirect_stdout(io.StringIO()):
            cli_main(argv)
        linhas = inv.read_text(encoding="utf-8").strip().splitlines()
        assert len(linhas) == 25

    def test_help_sai_com_zero(self) -> None:
        from onboarding.cli import main as cli_main

        with pytest.raises(SystemExit) as erro:
            cli_main(["--help"])
        assert erro.value.code == 0

    def test_sem_comando_falha(self) -> None:
        from onboarding.cli import main as cli_main

        with pytest.raises(SystemExit):
            cli_main([])