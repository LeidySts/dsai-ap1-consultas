# Estado do loop — manter o CI verde
## Volta 1 — 20/10/2026
- *O que o agente fez:* leu o PROMPT.md e o ESTADO.md, contou os testes com pytest --collect-only e consultou o último CI vermelho (commit 08588a3, 2/3). Encontrou o teste quebrado em tests/frontend/agenda.test.tsx: ele só passava quando "hoje" caía na semana de 05/10/2026, porque userEvent.clear + type não mudava o valor do campo de data. Trocou por fireEvent.change, sem mudar as asserções. Alterou só 1 arquivo, dentro de tests/ (commit 901d4e3).
- *Passou?* Sim. GitHub Actions do commit 901d4e3: 3/3 jobs verdes (backend, mcp, frontend).
- *Por quê:* a causa era o teste depender da data atual; com a data fixa, ele passa em qualquer dia. Nenhum teste foi apagado ou pulado, e nada fora de tests/ foi alterado.
- *Decisão do porteiro:* parar. Critério de parada atingido na primeira volta.