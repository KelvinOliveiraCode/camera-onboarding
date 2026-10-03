# Onboarding-em-massa — Procedimento Operacional Padrão

Este documento descreve o procedimento operacional real para onboarding em massa no inventário, apoiado no padrão CLI-ANDAR-CAM-001 (src/onboarding/naming.py) e na propriedade de idempotencia do fluxo.

## 1. Ordem: descobrir, nomear, configurar, registrar, verificar

As cinco etapas são sequenciais e obrigatórias; a saída de uma é a entrada da seguinte.

Descobrir. A fase de descoberta localiza equipamentos ainda não cadastrados. Só aceita endereços privados RFC 1918 e localhost: qualquer faixa fora disso é recusada antes de qualquer varredura. A varredura não abre socket: consulta o registro de referência, sem alterar o ambiente de produção. Resultado: lista de candidatos sem nome oficial.

Nomear. Cada candidato recebe um identificador único seguindo o padrão CLI-ANDAR-CAM-001: cliente, andar, o literal CAM e número sequencial de três dígitos. O cliente identifica o dono; sem dono, obriga a abrir o cadastro. O andar indica para onde o técnico deve ir, sem consultar planta. O tipo CAM distingue câmeras de NVR, SW e SRV. O número registra ordem de cadastro, não de instalação, e nunca é reutilizado: removida, a câmera deixa um buraco que conta que ali houve uma câmera.

Configurar. Com o nome oficial, aplicam-se credenciais padrão, VLAN, servidor NTP e políticas de segurança. A configuração é atrelada ao nome, não ao IP, porque o IP pode migrar enquanto o nome é estável.

Registrar. O registro grava a câmera: nome, endereço, andar, usuário, VLAN e NTP. É a fonte da verdade da qual idempotencia e verificação operam.

Verificar. Confirma-se acesso, hora sincronizada e vídeo no inventário. Barreira final antes do lote ser concluído.

## 2. Verificação: o que confere em cada etapa e qual evidencia fica

A verificação acompanha cada estágio, com evidências gravadas.

Na descoberta, confere-se que os candidatos pertencem às faixas privadas permitidas e que a lista coincide com o arquivo de faixa-alvo. A evidência é o relatório de descoberta, com o escaneado, o retido e o por quê.

Na nomeação, confere-se que cada nome obedece ao padrão CLI-ANDAR-CAM-001 e ao validador. Nome fora do padrão não é "quase certo": é outra coisa. CLI-ANDAR-001, sem o CAM, e CLI-ANDAR-CAM-1, sem o zero, são recusados, porque aceitar o quase cria duas formas de dizer a mesma coisa. A evidência é a lista de nomes aprovados com o trio decomposto (cliente, andar, número).

Na configuração, confere-se que as credenciais foram aplicadas, o NTP está respondendo e a VLAN está correta. A evidência é o log de configuração, com o alterado e o resultado de cada comando.

No registro, confere-se integridade do inventário: nenhum nome repetido, campos obrigatórios preenchidos e consistência entre os dados gravados e as etapas anteriores. A evidência é o próprio arquivo do inventário, cuja ordem e presença são auditáveis.

Na verificação final, confere-se acesso, hora sincronizada e vídeo disponível. A evidência é o relatório de verificação, que marca cada câmera como presente ou ausente, com a razão da ausência.

## 3. Idempotencia: por que rodar duas vezes não duplica nem quebra

O fluxo foi desenhado para ser executado mais de uma vez sem estragar. A chave é que o nome é chave única e o número sequencial é sempre calculado a partir do inventário já existente, nunca escolhido no vácuo.

Se o processo é reiniciado e encontra uma câmera já registrada, ele reconfere o nome, reaplica a configuração e revalida o registro, sem criar uma segunda entrada. Nomes fora do padrão continuam sendo recusados, independentemente de quantas vezes o comando roda.

A regra contra duplicidade é que números nunca são reutilizados. O próximo número livre é o maior já usado mais um. Um buraco deixado por uma remoção continua sendo um buraco, o que impede que o histórico de duas câmeras se misture no mesmo identificador. Como resultado, executar o fluxo duas vezes deixa o inventário idêntico ao de uma única execução: nem entrada duplicada, nem dado corrompido, nem nome alterado.

## 4. Quando dá erro em um de um lote: isola, registra, segue o lote, volta depois

Em operações em massa, o problema em um item não paralisa o lote inteiro. O procedimento correto é isolar: retirar o item que falhou da fila de sucesso e colocá-lo em uma lista de exceções, mantendo o resto do fluxo ativo.

Em seguida, registra: anota o identificador, a etapa do erro, a mensagem ou sintoma e o que já foi tentado. Essa anotação transforma um bloqueio em um item recuperável.

Depois, segue o lote: continua com os demais, porque cada um tem nome próprio e configuração independente. Parar por causa de um erro isolado só amplifica o dano e atrasa a entrega.

Por fim, volta depois: trata-se a lista de exceções fora do horário de pico, investigando a causa raiz — endereço fora da faixa permitida, credencial inválida, falha de comunicação ou nome fora do padrão CLI-ANDAR-CAM-001 gerado fora do fluxo. O retorno só acontece depois que a causa foi identificada, para que a correção não repita o mesmo erro na próxima rodada.

## 5. O que levar na mochila: lista honesta de quem vai a campo

Quem executa o procedimento a campo precisa do indispensável, nada mais, porque excesso pesa e distrai.

- Caderno ou formulário digital padronizado para anotações.
- Acesso ao inventário e ao relatório de descoberta em dispositivo local, com a faixa-alvo à mão.
- Ferramenta de conferência de nome, de preferência um validador que mostre o trio decomposto.
- Credenciais padrão no local seguro, não anotadas à vista.
- Acesso de rede à faixa permitida.
- Calculadora ou planilha simples para conferir sequência numérica.
- Identificação e material de sinalização para o ambiente.
- Botão de parar e de isolar o item em caso de erro.

O que não se leva: suposições, nomes fora do padrão e pressa. Se algo não cabe na lista, é porque ainda não foi resolvido no procedimento, e aí o procedimento é que muda, não a mochila.
