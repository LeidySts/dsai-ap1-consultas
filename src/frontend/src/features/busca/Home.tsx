import { useNavigate } from "react-router-dom";
import FormularioBusca from "./FormularioBusca";

export default function Home() {
  const navegar = useNavigate();
  return (
    <section>
      <h1>Marque sua consulta sem telefonema</h1>
      <p>Encontre profissionais por especialidade, veja horários livres e marque em poucos cliques.</p>
      <FormularioBusca inicial={new URLSearchParams()} aoBuscar={(params) => navegar(`/busca?${params}`)} />
    </section>
  );
}
