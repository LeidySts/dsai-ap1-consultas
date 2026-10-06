import { useQuery } from "@tanstack/react-query";
import { api } from "@/shared/api";
import { diaLocal, formatarData, formatarHora } from "@/shared/datas";

export type HorarioLivre = { inicio: string; fim: string; unidade_id: number };

type Props = {
  profissionalId: number;
  tipoConsultaId: number;
  unidades: { id: number; nome: string }[];
  selecionado: HorarioLivre | null;
  aoSelecionar: (horario: HorarioLivre) => void;
};

function intervalo(): { de: string; ate: string } {
  const hoje = new Date();
  const ate = new Date(hoje.getTime() + 30 * 24 * 3600 * 1000);
  return { de: diaLocal(hoje.toISOString()), ate: diaLocal(ate.toISOString()) };
}

export function agruparPorDia(horarios: HorarioLivre[]): [string, HorarioLivre[]][] {
  const grupos = new Map<string, HorarioLivre[]>();
  for (const h of horarios) {
    const dia = diaLocal(h.inicio);
    grupos.set(dia, [...(grupos.get(dia) ?? []), h]);
  }
  return [...grupos.entries()];
}

export default function SeletorHorarios({ profissionalId, tipoConsultaId, unidades, selecionado, aoSelecionar }: Props) {
  const { de, ate } = intervalo();
  const { data, isLoading, error } = useQuery({
    queryKey: ["horarios", profissionalId, tipoConsultaId, de],
    queryFn: () =>
      api<HorarioLivre[]>(
        `/publico/profissionais/${profissionalId}/horarios-livres?tipo_consulta_id=${tipoConsultaId}&de=${de}&ate=${ate}`,
      ),
  });
  const nomeUnidade = (id: number) => unidades.find((u) => u.id === id)?.nome ?? "";

  if (isLoading) return <p className="suave">Carregando horários…</p>;
  if (error) return <p className="erro">{(error as Error).message}</p>;
  if (!data?.length) return <p className="suave">Sem horários livres nos próximos 30 dias.</p>;

  return (
    <div>
      {agruparPorDia(data).map(([dia, horarios]) => (
        <section key={dia} aria-label={formatarData(horarios[0].inicio)}>
          <h3>{formatarData(horarios[0].inicio)}</h3>
          <div className="horarios">
            {horarios.map((h) => (
              <button
                key={h.inicio}
                type="button"
                aria-pressed={selecionado?.inicio === h.inicio}
                title={nomeUnidade(h.unidade_id)}
                onClick={() => aoSelecionar(h)}
              >
                {formatarHora(h.inicio)}
                {unidades.length > 1 && <small> · {nomeUnidade(h.unidade_id)}</small>}
              </button>
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}
