import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router-dom";
import { api } from "@/shared/api";
import { formatarDataHora, formatarPreco } from "@/shared/datas";
import { ROTULO_STATUS, type Consulta } from "./tipos";

type Minhas = { proximas: Consulta[]; passadas: Consulta[] };

export function CartaoConsulta({ consulta, acoes }: { consulta: Consulta; acoes?: React.ReactNode }) {
  return (
    <article className="cartao">
      <p className="acoes">
        <strong>{formatarDataHora(consulta.inicio)}</strong>
        <span className={`status status-${consulta.status}`}>{ROTULO_STATUS[consulta.status] ?? consulta.status}</span>
      </p>
      <p>
        {consulta.profissional.nome} · {consulta.tipo_consulta.nome}
      </p>
      <p className="suave">
        {consulta.unidade.nome} — {consulta.unidade.endereco} · {formatarPreco(consulta.preco_centavos)}
      </p>
      {acoes}
    </article>
  );
}

export default function MinhasConsultas() {
  const [aba, setAba] = useState<"proximas" | "passadas">("proximas");
  const queryClient = useQueryClient();
  const { data, isLoading, error } = useQuery({
    queryKey: ["minhas-consultas"],
    queryFn: () => api<Minhas>("/consultas/minhas"),
  });
  const cancelar = useMutation({
    mutationFn: (id: number) => api<Consulta>(`/consultas/${id}/cancelar`, { method: "POST" }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["minhas-consultas"] }),
  });

  const lista = data?.[aba] ?? [];
  return (
    <section>
      <h1>Minhas consultas</h1>
      <div className="abas" role="tablist">
        <button role="tab" aria-selected={aba === "proximas"} className={aba === "proximas" ? "" : "secundario"} onClick={() => setAba("proximas")}>
          Próximas ({data?.proximas.length ?? 0})
        </button>
        <button role="tab" aria-selected={aba === "passadas"} className={aba === "passadas" ? "" : "secundario"} onClick={() => setAba("passadas")}>
          Passadas ({data?.passadas.length ?? 0})
        </button>
      </div>
      {isLoading && <p className="suave">Carregando…</p>}
      {error && <p className="erro">{(error as Error).message}</p>}
      {cancelar.error && (
        <p role="alert" className="erro">
          {(cancelar.error as Error).message}
        </p>
      )}
      {data && lista.length === 0 && (
        <p className="suave">
          {aba === "proximas" ? (
            <>
              Nenhuma consulta marcada. <Link to="/busca">Buscar profissionais</Link>
            </>
          ) : (
            "Nenhuma consulta anterior."
          )}
        </p>
      )}
      {lista.map((c) => (
        <CartaoConsulta
          key={c.id}
          consulta={c}
          acoes={
            (c.pode_cancelar || c.pode_remarcar) && (
              <div className="acoes">
                {c.pode_remarcar && (
                  <Link className="botao" to={`/minhas-consultas/${c.id}/remarcar`}>
                    Remarcar
                  </Link>
                )}
                {c.pode_cancelar && (
                  <button
                    className="secundario"
                    disabled={cancelar.isPending}
                    onClick={() => {
                      if (window.confirm("Cancelar esta consulta?")) cancelar.mutate(c.id);
                    }}
                  >
                    Cancelar
                  </button>
                )}
              </div>
            )
          }
        />
      ))}
    </section>
  );
}
