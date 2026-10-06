# MarcaConsulta

Aplicação web para marcação de consultas em clínicas, construída com um agente de IA seguindo
Spec-Driven Development (spec → plan → tasks). Atividade Prática 1 de Desenvolvimento de Software
Apoiado por IA (UFPA, 2026.4, Prof. Gustavo Pinto).

## 🔗 Aplicação publicada
**URL:** <https://marcaconsulta.onrender.com>

> Se o serviço estiver "dormindo" (plano gratuito), o primeiro acesso pode levar até 1 minuto.

### Usuários de demonstração
| Perfil | E-mail | Senha |
|---|---|---|
| Paciente | paciente@demo.com | demo1234 |
| Profissional | medico@demo.com | demo1234 |
| Recepção | recepcao@demo.com | demo1234 |
| Administrador | admin@demo.com | demo1234 |

## 👥 Dupla
| Nome | GitHub |
|---|---|
| PREENCHER | @PREENCHER |
| PREENCHER | @PREENCHER |

## 🧱 Stack
- **Backend:** Python 3.12, FastAPI, SQLAlchemy 2, Alembic, PostgreSQL, pytest
- **Frontend:** React 18, TypeScript, Vite, React Router, TanStack Query, Vitest
- **Publicação:** Docker no Render (`render.yaml`) + PostgreSQL gerenciado do Render

## ▶️ Como rodar localmente
```bash
cp .env.example .env              # preencha os valores
docker compose up -d db           # sobe o PostgreSQL
cd src/backend && pip install -r requirements.txt
alembic upgrade head && python -m app.seed
uvicorn app.main:app --reload     # API em http://localhost:8000
cd ../frontend && npm install && npm run dev   # front em http://localhost:5173
```
Testes: `pip install -r src/backend/requirements-dev.txt`, depois `pytest` (backend) e `npm test` (frontend), na raiz.
Sem `TEST_DATABASE_URL`, os testes do backend sobem um PostgreSQL embutido (`pgserver`).

## 📐 Specs
Uma spec por parte do sistema, datada, em [`SPEC/`](SPEC/). Comece por
[`SPEC/2026-09-30-visao-geral.md`](SPEC/2026-09-30-visao-geral.md).

## 🤖 Ferramentas e modelos usados
| Ferramenta | Modelo | Usada para |
|---|---|---|
| Claude (claude.ai) | Claude Opus 5.5 | Leitura da atividade, rascunho das specs, README e AGENTS.md |
| PREENCHER (ex.: Claude Code) | PREENCHER (ex.: claude-sonnet-5-5) | Implementação |

Todas as sessões, do primeiro ao último prompt, estão em [`prompts/sessoes/`](prompts/sessoes/)
(exportações brutas, nome `AAAA-MM-DD-HHMM-<ferramenta>.<ext>`).

## 📊 Números
| | |
|---|---|
| Specs | PREENCHER |
| Sessões | PREENCHER |
| Prompts | PREENCHER |
| Horas | PREENCHER |

## 📏 Contagem de linhas (cloc)
Comando:
```bash
cloc . --vcs=git \
  --exclude-dir=node_modules,vendor,dist,build,prompts \
  --exclude-lang=Markdown,JSON,YAML,CSV,Text,SVG \
  --not-match-f='(lock|\.min\.)'
```

### Total
```
COLE AQUI A SAÍDA DO COMANDO ACIMA
```

### Só testes
```
COLE AQUI A SAÍDA DO MESMO COMANDO RODADO EM tests/ (e nos testes do frontend)
```

### Sem testes
```
COLE AQUI A SAÍDA DO MESMO COMANDO COM --exclude-dir=...,tests
```
