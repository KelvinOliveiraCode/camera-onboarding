# camera-onboarding

<img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python&logoColor=white" alt="Python">
<img src="https://img.shields.io/badge/tests-37%20passing-brightgreen?style=flat-square" alt="Tests">
<img src="https://img.shields.io/badge/coverage-83%25-yellowgreen?style=flat-square" alt="Coverage">
<img src="https://img.shields.io/badge/deps-PyYAML%20only-blue?style=flat-square" alt="Deps">
<img src="https://img.shields.io/badge/license-MIT-yellow?style=flat-square" alt="License">
<img src="https://img.shields.io/badge/platform-Windows-blue?style=flat-square" alt="Windows">

Prepara camera IP em lote, com nome padronizado, registro em inventario e log por camera.

## Problema / Por que existe

Onboarding em massa de camera IP e feito a mao, uma por uma, na interface web, sem registro do que foi aplicado e sem como repetir. O custo nao esta em configurar a camera, esta em nao poder provar depois o que cada uma recebeu. Uma camera com problema nao pode parar as outras 23.

## O que faz

Lê um CSV de inventario e um YAML de faixa-alvo. Para cada camera: valida o nome no padrao CLI-ANDAR-CAM-001, confere se o IP e RFC 1918 e esta dentro da faixa-alvo, aplica VLAN, NTP, usuario e troca a senha padrao, registra o resultado no CSV sem duplicar e grava um log em markdown com o estado e o motivo de cada falha. Falha individual vira linha no relatorio, nunca aborta o lote. Rodar duas vezes nao duplica entrada no inventario.

## Stack

- Python 3.10+
- PyYAML>=6.0, a unica dependencia de execucao; so le o YAML da faixa-alvo
- pytest, pytest-cov, dependencias de desenvolvimento
- csv, ipaddress e statistics da biblioteca padrao; nenhum pacote sai do processo, a descoberta consulta um registro simulado em memoria

## Como funciona

O comando `executar` processa o inventario inteiro, camera por camera, em cinco passos.

1. Lê a faixa-alvo do YAML (CIDR, NTP, senha padrao).
2. Carrega o inventario CSV (cabecalho: nome, ip, andar, usuario, senha, vlan, ntp, estado).
3. Para cada entrada, monta uma `Configuracao` (VLAN 30, NTP do YAML, usuario admin, senha derivada do nome) e chama o configurador.
4. O configurador valida o nome (CLI-ANDAR-CAM-001), confere IP RFC 1918 e dentro da faixa, aplica VLAN, NTP, usuario e troca de senha. Nome ou IP invalido falha sem aplicar nada; falha de uma etapa para a sequencia e vira erro no resultado, nunca excecao.
5. Registra no CSV por nome: atualiza se ja existe, nao duplica. Gera o log markdown com tabela, contagens e lista de falhas com motivo.

O comando retorna 0 quando todas as cameras sao configuradas, 1 quando ha pelo menos uma falha e 2 quando ha erro de inventario.

O padrao de nomenclatura e `CLI-ANDAR-CAM-001`, com cliente (2 a 6 letras maiúsculas), andar (2 a 10 letras maiúsculas), literal `CAM` e numero com tres digitos. O numero nunca e reutilizado: uma camera removida deixa o buraco, para que o historico de duas cameras nao se misture no mesmo identificador.

## Como rodar

Instale o ambiente na primeira vez, no Windows PowerShell.

python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .

Valide a instalacao rodando os testes.

python -m pytest tests/ -v

Execute o lote da raiz do repositorio.

python -m onboarding executar --faixa dados/faixa-alvo.yaml --inventario dados/inventario-inicial.csv --log exemplos/log-onboarding.md

O exemplo incluso produz esta saida. O codigo de saida e 1 porque uma camera foi sinalizada.

cameras processadas: 24
configuradas: 23  com falha: 1
log gravado em exemplos/log-onboarding.md

A falha registrada e a camera CLI-SEGUNDO-CAM-013 (IP 10.99.99.99, fora da faixa-alvo 192.168.30.0/24); as outras 23 sao configuradas.

Rode direto do repositorio, sem instalar nada.

$env:PYTHONPATH="$PWD\src"; python -m onboarding executar --faixa dados/faixa-alvo.yaml --inventario dados/inventario-inicial.csv --log exemplos/log-onboarding.md

Rodar duas vezes no mesmo inventario nao duplica nenhuma linha (ver tests/test_fluxo.py e tools/verificar_aceite.py).

## Estrutura do projeto

camera-onboarding/
├── src/onboarding/
│   ├── cli.py          ponto de entrada e comando executar
│   ├── configurador.py VLAN, NTP, usuario e troca de senha (simulado)
│   ├── inventario.py   registro idempotente em CSV por nome
│   ├── descoberta.py   varredura simulada em faixa RFC 1918, sem socket
│   ├── naming.py       padrao e validador CLI-ANDAR-CAM-001
│   ├── relatorio.py    log em markdown com tabela e falhas
│   └── __main__.py     permite python -m onboarding
├── tests/              test_fluxo.py, test_naming.py (37 testes)
├── dados/              faixa-alvo.yaml, inventario-inicial.csv (24 cameras simuladas)
├── docs/               padrao-de-nomenclatura.md, onboarding-em-massa.md
├── exemplos/           log-onboarding.md (saida de referencia)
├── tools/              verificar_aceite.py, verificar_encoding.py, gerar_inventario.py
├── pyproject.toml      build, scripts, pytest e cobertura
├── requirements.txt    PyYAML e dependencias de desenvolvimento
└── LICENSE             MIT

## Trade-offs e decisoes

- CSV como inventario: simples, auditavel e sem servidor de banco; concorrencia e historico ficam para um banco de verdade.
- Simulacao sem rede: nenhuma varredura com socket, consulta registro em memoria. Permite testar sem tocar em producao, mas nao configura cameras IP reais.
- Senha nova derivada do nome (`Nova` + tres ultimos caracteres do nome): prova que a troca acontece, longe de uma politica real de segredo.
- Sem rollback: falha no meio deixa etapas aplicadas; nao ha desfazer.
- Nome como chave unica do inventario: a idempotencia depende de uma chave estável; sem ela a segunda execucao cria uma linha nova em vez de atualizar a antiga.
- IP fora da faixa-alvo e diferente de IP invalido RFC 1918: o configurador separa os dois casos e o relatorio diz qual falhou.
- Codigo de saida 1 quando ha falhas: um lote com falha individual nao e um sucesso limpo.

## Limitações conhecidas

- Simulacao, nao rede: nenhum pacote sai do processo; a descoberta consulta um registro em memoria.
- Senha "nova" derivada do nome: suficiente para provar que a troca acontece, longe de uma politica real de segredo.
- Sem rollback: falha no meio deixa etapas aplicadas, sem desfazer.
- Inventario e CSV: concorrencia e historico ficam para um banco de verdade.
- Nao configura cameras IP reais: ambiente simulado e ficticio.

## Licenca

MIT. Ver [LICENSE](LICENSE).

## Autor

Kelvin Oliveira - https://github.com/KelvinOliveiraCode - https://kelvinoliveiracode.github.io/portfolio/
