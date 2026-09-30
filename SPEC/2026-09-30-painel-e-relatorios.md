# Painel administrativo e relatórios (2026-09-30)

## O quê e por quê
O administrador precisa ver como a clínica está: ocupação, faltas, receita e satisfação.

## Critérios de aceitação
- Painel inicial do admin com indicadores do período escolhido (padrão: últimos 30 dias): consultas marcadas, realizadas, canceladas, taxa de faltas, taxa de ocupação da agenda, receita particular, nota média.
- Taxa de ocupação = minutos com consulta marcada ou realizada ÷ minutos de grade disponível no período (teste com números conhecidos).
- Gráficos: consultas por dia (linha), consultas por especialidade (barras), faltas por dia da semana (barras).
- Filtros por unidade, especialidade e profissional, aplicados a todos os indicadores.
- Relatório de consultas com exportação em CSV (as colunas estão documentadas na tela).
- **Registro de auditoria**: ações sensíveis (criar/desativar profissional, cancelar pela clínica, ocultar avaliação, alterar convênio) ficam registradas com autor, data e dados antes/depois; o admin consulta com filtros.
- Profissional vê um painel próprio só com os números dele.

## Fora do escopo
Relatórios financeiros contábeis. Exportação em Excel/PDF (só CSV).
