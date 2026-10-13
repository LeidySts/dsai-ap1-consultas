import asyncio
import json
from datetime import date, timedelta

import httpx
import pytest
import servidor
from mcp.server.mcpserver.exceptions import ToolError

FILTROS = {
    "especialidades": [{"id": 1, "nome": "Cardiologia"}, {"id": 2, "nome": "Clínica Geral"}],
    "unidades": [{"id": 1, "nome": "Unidade Centro"}, {"id": 2, "nome": "Unidade Nazaré"}],
}
PERFIL = {
    "id": 7, "nome": "Dra. Ana", "registro": "CRM 1", "foto_url": None, "biografia": "",
    "especialidades": [{"id": 1, "nome": "Cardiologia", "tipos": [
        {"id": 3, "nome": "Consulta", "duracao_min": 30, "preco_centavos": 28000},
        {"id": 4, "nome": "Retorno", "duracao_min": 20, "preco_centavos": 0},
    ]}],
    "unidades": [{"id": 2, "nome": "Unidade Nazaré", "endereco": "Rua X", "telefone": "1"}],
}
CONSULTA = {
    "id": 55, "inicio": "2026-10-20T12:00:00Z", "fim": "2026-10-20T12:30:00Z", "status": "marcada",
    "forma_pagamento": "particular", "preco_centavos": 28050, "remarcacoes": 0,
    "paciente": {"id": 1, "nome": "Paciente"}, "profissional": {"id": 7, "nome": "Dra. Ana"},
    "unidade": {"id": 2, "nome": "Unidade Nazaré", "endereco": "Rua X"},
    "tipo_consulta": {"id": 3, "nome": "Consulta", "duracao_min": 30},
    "pode_cancelar": True, "pode_remarcar": True,
}


def test_as_cinco_tools_sao_registradas_com_docstring_de_quando_usar():
    tools = {t.name: t for t in asyncio.run(servidor.servidor.list_tools())}
    assert set(tools) == {
        "buscar_profissionais", "ver_horarios_livres", "listar_minhas_consultas",
        "marcar_consulta", "cancelar_consulta",
    }
    for tool in tools.values():
        assert "QUANDO USAR" in tool.description
    assert tools["buscar_profissionais"].annotations.read_only_hint is True
    assert tools["cancelar_consulta"].annotations.destructive_hint is True


def test_credenciais_vem_do_ambiente(monkeypatch):
    monkeypatch.setenv("MARCACONSULTA_EMAIL", "a@b.com")
    monkeypatch.setenv("MARCACONSULTA_SENHA", "x")
    monkeypatch.delenv("MARCACONSULTA_API_URL", raising=False)
    cliente = servidor.ClienteAPI.do_ambiente()
    assert (cliente.email, cliente.senha) == ("a@b.com", "x")
    assert str(cliente._http.base_url) == "https://marcaconsulta.onrender.com/api/"


def test_buscar_resolve_especialidade_sem_acento_e_formata_resultado(api_falsa):
    api_falsa.responder("GET", "/publico/filtros", (200, FILTROS))
    api_falsa.responder("GET", "/publico/profissionais", (200, {"total": 1, "pagina": 1, "paginas": 1, "itens": [{
        "id": 7, "nome": "Dra. Ana", "foto_url": None, "especialidades": ["Clínica Geral"],
        "unidades": ["Unidade Nazaré"], "nota_media": None, "preco_centavos": 28000, "tipo_consulta_id": 3,
        "proximo_horario": {"inicio": "2026-10-14T11:00:00Z", "unidade_id": 2, "unidade_nome": "Unidade Nazaré"},
        "aviso": None,
    }]}))
    texto = servidor.buscar_profissionais(especialidade="clinica geral", unidade="nazare", data="2026-10-14")
    params = api_falsa.pedidos[-1].url.params
    assert params["especialidade_id"] == "2" and params["unidade_id"] == "2" and params["data"] == "2026-10-14"
    assert "nome" not in params
    assert "profissional_id=7" in texto and "tipo_consulta_id=3" in texto
    assert "R$ 280,00" in texto
    assert "14/10/2026 08:00" in texto  # 11:00 UTC exibido em America/Sao_Paulo


def test_buscar_especialidade_inexistente_lista_opcoes(api_falsa):
    api_falsa.responder("GET", "/publico/filtros", (200, FILTROS))
    with pytest.raises(ToolError, match="não existe.*Cardiologia, Clínica Geral"):
        servidor.buscar_profissionais(especialidade="Astrologia")


def test_buscar_sem_resultados(api_falsa):
    api_falsa.responder("GET", "/publico/filtros", (200, FILTROS))
    api_falsa.responder("GET", "/publico/profissionais", (200, {"total": 0, "pagina": 1, "paginas": 0, "itens": []}))
    assert "Nenhum profissional" in servidor.buscar_profissionais(nome="Zé")


def test_horarios_usa_primeiro_tipo_e_periodo_informado(api_falsa):
    api_falsa.responder("GET", "/publico/profissionais/7", (200, PERFIL))
    api_falsa.responder("GET", "/publico/profissionais/7/horarios-livres", (200, [
        {"inicio": "2026-10-15T11:00:00Z", "fim": "2026-10-15T11:30:00Z", "unidade_id": 2},
    ]))
    texto = servidor.ver_horarios_livres(7, de="2026-10-15", ate="2026-10-16")
    params = api_falsa.pedidos[-1].url.params
    assert (params["tipo_consulta_id"], params["de"], params["ate"]) == ("3", "2026-10-15", "2026-10-16")
    assert "15/10/2026 08:00 | Unidade Nazaré (unidade_id=2) | inicio=2026-10-15T11:00:00Z" in texto


def test_horarios_periodo_padrao_e_sete_dias(api_falsa):
    api_falsa.responder("GET", "/publico/profissionais/7", (200, PERFIL))
    api_falsa.responder("GET", "/publico/profissionais/7/horarios-livres", (200, []))
    texto = servidor.ver_horarios_livres(7, tipo_consulta_id=4)
    params = api_falsa.pedidos[-1].url.params
    assert date.fromisoformat(params["ate"]) - date.fromisoformat(params["de"]) == timedelta(days=7)
    assert params["tipo_consulta_id"] == "4" and "Nenhum horário livre" in texto


def test_horarios_tipo_invalido(api_falsa):
    api_falsa.responder("GET", "/publico/profissionais/7", (200, PERFIL))
    with pytest.raises(ToolError, match="Válidos: 3 \\(Consulta\\), 4 \\(Retorno\\)"):
        servidor.ver_horarios_livres(7, tipo_consulta_id=99)


def test_listar_minhas_consultas_faz_login_e_separa(api_falsa):
    api_falsa.responder("GET", "/consultas/minhas", (200, {"proximas": [CONSULTA], "passadas": []}))
    texto = servidor.listar_minhas_consultas()
    assert api_falsa.logins == 1
    assert api_falsa.pedidos[-1].headers["Authorization"] == "Bearer token-1"
    assert "Próximas (1):" in texto and "consulta_id=55" in texto and "pode cancelar" in texto
    assert "R$ 280,50" in texto and "20/10/2026 09:00" in texto
    assert "Passadas (0):\n- nenhuma" in texto
    servidor.listar_minhas_consultas()
    assert api_falsa.logins == 1  # token reaproveitado


def test_relogin_apos_401(api_falsa):
    api_falsa.responder("GET", "/consultas/minhas", (200, {"proximas": [], "passadas": []}))
    servidor.listar_minhas_consultas()
    api_falsa.tokens_validos = {"token-2"}  # token-1 expirou
    servidor.listar_minhas_consultas()
    assert api_falsa.logins == 2
    assert api_falsa.pedidos[-1].headers["Authorization"] == "Bearer token-2"


def test_sem_credenciais_mensagem_clara(api_falsa):
    servidor.api.email = None
    with pytest.raises(ToolError, match="MARCACONSULTA_EMAIL e MARCACONSULTA_SENHA"):
        servidor.listar_minhas_consultas()
    assert api_falsa.pedidos == []


def test_senha_errada(api_falsa):
    servidor.api.senha = "errada"
    with pytest.raises(ToolError, match="Falha no login do paciente \\(401\\): E-mail ou senha inválidos"):
        servidor.listar_minhas_consultas()


def test_marcar_envia_horario_com_fuso(api_falsa):
    api_falsa.responder("POST", "/consultas", (201, CONSULTA))
    texto = servidor.marcar_consulta(7, 2, 3, "2026-10-20T09:00:00")
    corpo = json.loads(api_falsa.pedidos[-1].content)
    assert corpo == {"profissional_id": 7, "unidade_id": 2, "tipo_consulta_id": 3,
                     "inicio": "2026-10-20T09:00:00-03:00", "forma_pagamento": "particular"}
    assert texto.startswith("Consulta marcada:") and "consulta_id=55" in texto


def test_marcar_conflito_vira_mensagem(api_falsa):
    api_falsa.responder("POST", "/consultas", (409, {"detail": "Horário não está mais disponível."}))
    with pytest.raises(ToolError, match="\\(409\\): Horário não está mais disponível"):
        servidor.marcar_consulta(7, 2, 3, "2026-10-20T12:00:00Z")


def test_marcar_inicio_invalido(api_falsa):
    with pytest.raises(ToolError, match="Início inválido"):
        servidor.marcar_consulta(7, 2, 3, "amanhã cedo")


def test_erro_de_validacao_do_fastapi(api_falsa):
    api_falsa.responder("POST", "/consultas", (422, {"detail": [
        {"loc": ["body", "inicio"], "msg": "Input should be a valid datetime"},
    ]}))
    with pytest.raises(ToolError, match="inicio: Input should be a valid datetime"):
        servidor.marcar_consulta(7, 2, 3, "2026-10-20T12:00:00Z")


def test_cancelar(api_falsa):
    api_falsa.responder("POST", "/consultas/55/cancelar", (200, {**CONSULTA, "status": "cancelada_paciente"}))
    texto = servidor.cancelar_consulta(55)
    assert "Consulta cancelada" in texto and "status=cancelada_paciente" in texto


def test_cancelar_menos_de_24h(api_falsa):
    api_falsa.responder("POST", "/consultas/55/cancelar", (422, {"detail": "Cancelamento só até 24 h antes."}))
    with pytest.raises(ToolError, match="24 h antes"):
        servidor.cancelar_consulta(55)


def test_api_fora_do_ar(monkeypatch):
    def cair(_):
        raise httpx.ConnectError("sem rede")
    cliente = servidor.ClienteAPI("https://x.test/api", "a", "b", transport=httpx.MockTransport(cair))
    monkeypatch.setattr(servidor, "api", cliente)
    with pytest.raises(ToolError, match="Não foi possível falar com a API"):
        servidor.buscar_profissionais()
