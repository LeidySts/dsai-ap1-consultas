import { useQuery } from "@tanstack/react-query";
import { api } from "@/shared/api";

export type MeuCadastro = { id: number; nome: string; unidades: { id: number; nome: string }[] };

export function useMeuCadastro() {
  return useQuery({ queryKey: ["eu-profissional"], queryFn: () => api<MeuCadastro>("/eu/profissional") });
}
