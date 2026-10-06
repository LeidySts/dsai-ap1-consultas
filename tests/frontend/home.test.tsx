import { screen } from "@testing-library/react";
import Home from "@/features/busca/Home";
import { mockFetch, renderizar } from "./apoio";

test("home renderiza sem login, com o formulário de busca", async () => {
  mockFetch((url) =>
    url.endsWith("/publico/filtros")
      ? { corpo: { especialidades: [{ id: 1, nome: "Cardiologia" }], unidades: [{ id: 2, nome: "Unidade Centro" }] } }
      : undefined,
  );
  renderizar(<Home />);
  expect(screen.getByRole("heading", { name: /marque sua consulta/i })).toBeInTheDocument();
  expect(await screen.findByRole("option", { name: "Cardiologia" })).toBeInTheDocument();
});
