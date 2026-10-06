import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import AgendarRecepcao from "@/features/agendamento/AgendarRecepcao";
import { mockFetch, renderizar } from "./apoio";

test("recepção escolhe paciente, profissional e horário e marca em nome dele", async () => {
  const fetch = mockFetch(
    (url) => (url.includes("/pacientes?q=") ? { corpo: [{ id: 42, nome: "Carlos Pereira", email: "c@x.com", cpf: "52998224725" }] } : undefined),
    (url) =>
      url.includes("/publico/profissionais?nome=")
        ? { corpo: { itens: [{ id: 10, nome: "Dr. João Souza", especialidades: ["Cardiologia"] }], total: 1, pagina: 1, paginas: 1 } }
        : undefined,
    (url) =>
      url.endsWith("/publico/profissionais/10")
        ? {
            corpo: {
              id: 10, nome: "Dr. João Souza", unidades: [{ id: 5, nome: "Unidade Centro" }],
              especialidades: [{ id: 1, nome: "Cardiologia", tipos: [{ id: 3, nome: "Consulta", duracao_min: 30, preco_centavos: 1 }] }],
            },
          }
        : undefined,
    (url) => (url.includes("/horarios-livres") ? { corpo: [{ inicio: "2026-10-13T12:00:00Z", fim: "2026-10-13T12:30:00Z", unidade_id: 5 }] } : undefined),
    (url, init) =>
      url.endsWith("/consultas") && init?.method === "POST"
        ? {
            status: 201,
            corpo: {
              id: 1, inicio: "2026-10-13T12:00:00Z", paciente: { nome: "Carlos Pereira" },
              profissional: { nome: "Dr. João Souza" }, unidade: { nome: "Unidade Centro" },
            },
          }
        : undefined,
  );
  renderizar(<AgendarRecepcao />);
  await userEvent.type(screen.getByLabelText("Nome, e-mail ou CPF"), "carlos");
  const opcao = await screen.findByRole("button", { name: /Carlos Pereira/ });
  expect(opcao).toHaveTextContent("***.982.247-**");
  await userEvent.click(opcao);
  await userEvent.type(screen.getByLabelText("Nome do profissional ou especialidade"), "joao");
  await userEvent.click(await screen.findByRole("button", { name: /Dr. João Souza/ }));
  await userEvent.click(await screen.findByRole("button", { name: /09:00/ }));
  await userEvent.click(screen.getByRole("button", { name: "Confirmar marcação" }));
  expect(await screen.findByRole("heading", { name: "Consulta marcada!" })).toBeInTheDocument();
  const post = fetch.mock.calls.find(([, init]) => init?.method === "POST");
  expect(JSON.parse(String(post?.[1]?.body))).toMatchObject({ paciente_id: 42, profissional_id: 10, tipo_consulta_id: 3, unidade_id: 5 });
});
