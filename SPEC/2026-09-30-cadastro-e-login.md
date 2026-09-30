# Cadastro e login (2026-09-30)

## O quê e por quê
Cada pessoa acessa a aplicação com uma conta própria e só vê o que o seu perfil permite.
Pacientes se cadastram sozinhos; profissionais e recepcionistas são convidados pelo administrador.

## Critérios de aceitação
- Paciente se cadastra com nome, e-mail, CPF, data de nascimento, telefone e senha.
- E-mail e CPF são únicos; CPF é validado pelos dígitos verificadores.
- Senha tem no mínimo 8 caracteres, com letra e número; é guardada com hash (bcrypt ou argon2), nunca em texto.
- Login com e-mail e senha devolve um token de acesso (JWT, 30 min) e um token de renovação (7 dias).
- Após 5 tentativas de login erradas seguidas, a conta fica bloqueada por 15 minutos.
- Logout invalida o token de renovação.
- Recuperação de senha gera um link de uso único válido por 1 hora (em ambiente de demonstração, o link aparece no log/caixa de e-mails simulada).
- Administrador convida profissional ou recepcionista por e-mail; o convite expira em 72 horas.
- Os perfis são: `paciente`, `profissional`, `recepcao`, `admin`. Uma rota proibida para o perfil devolve 403.
- Paciente pode editar os próprios dados, exceto CPF.
- Paciente pode pedir exclusão da conta; os dados pessoais são anonimizados e as consultas passadas ficam para relatório.
- Frontend: telas de cadastro, login, esqueci minha senha, redefinir senha, meu perfil; mensagens de erro em português.

## Fora do escopo
Login com Google/Gov.br. Autenticação em dois fatores.
