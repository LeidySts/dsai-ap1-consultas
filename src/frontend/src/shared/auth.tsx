import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import { api, lerTokens, salvarTokens, type Tokens } from "./api";

export type Perfil = "paciente" | "profissional" | "recepcao" | "admin";
export type Usuario = { id: number; nome: string; email: string; perfil: Perfil };

type ContextoAuth = {
  usuario: Usuario | null;
  carregando: boolean;
  entrar: (email: string, senha: string) => Promise<Usuario>;
  sair: () => Promise<void>;
};

const Contexto = createContext<ContextoAuth | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [usuario, setUsuario] = useState<Usuario | null>(null);
  const [carregando, setCarregando] = useState(() => lerTokens() !== null);

  useEffect(() => {
    if (!lerTokens()) return;
    api<Usuario>("/auth/eu")
      .then(setUsuario)
      .catch(() => salvarTokens(null))
      .finally(() => setCarregando(false));
  }, []);

  const entrar = useCallback(async (email: string, senha: string) => {
    const tokens = await api<Tokens>("/auth/login", { method: "POST", body: JSON.stringify({ email, senha }) });
    salvarTokens(tokens);
    const eu = await api<Usuario>("/auth/eu");
    setUsuario(eu);
    return eu;
  }, []);

  const sair = useCallback(async () => {
    const tokens = lerTokens();
    if (tokens) {
      await api("/auth/logout", { method: "POST", body: JSON.stringify({ refresh_token: tokens.refresh_token }) }).catch(
        () => undefined,
      );
    }
    salvarTokens(null);
    setUsuario(null);
  }, []);

  return <Contexto.Provider value={{ usuario, carregando, entrar, sair }}>{children}</Contexto.Provider>;
}

export function useAuth(): ContextoAuth {
  const contexto = useContext(Contexto);
  if (!contexto) throw new Error("useAuth fora do AuthProvider");
  return contexto;
}
