"""Servidor MCP do MarcaConsulta: o agente age como o paciente de demonstração pela API pública.

Configuração (variáveis de ambiente):
- MARCACONSULTA_EMAIL / MARCACONSULTA_SENHA: login do paciente (obrigatórias nas tools com login)
- MARCACONSULTA_API_URL: opcional, padrão https://marcaconsulta.onrender.com/api
"""

import os
import unicodedata
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import httpx
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations

URL_PADRAO = "https://marcaconsulta.onrender.com/api"
FUSO_LOCAL = ZoneInfo("America/Sao_Paulo")
LEITURA = ToolAnnotations(read_only_hint=True, open_world_hint=True)
ESCRITA = ToolAnnotations(read_only_hint=False, destructive_hint=False, open_world_hint=True)
CANCELAMENTO = ToolAnnotations(read_only_hint=False, destructive_hint=True, open_world_hint=True)


class ClienteAPI:
    """Cliente HTTP da API com login sob demanda e um relogin automático após 401."""

    def __init__(self, base_url: str, email: str | None, senha: str | None, transport: httpx.BaseTransport | None = None):
        self.email = email
        self.senha = senha
        self._token: str | None = None
        # a API no Render pode levar ~1 min para acordar
        self._http = httpx.Client(base_url=base_url.rstrip("/"), timeout=90, transport=transport)

    @classmethod
    def do_ambiente(cls) -> "ClienteAPI":
        return cls(
            os.environ.get("MARCACONSULTA_API_URL") or URL_PADRAO,
            os.environ.get("MARCACONSULTA_EMAIL"),
            os.environ.get("MARCACONSULTA_SENHA"),
        )

    def get(self, caminho: str, autenticado: bool = False, **params):
        params = {k: v for k, v in params.items() if v is not None}
        return self._pedir("GET", caminho, autenticado, params=params)

    def post(self, caminho: str, corpo: dict | None = None):
        return self._pedir("POST", caminho, True, json=corpo)

    def _pedir(self, metodo: str, caminho: str, autenticado: bool, **kwargs):
        try:
            resposta = self._http.request(metodo, caminho, headers=self._cabecalhos(autenticado), **kwargs)
            if autenticado and resposta.status_code == 401:
                self._token = None
                resposta = self._http.request(metodo, caminho, headers=self._cabecalhos(True), **kwargs)
        except httpx.HTTPError as exc:
            raise ToolError(f"Não foi possível falar com a API do MarcaConsulta: {exc}") from exc
        _verificar(resposta)
        return resposta.json() if resposta.content else None

    def _cabecalhos(self, autenticado: bool) -> dict:
        if not autenticado:
            return {}
        if self._token is None:
            self._login()
        return {"Authorization": f"Bearer {self._token}"}

    def _login(self) -> None:
        if not self.email or not self.senha:
            raise ToolError(
                "Credenciais ausentes: defina as variáveis de ambiente MARCACONSULTA_EMAIL e "
                "MARCACONSULTA_SENHA com o login do paciente de demonstração."
            )
        try:
            resposta = self._http.post("/auth/login", json={"email": self.email, "senha": self.senha})
        except httpx.HTTPError as exc:
            raise ToolError(f"Não foi possível falar com a API do MarcaConsulta: {exc}") from exc
        _verificar(resposta, prefixo="Falha no login do paciente")
        self._token = resposta.json()["access_token"]


def _verificar(resposta: httpx.Response, prefixo: str = "A API recusou o pedido") -> None:
    if resposta.is_success:
        return
    try:
        detalhe = resposta.json().get("detail")
    except ValueError:
        detalhe = None
    if isinstance(detalhe, list):  # erro de validação do FastAPI
        detalhe = "; ".join(f"{'.'.join(map(str, e.get('loc', [])[1:]))}: {e.get('msg')}" for e in detalhe)
    raise ToolError(f"{prefixo} ({resposta.status_code}): {detalhe or resposta.text or 'sem detalhes'}")


api = ClienteAPI.do_ambiente()
servidor = MCPServer(
    "marcaconsulta",
    instructions=(
        "Agenda consultas no MarcaConsulta como o paciente de demonstração. Fluxo típico: "
        "buscar_profissionais -> ver_horarios_livres -> marcar_consulta. Horários em America/Sao_Paulo."
    ),
)


# ---------- formatação ----------

def _normalizar(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return sem_acento.casefold().strip()


def _resolver_opcao(opcoes: list[dict], nome: str | None, rotulo: str) -> int | None:
    if not nome:
        return None
    alvo = _normalizar(nome)
    exatas = [o for o in opcoes if _normalizar(o["nome"]) == alvo]
    parciais = exatas or [o for o in opcoes if alvo in _normalizar(o["nome"])]
    if len(parciais) == 1:
        return parciais[0]["id"]
    validas = ", ".join(o["nome"] for o in opcoes)
    motivo = "é ambígua" if parciais else "não existe"
    raise ToolError(f"A {rotulo} '{nome}' {motivo}. Opções válidas: {validas}.")


def _hora_local(valor: str) -> str:
    return datetime.fromisoformat(valor).astimezone(FUSO_LOCAL).strftime("%d/%m/%Y %H:%M")


def _reais(centavos: int | None) -> str:
    if centavos is None:
        return "preço não informado"
    return f"R$ {centavos // 100},{centavos % 100:02d}"


def _data(valor: str | None, rotulo: str) -> date | None:
    if not valor:
        return None
    try:
        return date.fromisoformat(valor)
    except ValueError:
        raise ToolError(f"{rotulo} inválida: '{valor}'. Use o formato AAAA-MM-DD.") from None


def _linha_consulta(c: dict) -> str:
    acoes = "pode cancelar" if c.get("pode_cancelar") else "não pode cancelar pelo paciente"
    return (
        f"- consulta_id={c['id']} | {_hora_local(c['inicio'])} | {c['profissional']['nome']} | "
        f"{c['tipo_consulta']['nome']} | {c['unidade']['nome']} | status={c['status']} | "
        f"{_reais(c['preco_centavos'])} | {acoes}"
    )


# ---------- tools de leitura ----------

@servidor.tool(annotations=LEITURA)
def buscar_profissionais(
    especialidade: str | None = None,
    nome: str | None = None,
    unidade: str | None = None,
    data: str | None = None,
) -> str:
    """Busca profissionais de saúde do MarcaConsulta.

    QUANDO USAR: primeiro passo quando o usuário quer marcar uma consulta ou saber quem atende
    uma especialidade, em qual unidade, por quanto, e qual o próximo horário. Use para descobrir
    o profissional_id e o tipo_consulta_id exigidos por ver_horarios_livres e marcar_consulta.
    NÃO USE para ver consultas já marcadas (use listar_minhas_consultas).

    Args:
        especialidade: nome da especialidade, ex. "Cardiologia" (sem diferenciar acentos/maiúsculas).
        nome: parte do nome do profissional.
        unidade: nome da unidade/clínica.
        data: só profissionais com horário livre nesta data (AAAA-MM-DD).
    """
    filtros = api.get("/publico/filtros")
    pagina = api.get(
        "/publico/profissionais",
        especialidade_id=_resolver_opcao(filtros["especialidades"], especialidade, "especialidade"),
        unidade_id=_resolver_opcao(filtros["unidades"], unidade, "unidade"),
        nome=nome or None,
        data=(d := _data(data, "Data")) and d.isoformat(),
    )
    if not pagina["itens"]:
        return "Nenhum profissional encontrado com esses filtros."
    linhas = [f"{pagina['total']} profissional(is) encontrado(s) (mostrando página {pagina['pagina']} de {pagina['paginas']}):"]
    for p in pagina["itens"]:
        proximo = p.get("proximo_horario")
        quando = f"{_hora_local(proximo['inicio'])} em {proximo['unidade_nome']}" if proximo else "sem horário livre"
        linhas.append(
            f"- profissional_id={p['id']} | {p['nome']} | {', '.join(p['especialidades'])} | "
            f"unidades: {', '.join(p['unidades'])} | {_reais(p['preco_centavos'])} | "
            f"tipo_consulta_id={p['tipo_consulta_id']} | próximo horário: {quando}"
        )
    return "\n".join(linhas)


@servidor.tool(annotations=LEITURA)
def ver_horarios_livres(
    profissional_id: int,
    tipo_consulta_id: int | None = None,
    de: str | None = None,
    ate: str | None = None,
) -> str:
    """Lista os horários livres de um profissional num período.

    QUANDO USAR: depois de escolher o profissional (buscar_profissionais) e antes de marcar_consulta,
    para mostrar ao usuário as opções e obter o valor exato de `inicio` e o `unidade_id`.
    Também quando o usuário pergunta "quando o Dr. X tem horário?".

    Args:
        profissional_id: id vindo de buscar_profissionais.
        tipo_consulta_id: tipo de consulta; se omitido, usa o primeiro tipo do profissional.
        de: data inicial AAAA-MM-DD (padrão: hoje).
        ate: data final AAAA-MM-DD (padrão: 7 dias depois de `de`).
    """
    inicio = _data(de, "Data inicial") or datetime.now(FUSO_LOCAL).date()
    fim = _data(ate, "Data final") or inicio + timedelta(days=7)
    perfil = api.get(f"/publico/profissionais/{profissional_id}")
    tipos = {t["id"]: t for e in perfil["especialidades"] for t in e["tipos"]}
    if not tipos:
        raise ToolError(f"{perfil['nome']} não tem tipos de consulta cadastrados.")
    tipo = tipos.get(tipo_consulta_id) if tipo_consulta_id is not None else next(iter(tipos.values()))
    if tipo is None:
        validos = ", ".join(f"{t['id']} ({t['nome']})" for t in tipos.values())
        raise ToolError(f"Tipo de consulta {tipo_consulta_id} não é atendido por {perfil['nome']}. Válidos: {validos}.")
    horarios = api.get(
        f"/publico/profissionais/{profissional_id}/horarios-livres",
        tipo_consulta_id=tipo["id"], de=inicio.isoformat(), ate=fim.isoformat(),
    )
    cabecalho = (
        f"{perfil['nome']} — {tipo['nome']} (tipo_consulta_id={tipo['id']}), "
        f"de {inicio:%d/%m/%Y} a {fim:%d/%m/%Y}:"
    )
    if not horarios:
        return f"{cabecalho}\nNenhum horário livre no período."
    unidades = {u["id"]: u["nome"] for u in perfil["unidades"]}
    linhas = [cabecalho]
    for h in horarios:
        linhas.append(
            f"- {_hora_local(h['inicio'])} | {unidades.get(h['unidade_id'], 'unidade')} "
            f"(unidade_id={h['unidade_id']}) | inicio={h['inicio']}"
        )
    return "\n".join(linhas)


@servidor.tool(annotations=LEITURA)
def listar_minhas_consultas() -> str:
    """Lista as consultas do paciente logado, separadas em próximas e passadas.

    QUANDO USAR: quando o usuário pergunta pelas consultas dele ("o que tenho marcado?"),
    para confirmar uma marcação recém-feita, e SEMPRE antes de cancelar_consulta para obter o
    consulta_id e saber se o cancelamento ainda é permitido (até 24 h antes).
    """
    dados = api.get("/consultas/minhas", autenticado=True)
    partes = []
    for chave, titulo in (("proximas", "Próximas"), ("passadas", "Passadas")):
        consultas = dados[chave]
        partes.append(f"{titulo} ({len(consultas)}):")
        partes.extend(_linha_consulta(c) for c in consultas)
        if not consultas:
            partes.append("- nenhuma")
    return "\n".join(partes)


# ---------- tools de escrita ----------

@servidor.tool(annotations=ESCRITA)
def marcar_consulta(profissional_id: int, unidade_id: int, tipo_consulta_id: int, inicio: str) -> str:
    """Marca uma consulta particular para o paciente logado.

    QUANDO USAR: somente depois que o usuário escolheu e confirmou explicitamente um horário
    mostrado por ver_horarios_livres. Não invente horários nem marque "para testar".
    Regras da clínica: no máximo 3 consultas futuras marcadas e nenhuma sobreposição de horário.

    Args:
        profissional_id: id do profissional.
        unidade_id: unidade do horário escolhido (vem de ver_horarios_livres).
        tipo_consulta_id: tipo de consulta usado na busca de horários.
        inicio: valor `inicio=` copiado de ver_horarios_livres (ISO 8601; sem fuso, assume America/Sao_Paulo).
    """
    try:
        quando = datetime.fromisoformat(inicio)
    except ValueError:
        raise ToolError(f"Início inválido: '{inicio}'. Use o valor inicio= mostrado por ver_horarios_livres.") from None
    if quando.tzinfo is None:
        quando = quando.replace(tzinfo=FUSO_LOCAL)
    consulta = api.post("/consultas", {
        "profissional_id": profissional_id,
        "unidade_id": unidade_id,
        "tipo_consulta_id": tipo_consulta_id,
        "inicio": quando.isoformat(),
        "forma_pagamento": "particular",
    })
    return "Consulta marcada:\n" + _linha_consulta(consulta)


@servidor.tool(annotations=CANCELAMENTO)
def cancelar_consulta(consulta_id: int) -> str:
    """Cancela uma consulta do paciente logado.

    QUANDO USAR: somente quando o usuário pedir explicitamente para cancelar uma consulta
    específica, identificada pelo consulta_id obtido em listar_minhas_consultas. O paciente só
    cancela até 24 h antes; depois disso, oriente o usuário a falar com a recepção.
    Para trocar de horário, NÃO cancele por conta própria: confirme com o usuário antes.
    """
    consulta = api.post(f"/consultas/{consulta_id}/cancelar")
    return "Consulta cancelada:\n" + _linha_consulta(consulta)


if __name__ == "__main__":
    servidor.run()
