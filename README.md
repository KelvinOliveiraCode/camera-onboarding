<div align="center">

<p>
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/tests-37%20passing-brightgreen?style=flat-square" alt="Tests">
  <img src="https://img.shields.io/badge/coverage-83%25-yellowgreen-brightgreen?style=flat-square" alt="Coverage">
  <img src="https://img.shields.io/badge/license-MIT-yellow?style=flat-square" alt="License">
  <img src="https://img.shields.io/badge/platform-Windows-blue?style=flat-square" alt="Windows">
</p>

# camera-onboarding

**Prepara camera IP em lote, com nome padronizado, registro em inventario e log por camera.**

</div>

---

## PT-BR

### O que e

Script que pega uma camera nova na rede, aplica VLAN de CFTV, NTP, senha e nome,
e registra no inventario de forma idempotente. Camera com problema vira linha no
relatorio e nao aborta o lote.

### Por que foi feito

Onboarding em massa e trabalho real de projeto: o tipo de tarefa que alguem
executa no primeiro mes, camera por camera, na interface web, sem registro do
que foi feito e sem como repetir. O custo nao esta em configurar a camera, esta
em nao ter como provar depois o que foi aplicado em cada uma.

### Como rodar

```powershell
# 1. Instalar
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .

# 2. Validar
python -m pytest tests/ -v

# 3. Executar
python -m onboarding executar --faixa dados/faixa-alvo.yaml `
    --inventario dados/inventario-inicial.csv --log exemplos/log-onboarding.md
```

Saida real (o comando termina com codigo 1 porque uma camera foi sinalizada e
nao processada):

```
cameras processadas: 24
configuradas: 23  com falha: 1
log gravado em exemplos/log-onboarding.md
```

A segunda execucao nao duplica nada. Isso esta no criterio de aceite, nao numa
frase de README.

Sem instalar nada, da raiz do repositorio:

```powershell
$env:PYTHONPATH="$PWD\src"; python -m onboarding executar --faixa dados/faixa-alvo.yaml --inventario dados/inventario-inicial.csv --log exemplos/log-onboarding.md
```

### Nomenclatura: CLI-ANDAR-CAM-001

Cliente, andar, o literal `CAM` e o numero com tres digitos. Cada parte existe
por um motivo operacional; numero nunca e reutilizado, porque buraco de camera
removida continua buraco. Ver `docs/padrao-de-nomenclatura.md`.

### Falhas individuais

Duas cameras tem problema de proposito: CAM-007 com senha padrao (corrigida no
onboarding) e CAM-013 com IP fora da faixa (sinalizada, nao processada). Uma
camera com problema nao para as outras 23.

### O que aprendi

- **Idempotencia se exercita, nao se declara.** Rodar duas vezes e parte do
  criterio de aceite: sem isso, "atualizar" vira "duplicar" silenciosamente.
- **Registro e por nome.** Sem chave estavel no CSV, a segunda execucao cria
  uma linha nova em vez de atualizar a antiga.
- **Fora da faixa nao e fora da RFC.** Endereco privado e valido, mas nao e
  deste projeto. O configurador separa as duas coisas, e o relatorio diz qual
  das duas falhou.
- **Motivo vazio e relatorio mudo.** A primeira versao sinalizava a falha sem
  dizer por que; o adapter agora passa o motivo, e o log fica acionavel.

### Limitacoes

- **Simulacao, nao rede.** Nenhum pacote sai do processo: a descoberta consulta
  um registro em memoria.
- **Senha "nova" e derivada do nome.** Suficiente para provar que a troca
  acontece, longe de politica real de segredo.
- **Sem rollback.** Falha no meio deixa etapas aplicadas e nao ha desfazer.
- **Inventario e CSV.** Concorrencia e historico ficam para um banco de verdade.

### Licenca

MIT. Ver [LICENSE](LICENSE).

---

## EN

### What it is

A script that takes a new camera on the network, applies the CFTV VLAN, NTP,
password and name, and registers it in the inventory, idempotently. A camera
with a problem becomes a report line and never aborts the batch.

### Why it was built

Bulk onboarding is real project work: the kind of task someone does in their
first month, one camera at a time, through the web interface, with no record of
what was applied and no way to repeat it. The cost is not in configuring the
camera; it is in having no way to prove afterwards what each one received.

### How to run

```powershell
# 1. Install
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .

# 2. Validate
python -m pytest tests/ -v

# 3. Run
python -m onboarding executar --faixa dados/faixa-alvo.yaml `
    --inventario dados/inventario-inicial.csv --log exemplos/log-onboarding.md
```

Real output (the command exits with code 1 because one camera was flagged and
not processed):

```
cameras processadas: 24
configuradas: 23  com falha: 1
log gravado em exemplos/log-onboarding.md
```

The second run duplicates nothing, and that is covered by the acceptance check
rather than promised here.

Without installing anything, from the repository root:

```powershell
$env:PYTHONPATH="$PWD\src"; python -m onboarding executar --faixa dados/faixa-alvo.yaml --inventario dados/inventario-inicial.csv --log exemplos/log-onboarding.md
```

### Naming: CLI-ANDAR-CAM-001

Client, floor, the literal `CAM` and a three-digit number. Every part exists
for an operational reason, and a number is never reused: the hole left by a
removed camera stays a hole. See `docs/padrao-de-nomenclatura.md`.

### Individual failures

Two cameras have a problem on purpose: CAM-007 with the factory password
(fixed by the onboarding) and CAM-013 with an out-of-range IP (flagged, not
processed). One camera with a problem does not stop the other 23.

### What I learned

- **Idempotency is exercised, not declared.** Running twice is part of the
  acceptance check; without it, "update" silently becomes "duplicate".
- **The record is keyed by name.** Without a stable key in the CSV, the second
  run appends a row instead of updating the existing one.
- **Out of range is not the same as out of RFC.** A private address is valid,
  but it is not part of this project. The configurator separates the two cases
  and the report says which one failed.
- **An empty reason is a mute report.** The first version flagged the failure
  without saying why; the adapter now passes the reason, so the log is
  actionable.

### Limitations

- **Simulation, not network.** No packet leaves the process: discovery reads an
  in-memory registry.
- **The "new" password is derived from the name.** Enough to prove the rotation
  happens, far from a real secret policy.
- **No rollback.** A failure halfway leaves steps applied, with no undo.
- **The inventory is a CSV.** Concurrency and history are left to a real
  database.

### License

MIT. See [LICENSE](LICENSE).

---

<div align="center">
  <sub>Por <a href="https://github.com/KelvinOliveiraCode">Kelvin Oliveira</a> &middot;
  <a href="https://kelvinoliveiracode.github.io/portfolio/">portfolio</a></sub>
</div>
