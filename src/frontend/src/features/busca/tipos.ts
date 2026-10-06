export type Opcao = { id: number; nome: string };
export type Filtros = { especialidades: Opcao[]; unidades: Opcao[] };

export type ResultadoBusca = {
  id: number;
  nome: string;
  foto_url: string | null;
  especialidades: string[];
  unidades: string[];
  nota_media: number | null;
  preco_centavos: number | null;
  tipo_consulta_id: number | null;
  proximo_horario: { inicio: string; unidade_id: number; unidade_nome: string } | null;
  aviso: string | null;
};

export type PaginaBusca = { itens: ResultadoBusca[]; total: number; pagina: number; paginas: number };

export const CAMPOS_FILTRO = ["especialidade_id", "unidade_id", "nome", "data", "turno", "ordem"] as const;
