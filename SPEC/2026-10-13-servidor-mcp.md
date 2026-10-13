# Servidor MCP (2026-10-13)

## O quê e por quê
Um servidor MCP em Python (pasta `mcp/`) que deixa um agente (Claude Code ou outro cliente MCP)
usar o MarcaConsulta como o paciente de demonstração: buscar profissionais, ver horários livres,
listar, marcar e cancelar consultas. Ele não acessa o banco: fala apenas com a API pública em
`https://marcaconsulta.onrender.com/api`, respeitando as mesmas regras que a interface web.

## Critérios de aceitação
- O servidor fica em `mcp/servidor.py`, usa o SDK oficial `mcp` (FastMCP, transporte stdio) e
  `httpx`; as dependências ficam em `mcp/requirements.txt`.
- Configuração só por variáveis de ambiente:
  - `MARCACONSULTA_EMAIL` e `MARCACONSULTA_SENHA` — login do paciente de demonstração (obrigatórias
    para as tools que exigem login; nunca no código nem no git);
  - `MARCACONSULTA_API_URL` — opcional, padrão `https://marcaconsulta.onrender.com/api`.
  - Estão documentadas no `.env.example` sem valores reais.
- Tools de **leitura**:
  - `buscar_profissionais` — filtros opcionais por especialidade (nome), nome do profissional,
    unidade (nome) e data; especialidade/unidade inexistente devolve mensagem dizendo as opções válidas.
    Cada resultado traz id, nome, especialidades, unidades, preço, `tipo_consulta_id` e próximo horário.
  - `ver_horarios_livres` — por profissional; se o tipo de consulta não for informado usa o primeiro
    tipo do profissional; período padrão de hoje a 7 dias.
  - `listar_minhas_consultas` — próximas e passadas do paciente logado, com id, status e se pode cancelar.
- Tools de **escrita**:
  - `marcar_consulta` — profissional, unidade, tipo de consulta e início (de um horário livre).
  - `cancelar_consulta` — pelo id da consulta.
- A docstring de cada tool diz **quando** usá-la (e quando não).
- Login sob demanda (`POST /auth/login`) só nas tools que precisam; o token é reaproveitado e, se a
  API responder 401, o servidor faz login de novo uma vez.
- Datas exibidas em `America/Sao_Paulo`; datas enviadas à API com fuso; preço convertido de centavos
  para reais só na exibição.
- Erros da API (`detail`) voltam para o agente como mensagem em português, sem derrubar o servidor;
  falta de credenciais gera mensagem clara dizendo quais variáveis definir.
- `.mcp.json` versionado na raiz registra o servidor `marcaconsulta`, repassando as variáveis
  de ambiente por expansão (`${...}`), sem valores.
- `.claude/settings.json` versionado: tools de leitura em `allow`, tools de escrita em `ask`.
- Testes em `tests/mcp/` (pytest, API simulada com `httpx.MockTransport`, sem rede) cobrem cada
  tool, o relogin após 401, a falta de credenciais e a tradução de erros; o CI os executa.

## Fora do escopo
Remarcar consulta, lista de espera, avaliações e qualquer ação de recepção/profissional/admin.
Login de outros usuários além do configurado. Transporte HTTP/SSE (só stdio).
