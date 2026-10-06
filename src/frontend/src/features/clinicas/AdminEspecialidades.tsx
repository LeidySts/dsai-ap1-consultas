import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { api } from "@/shared/api";
import { formatarPreco } from "@/shared/datas";
import { ErroAdmin, Secao, useListaAdmin } from "./ListaAdmin";

type Tipo = { id: number; nome: string; duracao_min: number; preco_centavos: number };
type Especialidade = { id: number; nome: string; tipos: Tipo[] };

export function reaisParaCentavos(valor: string): number {
  return Math.round(Number(valor.replace(/\./g, "").replace(",", ".")) * 100);
}

function NovoTipo({ especialidade, aoCriar }: { especialidade: Especialidade; aoCriar: () => void }) {
  const [tipo, setTipo] = useState({ nome: "", duracao_min: "30", preco: "" });
  const criar = useMutation({
    mutationFn: () =>
      api(`/especialidades/${especialidade.id}/tipos-consulta`, {
        method: "POST",
        body: JSON.stringify({ nome: tipo.nome, duracao_min: Number(tipo.duracao_min), preco_centavos: reaisParaCentavos(tipo.preco) }),
      }),
    onSuccess: () => {
      setTipo({ nome: "", duracao_min: "30", preco: "" });
      aoCriar();
    },
  });
  return (
    <form
      className="formulario linha"
      aria-label={`Novo tipo de ${especialidade.nome}`}
      onSubmit={(e: FormEvent) => {
        e.preventDefault();
        criar.mutate();
      }}
    >
      <label>
        Tipo
        <input value={tipo.nome} onChange={(e) => setTipo({ ...tipo, nome: e.target.value })} required />
      </label>
      <label>
        Duração (min)
        <input type="number" min={15} max={120} step={5} value={tipo.duracao_min} onChange={(e) => setTipo({ ...tipo, duracao_min: e.target.value })} />
      </label>
      <label>
        Preço (R$)
        <input inputMode="decimal" value={tipo.preco} onChange={(e) => setTipo({ ...tipo, preco: e.target.value })} placeholder="250,00" required />
      </label>
      <button type="submit">Adicionar tipo</button>
      <ErroAdmin erro={criar.error} />
    </form>
  );
}

export default function AdminEspecialidades() {
  const lista = useListaAdmin<Especialidade>("especialidades");
  const queryClient = useQueryClient();
  const [nome, setNome] = useState("");
  const atualizar = () => queryClient.invalidateQueries({ queryKey: ["especialidades"] });
  const criar = useMutation({
    mutationFn: () => api("/especialidades", { method: "POST", body: JSON.stringify({ nome }) }),
    onSuccess: () => {
      setNome("");
      return atualizar();
    },
  });

  return (
    <section>
      <h1>Especialidades e tipos de consulta</h1>
      <Secao titulo="Nova especialidade">
        <form
          className="formulario linha"
          onSubmit={(e: FormEvent) => {
            e.preventDefault();
            criar.mutate();
          }}
        >
          <label>
            Nome
            <input value={nome} onChange={(e) => setNome(e.target.value)} required />
          </label>
          <button type="submit">Cadastrar</button>
        </form>
        <ErroAdmin erro={criar.error} />
      </Secao>
      {lista.controles}
      {lista.data?.itens.map((esp) => (
        <Secao key={esp.id} titulo={esp.nome}>
          <ul>
            {esp.tipos.map((t) => (
              <li key={t.id}>
                {t.nome} — {t.duracao_min} min — {formatarPreco(t.preco_centavos)}
              </li>
            ))}
          </ul>
          <NovoTipo especialidade={esp} aoCriar={atualizar} />
        </Secao>
      ))}
      {lista.paginacao}
    </section>
  );
}
