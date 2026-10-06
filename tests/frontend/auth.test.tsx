import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Route } from "react-router-dom";
import Cadastro from "@/features/auth/Cadastro";
import Login from "@/features/auth/Login";
import { cpfValido, senhaValida } from "@/features/auth/validacao";
import { mockFetch, renderizar } from "./apoio";

const tokens = { access_token: "a", refresh_token: "r" };
const eu = { id: 1, nome: "Maria Silva", email: "maria@teste.com", perfil: "paciente" };

test("valida CPF e senha como o backend", () => {
  expect(cpfValido("529.982.247-25")).toBe(true);
  expect(cpfValido("529.982.247-26")).toBe(false);
  expect(senhaValida("segura123")).toBe(true);
  expect(senhaValida("semnumero")).toBe(false);
});

test("login sem preencher mostra erro em português", async () => {
  renderizar(<Login />, { rota: "/login" });
  await userEvent.click(screen.getByRole("button", { name: "Entrar" }));
  expect(screen.getByRole("alert")).toHaveTextContent("Informe e-mail e senha.");
});

test("login com senha errada mostra a mensagem do servidor", async () => {
  mockFetch((url) => (url.endsWith("/auth/login") ? { status: 401, corpo: { detail: "E-mail ou senha incorretos." } } : undefined));
  renderizar(<Login />, { rota: "/login" });
  await userEvent.type(screen.getByLabelText("E-mail"), "maria@teste.com");
  await userEvent.type(screen.getByLabelText("Senha"), "errada123");
  await userEvent.click(screen.getByRole("button", { name: "Entrar" }));
  expect(await screen.findByRole("alert")).toHaveTextContent("E-mail ou senha incorretos.");
});

test("login volta para a página de origem", async () => {
  mockFetch(
    (url) => (url.endsWith("/auth/login") ? { corpo: tokens } : undefined),
    (url) => (url.endsWith("/auth/eu") ? { corpo: eu } : undefined),
  );
  renderizar(<Login />, {
    rota: { pathname: "/login", state: { de: "/minhas-consultas" } },
    caminho: "/login",
    extras: [<Route key="d" path="/minhas-consultas" element={<p>Página de origem</p>} />],
  });
  await userEvent.type(screen.getByLabelText("E-mail"), "maria@teste.com");
  await userEvent.type(screen.getByLabelText("Senha"), "segura123");
  await userEvent.click(screen.getByRole("button", { name: "Entrar" }));
  expect(await screen.findByText("Página de origem")).toBeInTheDocument();
});

test("cadastro valida CPF no cliente antes de enviar", async () => {
  const fetch = mockFetch();
  renderizar(<Cadastro />, { rota: "/cadastro" });
  await userEvent.type(screen.getByLabelText("Nome completo"), "Maria Silva");
  await userEvent.type(screen.getByLabelText("E-mail"), "maria@teste.com");
  await userEvent.type(screen.getByLabelText("CPF"), "123.456.789-00");
  await userEvent.type(screen.getByLabelText("Data de nascimento"), "1990-05-10");
  await userEvent.type(screen.getByLabelText("Telefone"), "91988887777");
  await userEvent.type(screen.getByLabelText("Senha"), "segura123");
  await userEvent.click(screen.getByRole("button", { name: "Criar conta" }));
  expect(screen.getByRole("alert")).toHaveTextContent("CPF inválido.");
  expect(fetch).not.toHaveBeenCalled();
});

test("cadastro mostra conflito de e-mail vindo do servidor", async () => {
  mockFetch((url) =>
    url.endsWith("/auth/cadastro") ? { status: 409, corpo: { detail: "Este e-mail já está cadastrado." } } : undefined,
  );
  renderizar(<Cadastro />, { rota: "/cadastro" });
  await userEvent.type(screen.getByLabelText("Nome completo"), "Maria Silva");
  await userEvent.type(screen.getByLabelText("E-mail"), "maria@teste.com");
  await userEvent.type(screen.getByLabelText("CPF"), "529.982.247-25");
  await userEvent.type(screen.getByLabelText("Data de nascimento"), "1990-05-10");
  await userEvent.type(screen.getByLabelText("Telefone"), "91988887777");
  await userEvent.type(screen.getByLabelText("Senha"), "segura123");
  await userEvent.click(screen.getByRole("button", { name: "Criar conta" }));
  expect(await screen.findByRole("alert")).toHaveTextContent("Este e-mail já está cadastrado.");
});
