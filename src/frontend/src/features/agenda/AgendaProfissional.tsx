import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { ROTULO_STATUS, type Consulta } from "@/features/agendamento/tipos";
import { api } from "@/shared/api";
import { diaLocal, formatarData, formatarHora, inicioDaSemana, somarDias } from "@/shared/datas";
import { useMeuCadastro } from "./useMeuCadastro";

type Visao = "dia" | "semana";

export default function AgendaProfissional() {
  const { data: eu, error: erroCadastro } = useMeuCadastro();
  const [visao, setVisao] = useState<Visao>("dia");
  const [dia, setDia] = useState(() => diaLocal(new Date().toISOString()));
  const de = visao === "dia" ? dia : inicioDaSemana(dia);
  const ate = visao === "dia" ? dia : somarDias(de, 6);
  const { data: consultas, isLoading } = useQuery({
    queryKey: ["agenda", eu?.id, de, ate],
    queryFn: () => api<Consulta[]>(`/profissionais/${eu!.id}/agenda?de=${de}&ate=${ate}`),
    enabled: Boolean(eu),
  });

  if (erroCadastro) return <p className="erro">{(erroCadastro as Error).message}</p>;

  const dias = Array.from({ length: visao === "dia" ? 1 : 7 }, (_, i) => somarDias(de, i));
  const passo = visao === "dia" ? 1 : 7;

  return (
    <section>
      <h1>Minha agenda</h1>
      <div className="acoes">
        <div className="abas" role="tablist">
          {(["dia", "semana"] as Visao[]).map((v) => (
            <button key={v} role="tab" aria-selected={visao === v} className={visao === v ? "" : "secundario"} onClick={() => setVisao(v)}>
              {v === "dia" ? "Dia" : "Semana"}
            </button>
          ))}
        </div>
        <button className="secundario" onClick={() => setDia(somarDias(dia, -passo))} aria-label="Anterior">
          ←
        </button>
        <input type="date" value={dia} onChange={(e) => e.target.value && setDia(e.target.value)} aria-label="Data" />
        <button className="secundario" onClick={() => setDia(somarDias(dia, passo))} aria-label="Próximo">
          →
        </button>
      </div>
      <p className="acoes suave">
        {Object.entries(ROTULO_STATUS).map(([status, rotulo]) => (
          <span key={status} className={`status status-${status}`}>
            {rotulo}
          </span>
        ))}
      </p>
      {isLoading && <p className="suave">Carregando…</p>}
      {dias.map((d) => {
        const doDia = (consultas ?? []).filter((c) => diaLocal(c.inicio) === d);
        return (
          <section key={d} className="cartao" aria-label={d}>
            <h2>{formatarData(`${d}T15:00:00Z`)}</h2>
            {doDia.length === 0 ? (
              <p className="suave">Nenhuma consulta.</p>
            ) : (
              <ul>
                {doDia.map((c) => (
                  <li key={c.id} className="acoes">
                    <strong>
                      {formatarHora(c.inicio)}–{formatarHora(c.fim)}
                    </strong>
                    <span>{c.paciente.nome}</span>
                    <span className="suave">
                      {c.tipo_consulta.nome} · {c.unidade.nome}
                    </span>
                    <span className={`status status-${c.status}`}>{ROTULO_STATUS[c.status] ?? c.status}</span>
                  </li>
                ))}
              </ul>
            )}
          </section>
        );
      })}
    </section>
  );
}
