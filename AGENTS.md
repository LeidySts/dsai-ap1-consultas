# Instruções para o agente

Este projeto segue Spec-Driven Development. Leia isto antes de qualquer tarefa.

## Fluxo obrigatório
1. Toda implementação parte de uma spec em `SPEC/`. Leia a spec da parte antes de escrever código.
2. Antes de codificar, proponha um plano curto e uma lista de tarefas (pode ir em `PLAN.md` / `TASKS.md`).
3. Implemente uma tarefa por vez. Cada critério de aceitação da spec deve virar pelo menos um teste.
4. Só considere a parte pronta quando todos os critérios de aceitação tiverem teste passando.
5. Não implemente nada que a spec coloca em "Fora do escopo".
6. Se precisar mudar o que a spec diz, pare e avise: mudança pequena = editar a spec; mudança de rumo = nova spec datada dizendo qual substitui. A spec sempre entra em commit ANTES do código.

## Estrutura
- `src/backend/` — FastAPI (pacote `app`), organizado por módulo: `app/<modulo>/{models,schemas,service,router}.py`
- `src/frontend/` — React + TypeScript + Vite, organizado por funcionalidade: `src/features/<parte>/`
- `tests/backend/` — pytest; `tests/frontend/` — Vitest + Testing Library
- Nada de código gerado automaticamente sem uso, arquivos duplicados ou dados embutidos em código.

## Commits
- Pequenos e frequentes, pelo menos um por parte. Mensagem: `<parte>: <o que mudou>`.
- Sempre terminar com os trailers:
  ```
  Agent: <ferramenta>/<modelo>
  Spec: SPEC/<arquivo-da-spec>.md
  ```
  Editado à mão depois: `Agent: <ferramenta>/<modelo> + manual`. Escrito à mão: `Agent: none`.
- Nunca: squash, rebase do que já foi enviado, `git push --force`, `git commit --amend` de commit enviado.

## Segurança
- Nenhum segredo no código ou no git. Configuração por variáveis de ambiente; manter `.env.example` atualizado.
- Nunca commitar `.env`.

## Padrões
- Datas em UTC no banco, exibidas em `America/Sao_Paulo`. Dinheiro em centavos (inteiro).
- Textos da interface e mensagens de erro em português.
- Rodar `pytest` e `npm test` antes de cada commit.
