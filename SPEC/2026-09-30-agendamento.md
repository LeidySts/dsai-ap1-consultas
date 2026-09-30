# Agendamento (2026-09-30)

## O quê e por quê
É o coração da aplicação: transformar um horário livre em consulta marcada, sem duplicidade, e
permitir remarcar e cancelar com regras claras.

## Critérios de aceitação
- Paciente marca escolhendo profissional, unidade, tipo de consulta, horário livre e forma de pagamento (particular ou convênio).
- Recepção pode marcar em nome de qualquer paciente cadastrado.
- **Dois pedidos simultâneos para o mesmo horário: só um é aceito**; o outro recebe 409 "horário não está mais disponível" (garantido no banco, com restrição de unicidade ou lock, e coberto por teste de concorrência).
- Paciente não pode ter duas consultas que se sobrepõem no tempo.
- Paciente pode ter no máximo 3 consultas futuras com status `marcada` ao mesmo tempo.
- Status possíveis: `marcada`, `confirmada`, `em_atendimento`, `realizada`, `cancelada_paciente`, `cancelada_clinica`, `faltou`. Transições inválidas devolvem 422.
- **Cancelar** pelo paciente é permitido até 24 horas antes; depois disso, só a recepção cancela.
- **Remarcar** é cancelar + marcar numa operação só: se o novo horário falhar, a consulta original continua marcada.
- Cada consulta pode ser remarcada no máximo 2 vezes.
- Paciente com 3 faltas nos últimos 90 dias fica impedido de marcar pela web por 30 dias (a recepção ainda pode marcar).
- **Lista de espera**: se não houver horário na data desejada, o paciente entra na lista; quando um horário daquele profissional é liberado, o primeiro da lista é avisado e tem 2 horas para confirmar antes de passar ao próximo.
- Paciente vê "Minhas consultas" separadas em próximas e passadas, com ações de cancelar/remarcar quando permitidas.
- Toda mudança de status fica registrada num histórico (quem, quando, de qual para qual status).

## Fora do escopo
Consultas em grupo. Marcação recorrente (ex.: toda semana).
