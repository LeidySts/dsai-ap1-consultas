import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import type { Filtros } from "@/features/busca/tipos";
import { api } from "@/shared/api";
import { ErroAdmin, Secao } from "./ListaAdmin";

type Feriado = { id: number; data: string; nome: string; unidade_id: number | null };

export default function AdminFeriados() {
  const queryClient = useQueryClient();
  const { data: feriados } = useQuery({ queryKey: ["feriados"], queryFn: () => api<Feriado[]>("/feriados") });
  const { data: opcoes } = useQuery({ queryKey: ["filtros"], queryFn: () => api<Filtros>("/publico/filtros") });
  const [form, setForm] = useState({ data: "", nome: "", unidade_id: "" });
  const atualizar = () => queryClient.invalidateQueries({ queryKey: ["feriados"] });
  const criar = useMutation({
    mutationFn: () =>
      api("/feriados", {
        method: "POST",
        body: JSON.stringify({ data: form.data, nome: form.nome, unidade_id: form.unidade_id ? Number(form.unidade_id) : null }),
      }),
    onSuccess: () => {
      setForm({ data: "", nome: "", unidade_id: "" });
      return atualizar();
    },
  });
  const remover = useMutation({ mutationFn: (id: number) => api(`/feriados/${id}`, { method: "DELETE" }), onSuccess: atualizar });
  const nomeUnidade = (id: number | null) => (id === null ? "Nacional" : opcoes?.unidades.find((u) => u.id === id)?.nome ?? `Unidade ${id}`);

  return (
    <section>
      <h1>Feriados</h1>
      <Secao titulo="Novo feriado">
        <form
          className="formulario linha"
          onSubmit={(e: FormEvent) => {
            e.preventDefault();
            criar.mutate();
          }}
        >
          <label>
            Data
            <input type="date" value={form.data} onChange={(e) => setForm({ ...form, data: e.target.value })} required />
          </label>
          <label>
            Nome
            <input value={form.nome} onChange={(e) => setForm({ ...form, nome: e.target.value })} required />
          </label>
          <label>
            Abrangência
            <select value={form.unidade_id} onChange={(e) => setForm({ ...form, unidade_id: e.target.value })}>
              <option value="">Nacional (todas as unidades)</option>
              {opcoes?.unidades.map((u) => (
                <option key={u.id} value={u.id}>
                  {u.nome}
                </option>
              ))}
            </select>
          </label>
          <button type="submit">Cadastrar</button>
        </form>
        <ErroAdmin erro={criar.error} />
      </Secao>
      <Secao titulo="Cadastrados">
        <ul>
          {feriados?.map((f) => (
            <li key={f.id} className="acoes">
              {f.data.split("-").reverse().join("/")} — {f.nome} ({nomeUnidade(f.unidade_id)})
              <button className="secundario" onClick={() => remover.mutate(f.id)}>
                Remover
              </button>
            </li>
          ))}
        </ul>
      </Secao>
    </section>
  );
}
