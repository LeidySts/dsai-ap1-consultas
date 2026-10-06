import { useMutation, useQuery } from "@tanstack/react-query";
import { useState } from "react";
import SeletorHorarios, { type HorarioLivre } from "@/features/agenda/SeletorHorarios";
import type { PaginaBusca } from "@/features/busca/tipos";
import type { ProfissionalPublico } from "@/features/clinicas/PaginaProfissional";
import { api } from "@/shared/api";
import { formatarDataHora } from "@/shared/datas";
import type { Consulta } from "./tipos";

type Paciente = { id: number; nome: string; email: string; cpf: string | null };

function mascararCpf(cpf: string | null): string {
  return cpf ? `***.${cpf.slice(3, 6)}.${cpf.slice(6, 9)}-**` : "";
}

export default function AgendarRecepcao() {
  const [buscaPaciente, setBuscaPaciente] = useState("");
  const [paciente, setPaciente] = useState<Paciente | null>(null);
  const [buscaProf, setBuscaProf] = useState("");
  const [profId, setProfId] = useState<number | null>(null);
  const [tipoId, setTipoId] = useState<number | null>(null);
  const [horario, setHorario] = useState<HorarioLivre | null>(null);

  const pacientes = useQuery({
    queryKey: ["pacientes", buscaPaciente],
    queryFn: () => api<Paciente[]>(`/pacientes?q=${encodeURIComponent(buscaPaciente)}`),
    enabled: buscaPaciente.trim().length >= 2 && !paciente,
  });
  const profissionais = useQuery({
    queryKey: ["busca-recepcao", buscaProf],
    queryFn: () => api<PaginaBusca>(`/publico/profissionais?nome=${encodeURIComponent(buscaProf)}`),
    enabled: buscaProf.trim().length >= 2 && !profId,
  });
  const prof = useQuery({
    queryKey: ["profissional", String(profId)],
    queryFn: () => api<ProfissionalPublico>(`/publico/profissionais/${profId}`),
    enabled: Boolean(profId),
  });
  const tipos = prof.data?.especialidades.flatMap((e) => e.tipos.map((t) => ({ ...t, especialidade: e.nome }))) ?? [];
  const tipoAtual = tipos.find((t) => t.id === tipoId) ?? tipos[0];

  const marcar = useMutation({
    mutationFn: () =>
      api<Consulta>("/consultas", {
        method: "POST",
        body: JSON.stringify({
          paciente_id: paciente!.id,
          profissional_id: profId,
          tipo_consulta_id: tipoAtual!.id,
          unidade_id: horario!.unidade_id,
          inicio: horario!.inicio,
        }),
      }),
  });

  function recomecar() {
    setPaciente(null);
    setBuscaPaciente("");
    setProfId(null);
    setBuscaProf("");
    setHorario(null);
    marcar.reset();
  }

  if (marcar.isSuccess) {
    return (
      <section className="cartao">
        <h1 className="sucesso">Consulta marcada!</h1>
        <p>
          {marcar.data.paciente.nome} com {marcar.data.profissional.nome} em {formatarDataHora(marcar.data.inicio)} ({marcar.data.unidade.nome}).
        </p>
        <button onClick={recomecar}>Marcar outra</button>
      </section>
    );
  }

  return (
    <section>
      <h1>Marcar para paciente</h1>
      <article className="cartao">
        <h2>1. Paciente</h2>
        {paciente ? (
          <p className="acoes">
            <strong>{paciente.nome}</strong> <span className="suave">{paciente.email}</span>
            <button className="secundario" onClick={() => setPaciente(null)}>
              Trocar
            </button>
          </p>
        ) : (
          <>
            <label>
              Nome, e-mail ou CPF
              <input value={buscaPaciente} onChange={(e) => setBuscaPaciente(e.target.value)} />
            </label>
            <ul>
              {pacientes.data?.map((p) => (
                <li key={p.id}>
                  <button className="secundario" onClick={() => setPaciente(p)}>
                    {p.nome} · {p.email} · {mascararCpf(p.cpf)}
                  </button>
                </li>
              ))}
            </ul>
            {pacientes.data?.length === 0 && <p className="suave">Nenhum paciente encontrado.</p>}
          </>
        )}
      </article>

      {paciente && (
        <article className="cartao">
          <h2>2. Profissional e horário</h2>
          {profId && prof.data ? (
            <>
              <p className="acoes">
                <strong>{prof.data.nome}</strong>
                <button
                  className="secundario"
                  onClick={() => {
                    setProfId(null);
                    setHorario(null);
                  }}
                >
                  Trocar
                </button>
              </p>
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
                      {t.especialidade} — {t.nome} ({t.duracao_min} min)
                    </option>
                  ))}
                </select>
              </label>
              {tipoAtual && (
                <SeletorHorarios
                  profissionalId={prof.data.id}
                  tipoConsultaId={tipoAtual.id}
                  unidades={prof.data.unidades}
                  selecionado={horario}
                  aoSelecionar={setHorario}
                />
              )}
            </>
          ) : (
            <>
              <label>
                Nome do profissional ou especialidade
                <input value={buscaProf} onChange={(e) => setBuscaProf(e.target.value)} />
              </label>
              <ul>
                {profissionais.data?.itens.map((p) => (
                  <li key={p.id}>
                    <button className="secundario" onClick={() => setProfId(p.id)}>
                      {p.nome} · {p.especialidades.join(", ")}
                    </button>
                  </li>
                ))}
              </ul>
            </>
          )}
        </article>
      )}

      {paciente && horario && (
        <article className="cartao">
          <h2>3. Confirmar</h2>
          <p>
            {paciente.nome} — {formatarDataHora(horario.inicio)}
          </p>
          {marcar.error && (
            <p role="alert" className="erro">
              {(marcar.error as Error).message}
            </p>
          )}
          <button onClick={() => marcar.mutate()} disabled={marcar.isPending}>
            Confirmar marcação
          </button>
        </article>
      )}
    </section>
  );
}
