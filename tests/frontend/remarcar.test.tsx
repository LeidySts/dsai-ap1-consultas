import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Route } from "react-router-dom";
import { vi } from "vitest";
import MinhasConsultas from "@/features/agendamento/MinhasConsultas";
import Remarcar from "@/features/agendamento/Remarcar";
import { mockFetch, renderizar } from "./apoio";

const consulta = (extra = {}) => ({
  id: 7, inicio: "2026-10-12T12:00:00Z", fim: "2026-10-12T12:30:00Z", status: "marcada", forma_pagamento: "particular",
  preco_centavos: 25000, remarcacoes: 0, paciente: { id: 2, nome: "Maria" }, profissional: { id: 10, nome: "Dr. João" },
  unidade: { id: 5, nome: "Unidade Centro", endereco: "Rua A" }, tipo_consulta: { id: 3, nome: "Consulta", duracao_min: 30 },
  pode_cancelar: true, pode_remarcar: true, ...extra,
});

test("remarcar envia o novo horário e volta para minhas consultas", async () => {
  const fetch = mockFetch(
    (url, init) => (url.endsWith("/consultas/7/remarcar") && init?.method === "POST" ? { status: 201, corpo: consulta({ id: 8 }) } : undefined),
    (url) => (url.endsWith("/consultas/7") ? { corpo: consulta() } : undefined),
    (url) => (url.endsWith("/publico/profissionais/10") ? { corpo: { unidades: [{ id: 5, nome: "Unidade Centro" }] } } : undefined),
    (url) => (url.includes("/horarios-livres") ? { corpo: [{ inicio: "2026-10-13T12:00:00Z", fim: "2026-10-13T12:30:00Z", unidade_id: 5 }] } : undefined),
  );
  renderizar(<Remarcar />, {
    rota: "/minhas-consultas/7/remarcar",
    caminho: "/minhas-consultas/:id/remarcar",
    extras: [<Route key="m" path="/minhas-consultas" element={<p>Lista</p>} />],
  });
  await userEvent.click(await screen.findByRole("button", { name: /09:00/ }));
  await userEvent.click(screen.getByRole("button", { name: /Remarcar para 13\/10\/2026/ }));
  expect(await screen.findByText("Lista")).toBeInTheDocument();
  const post = fetch.mock.calls.find(([, init]) => init?.method === "POST");
  expect(JSON.parse(String(post?.[1]?.body))).toEqual({ inicio: "2026-10-13T12:00:00Z", unidade_id: 5 });
});

test("consulta que não pode ser remarcada mostra aviso", async () => {
  mockFetch((url) => (url.endsWith("/consultas/7") ? { corpo: consulta({ pode_remarcar: false }) } : undefined));
  renderizar(<Remarcar />, { rota: "/minhas-consultas/7/remarcar", caminho: "/minhas-consultas/:id/remarcar" });
  expect(await screen.findByText(/não pode mais ser remarcada/)).toBeInTheDocument();
});

test("cancelar em minhas consultas pede confirmação e chama a API", async () => {
  vi.spyOn(window, "confirm").mockReturnValue(true);
  const fetch = mockFetch(
    (url, init) => (url.endsWith("/consultas/7/cancelar") && init?.method === "POST" ? { corpo: consulta({ status: "cancelada_paciente" }) } : undefined),
    (url) => (url.endsWith("/consultas/minhas") ? { corpo: { proximas: [consulta()], passadas: [] } } : undefined),
  );
  renderizar(<MinhasConsultas />);
  await userEvent.click(await screen.findByRole("button", { name: "Cancelar" }));
  expect(window.confirm).toHaveBeenCalled();
  expect(fetch.mock.calls.some(([u, init]) => String(u).endsWith("/consultas/7/cancelar") && init?.method === "POST")).toBe(true);
});
