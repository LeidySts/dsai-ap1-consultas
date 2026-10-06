import { Link, Outlet } from "react-router-dom";

export default function Layout() {
  return (
    <>
      <header className="topo">
        <Link to="/" className="marca">
          MarcaConsulta
        </Link>
      </header>
      <main className="conteudo">
        <Outlet />
      </main>
    </>
  );
}
