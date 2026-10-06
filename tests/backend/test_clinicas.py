"""Spec: clinicas-e-profissionais."""
import pytest

from apoio import auth, criar_especialidade, criar_profissional, criar_unidade, criar_usuario

UNIDADE = {
    "nome": "Unidade Centro", "endereco": "Av. Nazaré, 100", "cep": "66035-000", "telefone": "9132220000",
    "abertura": "07:00", "fechamento": "19:00", "dias_funcionamento": [0, 1, 2, 3, 4],
}


@pytest.fixture
def admin(db):
    return auth(criar_usuario(db, "admin"))


def test_admin_cria_e_edita_unidade(client, admin):
    r = client.post("/api/unidades", json=UNIDADE, headers=admin)
    assert r.status_code == 201
    assert r.json()["cep"] == "66035000"
    r = client.patch(f"/api/unidades/{r.json()['id']}", json={"telefone": "9133334444"}, headers=admin)
    assert r.status_code == 200 and r.json()["telefone"] == "9133334444"


def test_unidade_com_abertura_depois_do_fechamento_e_recusada(client, admin):
    r = client.post("/api/unidades", json={**UNIDADE, "abertura": "19:00", "fechamento": "07:00"}, headers=admin)
    assert r.status_code == 422


def test_nome_de_especialidade_e_unico(client, admin):
    assert client.post("/api/especialidades", json={"nome": "Cardiologia"}, headers=admin).status_code == 201
    r = client.post("/api/especialidades", json={"nome": "cardiologia"}, headers=admin)
    assert r.status_code == 409
    assert r.json()["detail"] == "Já existe uma especialidade com este nome."


@pytest.mark.parametrize("duracao,esperado", [(15, 201), (120, 201), (45, 201), (10, 422), (125, 422), (32, 422)])
def test_duracao_do_tipo_de_consulta(client, admin, db, duracao, esperado):
    esp = criar_especialidade(db, tipos=())
    r = client.post(
        f"/api/especialidades/{esp.id}/tipos-consulta",
        json={"nome": "Retorno", "duracao_min": duracao, "preco_centavos": 15000},
        headers=admin,
    )
    assert r.status_code == esperado


def test_tipo_de_consulta_tem_preco_em_centavos(client, admin, db):
    esp = criar_especialidade(db, tipos=())
    r = client.post(
        f"/api/especialidades/{esp.id}/tipos-consulta",
        json={"nome": "Consulta", "duracao_min": 30, "preco_centavos": 25050},
        headers=admin,
    )
    assert r.json()["preco_centavos"] == 25050


def test_admin_cria_profissional_com_especialidades_e_unidades(client, admin, db):
    esp1, esp2 = criar_especialidade(db, "Cardiologia"), criar_especialidade(db, "Clínica Geral")
    uni = criar_unidade(db)
    r = client.post("/api/profissionais", json={
        "nome": "Dra. Ana Lima", "conselho": "crm", "registro_numero": "12345", "registro_uf": "pa",
        "biografia": "Cardiologista.", "especialidade_ids": [esp1.id, esp2.id], "unidade_ids": [uni.id],
    }, headers=admin)
    assert r.status_code == 201
    corpo = r.json()
    assert corpo["registro"] == "CRM 12345/PA"
    assert {e["nome"] for e in corpo["especialidades"]} == {"Cardiologia", "Clínica Geral"}
    assert corpo["unidades"][0]["id"] == uni.id
    assert corpo["foto_url"] is None


def test_registro_unico_por_conselho_e_uf(client, admin, db):
    esp, uni = criar_especialidade(db), criar_unidade(db)
    base = {"nome": "Dr. X", "conselho": "CRM", "registro_numero": "12345", "registro_uf": "PA",
            "especialidade_ids": [esp.id], "unidade_ids": [uni.id]}
    assert client.post("/api/profissionais", json=base, headers=admin).status_code == 201
    assert client.post("/api/profissionais", json=base, headers=admin).status_code == 409
    # mesmo número em outra UF é outro registro
    assert client.post("/api/profissionais", json={**base, "registro_uf": "SP"}, headers=admin).status_code == 201


@pytest.mark.parametrize("perfil", ["paciente", "profissional", "recepcao"])
def test_somente_admin_altera_cadastro(client, db, perfil):
    cab = auth(criar_usuario(db, perfil))
    assert client.post("/api/unidades", json=UNIDADE, headers=cab).status_code == 403
    assert client.post("/api/especialidades", json={"nome": "X"}, headers=cab).status_code == 403


def test_listagem_pagina_de_20_em_20(client, admin, db):
    uni, esp = criar_unidade(db), criar_especialidade(db)
    for i in range(25):
        criar_profissional(db, nome=f"Profissional {i:02d}", especialidades=[esp], unidades=[uni])
    p1 = client.get("/api/profissionais", headers=admin).json()
    p2 = client.get("/api/profissionais?pagina=2", headers=admin).json()
    assert (len(p1["itens"]), len(p2["itens"]), p1["total"], p1["paginas"]) == (20, 5, 25, 2)


def test_listagem_filtra_por_texto_sem_acento(client, admin, db):
    uni, esp = criar_unidade(db), criar_especialidade(db)
    criar_profissional(db, nome="Dr. João Souza", especialidades=[esp], unidades=[uni])
    criar_profissional(db, nome="Dra. Maria Lima", especialidades=[esp], unidades=[uni])
    itens = client.get("/api/profissionais?q=JOAO", headers=admin).json()["itens"]
    assert [p["nome"] for p in itens] == ["Dr. João Souza"]


def test_listagem_ordena_por_nome(client, admin, db):
    for nome in ("Beta", "Alfa", "Gama"):
        criar_especialidade(db, nome)
    asc = [e["nome"] for e in client.get("/api/especialidades?ordem=nome", headers=admin).json()["itens"]]
    desc = [e["nome"] for e in client.get("/api/especialidades?ordem=-nome", headers=admin).json()["itens"]]
    assert asc == ["Alfa", "Beta", "Gama"] and desc == ["Gama", "Beta", "Alfa"]
    assert client.get("/api/especialidades?ordem=xyz", headers=admin).status_code == 422


# ---------- desativação ----------

def _com_consultas(db):
    from app.agendamento.models import Consulta
    from app.core.tempo import Relogio
    from apoio import criar_consulta, local

    Relogio.atual = local("2026-10-05 08:00")
    uni, esp = criar_unidade(db), criar_especialidade(db)
    prof = criar_profissional(db, especialidades=[esp], unidades=[uni])
    paciente = criar_usuario(db)
    passada = criar_consulta(db, paciente, prof, uni, esp.tipos[0], local("2026-09-28 09:00"), status="realizada")
    futura = criar_consulta(db, paciente, prof, uni, esp.tipos[0], local("2026-10-12 09:00"))
    return uni, prof, passada, futura, Consulta


@pytest.mark.parametrize("alvo", ["unidades", "profissionais"])
def test_desativar_com_consultas_futuras_devolve_409_com_a_lista(client, admin, db, alvo):
    uni, prof, _, futura, _ = _com_consultas(db)
    alvo_id = uni.id if alvo == "unidades" else prof.id
    r = client.post(f"/api/{alvo}/{alvo_id}/desativar", headers=admin)
    assert r.status_code == 409
    assert [x["id"] for x in r.json()["consultas"]] == [futura.id]


@pytest.mark.parametrize("alvo", ["unidades", "profissionais"])
def test_desativar_sem_pendencias_mantem_consultas_passadas(client, admin, db, alvo):
    uni, prof, passada, futura, Consulta = _com_consultas(db)
    futura.status = "cancelada_clinica"
    db.commit()
    alvo_id = uni.id if alvo == "unidades" else prof.id
    r = client.post(f"/api/{alvo}/{alvo_id}/desativar", headers=admin)
    assert r.status_code == 200
    assert r.json()["ativa" if alvo == "unidades" else "ativo"] is False
    db.expire_all()
    assert db.get(Consulta, passada.id).status == "realizada"


def test_profissional_desativado_some_da_busca(client, admin, db):
    _, prof, _, futura, _ = _com_consultas(db)
    futura.status = "cancelada_clinica"
    db.commit()
    client.post(f"/api/profissionais/{prof.id}/desativar", headers=admin)
    assert client.get("/api/publico/profissionais").json()["total"] == 0
    assert client.get(f"/api/publico/profissionais/{prof.id}").status_code == 404
