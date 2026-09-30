# Notificações e lembretes (2026-09-30)

## O quê e por quê
Lembretes reduzem faltas; avisos de cancelamento evitam viagens perdidas.

## Critérios de aceitação
- Eventos que geram notificação: consulta marcada, remarcada, cancelada (por qualquer lado), lembrete 24 horas antes, lembrete 2 horas antes, vaga da lista de espera, convite de profissional, recuperação de senha.
- Canais: **notificação dentro da aplicação** (sino com contador de não lidas) e **e-mail**.
- Em ambiente de demonstração o e-mail não sai de verdade: vai para uma caixa de e-mails simulada visível ao admin em `/admin/emails`.
- Textos das mensagens ficam em modelos (templates) com variáveis; nenhum texto de mensagem fixo no meio da regra de negócio.
- Lembretes são enviados por uma tarefa periódica; uma consulta nunca recebe o mesmo lembrete duas vezes (idempotência, com teste).
- Consulta cancelada não recebe lembretes pendentes.
- Paciente escolhe no perfil se quer receber e-mails de lembrete (as notificações na aplicação sempre existem).
- Paciente marca notificações como lidas, uma a uma ou todas.

## Fora do escopo
SMS, WhatsApp e push no celular.
