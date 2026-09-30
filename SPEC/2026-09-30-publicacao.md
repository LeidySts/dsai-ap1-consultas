# Publicação (2026-09-30)

## O quê e por quê
A atividade exige a aplicação aberta em uma URL pública no dia da apresentação.

## Critérios de aceitação
- Um `Dockerfile` na raiz gera uma imagem que compila o frontend (Vite) e serve o build pelo FastAPI, junto com a API em `/api`.
- Banco PostgreSQL gerenciado; a URL do banco e a chave do JWT vêm de variáveis de ambiente (`DATABASE_URL`, `JWT_SECRET`), nunca do código.
- As migrações (Alembic) rodam automaticamente ao iniciar.
- Um comando `seed` cria os dados de demonstração: 3 unidades, 12 especialidades, pelo menos 40 profissionais, 100 pacientes, consultas passadas e futuras, e um usuário de demonstração de cada perfil.
- `GET /api/health` devolve 200 com a versão (hash do commit).
- A URL pública abre a página inicial em um clique, sem login.
- Existe um `.env.example` com todas as variáveis, sem valores reais.
- CI no GitHub Actions roda os testes do backend e do frontend a cada push.

## Fora do escopo
Domínio próprio. Vários ambientes (homologação/produção).
