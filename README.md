# onboarding

Script que pega uma câmera nova na rede, aplica VLAN de CFTV, NTP, senha e
nome, e registra no inventário — de forma automática e idempotente.

A script that takes a new camera on the network, applies CFTV VLAN, NTP,
password and name, and registers it in the inventory — automatically and
idempotently.

> **Nada aqui é real.** As câmeras alvo são simuladas localmente. O scanner
> recusa qualquer faixa fora de RFC 1918 ou localhost, e nenhum socket é
> aberto em nenhum caminho.

## O que é

Descoberta de faixa, configuração (VLAN, NTP, usuário, troca de senha
padrão), registro em CSV sem duplicar, e log em Markdown. Falha individual
vira linha no relatório, nunca aborta o lote.

## Por que foi feito

Onboarding em massa é trabalho real de projeto — o tipo de tarefa que um
estagiário executa no primeiro mês. E o erro clássico é configurar uma a uma
na interface web, sem registro do que foi feito e sem como repetir.

## Como rodar

```powershell
python -m onboarding executar --faixa dados/faixa-alvo.yaml --inventario dados/inventario-inicial.csv --log exemplos/log-onboarding.md
```

```
cameras processadas: 24
configuradas: 23  com falha: 1
log gravado em exemplos/log-onboarding.md
```

A segunda execução não duplica nada — idempotência exercitada, não declarada.

Instalação:

```powershell
pip install -e ".[dev]"
```

## Nomenclatura: CLI-ANDAR-CAM-001

Cliente, andar, o literal `CAM` e o número com três dígitos. Cada parte existe
por um motivo operacional; número nunca é reutilizado — buraco de câmera
removida continua buraco. Ver `docs/padrao-de-nomenclatura.md`.

## Falhas individuais

Duas câmeras têm problema de propósito: CAM-007 com senha padrão (corrigida
no onboarding) e CAM-013 com IP fora da faixa (sinalizada, não processada).
Uma câmera com problema não para as outras 23.

## O que aprendi

- **Idempotência se exercita, não se declara.** Rodar duas vezes faz parte do
  critério de aceite.
- **Registro é por nome.** Sem chave estável, "atualizar" vira "duplicar".
- **Fora da faixa não é fora da RFC.** 10.99.99.99 é privado e válido — mas
  não é deste projeto. O configurador distingue os dois.
- **Motivo vazio é relatório mudo.** A primeira versão mostrava a falha sem
  dizer por quê; o adapter agora passa o motivo.

## Testes

```powershell
python -m pytest -v
```

37 testes, 82% de cobertura. Cobrem nomenclatura, descoberta sem socket,
configurador com os casos individuais, inventário idempotente, relatório e CLI.

```powershell
python tools/verificar_aceite.py     # 24 em 2 execucoes + falha registrada
python tools/verificar_encoding.py   # nenhum caractere corrompido
```

## Limitações

- **Simulação, não rede.** Nenhum pacote sai; descoberta consulta registro
  em memória.
- **Senha "nova" é derivada do nome.** Suficiente para provar a troca, longe
  de política real de segredo.
- **Sem rollback.** Falha no meio deixa etapas aplicadas; não há desfazer.
- **Inventário é CSV.** Concorrência e histórico ficam para um banco de
  verdade.

## Licença

MIT.

---

## English

Automatic, idempotent camera onboarding: discovery, configuration (VLAN, NTP,
user, password rotation), CSV inventory without duplication, Markdown log.
Individual failure is a report line, never aborts the batch.

Naming: `CLI-ANDAR-CAM-001`. Second run duplicates nothing. Out-of-range IP
is flagged, not processed.

### Tests

37 tests, 82% coverage.

```powershell
python -m pytest -v
python tools/verificar_aceite.py
python tools/verificar_encoding.py
```

### Limitations

Simulated network; derived passwords; no rollback; CSV inventory.

### License

MIT.