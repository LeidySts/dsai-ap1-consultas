import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import AgendaProfissional from "@/features/agenda/AgendaProfissional";
import Disponibilidade from "@/features/agenda/Disponibilidade";
import { inicioDaSemana, localParaIso, somarDias } from "@/shared/datas";
import { mockFetch, renderizar } from "./apoio";

const eu = { id: 1, nome: "Dr. Marcos", unidades: [{ id: 5, nome: "Unidade Centro" }] };

test("utilitários de data", () => {
  expect(somarDias("2026-10-31", 1)).toBe("2026-11-01");
  expect(inicioDaSemana("2026-10-08")).toBe("2026-10-05"); // quinta -> segunda
  expect(inicioDaSemana("2026-10-11")).toBe("2026-10-05"); // domingo -> segunda anterior
  expect(localParaIso("2026-10-12T09:00")).toBe("2026-10-12T09:00:00-03:00");
});

test("agenda semanal busca a semana inteira e colore por status", async () => {
  const fetch = mockFetch(
    (url) => (url.endsWith("/eu/profissional") ? { corpo: eu } : undefined),
    (url) =>
      url.includes("/profissionais/1/agenda")
        ? {
            corpo: [
              {
                id: 9, inicio: "2026-10-07T12:00:00Z", fim: "2026-10-07T12:30:00Z", status: "confirmada",
                paciente: { id: 2, nome: "Carlos" }, profissional: { id: 1, nome: "Dr. Marcos" },
                unidade: { id: 5, nome: "Unidade Centro", endereco: "" }, tipo_consulta: { id: 3, nome: "Consulta", duracao_min: 30 },
              },
            ],
          }
        : undefined,
  );
  renderizar(<AgendaProfissional />);
  await userEvent.click(await screen.findByRole("tab", { name: "Semana" }));
  const data = screen.getByLabelText("Data");
  await userEvent.clear(data);
  await userEvent.type(data, "2026-10-08");
  const quarta = await screen.findByRole("region", { name: "2026-10-07" });
  expect(await within(quarta).findByText("Carlos")).toBeInTheDocument();
  expect(within(quarta).getByText("Confirmada")).toHaveClass("status-confirmada");
  const urls = fetch.mock.calls.map((c) => String(c[0]));
  expect(urls.some((u) => u.includes("de=2026-10-05&ate=2026-10-11"))).toBe(true);
});

test("bloqueio que colide mostra a lista de consultas afetadas", async () => {
  mockFetch(
    (url) => (url.endsWith("/eu/profissional") ? { corpo: eu } : undefined),
    (url) => (url.endsWith("/grade") ? { corpo: [{ id: 1, unidade_id: 5, dia_semana: 0, hora_inicio: "08:00:00", hora_fim: "12:00:00" }] } : undefined),
    (url, init) =>
      url.endsWith("/bloqueios") && init?.method === "POST"
        ? {
            status: 409,
            corpo: {
              detail: "O bloqueio colide com consultas marcadas. Remarque ou cancele antes.",
              consultas: [{ id: 4, inicio: "2026-10-12T12:00:00Z", paciente: "Carlos Pereira" }],
            },
          }
        : undefined,
    (url) => (url.endsWith("/bloqueios") ? { corpo: [] } : undefined),
  );
  renderizar(<Disponibilidade />);
  expect(await screen.findByText("Segunda", { selector: "td" })).toBeInTheDocument();
  expect(screen.getByText("08:00–12:00")).toBeInTheDocument();
  const [inicio, fim] = screen.getAllByLabelText(/Início|Fim/).filter((e) => e.getAttribute("type") === "datetime-local");
  await userEvent.type(inicio, "2026-10-12T08:00");
  await userEvent.type(fim, "2026-10-12T12:00");
  await userEvent.type(screen.getByLabelText("Motivo"), "Congresso");
  await userEvent.click(screen.getByRole("button", { name: "Bloquear período" }));
  const alerta = await screen.findByRole("alert");
  expect(alerta).toHaveTextContent("colide com consultas marcadas");
  expect(alerta).toHaveTextContent("Carlos Pereira");
});
