import { useQuery } from "@tanstack/react-query";
import { useState, type ReactNode } from "react";
import { api, ErroApi } from "@/shared/api";
import { formatarDataHora } from "@/shared/datas";

export type Pagina<T> = { itens: T[]; total: number; pagina: number; paginas: number };

/** Lista paginada (20 por página) com filtro por texto e ordenação, como na API do admin. */
export function useListaAdmin<T>(recurso: string) {
  const [pagina, setPagina] = useState(1);
  const [q, setQ] = useState("");
  const [ordem, setOrdem] = useState("nome");
  const params = new URLSearchParams({ pagina: String(pagina), ordem, ...(q ? { q } : {}) });
  const consulta = useQuery({ queryKey: [recurso, params.toString()], queryFn: () => api<Pagina<T>>(`/${recurso}?${params}`) });
  const controles = (
    <div className="formulario linha">
      <label>
        Filtrar
        <input
          value={q}
          onChange={(e) => {
            setQ(e.target.value);
            setPagina(1);
          }}
          placeholder="Digite parte do nome"
        />
      </label>
      <label>
        Ordenar
        <select value={ordem} onChange={(e) => setOrdem(e.target.value)}>
          <option value="nome">Nome (A–Z)</option>
          <option value="-nome">Nome (Z–A)</option>
          <option value="recentes">Mais recentes</option>
        </select>
      </label>
    </div>
  );
  const paginacao = consulta.data && (
    <nav className="acoes" aria-label="Paginação">
      <button className="secundario" disabled={pagina <= 1} onClick={() => setPagina(pagina - 1)}>
        Anterior
      </button>
      <span>
        Página {consulta.data.pagina} de {consulta.data.paginas} · {consulta.data.total} registro(s)
      </span>
      <button className="secundario" disabled={pagina >= consulta.data.paginas} onClick={() => setPagina(pagina + 1)}>
        Próxima
      </button>
    </nav>
  );
  return { ...consulta, controles, paginacao };
}

type ConsultaPendente = { id: number; inicio: string; paciente: string; profissional?: string };

export function ErroAdmin({ erro }: { erro: unknown }) {
  if (!erro) return null;
  const consultas = (erro instanceof ErroApi ? erro.dados.consultas : undefined) as ConsultaPendente[] | undefined;
  return (
    <div role="alert" className="erro">
      <p>{(erro as Error).message}</p>
      {consultas && (
        <ul>
          {consultas.map((c) => (
            <li key={c.id}>
              {formatarDataHora(c.inicio)} — {c.paciente}
              {c.profissional && ` com ${c.profissional}`}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export function Secao({ titulo, children }: { titulo: string; children: ReactNode }) {
  return (
    <article className="cartao">
      <h2>{titulo}</h2>
      {children}
    </article>
  );
}
