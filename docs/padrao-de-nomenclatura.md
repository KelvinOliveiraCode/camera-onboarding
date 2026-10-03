# Padrão de nomenclatura

O formato é `CLI-ANDAR-CAM-001`: cliente, andar, o literal `CAM` e o número
sequencial com três dígitos.

## Por que cada parte existe

**Cliente** (`CLI`): quem é o dono. Numa prestadora com vários clientes no
mesmo NVR, o nome sem dono obriga a abrir o cadastro para saber de quem é a
câmera que caiu — e câmera que caiu é sempre urgente.

**Andar** (`TERREO`): onde fisicamente. O técnico que sobe com a escada precisa
saber para onde ir sem abrir planta. Nome sem lugar é nome que atrasa visita.

**`CAM`**: o tipo. Distingue de `NVR`, `SW` e `SRV` no mesmo inventário, onde
tudo convive na mesma planilha.

**Número** (`001`): ordem de cadastro, não de instalação. Três dígitos porque
ordenação lexicográfica: `CAM-001` vem antes de `CAM-010` em qualquer listagem.
Maiúsculas porque `cam-1` e `CAM-01` viram duas câmeras diferentes num
inventário editado à mão.

## O que não entra no nome

Resolução, modelo, IP, data de instalação. Tudo isso muda; nome não muda.
Quem põe IP no nome descobre no primeiro remanejamento que o nome mente — e
nome que mente é pior do que nome feio.

## Número nunca reutilizado

Uma câmera removida deixa o buraco, e o buraco conta a história de que ali já
houve uma câmera. Reutilizar número mistura o histórico de duas câmeras no
mesmo identificador, e histórico misturado é evidência contaminada.
