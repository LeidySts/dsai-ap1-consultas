import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Route, useLocation } from "react-router-dom";
import { agruparPorDia } from "@/features/agenda/SeletorHorarios";
import Home from "@/features/busca/Home";
import ResultadosBusca from "@/features/busca/ResultadosBusca";
import PaginaProfissional from "@/features/clinicas/PaginaProfissional";
import { mockFetch, renderizar } from "./apoio";

const filtros = {
  especialidades: [
    { id: 1, nome: "Cardiologia" },
    { id: 2, nome: "Pediatria" },
  ],
  unidades: [{ id: 5, nome: "Unidade Centro" }],
};

const pagina = {
  itens: [
    {
      id: 10, nome: "Dr. João Souza", foto_url: null, especialidades: ["Cardiologia"], unidades: ["Unidade Centro"],
      nota_media: null, preco_centavos: 25000, tipo_consulta_id: 3,
      proximo_horario: { inicio: "2026-10-07T11:00:00Z", unidade_id: 5, unidade_nome: "Unidade Centro" }, aviso: null,
    },
    {
      id: 11, nome: "Dr. Sem Agenda", foto_url: null, especialidades: ["Cardiologia"], unidades: ["Unidade Centro"],
      nota_media: null, preco_centavos: 25000, tipo_consulta_id: 3, proximo_horario: null,
      aviso: "sem horários nos próximos 30 dias",
    },
  ],
  total: 2, pagina: 1, paginas: 1,
};

function MostraUrl() {
  const local = useLocation();
  return <p data-testid="url">{local.pathname + local.search}</p>;
}

const rotasApi = [
  (url: string) => (url.endsWith("/publico/filtros") ? { corpo: filtros } : undefined),
  (url: string) => (url.includes("/publico/profissionais?") ? { corpo: pagina } : undefined),
];

test("formulário da home leva os filtros para a URL", async () => {
  mockFetch(...rotasApi);
  renderizar(<Home />, { caminho: "/", extras: [<Route key="b" path="/busca" element={<MostraUrl />} />] });
  await screen.findByRole("option", { name: "Pediatria" });
  await userEvent.selectOptions(screen.getByLabelText("Especialidade"), "2");
  await userEvent.selectOptions(screen.getByLabelText("Turno"), "tarde");
  await userEvent.click(screen.getByRole("button", { name: "Buscar" }));
  expect(screen.getByTestId("url")).toHaveTextContent("/busca?especialidade_id=2&turno=tarde");
});

test("resultados leem os filtros da URL e mostram próximo horário e aviso", async () => {
  const fetch = mockFetch(...rotasApi);
  renderizar(<ResultadosBusca />, { rota: "/busca?nome=joao&ordem=preco&pagina=1" });
  expect(await screen.findByText("Dr. João Souza")).toBeInTheDocument();
  const chamada = fetch.mock.calls.map((c) => String(c[0])).find((u) => u.includes("/publico/profissionais?"));
  expect(chamada).toContain("nome=joao");
  expect(chamada).toContain("ordem=preco");
  expect(screen.getByText(/Próximo horário: 07\/10\/2026, 08:00/)).toBeInTheDocument();
  expect(screen.getByText("sem horários nos próximos 30 dias")).toBeInTheDocument();
  expect(screen.getByLabelText("Nome ou especialidade")).toHaveValue("joao");
});

test("trocar a ordenação atualiza a URL", async () => {
  mockFetch(...rotasApi);
  renderizar(
    <>
      <ResultadosBusca />
      <MostraUrl />
    </>,
    { rota: "/busca?nome=joao" },
  );
  await screen.findByText("Dr. João Souza");
  await userEvent.selectOptions(screen.getByLabelText("Ordenar por"), "preco");
  expect(screen.getByTestId("url")).toHaveTextContent("ordem=preco");
});

test("horários são agrupados por dia no fuso de São Paulo", () => {
  const grupos = agruparPorDia([
    { inicio: "2026-10-07T11:00:00Z", fim: "2026-10-07T11:30:00Z", unidade_id: 1 },
    { inicio: "2026-10-08T02:30:00Z", fim: "2026-10-08T03:00:00Z", unidade_id: 1 }, // 23:30 do dia 07 em SP
    { inicio: "2026-10-08T11:00:00Z", fim: "2026-10-08T11:30:00Z", unidade_id: 1 },
  ]);
  expect(grupos.map(([dia, hs]) => [dia, hs.length])).toEqual([
    ["2026-10-07", 2],
    ["2026-10-08", 1],
  ]);
});

test("página do profissional mostra dados e permite escolher horário", async () => {
  mockFetch(
    (url) =>
      url.endsWith("/publico/profissionais/10")
        ? {
            corpo: {
              id: 10, nome: "Dr. João Souza", registro: "CRM 123/PA", foto_url: null, biografia: "Cardiologista.",
              especialidades: [{ id: 1, nome: "Cardiologia", tipos: [{ id: 3, nome: "Consulta", duracao_min: 30, preco_centavos: 25000 }] }],
              unidades: [{ id: 5, nome: "Unidade Centro", endereco: "Rua A", telefone: "91" }],
              nota_media: null, total_avaliacoes: 0,
            },
          }
        : undefined,
    (url) =>
      url.includes("/horarios-livres")
        ? { corpo: [{ inicio: "2026-10-07T11:00:00Z", fim: "2026-10-07T11:30:00Z", unidade_id: 5 }] }
        : undefined,
  );
  renderizar(<PaginaProfissional />, {
    rota: "/profissionais/10",
    caminho: "/profissionais/:id",
    extras: [<Route key="c" path="/agendar/confirmar" element={<MostraUrl />} />],
  });
  expect(await screen.findByRole("heading", { name: "Dr. João Souza" })).toBeInTheDocument();
  const dia = await screen.findByRole("region", { name: /07\/10/ });
  await userEvent.click(within(dia).getByRole("button", { name: /08:00/ }));
  await userEvent.click(screen.getByRole("button", { name: "Continuar" }));
  expect(screen.getByTestId("url")).toHaveTextContent("/agendar/confirmar?profissional=10&tipo=3&unidade=5");
});
