"""Configurador de onboarding da camera simulada.

Camera onboarding configurator for the simulated camera.

Aplica VLAN, NTP, usuario e senha, nesta ordem. Nome ou IP invalidos
falham sem aplicar nada; falha individual de etapa vira erro no
resultado, nunca excecao. A camera nasce com a senha padrao admin123 e,
se tudo passar, termina sem a senha padrao.
"""

from __future__ import annotations

import ipaddress
from dataclasses import dataclass, field

from .naming import ErroDeNome, validar

SENHA_PADRAO = "admin123"


@dataclass
class Configuracao:
    """Parametros de rede, NTP e acesso da camera.

    Camera network, NTP and access parameters.
    """

    vlan: int
    ntp: str
    usuario: str
    senha_nova: str


@dataclass
class ResultadoConfig:
    """Resultado da configuracao simulada.

    Result of the simulated configuration.
    """

    nome: str
    ok: bool
    etapas: list[str] = field(default_factory=list)
    erro: str = ""


class _CameraSimulada:
    """Estado da camera simulada durante a configuracao.

    Simulated camera state during configuration.
    """

    def __init__(self, nome: str, ip: str) -> None:
        self.nome = nome
        self.ip = ip
        self.vlan = None
        self.ntp = ""
        self.usuario = ""
        self.senha = SENHA_PADRAO


def _e_rfc1918(ip: str) -> bool:
    """Verifica se o IP e das faixas RFC 1918.

    Check whether the IP belongs to an RFC 1918 range.
    """
    try:
        endereco = ipaddress.ip_address(str(ip).strip())
    except ValueError:
        return False
    if endereco.version != 4:
        return False
    octetos = [int(p) for p in endereco.exploded.split(".")]
    primeiro, segundo = octetos[0], octetos[1]
    if primeiro == 10:
        return True
    if primeiro == 172 and 16 <= segundo <= 31:
        return True
    return primeiro == 192 and segundo == 168


def _aplicar_vlan(camera: _CameraSimulada, vlan: int) -> str:
    """Aplica a VLAN; devolve o texto da etapa.

    Apply the VLAN; return the step text.
    """
    try:
        valor = int(vlan)
    except (TypeError, ValueError):
        raise ValueError(f"VLAN {vlan!r} invalida: inteiro esperado")
    if not 1 <= valor <= 4094:
        raise ValueError(f"VLAN {valor} fora de 1..4094")
    camera.vlan = valor
    return f"VLAN {valor} aplicada"


def _aplicar_ntp(camera: _CameraSimulada, ntp: str) -> str:
    """Aplica o servidor NTP; devolve o texto da etapa.

    Apply the NTP server; return the step text.
    """
    valor = str(ntp).strip()
    if not valor:
        raise ValueError("NTP invalido: host vazio")
    camera.ntp = valor
    return f"NTP {valor} aplicado"


def _definir_usuario(camera: _CameraSimulada, usuario: str) -> str:
    """Define o usuario de acesso; devolve o texto da etapa.

    Set the access user; return the step text.
    """
    valor = str(usuario).strip()
    if not valor:
        raise ValueError("usuario invalido: vazio")
    camera.usuario = valor
    return f"usuario {valor} definido"


def _trocar_senha(camera: _CameraSimulada, senha_nova: str) -> str:
    """Troca a senha padrao; devolve o texto da etapa.

    Change the default password; return the step text.
    """
    valor = str(senha_nova)
    if not valor:
        raise ValueError("senha nova invalida: vazia")
    if valor == SENHA_PADRAO:
        raise ValueError("senha nova igual a padrao, recusada")
    camera.senha = valor
    return f"senha padrao {SENHA_PADRAO} trocada"


def configurar(
    nome: str,
    ip_atual: str,
    config: Configuracao,
    faixa: str | None = None,
) -> ResultadoConfig:
    """Simula a configuracao completa da camera.

    Simulate the full camera configuration.

    Ordem das etapas: VLAN, NTP, usuario, troca da senha padrao. Nome ou
    IP invalidos falham sem aplicar nada; falha individual de etapa
    interrompe a sequencia e vira erro no resultado, nunca excecao.

    Args:
        nome: Nome no padrao CLI-ANDAR-CAM-001.
        ip_atual: IP atual da camera, deve ser RFC 1918.
        config: Parametros a aplicar.
        faixa: CIDR da faixa-alvo, se houver. IP fora dela falha: configurar
            camera fora do escopo e como configurar a camera do vizinho.

    Returns:
        ResultadoConfig com as etapas aplicadas ou o erro.
    """
    nome_txt = str(nome).strip()
    ip_txt = str(ip_atual).strip()

    try:
        validar(nome_txt)
    except ErroDeNome as exc:
        return ResultadoConfig(nome=nome_txt, ok=False, erro=str(exc))

    if not _e_rfc1918(ip_txt):
        return ResultadoConfig(
            nome=nome_txt,
            ok=False,
            erro=f"IP {ip_txt!r} fora das faixas RFC 1918",
        )

    if faixa:
        try:
            rede = ipaddress.ip_network(str(faixa).strip(), strict=False)
            if ipaddress.ip_address(ip_txt) not in rede:
                return ResultadoConfig(
                    nome=nome_txt,
                    ok=False,
                    erro=f"IP {ip_txt!r} fora da faixa-alvo {rede}",
                )
        except ValueError as exc:
            return ResultadoConfig(
                nome=nome_txt, ok=False, erro=f"faixa invalida: {exc}"
            )

    camera = _CameraSimulada(nome=nome_txt, ip=ip_txt)
    etapas: list[str] = []
    passos = (
        lambda: _aplicar_vlan(camera, config.vlan),
        lambda: _aplicar_ntp(camera, config.ntp),
        lambda: _definir_usuario(camera, config.usuario),
        lambda: _trocar_senha(camera, config.senha_nova),
    )
    for passo in passos:
        try:
            etapas.append(passo())
        except Exception as exc:
            # Falha individual: registra e para, sem propagar excecao.
            return ResultadoConfig(
                nome=nome_txt, ok=False, etapas=etapas, erro=str(exc)
            )

    if camera.senha == SENHA_PADRAO:
        return ResultadoConfig(
            nome=nome_txt,
            ok=False,
            etapas=etapas,
            erro="senha padrao continua em uso apos a configuracao",
        )

    return ResultadoConfig(nome=nome_txt, ok=True, etapas=etapas)
