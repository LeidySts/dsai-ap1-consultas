# Check-in e atendimento (2026-09-30)

## O quê e por quê
No dia da consulta, a recepção precisa saber quem chegou e o profissional precisa chamar o
próximo e registrar o que aconteceu.

## Critérios de aceitação
- Recepção vê a **fila do dia** por unidade: consultas do dia ordenadas por horário, com status.
- Check-in só é possível no dia da consulta, a partir de 1 hora antes do horário; muda o status para `confirmada` e registra a hora de chegada.
- Profissional clica em "chamar" → status `em_atendimento` e hora de início registrada.
- Profissional finaliza com uma **anotação de atendimento** (texto livre, até 5.000 caracteres) → status `realizada` e hora de fim registrada.
- A anotação só é visível para o profissional que a escreveu e para outros profissionais da mesma especialidade; recepção e paciente não veem.
- 30 minutos após o horário sem check-in, a recepção pode marcar `faltou`; às 23:59 do dia, consultas ainda `marcada` viram `faltou` automaticamente (tarefa agendada).
- Paciente pode baixar um **comprovante de comparecimento** em PDF de consulta `realizada`.
- A fila atualiza sozinha a cada 30 segundos (ou por WebSocket).

## Fora do escopo
Painel de TV chamando senha. Prontuário estruturado (CID, exames, prescrição).
