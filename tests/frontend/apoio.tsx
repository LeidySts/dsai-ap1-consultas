import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render } from "@testing-library/react";
import type { ReactElement } from "react";
import { MemoryRouter, Route, Routes, type InitialEntry } from "react-router-dom";
import { vi } from "vitest";
import { AuthProvider } from "@/shared/auth";

type Resposta = { status?: number; corpo?: unknown };
type Rota = (url: string, init?: RequestInit) => Resposta | undefined;

/** Substitui fetch: cada chamada passa pelas rotas até alguma responder. */
export function mockFetch(...rotas: Rota[]) {
  const fn = vi.fn(async (entrada: RequestInfo | URL, init?: RequestInit) => {
    const url = String(entrada);
    for (const rota of rotas) {
      const r = rota(url, init);
      if (r) {
        return new Response(r.status === 204 ? null : JSON.stringify(r.corpo ?? {}), {
          status: r.status ?? 200,
          headers: { "Content-Type": "application/json" },
        });
      }
    }
    return new Response(JSON.stringify({ detail: `sem mock para ${url}` }), { status: 500 });
  });
  vi.stubGlobal("fetch", fn);
  return fn;
}

export function renderizar(elemento: ReactElement, { rota = "/" as InitialEntry, caminho = "*", extras = [] as ReactElement[] } = {}) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[rota]}>
        <AuthProvider>
          <Routes>
            <Route path={caminho} element={elemento} />
            {extras}
          </Routes>
        </AuthProvider>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}
