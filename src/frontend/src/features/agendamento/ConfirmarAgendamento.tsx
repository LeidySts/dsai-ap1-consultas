import { useMutation, useQuery } from "@tanstack/react-query";
import { Link, useSearchParams } from "react-router-dom";
import type { ProfissionalPublico } from "@/features/clinicas/PaginaProfissional";
import { api, ErroApi } from "@/shared/api";
import { formatarDataHora, formatarPreco } from "@/shared/datas";
import type { Consulta } from "./tipos";

export default function ConfirmarAgendamento() {
  const [params] = useSearchParams();
  const profissionalId = Number(params.get("profissional"));
  const tipoId = Number(params.get("tipo"));
  const unidadeId = Number(params.get("unidade"));
  const inicio = params.get("inicio") ?? "";

  const { data: prof } = useQuery({
    queryKey: ["profissional", String(profissionalId)],
    queryFn: () => api<ProfissionalPublico>(`/publico/profissionais/${profissionalId}`),
    enabled: Boolean(profissionalId),
  });
  const marcar = useMutation({
    mutationFn: () =>
      api<Consulta>("/consultas", {
        method: "POST",
        body: JSON.stringify({
          profissional_id: profissionalId,
          tipo_consulta_id: tipoId,
          unidade_id: unidadeId,
          inicio,
          forma_pagamento: "particular",
        }),
      }),
  });

  if (!profissionalId || !tipoId || !unidadeId || !inicio) {
    return <p className="erro">Escolha um horário na página do profissional.</p>;
  }
  const tipo = prof?.especialidades.flatMap((e) => e.tipos).find((t) => t.id === tipoId);
  const unidade = prof?.unidades.find((u) => u.id === unidadeId);

  if (marcar.isSuccess) {
    return (
      <section className="cartao">
        <h1 className="sucesso">Consulta marcada!</h1>
        <p>
          {marcar.data.profissional.nome} — {formatarDataHora(marcar.data.inicio)} na {marcar.data.unidade.nome}.
        </p>
        <Link className="botao" to="/minhas-consultas">
          Ver minhas consultas
        </Link>
      </section>
    );
  }

  const erro = marcar.error as ErroApi | null;
  return (
    <section className="cartao">
      <h1>Confirmar consulta</h1>
      <dl>
        <dt>Profissional</dt>
        <dd>{prof?.nome ?? "…"}</dd>
        <dt>Tipo</dt>
        <dd>{tipo ? `${tipo.nome} (${tipo.duracao_min} min)` : "…"}</dd>
        <dt>Data e hora</dt>
        <dd>{formatarDataHora(inicio)}</dd>
        <dt>Unidade</dt>
        <dd>{unidade ? `${unidade.nome} — ${unidade.endereco}` : "…"}</dd>
        <dt>Valor (particular)</dt>
        <dd>{tipo ? formatarPreco(tipo.preco_centavos) : "…"}</dd>
      </dl>
      {erro && (
        <p role="alert" className="erro">
          {erro.message}{" "}
          {erro.status === 409 && <Link to={`/profissionais/${profissionalId}`}>Escolher outro horário</Link>}
        </p>
      )}
      <div className="acoes">
        <button onClick={() => marcar.mutate()} disabled={marcar.isPending}>
          {marcar.isPending ? "Marcando…" : "Confirmar"}
        </button>
        <Link to={`/profissionais/${profissionalId}`}>Voltar</Link>
      </div>
    </section>
  );
}
