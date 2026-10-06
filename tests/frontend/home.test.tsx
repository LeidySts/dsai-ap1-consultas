import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import Home from "@/features/busca/Home";

test("home renderiza sem login", () => {
  render(
    <MemoryRouter>
      <Home />
    </MemoryRouter>,
  );
  expect(screen.getByRole("heading", { name: /marque sua consulta/i })).toBeInTheDocument();
});
