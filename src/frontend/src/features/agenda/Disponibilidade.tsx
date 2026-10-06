import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { api, ErroApi } from "@/shared/api";
import { formatarDataHora, localParaIso } from "@/shared/datas";
import { useMeuCadastro } from "./useMeuCadastro";

export const DIAS = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"];

type Faixa = { id: number; unidade_id: number; dia_semana: number; hora_inicio: string; hora_fim: string };
type Bloqueio = { id: number; inicio: string; fim: string; motivo: string };
type ConsultaConflito = { id: number; inicio: string; paciente: string };

function MensagemErro({ erro }: { erro: unknown }) {
  if (!erro) return null;
  const consultas = (erro instanceof ErroApi ? erro.dados.consultas : undefined) as ConsultaConflito[] | undefined;
  return (
    <div role="alert" className="erro">
      <p>{(erro as Error).message}</p>
      {consultas && (
        <ul>
          {consultas.map((c) => (
            <li key={c.id}>
              {formatarDataHora(c.inicio)} — {c.paciente}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default function Disponibilidade() {
  const { data: eu, error } = useMeuCadastro();
  const queryClient = useQueryClient();
  const id = eu?.id;
  const { data: grade } = useQuery({
    queryKey: ["grade", id],
    queryFn: () => api<Faixa[]>(`/profissionais/${id}/grade`),
    enabled: Boolean(id),
  });
  const { data: bloqueios } = useQuery({
    queryKey: ["bloqueios", id],
    queryFn: () => api<Bloqueio[]>(`/profissionais/${id}/bloqueios`),
    enabled: Boolean(id),
  });
  const atualizar = () => queryClient.invalidateQueries({ predicate: (q) => ["grade", "bloqueios"].includes(String(q.queryKey[0])) });

  const [faixa, setFaixa] = useState({ unidade_id: "", dia_semana: "0", hora_inicio: "08:00", hora_fim: "12:00" });
  const [bloqueio, setBloqueio] = useState({ inicio: "", fim: "", motivo: "" });

  const criarFaixa = useMutation({
    mutationFn: () =>
      api(`/profissionais/${id}/grade`, {
        method: "POST",
        body: JSON.stringify({ ...faixa, unidade_id: Number(faixa.unidade_id || eu?.unidades[0]?.id), dia_semana: Number(faixa.dia_semana) }),
      }),
    onSuccess: atualizar,
  });
  const removerFaixa = useMutation({ mutationFn: (f: number) => api(`/grade/${f}`, { method: "DELETE" }), onSuccess: atualizar });
  const criarBloqueio = useMutation({
    mutationFn: () =>
      api(`/profissionais/${id}/bloqueios`, {
        method: "POST",
        body: JSON.stringify({ inicio: localParaIso(bloqueio.inicio), fim: localParaIso(bloqueio.fim), motivo: bloqueio.motivo }),
      }),
    onSuccess: () => {
      setBloqueio({ inicio: "", fim: "", motivo: "" });
      return atualizar();
    },
  });
  const removerBloqueio = useMutation({ mutationFn: (b: number) => api(`/bloqueios/${b}`, { method: "DELETE" }), onSuccess: atualizar });

  if (error) return <p className="erro">{(error as Error).message}</p>;
  if (!eu) return <p className="suave">Carregando…</p>;
  const nomeUnidade = (u: number) => eu.unidades.find((x) => x.id === u)?.nome ?? "";

  return (
    <section>
      <h1>Disponibilidade</h1>
      <article className="cartao">
        <h2>Grade semanal</h2>
        <div className="tabela-rolagem">
          <table>
            <thead>
              <tr>
                <th>Dia</th>
                <th>Horário</th>
                <th>Unidade</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {grade?.map((f) => (
                <tr key={f.id}>
                  <td>{DIAS[f.dia_semana]}</td>
                  <td>
                    {f.hora_inicio.slice(0, 5)}–{f.hora_fim.slice(0, 5)}
                  </td>
                  <td>{nomeUnidade(f.unidade_id)}</td>
                  <td>
                    <button className="secundario" onClick={() => removerFaixa.mutate(f.id)}>
                      Remover
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <form
          className="formulario linha"
          onSubmit={(e: FormEvent) => {
            e.preventDefault();
            criarFaixa.mutate();
          }}
        >
          <label>
            Dia
            <select value={faixa.dia_semana} onChange={(e) => setFaixa({ ...faixa, dia_semana: e.target.value })}>
              {DIAS.map((d, i) => (
                <option key={d} value={i}>
                  {d}
                </option>
              ))}
            </select>
          </label>
          <label>
            Início
            <input type="time" value={faixa.hora_inicio} onChange={(e) => setFaixa({ ...faixa, hora_inicio: e.target.value })} />
          </label>
          <label>
            Fim
            <input type="time" value={faixa.hora_fim} onChange={(e) => setFaixa({ ...faixa, hora_fim: e.target.value })} />
          </label>
          <label>
            Unidade
            <select value={faixa.unidade_id} onChange={(e) => setFaixa({ ...faixa, unidade_id: e.target.value })}>
              {eu.unidades.map((u) => (
                <option key={u.id} value={u.id}>
                  {u.nome}
                </option>
              ))}
            </select>
          </label>
          <button type="submit">Adicionar faixa</button>
        </form>
        <MensagemErro erro={criarFaixa.error} />
      </article>

      <article className="cartao">
        <h2>Bloqueios (férias, congressos)</h2>
        <ul>
          {bloqueios?.map((b) => (
            <li key={b.id} className="acoes">
              {formatarDataHora(b.inicio)} até {formatarDataHora(b.fim)} — {b.motivo}
              <button className="secundario" onClick={() => removerBloqueio.mutate(b.id)}>
                Remover
              </button>
            </li>
          ))}
        </ul>
        <form
          className="formulario linha"
          onSubmit={(e: FormEvent) => {
            e.preventDefault();
            criarBloqueio.mutate();
          }}
        >
          <label>
            Início
            <input type="datetime-local" value={bloqueio.inicio} onChange={(e) => setBloqueio({ ...bloqueio, inicio: e.target.value })} required />
          </label>
          <label>
            Fim
            <input type="datetime-local" value={bloqueio.fim} onChange={(e) => setBloqueio({ ...bloqueio, fim: e.target.value })} required />
          </label>
          <label>
            Motivo
            <input value={bloqueio.motivo} onChange={(e) => setBloqueio({ ...bloqueio, motivo: e.target.value })} required />
          </label>
          <button type="submit">Bloquear período</button>
        </form>
        <MensagemErro erro={criarBloqueio.error} />
      </article>
    </section>
  );
}
