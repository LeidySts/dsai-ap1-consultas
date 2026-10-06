import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import type { Filtros } from "@/features/busca/tipos";
import { api } from "@/shared/api";
import { ErroAdmin, Secao, useListaAdmin } from "./ListaAdmin";

type Profissional = {
  id: number;
  nome: string;
  registro: string;
  ativo: boolean;
  especialidades: { id: number; nome: string }[];
  unidades: { id: number; nome: string }[];
};

const VAZIO = { nome: "", conselho: "CRM", registro_numero: "", registro_uf: "PA", biografia: "", especialidade_ids: [] as number[], unidade_ids: [] as number[] };

function alternar(lista: number[], id: number, marcado: boolean): number[] {
  return marcado ? [...lista, id] : lista.filter((x) => x !== id);
}

export default function AdminProfissionais() {
  const lista = useListaAdmin<Profissional>("profissionais");
  const { data: opcoes } = useQuery({ queryKey: ["filtros"], queryFn: () => api<Filtros>("/publico/filtros") });
  const queryClient = useQueryClient();
  const [form, setForm] = useState(VAZIO);
  const atualizar = () => queryClient.invalidateQueries({ queryKey: ["profissionais"] });
  const criar = useMutation({
    mutationFn: () => api("/profissionais", { method: "POST", body: JSON.stringify(form) }),
    onSuccess: () => {
      setForm(VAZIO);
      return atualizar();
    },
  });
  const desativar = useMutation({
    mutationFn: (id: number) => api(`/profissionais/${id}/desativar`, { method: "POST" }),
    onSuccess: atualizar,
  });

  return (
    <section>
      <h1>Profissionais</h1>
      <Secao titulo="Cadastrados">
        {lista.controles}
        <ErroAdmin erro={desativar.error} />
        <div className="tabela-rolagem">
          <table>
            <thead>
              <tr>
                <th>Nome</th>
                <th>Registro</th>
                <th>Especialidades</th>
                <th>Unidades</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {lista.data?.itens.map((p) => (
                <tr key={p.id}>
                  <td>{p.nome}</td>
                  <td>{p.registro}</td>
                  <td>{p.especialidades.map((e) => e.nome).join(", ")}</td>
                  <td>{p.unidades.map((u) => u.nome).join(", ")}</td>
                  <td>
                    {p.ativo ? (
                      <button className="secundario" onClick={() => desativar.mutate(p.id)}>
                        Desativar
                      </button>
                    ) : (
                      "Desativado"
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {lista.paginacao}
      </Secao>
      <Secao titulo="Novo profissional">
        <form
          className="formulario"
          onSubmit={(e: FormEvent) => {
            e.preventDefault();
            criar.mutate();
          }}
        >
          <label>
            Nome
            <input value={form.nome} onChange={(e) => setForm({ ...form, nome: e.target.value })} required />
          </label>
          <div className="formulario linha">
            <label>
              Conselho
              <input value={form.conselho} onChange={(e) => setForm({ ...form, conselho: e.target.value })} required />
            </label>
            <label>
              Número
              <input value={form.registro_numero} onChange={(e) => setForm({ ...form, registro_numero: e.target.value })} required />
            </label>
            <label>
              UF
              <input value={form.registro_uf} maxLength={2} onChange={(e) => setForm({ ...form, registro_uf: e.target.value })} required />
            </label>
          </div>
          <label>
            Biografia curta
            <textarea maxLength={500} value={form.biografia} onChange={(e) => setForm({ ...form, biografia: e.target.value })} />
          </label>
          <fieldset className="acoes">
            <legend>Especialidades</legend>
            {opcoes?.especialidades.map((e) => (
              <label key={e.id} className="acoes">
                <input
                  type="checkbox"
                  checked={form.especialidade_ids.includes(e.id)}
                  onChange={(ev) => setForm({ ...form, especialidade_ids: alternar(form.especialidade_ids, e.id, ev.target.checked) })}
                />
                {e.nome}
              </label>
            ))}
          </fieldset>
          <fieldset className="acoes">
            <legend>Unidades</legend>
            {opcoes?.unidades.map((u) => (
              <label key={u.id} className="acoes">
                <input
                  type="checkbox"
                  checked={form.unidade_ids.includes(u.id)}
                  onChange={(ev) => setForm({ ...form, unidade_ids: alternar(form.unidade_ids, u.id, ev.target.checked) })}
                />
                {u.nome}
              </label>
            ))}
          </fieldset>
          <ErroAdmin erro={criar.error} />
          <button type="submit">Cadastrar profissional</button>
        </form>
      </Secao>
    </section>
  );
}
