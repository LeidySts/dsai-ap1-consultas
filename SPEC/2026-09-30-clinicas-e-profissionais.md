# Clínicas, unidades, especialidades e profissionais (2026-09-30)

## O quê e por quê
A agenda depende de saber onde (unidade), quem (profissional) e o quê (especialidade e tipo de
consulta). O administrador mantém esse cadastro.

## Critérios de aceitação
- Administrador cria, edita e desativa **unidades** (nome, endereço, CEP, telefone, horário de funcionamento).
- Administrador cria e edita **especialidades** (ex.: Cardiologia, Pediatria); nome é único.
- Cada especialidade tem **tipos de consulta** com duração em minutos (15 a 120, múltiplo de 5) e preço particular.
- **Profissional** tem nome, registro no conselho (ex.: CRM 12345/PA), foto opcional, biografia curta, uma ou mais especialidades e uma ou mais unidades onde atende.
- Registro no conselho é único por conselho e UF.
- Desativar profissional ou unidade não apaga consultas passadas; consultas futuras dele/dela precisam ser remarcadas ou canceladas antes (a API devolve 409 listando as pendentes).
- Página pública do profissional mostra nome, especialidades, unidades, biografia e nota média das avaliações.
- Listagens do administrador têm paginação (20 por página), filtro por texto e ordenação.

## Fora do escopo
Várias clínicas independentes na mesma instalação (multi-tenant). Upload de documentos do profissional.
