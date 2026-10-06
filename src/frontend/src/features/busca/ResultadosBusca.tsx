import { useQuery } from "@tanstack/react-query";
import { Link, useSearchParams } from "react-router-dom";
import { api } from "@/shared/api";
import { formatarDataHora, formatarPreco } from "@/shared/datas";
import FormularioBusca from "./FormularioBusca";
import { CAMPOS_FILTRO, type PaginaBusca } from "./tipos";

export default function ResultadosBusca() {
  const [params, setParams] = useSearchParams();
  const consulta = new URLSearchParams();
  for (const campo of [...CAMPOS_FILTRO, "pagina"]) {
    const valor = params.get(campo);
    if (valor) consulta.set(campo, valor);
  }
  const { data, isLoading, error } = useQuery({
    queryKey: ["busca", consulta.toString()],
    queryFn: () => api<PaginaBusca>(`/publico/profissionais?${consulta}`),
  });

  function trocar(campo: string, valor: string) {
    const novos = new URLSearchParams(params);
    if (valor) novos.set(campo, valor);
    else novos.delete(campo);
    if (campo !== "pagina") novos.delete("pagina");
    setParams(novos);
  }

  return (
    <section>
      <h1>Profissionais</h1>
      <FormularioBusca key={params.toString()} inicial={params} aoBuscar={setParams} />
      <div className="acoes">
        <label>
          Ordenar por
          <select value={params.get("ordem") ?? "proximo"} onChange={(e) => trocar("ordem", e.target.value)}>
            <option value="proximo">Próximo horário livre</option>
            <option value="preco">Menor preço</option>
          </select>
        </label>
        {data && <span className="suave">{data.total} profissional(is) encontrado(s)</span>}
      </div>
      {isLoading && <p className="suave">Buscando…</p>}
      {error && <p className="erro">{(error as Error).message}</p>}
      {data?.itens.map((p) => (
        <article key={p.id} className="cartao">
          <h2>
            <Link to={`/profissionais/${p.id}`}>{p.nome}</Link>
          </h2>
          <p>{p.especialidades.join(", ")}</p>
          <p className="suave">{p.unidades.join(" · ")}</p>
          <p>
            {p.preco_centavos !== null && <>A partir de {formatarPreco(p.preco_centavos)} · </>}
            {p.nota_media !== null ? `Nota ${p.nota_media.toFixed(1)}` : "Sem avaliações"}
          </p>
          {p.proximo_horario ? (
            <p className="sucesso">
              Próximo horário: {formatarDataHora(p.proximo_horario.inicio)} ({p.proximo_horario.unidade_nome})
            </p>
          ) : (
            <p className="suave">{p.aviso}</p>
          )}
          <Link className="botao" to={`/profissionais/${p.id}`}>
            Ver horários
          </Link>
        </article>
      ))}
      {data && data.paginas > 1 && (
        <nav className="acoes" aria-label="Paginação">
          <button
            className="secundario"
            disabled={data.pagina <= 1}
            onClick={() => trocar("pagina", String(data.pagina - 1))}
          >
            Anterior
          </button>
          <span>
            Página {data.pagina} de {data.paginas}
          </span>
          <button
            className="secundario"
            disabled={data.pagina >= data.paginas}
            onClick={() => trocar("pagina", String(data.pagina + 1))}
          >
            Próxima
          </button>
        </nav>
      )}
    </section>
  );
}
