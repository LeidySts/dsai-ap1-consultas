# Loop da AP1 — manter o CI verde (MarcaConsulta)

## 1. Tarefa recorrente e gatilho
*Tarefa:* quando o CI (GitHub Actions) do repositório falha, descobrir qual teste quebrou e consertá-lo.

*Gatilho: evento.* O loop dispara quando um push na branch main termina com o CI vermelho.
Justificativa: a falha aparece no momento do push, e é aí que alguém precisa agir; rodar por agenda
gastaria voltas quando está tudo verde. Observação: no nosso caso, um teste quebrou só pela
passagem do tempo (depende da data atual), então uma execução diária por agenda também se
justificaria como complemento.

## 2. Critério de parada (conferível por máquina)
O loop para quando TODOS os itens abaixo forem verdadeiros:
1. pytest na raiz do repositório termina com código de saída 0.
2. pytest tests/mcp termina com código de saída 0.
3. npm test dentro de src/frontend termina com código de saída 0.
4. O número de testes coletados por pytest --collect-only -q não diminuiu em relação à volta anterior.
5. O commit enviado mostra 3/3 jobs verdes no GitHub Actions.

## 3. Quando parar e chamar os humanos
Pare e explique o motivo, sem continuar, se:
- a correção exigir mudar código da aplicação em src/ (só é permitido alterar arquivos em tests/);
- a única saída for apagar, pular (skip) ou enfraquecer um teste;
- precisar de senha, token, rede externa ou banco de produção;
- o mesmo erro continuar depois de duas tentativas nesta volta.

*Não pode tocar em:* src/, .github/, Dockerfile, render.yaml, docker-compose.yml,
.env*, mcp/, src/backend/alembic/.

## Instrução para o agente (uma volta)
1. Leia este arquivo e loop/ESTADO.md (o que já foi tentado).
2. Descubra qual teste falha e por quê (rode os testes; se o banco local não estiver disponível,
   explique isso e use a mensagem de erro do CI).
3. Faça a menor correção possível dentro dos limites acima.
4. Rode os testes, faça commit e push com a mensagem loop: volta N — ....
5. No final, diga em poucas linhas o que fez e se acha que o critério de parada foi atingido.
   Não escreva no ESTADO.md: quem registra é o porteiro.