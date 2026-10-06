import { Route, Routes } from "react-router-dom";
import ConfirmarAgendamento from "@/features/agendamento/ConfirmarAgendamento";
import MinhasConsultas from "@/features/agendamento/MinhasConsultas";
import Remarcar from "@/features/agendamento/Remarcar";
import Cadastro from "@/features/auth/Cadastro";
import Login from "@/features/auth/Login";
import Home from "@/features/busca/Home";
import ResultadosBusca from "@/features/busca/ResultadosBusca";
import PaginaProfissional from "@/features/clinicas/PaginaProfissional";
import { AuthProvider } from "@/shared/auth";
import Layout from "@/shared/Layout";
import RotaProtegida from "@/shared/RotaProtegida";

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Home />} />
          <Route path="/busca" element={<ResultadosBusca />} />
          <Route path="/profissionais/:id" element={<PaginaProfissional />} />
          <Route path="/login" element={<Login />} />
          <Route path="/cadastro" element={<Cadastro />} />
          <Route element={<RotaProtegida perfis={["paciente"]} />}>
            <Route path="/agendar/confirmar" element={<ConfirmarAgendamento />} />
            <Route path="/minhas-consultas" element={<MinhasConsultas />} />
            <Route path="/minhas-consultas/:id/remarcar" element={<Remarcar />} />
          </Route>
          <Route path="*" element={<p>Página não encontrada.</p>} />
        </Route>
      </Routes>
    </AuthProvider>
  );
}
