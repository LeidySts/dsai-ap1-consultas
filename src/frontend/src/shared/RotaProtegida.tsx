import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth, type Perfil } from "./auth";

export default function RotaProtegida({ perfis }: { perfis?: Perfil[] }) {
  const { usuario, carregando } = useAuth();
  const local = useLocation();
  if (carregando) return <p className="suave">Carregando…</p>;
  if (!usuario) return <Navigate to="/login" replace state={{ de: local.pathname + local.search }} />;
  if (perfis && !perfis.includes(usuario.perfil)) return <p className="erro">Seu perfil não tem acesso a esta página.</p>;
  return <Outlet />;
}
