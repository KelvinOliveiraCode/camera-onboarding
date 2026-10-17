# camera-onboarding

<img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python&logoColor=white" alt="Python">
<img src="https://img.shields.io/badge/tests-37%20passing-brightgreen?style=flat-square" alt="Tests">
<img src="https://img.shields.io/badge/coverage-83%25-yellowgreen?style=flat-square" alt="Coverage">
<img src="https://img.shields.io/badge/deps-PyYAML%20only-blue?style=flat-square" alt="Deps">
<img src="https://img.shields.io/badge/license-MIT-yellow?style=flat-square" alt="License">
<img src="https://img.shields.io/badge/platform-Windows-blue?style=flat-square" alt="Windows">

Prepares IP cameras in batch, with standardized name, inventory record and per-camera log.

## Problem / Why it exists

Bulk IP camera onboarding is done manually, one by one, on the web interface, with no record of what was applied and no way to repeat it. The cost is not configuring the camera, it is not being able to prove afterward what each one received. A faulty camera cannot stop the other 23.

## What it does

Reads a CSV inventory and a YAML target range. For each camera: validates the name against the CLI-ANDAR-CAM-001 pattern, checks if the IP is RFC 1918 and within the target range, applies VLAN, NTP, user and changes the default password, records the result in the CSV without duplicating, and writes a markdown log with status and failure reason per camera. Individual failure becomes a report line, never aborts the batch. Running twice does not duplicate entries in the inventory.

## Stack

- Python 3.10+
- PyYAML>=6.0, the only runtime dependency; only reads the target-range YAML
- pytest, pytest-cov, development dependencies
- csv, ipaddress and statistics from the standard library; no package leaves the process, discovery queries an in-memory simulated registry

## How it works

The `executar` command processes the entire inventory, camera by camera, in five steps.

1. Reads the target range from YAML (CIDR, NTP, default password).
2. Loads the CSV inventory (header: name, ip, floor, user, password, vlan, ntp, state).
3. For each entry, builds a `Configuracao` (VLAN 30, NTP from YAML, user admin, password derived from name) and calls the configurator.
4. The configurator validates the name (CLI-ANDAR-CAM-001), checks IP RFC 1918 and within range, applies VLAN, NTP, user and password change. Invalid name or IP fails without applying anything; failure at a step goes to the sequence and becomes an error in the result, never an exception.
5. Registers in CSV by name: updates if already exists, never duplicates. Generates markdown log with table, counts and failure list with reason.

The command returns 0 when all cameras are configured, 1 when there is at least one failure and 2 when there is inventory error.

The naming pattern is `CLI-ANDAR-CAM-001`, with client (2 to 6 uppercase letters), floor (2 to 10 uppercase letters), literal `CAM` and three-digit number. The number is never reused: a removed camera leaves the gap, so the history of two cameras does not mix under the same identifier.

## How to run

Install the environment for the first time, on Windows PowerShell.

python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .

Validate the installation by running the tests.

python -m pytest tests/ -v

Run the batch from the repository root.

python -m onboarding executar --faixa dados/faixa-alvo.yaml --inventario dados/inventario-inicial.csv --log exemplos/log-onboarding.md

The included example produces this output. Exit code is 1 because one camera was flagged.

cameras processed: 24
configured: 23  failed: 1
log written to exemplos/log-onboarding.md

The recorded failure is camera CLI-SEGUNDO-CAM-013 (IP 10.99.99.99, outside target range 192.168.30.0/24); the other 23 are configured.

Run directly from the repository, without installing anything.

$env:PYTHONPATH="$PWD\src"; python -m onboarding executar --faixa dados/faixa-alvo.yaml --inventario dados/inventario-inicial.csv --log exemplos/log-onboarding.md

Running twice on the same inventory does not duplicate any line (see tests/test_fluxo.py and tools/verificar_aceite.py).

## Project structure

camera-onboarding/
├── src/onboarding/
│   ├── cli.py          entry point and executar command
│   ├── configurador.py VLAN, NTP, user and password change (simulated)
│   ├── inventario.py   idempotent CSV registration by name
│   ├── descoberta.py   simulated RFC 1918 range scan, no socket
│   ├── naming.py       CLI-ANDAR-CAM-001 pattern and validator
│   ├── relatorio.py    markdown log with table and failures
│   └── __main__.py     allows python -m onboarding
├── tests/              test_fluxo.py, test_naming.py (37 tests)
├── dados/              faixa-alvo.yaml, inventario-inicial.csv (24 simulated cameras)
├── docs/               padrao-de-nomenclatura.md, onboarding-em-massa.md
├── exemplos/           log-onboarding.md (reference output)
├── tools/              verificar_aceite.py, verificar_encoding.py, gerar_inventario.py
├── pyproject.toml      build, scripts, pytest and coverage
├── requirements.txt    PyYAML and development dependencies
└── LICENSE             MIT

## Trade-offs and decisions

- CSV as inventory: simple, auditable and without database server; concurrency and history left to a real database.
- Simulation without network: no socket scan, queries an in-memory registry. Allows testing without touching production, but does not configure real IP cameras.
- New password derived from name (`Nova` + last three characters of name): proves the change happens, far from a real secret policy.
- No rollback: failure mid-way leaves applied steps; no undo.
- Name as unique inventory key: idempotency depends on a stable key; without it the second run creates a new line instead of updating the old one.
- IP outside target range is different from invalid RFC 1918 IP: the configurator separates the two cases and the report says which failed.
- Exit code 1 when there are failures: a batch with individual failure is not a clean success.

## Known limitations

- Simulation, not network: no packet leaves the process; discovery queries an in-memory registry.
- "New" password derived from name: enough to prove the change happens, far from a real secret policy.
- No rollback: mid-way failure leaves applied steps, no undo.
- Inventory is CSV: concurrency and history left to a real database.
- Does not configure real IP cameras: simulated and fictional environment.

## License

MIT. See [LICENSE](LICENSE).

## Author

Kelvin Oliveira - https://github.com/KelvinOliveiraCode - https://kelvinoliveiracode.github.io/portfolio/
