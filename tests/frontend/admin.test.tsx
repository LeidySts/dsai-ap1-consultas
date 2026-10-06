import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import AdminEspecialidades, { reaisParaCentavos } from "@/features/clinicas/AdminEspecialidades";
import AdminProfissionais from "@/features/clinicas/AdminProfissionais";
import AdminUnidades from "@/features/clinicas/AdminUnidades";
import { mockFetch, renderizar } from "./apoio";

const unidade = {
  id: 1, nome: "Unidade Centro", endereco: "Rua A", cep: "66000000", telefone: "91", abertura: "07:00:00",
  fechamento: "19:00:00", dias_funcionamento: [0, 1, 2, 3, 4], ativa: true,
};

test("preço digitado em reais vira centavos inteiros", () => {
  expect(reaisParaCentavos("250,00")).toBe(25000);
  expect(reaisParaCentavos("1.250,50")).toBe(125050);
  expect(reaisParaCentavos("99,99")).toBe(9999);
});

test("lista do admin manda filtro, ordem e página para a API", async () => {
  const fetch = mockFetch((url) =>
    url.includes("/unidades?") ? { corpo: { itens: [unidade], total: 25, pagina: 1, paginas: 2 } } : undefined,
  );
  renderizar(<AdminUnidades />);
  expect(await screen.findByText("Unidade Centro")).toBeInTheDocument();
  expect(screen.getByText(/Página 1 de 2 · 25 registro/)).toBeInTheDocument();
  await userEvent.type(screen.getByLabelText("Filtrar"), "cen");
  await userEvent.selectOptions(screen.getByLabelText("Ordenar"), "-nome");
  await userEvent.click(screen.getByRole("button", { name: "Próxima" }));
  const urls = fetch.mock.calls.map((c) => String(c[0]));
  expect(urls.some((u) => u.includes("pagina=2") && u.includes("ordem=-nome") && u.includes("q=cen"))).toBe(true);
});

test("desativar com consultas futuras mostra o 409 com a lista", async () => {
  mockFetch(
    (url, init) =>
      url.endsWith("/unidades/1/desativar") && init?.method === "POST"
        ? {
            status: 409,
            corpo: {
              detail: "A unidade tem consultas futuras. Remarque ou cancele antes de desativar.",
              consultas: [{ id: 3, inicio: "2026-10-12T12:00:00Z", paciente: "Carlos", profissional: "Dr. João" }],
            },
          }
        : undefined,
    (url) => (url.includes("/unidades?") ? { corpo: { itens: [unidade], total: 1, pagina: 1, paginas: 1 } } : undefined),
  );
  renderizar(<AdminUnidades />);
  await userEvent.click(await screen.findByRole("button", { name: "Desativar" }));
  const alerta = await screen.findByRole("alert");
  expect(alerta).toHaveTextContent("consultas futuras");
  expect(alerta).toHaveTextContent("Carlos com Dr. João");
});

test("especialidade duplicada mostra o erro do servidor", async () => {
  mockFetch(
    (url, init) =>
      url.endsWith("/especialidades") && init?.method === "POST"
        ? { status: 409, corpo: { detail: "Já existe uma especialidade com este nome." } }
        : undefined,
    (url) => (url.includes("/especialidades?") ? { corpo: { itens: [], total: 0, pagina: 1, paginas: 1 } } : undefined),
  );
  renderizar(<AdminEspecialidades />);
  await userEvent.type(screen.getByLabelText("Nome"), "Cardiologia");
  await userEvent.click(screen.getByRole("button", { name: "Cadastrar" }));
  expect(await screen.findByRole("alert")).toHaveTextContent("Já existe uma especialidade com este nome.");
});

test("novo profissional envia especialidades e unidades marcadas", async () => {
  const fetch = mockFetch(
    (url, init) => (url.endsWith("/profissionais") && init?.method === "POST" ? { status: 201, corpo: {} } : undefined),
    (url) => (url.includes("/profissionais?") ? { corpo: { itens: [], total: 0, pagina: 1, paginas: 1 } } : undefined),
    (url) =>
      url.endsWith("/publico/filtros")
        ? { corpo: { especialidades: [{ id: 7, nome: "Pediatria" }], unidades: [{ id: 1, nome: "Unidade Centro" }] } }
        : undefined,
  );
  renderizar(<AdminProfissionais />);
  await userEvent.type(screen.getByLabelText("Nome"), "Dra. Ana Lima");
  await userEvent.type(screen.getByLabelText("Número"), "12345");
  await userEvent.click(await screen.findByLabelText("Pediatria"));
  await userEvent.click(screen.getByLabelText("Unidade Centro"));
  await userEvent.click(screen.getByRole("button", { name: "Cadastrar profissional" }));
  const post = fetch.mock.calls.find(([, init]) => init?.method === "POST");
  expect(JSON.parse(String(post?.[1]?.body))).toMatchObject({
    nome: "Dra. Ana Lima", conselho: "CRM", registro_numero: "12345", especialidade_ids: [7], unidade_ids: [1],
  });
});
