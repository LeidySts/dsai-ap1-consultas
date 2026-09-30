# Convênios e pagamento (2026-09-30)

## O quê e por quê
A forma de pagamento define se o paciente paga na hora ou se a consulta é coberta por convênio.
O pagamento é simulado: o objetivo é registrar e conferir, não cobrar de verdade.

## Critérios de aceitação
- Administrador cadastra **convênios** (nome, código ANS de 6 dígitos, planos) e diz quais profissionais aceitam quais convênios.
- Paciente cadastra suas carteirinhas (convênio, plano, número, validade).
- Ao marcar com convênio: o profissional precisa aceitar aquele convênio e a carteirinha precisa estar válida na data da consulta; senão, 422 com o motivo.
- Consulta particular usa o preço do tipo de consulta; registra-se um **pagamento** com status `pendente`, `pago` ou `estornado`.
- Pagamento simulado: cartão (sempre aprovado, exceto número terminado em `0000`, que é recusado), Pix (gera código fictício e fica `pago` quando a recepção confirma) ou dinheiro no local.
- Cancelamento pelo paciente com mais de 24 h de antecedência estorna o pagamento; cancelamento pela clínica sempre estorna.
- Recepção vê o **caixa do dia**: total recebido por forma de pagamento e lista de pendentes.
- Valores em centavos (inteiros), nunca em ponto flutuante.

## Fora do escopo
Gateway de pagamento real. Emissão de nota fiscal. Guia TISS.
