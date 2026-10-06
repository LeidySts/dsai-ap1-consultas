import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { api } from "@/shared/api";
import { DIAS } from "@/shared/datas";
import { ErroAdmin, Secao, useListaAdmin } from "./ListaAdmin";

type Unidade = {
  id: number;
  nome: string;
  endereco: string;
  cep: string;
  telefone: string;
  abertura: string;
  fechamento: string;
  dias_funcionamento: number[];
  ativa: boolean;
};

const VAZIA = { nome: "", endereco: "", cep: "", telefone: "", abertura: "07:00", fechamento: "19:00", dias_funcionamento: [0, 1, 2, 3, 4] };

export default function AdminUnidades() {
  const lista = useListaAdmin<Unidade>("unidades");
  const queryClient = useQueryClient();
  const [form, setForm] = useState(VAZIA);
  const atualizar = () => queryClient.invalidateQueries({ queryKey: ["unidades"] });
  const criar = useMutation({
    mutationFn: () => api("/unidades", { method: "POST", body: JSON.stringify(form) }),
    onSuccess: () => {
      setForm(VAZIA);
      return atualizar();
    },
  });
  const desativar = useMutation({
    mutationFn: (id: number) => api(`/unidades/${id}/desativar`, { method: "POST" }),
    onSuccess: atualizar,
  });

  const campo = (nome: "nome" | "endereco" | "cep" | "telefone", rotulo: string) => (
    <label>
      {rotulo}
      <input value={form[nome]} onChange={(e) => setForm({ ...form, [nome]: e.target.value })} required />
    </label>
  );

  return (
    <section>
      <h1>Unidades</h1>
      <Secao titulo="Cadastradas">
        {lista.controles}
        <ErroAdmin erro={desativar.error} />
        <div className="tabela-rolagem">
          <table>
            <thead>
              <tr>
                <th>Nome</th>
                <th>Endereço</th>
                <th>Funcionamento</th>
                <th>Situação</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {lista.data?.itens.map((u) => (
                <tr key={u.id}>
                  <td>{u.nome}</td>
                  <td>
                    {u.endereco} · CEP {u.cep}
                  </td>
                  <td>
                    {u.dias_funcionamento.map((d) => DIAS[d].slice(0, 3)).join(", ")} · {u.abertura.slice(0, 5)}–{u.fechamento.slice(0, 5)}
                  </td>
                  <td>{u.ativa ? "Ativa" : "Desativada"}</td>
                  <td>
                    {u.ativa && (
                      <button className="secundario" onClick={() => desativar.mutate(u.id)}>
                        Desativar
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {lista.paginacao}
      </Secao>
      <Secao titulo="Nova unidade">
        <form
          className="formulario"
          onSubmit={(e: FormEvent) => {
            e.preventDefault();
            criar.mutate();
          }}
        >
          {campo("nome", "Nome")}
          {campo("endereco", "Endereço")}
          {campo("cep", "CEP")}
          {campo("telefone", "Telefone")}
          <label>
            Abre às
            <input type="time" value={form.abertura} onChange={(e) => setForm({ ...form, abertura: e.target.value })} />
          </label>
          <label>
            Fecha às
            <input type="time" value={form.fechamento} onChange={(e) => setForm({ ...form, fechamento: e.target.value })} />
          </label>
          <fieldset className="acoes">
            <legend>Dias de funcionamento</legend>
            {DIAS.map((d, i) => (
              <label key={d} className="acoes">
                <input
                  type="checkbox"
                  checked={form.dias_funcionamento.includes(i)}
                  onChange={(e) =>
                    setForm({
                      ...form,
                      dias_funcionamento: e.target.checked
                        ? [...form.dias_funcionamento, i]
                        : form.dias_funcionamento.filter((x) => x !== i),
                    })
                  }
                />
                {d}
              </label>
            ))}
          </fieldset>
          <ErroAdmin erro={criar.error} />
          <button type="submit">Cadastrar unidade</button>
        </form>
      </Secao>
    </section>
  );
}
