import { Link, Outlet, useNavigate } from "react-router-dom";
import { useAuth, type Perfil } from "./auth";

const MENU: Record<Perfil, { para: string; rotulo: string }[]> = {
  paciente: [{ para: "/minhas-consultas", rotulo: "Minhas consultas" }],
  profissional: [
    { para: "/profissional/agenda", rotulo: "Minha agenda" },
    { para: "/profissional/disponibilidade", rotulo: "Disponibilidade" },
  ],
  recepcao: [{ para: "/recepcao/agendar", rotulo: "Marcar para paciente" }],
  admin: [
    { para: "/admin/unidades", rotulo: "Unidades" },
    { para: "/admin/especialidades", rotulo: "Especialidades" },
    { para: "/admin/profissionais", rotulo: "Profissionais" },
    { para: "/admin/feriados", rotulo: "Feriados" },
  ],
};

export default function Layout() {
  const { usuario, sair } = useAuth();
  const navegar = useNavigate();

  return (
    <>
      <header className="topo">
        <Link to="/" className="marca">
          MarcaConsulta
        </Link>
        <nav aria-label="Principal">
          <Link to="/busca">Buscar profissionais</Link>
          {usuario ? (
            <>
              {MENU[usuario.perfil].map((item) => (
                <Link key={item.para} to={item.para}>
                  {item.rotulo}
                </Link>
              ))}
              <span className="suave">{usuario.nome.split(" ")[0]}</span>
              <button
                className="secundario"
                onClick={async () => {
                  await sair();
                  navegar("/");
                }}
              >
                Sair
              </button>
            </>
          ) : (
            <>
              <Link to="/login">Entrar</Link>
              <Link to="/cadastro" className="botao">
                Criar conta
              </Link>
            </>
          )}
        </nav>
      </header>
      <main className="conteudo">
        <Outlet />
      </main>
    </>
  );
}
