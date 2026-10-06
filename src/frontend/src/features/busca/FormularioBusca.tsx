import { useQuery } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { api } from "@/shared/api";
import type { Filtros } from "./tipos";

type Props = { inicial: URLSearchParams; aoBuscar: (params: URLSearchParams) => void };

export default function FormularioBusca({ inicial, aoBuscar }: Props) {
  const { data: filtros } = useQuery({ queryKey: ["filtros"], queryFn: () => api<Filtros>("/publico/filtros") });
  const [valores, setValores] = useState(() => ({
    especialidade_id: inicial.get("especialidade_id") ?? "",
    unidade_id: inicial.get("unidade_id") ?? "",
    nome: inicial.get("nome") ?? "",
    data: inicial.get("data") ?? "",
    turno: inicial.get("turno") ?? "",
  }));

  function enviar(e: FormEvent) {
    e.preventDefault();
    const params = new URLSearchParams();
    for (const [chave, valor] of Object.entries(valores)) if (valor) params.set(chave, valor);
    const ordem = inicial.get("ordem");
    if (ordem) params.set("ordem", ordem);
    aoBuscar(params);
  }

  const mudar = (campo: keyof typeof valores) => (e: { target: { value: string } }) =>
    setValores({ ...valores, [campo]: e.target.value });

  return (
    <form className="formulario linha cartao" onSubmit={enviar} role="search">
      <label>
        Especialidade
        <select value={valores.especialidade_id} onChange={mudar("especialidade_id")}>
          <option value="">Todas</option>
          {filtros?.especialidades.map((e) => (
            <option key={e.id} value={e.id}>
              {e.nome}
            </option>
          ))}
        </select>
      </label>
      <label>
        Unidade
        <select value={valores.unidade_id} onChange={mudar("unidade_id")}>
          <option value="">Todas</option>
          {filtros?.unidades.map((u) => (
            <option key={u.id} value={u.id}>
              {u.nome}
            </option>
          ))}
        </select>
      </label>
      <label>
        Nome ou especialidade
        <input value={valores.nome} onChange={mudar("nome")} placeholder="Ex.: joão, cardiologia" />
      </label>
      <label>
        A partir de
        <input type="date" value={valores.data} onChange={mudar("data")} />
      </label>
      <label>
        Turno
        <select value={valores.turno} onChange={mudar("turno")}>
          <option value="">Qualquer</option>
          <option value="manha">Manhã</option>
          <option value="tarde">Tarde</option>
          <option value="noite">Noite</option>
        </select>
      </label>
      <button type="submit">Buscar</button>
    </form>
  );
}
