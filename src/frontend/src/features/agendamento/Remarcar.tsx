import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import SeletorHorarios, { type HorarioLivre } from "@/features/agenda/SeletorHorarios";
import type { ProfissionalPublico } from "@/features/clinicas/PaginaProfissional";
import { api } from "@/shared/api";
import { formatarDataHora } from "@/shared/datas";
import type { Consulta } from "./tipos";

export default function Remarcar() {
  const { id } = useParams();
  const navegar = useNavigate();
  const queryClient = useQueryClient();
  const [horario, setHorario] = useState<HorarioLivre | null>(null);

  const { data: consulta, error } = useQuery({
    queryKey: ["consulta", id],
    queryFn: () => api<Consulta>(`/consultas/${id}`),
  });
  const { data: prof } = useQuery({
    queryKey: ["profissional", String(consulta?.profissional.id)],
    queryFn: () => api<ProfissionalPublico>(`/publico/profissionais/${consulta!.profissional.id}`),
    enabled: Boolean(consulta),
  });
  const remarcar = useMutation({
    mutationFn: (h: HorarioLivre) =>
      api<Consulta>(`/consultas/${id}/remarcar`, {
        method: "POST",
        body: JSON.stringify({ inicio: h.inicio, unidade_id: h.unidade_id }),
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["minhas-consultas"] });
      navegar("/minhas-consultas");
    },
  });

  if (error) return <p className="erro">{(error as Error).message}</p>;
  if (!consulta) return <p className="suave">Carregando…</p>;
  if (!consulta.pode_remarcar) {
    return (
      <p className="erro">
        Esta consulta não pode mais ser remarcada pela web. <Link to="/minhas-consultas">Voltar</Link>
      </p>
    );
  }

  return (
    <section className="cartao">
      <h1>Remarcar consulta</h1>
      <p>
        Atual: {formatarDataHora(consulta.inicio)} com {consulta.profissional.nome} ({consulta.tipo_consulta.nome}).
      </p>
      <p className="suave">Remarcações usadas: {consulta.remarcacoes} de 2.</p>
      <SeletorHorarios
        profissionalId={consulta.profissional.id}
        tipoConsultaId={consulta.tipo_consulta.id}
        unidades={prof?.unidades ?? [consulta.unidade]}
        selecionado={horario}
        aoSelecionar={setHorario}
      />
      {remarcar.error && (
        <p role="alert" className="erro">
          {(remarcar.error as Error).message}
        </p>
      )}
      <div className="acoes">
        <button disabled={!horario || remarcar.isPending} onClick={() => horario && remarcar.mutate(horario)}>
          {horario ? `Remarcar para ${formatarDataHora(horario.inicio)}` : "Escolha um horário"}
        </button>
        <Link to="/minhas-consultas">Voltar</Link>
      </div>
    </section>
  );
}
