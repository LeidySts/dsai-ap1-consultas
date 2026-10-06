import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import SeletorHorarios, { type HorarioLivre } from "@/features/agenda/SeletorHorarios";
import { api } from "@/shared/api";
import { formatarDataHora, formatarPreco } from "@/shared/datas";

type Tipo = { id: number; nome: string; duracao_min: number; preco_centavos: number };
export type ProfissionalPublico = {
  id: number;
  nome: string;
  registro: string;
  foto_url: string | null;
  biografia: string;
  especialidades: { id: number; nome: string; tipos: Tipo[] }[];
  unidades: { id: number; nome: string; endereco: string; telefone: string }[];
  nota_media: number | null;
  total_avaliacoes: number;
};

export default function PaginaProfissional() {
  const { id } = useParams();
  const navegar = useNavigate();
  const { data: prof, error } = useQuery({
    queryKey: ["profissional", id],
    queryFn: () => api<ProfissionalPublico>(`/publico/profissionais/${id}`),
  });
  const [tipoId, setTipoId] = useState<number | null>(null);
  const [horario, setHorario] = useState<HorarioLivre | null>(null);

  if (error) return <p className="erro">{(error as Error).message}</p>;
  if (!prof) return <p className="suave">Carregando…</p>;

  const tipos = prof.especialidades.flatMap((e) => e.tipos.map((t) => ({ ...t, especialidade: e.nome })));
  const tipoAtual = tipos.find((t) => t.id === tipoId) ?? tipos[0];

  function continuar() {
    if (!horario || !tipoAtual) return;
    const params = new URLSearchParams({
      profissional: String(prof!.id),
      tipo: String(tipoAtual.id),
      unidade: String(horario.unidade_id),
      inicio: horario.inicio,
    });
    navegar(`/agendar/confirmar?${params}`);
  }

  return (
    <section>
      <article className="cartao">
        <h1>{prof.nome}</h1>
        <p className="suave">{prof.registro}</p>
        <p>{prof.especialidades.map((e) => e.nome).join(", ")}</p>
        <p>{prof.biografia}</p>
        <p>{prof.nota_media !== null ? `Nota média ${prof.nota_media.toFixed(1)}` : "Sem avaliações ainda"}</p>
        <h2>Onde atende</h2>
        <ul>
          {prof.unidades.map((u) => (
            <li key={u.id}>
              <strong>{u.nome}</strong> — {u.endereco} · {u.telefone}
            </li>
          ))}
        </ul>
      </article>
      <article className="cartao">
        <h2>Horários livres</h2>
        <label>
          Tipo de consulta
          <select
            value={tipoAtual?.id ?? ""}
            onChange={(e) => {
              setTipoId(Number(e.target.value));
              setHorario(null);
            }}
          >
            {tipos.map((t) => (
              <option key={t.id} value={t.id}>
                {t.especialidade} — {t.nome} ({t.duracao_min} min, {formatarPreco(t.preco_centavos)})
              </option>
            ))}
          </select>
        </label>
        {tipoAtual && (
          <SeletorHorarios
            profissionalId={prof.id}
            tipoConsultaId={tipoAtual.id}
            unidades={prof.unidades}
            selecionado={horario}
            aoSelecionar={setHorario}
          />
        )}
        {horario && (
          <p className="acoes">
            <span>Selecionado: {formatarDataHora(horario.inicio)}</span>
            <button onClick={continuar}>Continuar</button>
          </p>
        )}
      </article>
    </section>
  );
}
