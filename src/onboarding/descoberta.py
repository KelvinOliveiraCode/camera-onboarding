"""Descoberta de cameras em faixa local, via registro simulado (sem socket).

Scans a target CIDR against an in-memory simulated registry of 24 fictitious
cameras and classifies each found service. No socket is ever opened.
"""

import ipaddress
from dataclasses import dataclass
from pathlib import Path

__all__ = ["Achado", "faixa_valida", "varrer", "identificar", "REGISTRO_SIMULADO"]

# Registro simulado em memoria: as 24 cameras ficticias do inventario
# (dados/inventario-inicial.csv). Chave: IP; valor: {porta: tipo}.
# Nenhuma varredura toca em rede real: tudo passa por este dict.
REGISTRO_SIMULADO = {
    "192.168.30.11": {554: "rtsp", 8554: "rtsp"},
    "192.168.30.12": {554: "rtsp", 8554: "rtsp"},
    "192.168.30.13": {554: "rtsp", 8554: "rtsp"},
    "192.168.30.14": {554: "rtsp", 8554: "rtsp"},
    "192.168.30.15": {554: "rtsp", 8554: "rtsp"},
    "192.168.30.16": {554: "rtsp", 8554: "rtsp"},
    "192.168.30.17": {554: "rtsp", 8554: "rtsp"},
    "192.168.30.18": {554: "rtsp", 8554: "rtsp"},
    "192.168.30.19": {554: "rtsp", 8554: "rtsp"},
    "192.168.30.20": {554: "rtsp", 8554: "rtsp"},
    "192.168.30.21": {554: "rtsp", 8554: "rtsp"},
    "192.168.30.22": {554: "rtsp", 8554: "rtsp"},
    "10.99.99.99": {554: "rtsp", 8554: "rtsp"},
    "192.168.30.24": {554: "rtsp", 8554: "rtsp"},
    "192.168.30.25": {554: "rtsp", 8554: "rtsp"},
    "192.168.30.26": {554: "rtsp", 8554: "rtsp"},
    "192.168.30.27": {554: "rtsp", 8554: "rtsp"},
    "192.168.30.28": {554: "rtsp", 8554: "rtsp"},
    "192.168.30.29": {554: "rtsp", 8554: "rtsp"},
    "192.168.30.30": {554: "rtsp", 8554: "rtsp"},
    "192.168.30.31": {554: "rtsp", 8554: "rtsp"},
    "192.168.30.32": {554: "rtsp", 8554: "rtsp"},
    "192.168.30.33": {554: "rtsp", 8554: "rtsp"},
    "192.168.30.34": {554: "rtsp", 8554: "rtsp"},
}

_RFC_1918 = (
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
)
_LOOPBACK = ipaddress.ip_network("127.0.0.0/8")
_PORTAS_CAMERA = {554, 8554, 80, 443}


def faixa_valida(cidr):
    """Devolve True so para RFC 1918 ou localhost; False para o resto.

    Returns True only for RFC 1918 private ranges or loopback.
    """
    try:
        rede = ipaddress.ip_network(str(cidr).strip(), strict=False)
    except ValueError:
        return False
    if rede.version != 4:
        return False
    for privada in _RFC_1918:
        if rede.subnet_of(privada):
            return True
    return rede.subnet_of(_LOOPBACK)


@dataclass(frozen=True)
class Achado:
    """Servico encontrado em um endereco. / A service found at a host."""

    ip: str
    porta: int
    tipo: str


def _enderecos(rede):
    """Yields todos os enderecos da rede, inclusive /31 e /32."""
    if rede.prefixlen >= 32:
        yield str(rede.network_address)
        return
    if rede.prefixlen == 31:
        yield str(rede.network_address)
        yield str(rede.network_address + 1)
        return
    for host in rede.hosts():
        yield str(host)


def varrer(faixa, portas):
    """Varre a faixa consultando o registro simulado, sem abrir socket.

    Scans the CIDR against the in-memory registry; rejects non-private or
    non-loopback ranges with ValueError.
    """
    if not faixa_valida(faixa):
        raise ValueError(
            "faixa rejeitada: so e aceita RFC 1918 ou localhost: %r" % (faixa,)
        )
    rede = ipaddress.ip_network(str(faixa).strip(), strict=False)
    achados = []
    for ip in _enderecos(rede):
        servicos = REGISTRO_SIMULADO.get(ip, {})
        for porta in portas:
            porta = int(porta)
            tipo = servicos.get(porta)
            if tipo is not None:
                achados.append(Achado(ip=ip, porta=porta, tipo=tipo))
    return achados


def identificar(achado):
    """Retorna 'camera' se a porta bate com o padrao, senao 'desconhecido'.

    Classifies a found service as a camera by its port pattern.
    """
    return "camera" if achado.porta in _PORTAS_CAMERA else "desconhecido"


def _carregar_faixa_alvo(caminho):
    """Le as chaves 'faixa' e 'portas' de um YAML plano.

    Reads only 'faixa' and 'portas' from a flat YAML file.
    """
    faixa = None
    portas = None
    with open(caminho, "r", encoding="utf-8") as arquivo:
        for linha in arquivo:
            linha = linha.strip()
            if not linha or linha.startswith("#"):
                continue
            if linha.startswith("faixa:"):
                faixa = linha.split(":", 1)[1].strip()
            elif linha.startswith("portas:"):
                trecho = linha.split(":", 1)[1].strip().strip("[]")
                portas = [int(p) for p in trecho.split(",") if p.strip()]
    if faixa is None or portas is None:
        raise ValueError("chaves 'faixa' e 'portas' nao encontradas")
    return faixa, portas


if __name__ == "__main__":
    # Gate final: confere o contrato e roda a varredura real da faixa alvo.
    try:
        varrer("8.8.8.0/24", [554])
        print("GATE 1 FALHOU: 8.8.8.0/24 nao foi recusada")
    except ValueError:
        print("GATE 1 OK: 8.8.8.0/24 recusada")
    print(
        "GATE 2 OK: 192.168.30.0/24 aceita, achados=%d"
        % len(varrer("192.168.30.0/24", [554, 8554]))
    )
    print(
        "GATE 3 OK: localhost 127.0.0.1 aceito, achados=%d"
        % len(varrer("127.0.0.1", [554]))
    )

    raiz = Path(__file__).resolve().parents[2]
    faixa, portas = _carregar_faixa_alvo(raiz / "dados" / "faixa-alvo.yaml")
    achados = varrer(faixa, portas)
    print("faixa=%s portas=%s" % (faixa, portas))
    print("achados: %d" % len(achados))
    print(
        "cameras identificadas: %d"
        % sum(1 for a in achados if identificar(a) == "camera")
    )
