import { Route, Routes } from "react-router-dom";
import Cadastro from "@/features/auth/Cadastro";
import Login from "@/features/auth/Login";
import Home from "@/features/busca/Home";
import { AuthProvider } from "@/shared/auth";
import Layout from "@/shared/Layout";

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<Login />} />
          <Route path="/cadastro" element={<Cadastro />} />
          <Route path="*" element={<p>Página não encontrada.</p>} />
        </Route>
      </Routes>
    </AuthProvider>
  );
}
