# Visão geral — MarcaConsulta (2026-09-30)

## O quê e por quê
MarcaConsulta é uma aplicação web para marcar consultas em clínicas. Pacientes encontram
profissionais de saúde por especialidade, veem horários livres e marcam, remarcam ou cancelam
consultas. Profissionais e recepcionistas gerenciam agendas, confirmam presença e registram o
atendimento. O administrador da clínica cadastra unidades, especialidades e profissionais e
acompanha indicadores.

Hoje muitas clínicas pequenas marcam consultas por telefone ou WhatsApp, o que gera horários
duplicados, faltas sem aviso e nenhuma visão de ocupação. A aplicação resolve isso com uma agenda
única, regras claras de marcação e lembretes.

## Perfis de usuário
- **Paciente**: busca, marca, remarca, cancela, avalia.
- **Profissional**: define disponibilidade, vê a agenda do dia, registra o atendimento.
- **Recepção**: marca em nome de pacientes, faz check-in, gerencia fila do dia.
- **Administrador**: cadastra clínica, unidades, especialidades, profissionais e vê relatórios.

## Partes do sistema (uma spec para cada)
| Parte | Spec |
|---|---|
| Cadastro e login | `2026-09-30-cadastro-e-login.md` |
| Clínicas, unidades, especialidades e profissionais | `2026-09-30-clinicas-e-profissionais.md` |
| Agenda e disponibilidade | `2026-09-30-agenda-e-disponibilidade.md` |
| Busca de profissionais | `2026-09-30-busca.md` |
| Agendamento (marcar, remarcar, cancelar, lista de espera) | `2026-09-30-agendamento.md` |
| Check-in e atendimento | `2026-09-30-check-in-e-atendimento.md` |
| Notificações e lembretes | `2026-09-30-notificacoes.md` |
| Convênios e pagamento | `2026-09-30-convenios-e-pagamento.md` |
| Avaliações | `2026-09-30-avaliacoes.md` |
| Painel administrativo e relatórios | `2026-09-30-painel-e-relatorios.md` |
| Publicação (deploy) | `2026-09-30-publicacao.md` |

## Stack
- Backend: Python 3.12, FastAPI, SQLAlchemy 2, Alembic, PostgreSQL, pytest.
- Frontend: React 18, TypeScript, Vite, React Router, TanStack Query, Vitest + Testing Library.
- Publicação: um único serviço (FastAPI servindo o build do React) com PostgreSQL gerenciado,
  em URL pública.

## Critérios de aceitação gerais
- A aplicação abre com um clique na URL pública e mostra a página inicial sem login.
- Existe um usuário de demonstração de cada perfil, descrito no README.
- O fluxo principal funciona de ponta a ponta: paciente se cadastra → busca por especialidade →
  escolhe horário → marca → recebe confirmação → recepção faz check-in → profissional registra
  atendimento → paciente avalia.
- Toda rota da API exige autenticação, exceto cadastro, login, busca pública e saúde (`/api/health`).
- Toda regra de negócio das specs tem pelo menos um teste automatizado.
- Datas e horas são guardadas em UTC e exibidas no fuso `America/Sao_Paulo`.
- Nenhum segredo (chave, senha) no repositório: configuração por variáveis de ambiente.

## Fora do escopo
- Telemedicina (vídeo-chamada).
- Prontuário eletrônico completo e prescrição digital com validade legal.
- Integração real com operadoras de convênio ou gateways de pagamento (pagamento é simulado).
- Aplicativo móvel nativo (a web deve funcionar no celular).
