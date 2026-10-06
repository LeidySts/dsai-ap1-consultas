export type Consulta = {
  id: number;
  inicio: string;
  fim: string;
  status: string;
  forma_pagamento: string;
  preco_centavos: number;
  remarcacoes: number;
  paciente: { id: number; nome: string };
  profissional: { id: number; nome: string };
  unidade: { id: number; nome: string; endereco: string };
  tipo_consulta: { id: number; nome: string; duracao_min: number };
  pode_cancelar: boolean;
  pode_remarcar: boolean;
};

export const ROTULO_STATUS: Record<string, string> = {
  marcada: "Marcada",
  confirmada: "Confirmada",
  em_atendimento: "Em atendimento",
  realizada: "Realizada",
  cancelada_paciente: "Cancelada pelo paciente",
  cancelada_clinica: "Cancelada pela clínica",
  faltou: "Faltou",
};
