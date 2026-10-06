import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import ConfirmarAgendamento from "@/features/agendamento/ConfirmarAgendamento";
import MinhasConsultas from "@/features/agendamento/MinhasConsultas";
import { mockFetch, renderizar } from "./apoio";

const prof = {
  id: 10, nome: "Dr. João Souza", registro: "CRM 1/PA", foto_url: null, biografia: "",
  especialidades: [{ id: 1, nome: "Cardiologia", tipos: [{ id: 3, nome: "Consulta", duracao_min: 30, preco_centavos: 25000 }] }],
  unidades: [{ id: 5, nome: "Unidade Centro", endereco: "Rua A, 1", telefone: "91" }],
  nota_media: null, total_avaliacoes: 0,
};

const consulta = (extra = {}) => ({
  id: 1, inicio: "2026-10-12T12:00:00Z", fim: "2026-10-12T12:30:00Z", status: "marcada", forma_pagamento: "particular",
  preco_centavos: 25000, remarcacoes: 0, paciente: { id: 2, nome: "Maria" }, profissional: { id: 10, nome: "Dr. João Souza" },
  unidade: { id: 5, nome: "Unidade Centro", endereco: "Rua A, 1" }, tipo_consulta: { id: 3, nome: "Consulta", duracao_min: 30 },
  pode_cancelar: true, pode_remarcar: true, ...extra,
});

const ROTA_CONFIRMAR = "/agendar/confirmar?profissional=10&tipo=3&unidade=5&inicio=2026-10-12T12%3A00%3A00Z";

test("confirmação mostra o resumo e marca a consulta", async () => {
  const fetch = mockFetch(
    (url) => (url.endsWith("/publico/profissionais/10") ? { corpo: prof } : undefined),
    (url, init) => (url.endsWith("/consultas") && init?.method === "POST" ? { status: 201, corpo: consulta() } : undefined),
  );
  renderizar(<ConfirmarAgendamento />, { rota: ROTA_CONFIRMAR });
  expect(await screen.findByText("Dr. João Souza")).toBeInTheDocument();
  expect(screen.getByText("12/10/2026, 09:00")).toBeInTheDocument();
  expect(screen.getByText("R$ 250,00", { normalize: (t) => t.replace(/\s/g, " ") })).toBeInTheDocument();
  await userEvent.click(screen.getByRole("button", { name: "Confirmar" }));
  expect(await screen.findByRole("heading", { name: "Consulta marcada!" })).toBeInTheDocument();
  const post = fetch.mock.calls.find(([, init]) => init?.method === "POST");
  expect(JSON.parse(String(post?.[1]?.body))).toMatchObject({ profissional_id: 10, tipo_consulta_id: 3, unidade_id: 5 });
});

test("conflito de horário mostra a mensagem e oferece outro horário", async () => {
  mockFetch(
    (url) => (url.endsWith("/publico/profissionais/10") ? { corpo: prof } : undefined),
    (url, init) =>
      url.endsWith("/consultas") && init?.method === "POST"
        ? { status: 409, corpo: { detail: "Horário não está mais disponível." } }
        : undefined,
  );
  renderizar(<ConfirmarAgendamento />, { rota: ROTA_CONFIRMAR });
  await userEvent.click(await screen.findByRole("button", { name: "Confirmar" }));
  expect(await screen.findByRole("alert")).toHaveTextContent("Horário não está mais disponível.");
  expect(screen.getByRole("link", { name: "Escolher outro horário" })).toHaveAttribute("href", "/profissionais/10");
});

test("minhas consultas separa próximas e passadas e mostra ações permitidas", async () => {
  mockFetch((url) =>
    url.endsWith("/consultas/minhas")
      ? {
          corpo: {
            proximas: [consulta(), consulta({ id: 2, pode_cancelar: false, pode_remarcar: false })],
            passadas: [consulta({ id: 3, status: "realizada", pode_cancelar: false, pode_remarcar: false })],
          },
        }
      : undefined,
  );
  renderizar(<MinhasConsultas />);
  expect(await screen.findByRole("tab", { name: "Próximas (2)" })).toBeInTheDocument();
  expect(screen.getAllByRole("button", { name: "Cancelar" })).toHaveLength(1);
  expect(screen.getAllByRole("link", { name: "Remarcar" })).toHaveLength(1);
  await userEvent.click(screen.getByRole("tab", { name: "Passadas (1)" }));
  expect(screen.getByText("Realizada")).toBeInTheDocument();
  expect(screen.queryByRole("button", { name: "Cancelar" })).not.toBeInTheDocument();
});
