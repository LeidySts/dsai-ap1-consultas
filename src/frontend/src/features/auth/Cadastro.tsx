import { useState, type FormEvent } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { api } from "@/shared/api";
import { useAuth } from "@/shared/auth";
import { cpfValido, senhaValida } from "./validacao";

const VAZIO = { nome: "", email: "", cpf: "", data_nascimento: "", telefone: "", senha: "" };
type Campos = typeof VAZIO;

const ROTULOS: Record<keyof Campos, string> = {
  nome: "Nome completo",
  email: "E-mail",
  cpf: "CPF",
  data_nascimento: "Data de nascimento",
  telefone: "Telefone",
  senha: "Senha",
};

function validar(c: Campos): string | null {
  const faltando = (Object.keys(c) as (keyof Campos)[]).find((k) => !c[k].trim());
  if (faltando) return `Preencha o campo ${ROTULOS[faltando]}.`;
  if (!cpfValido(c.cpf)) return "CPF inválido.";
  if (!senhaValida(c.senha)) return "A senha precisa ter no mínimo 8 caracteres, com letras e números.";
  return null;
}

export default function Cadastro() {
  const { entrar } = useAuth();
  const navegar = useNavigate();
  const local = useLocation();
  const destino = (local.state as { de?: string } | null)?.de ?? "/";
  const [campos, setCampos] = useState<Campos>(VAZIO);
  const [erro, setErro] = useState("");
  const [enviando, setEnviando] = useState(false);

  async function enviar(e: FormEvent) {
    e.preventDefault();
    const problema = validar(campos);
    setErro(problema ?? "");
    if (problema) return;
    setEnviando(true);
    try {
      await api("/auth/cadastro", { method: "POST", body: JSON.stringify(campos) });
      await entrar(campos.email, campos.senha);
      navegar(destino, { replace: true });
    } catch (err) {
      setErro((err as Error).message);
    } finally {
      setEnviando(false);
    }
  }

  const campo = (nome: keyof Campos, tipo = "text", autoComplete?: string) => (
    <label>
      {ROTULOS[nome]}
      <input
        type={tipo}
        value={campos[nome]}
        autoComplete={autoComplete}
        onChange={(e) => setCampos({ ...campos, [nome]: e.target.value })}
      />
    </label>
  );

  return (
    <section className="cartao">
      <h1>Criar conta de paciente</h1>
      <form className="formulario" onSubmit={enviar} noValidate>
        {campo("nome", "text", "name")}
        {campo("email", "email", "email")}
        {campo("cpf", "text")}
        {campo("data_nascimento", "date", "bday")}
        {campo("telefone", "tel", "tel")}
        {campo("senha", "password", "new-password")}
        <small className="suave">Mínimo de 8 caracteres, com letras e números.</small>
        {erro && (
          <p role="alert" className="erro">
            {erro}
          </p>
        )}
        <button type="submit" disabled={enviando}>
          {enviando ? "Criando conta…" : "Criar conta"}
        </button>
      </form>
    </section>
  );
}
