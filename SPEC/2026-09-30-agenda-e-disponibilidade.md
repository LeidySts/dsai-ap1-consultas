# Agenda e disponibilidade (2026-09-30)

## O quê e por quê
Para marcar, o sistema precisa saber em quais horários cada profissional está livre. A
disponibilidade vem de uma grade semanal menos bloqueios, feriados e consultas já marcadas.

## Critérios de aceitação
- Profissional (ou admin) define a **grade semanal** por unidade: dia da semana, hora de início e de fim (ex.: seg 08:00–12:00 na Unidade Centro).
- Intervalos da grade do mesmo profissional não podem se sobrepor, mesmo em unidades diferentes.
- A grade fica dentro do horário de funcionamento da unidade.
- Profissional cria **bloqueios** (férias, congresso) com início, fim e motivo; bloqueio que colide com consultas marcadas devolve 409 com a lista delas.
- Administrador cadastra **feriados** (nacionais e da unidade); em feriado não há horários livres.
- O endpoint de **horários livres** recebe profissional, tipo de consulta e intervalo de datas (máx. 31 dias) e devolve os inícios possíveis, em passos do tamanho da duração do tipo de consulta.
- Um horário livre nunca colide com consulta marcada, bloqueio ou feriado, e nunca está no passado.
- Não há horário livre com menos de 2 horas de antecedência.
- Profissional vê a **agenda do dia e da semana** em formato de calendário, com as consultas coloridas por status.

## Fora do escopo
Sincronização com Google Agenda/Outlook. Grade diferente por semana do mês.
