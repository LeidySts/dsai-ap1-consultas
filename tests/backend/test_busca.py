"""Spec: busca."""
import time as relogio_real
from datetime import datetime, time

import pytest

from app.agenda.models import GradeHorario
from app.clinicas.models import Profissional
from app.core.tempo import FUSO_LOCAL, Relogio
from app.core.texto import normalizar
from apoio import criar_consulta, criar_especialidade, criar_faixa, criar_profissional, criar_unidade, criar_usuario, local


@pytest.fixture
def c(db):
    """Agora = seg 05/10/2026 07:00. Três profissionais com agendas diferentes."""
    Relogio.atual = local("2026-10-05 07:00")
    centro, norte = criar_unidade(db, "Unidade Centro", "07:00", "21:00"), criar_unidade(db, "Unidade Norte")
    cardio = criar_especialidade(db, "Cardiologia", (("Consulta", 30, 30000),))
    pedi = criar_especialidade(db, "Pediatria", (("Consulta", 30, 20000),))
    joao = criar_profissional(db, "Dr. João Souza", [cardio], [centro])
    maria = criar_profissional(db, "Dra. Maria Lima", [cardio, pedi], [centro, norte])
    sem = criar_profissional(db, "Dr. Sem Agenda", [cardio], [centro])
    criar_faixa(db, joao, centro, 2, "08:00", "12:00")  # quarta de manhã
    criar_faixa(db, maria, norte, 1, "14:00", "18:00")  # terça à tarde
    criar_faixa(db, maria, centro, 3, "18:00", "20:00")  # quinta à noite
    return {"centro": centro, "norte": norte, "cardio": cardio, "pedi": pedi, "joao": joao, "maria": maria, "sem": sem}


def buscar(client, **params):
    r = client.get("/api/publico/profissionais", params=params)
    assert r.status_code == 200, r.text
    return r.json()


def nomes(resultado):
    return [i["nome"] for i in resultado["itens"]]


def test_busca_e_publica(client, c):
    assert client.get("/api/publico/profissionais").status_code == 200
    assert client.get("/api/publico/filtros").status_code == 200


def test_resultado_traz_os_campos_e_o_proximo_horario(client, c):
    item = next(i for i in buscar(client)["itens"] if i["nome"] == "Dr. João Souza")
    assert item["especialidades"] == ["Cardiologia"]
    assert item["unidades"] == ["Unidade Centro"]
    assert item["preco_centavos"] == 30000
    assert "foto_url" in item and "nota_media" in item
    inicio = datetime.fromisoformat(item["proximo_horario"]["inicio"]).astimezone(FUSO_LOCAL)
    assert inicio == local("2026-10-07 08:00")
    assert item["proximo_horario"]["unidade_nome"] == "Unidade Centro"


def test_ordena_por_proximo_horario_por_padrao_e_sem_horario_vai_para_o_fim(client, c):
    r = buscar(client)
    assert nomes(r) == ["Dra. Maria Lima", "Dr. João Souza", "Dr. Sem Agenda"]
    assert r["itens"][-1]["proximo_horario"] is None
    assert r["itens"][-1]["aviso"] == "sem horários nos próximos 30 dias"


def test_ordena_por_preco(client, c):
    assert nomes(buscar(client, ordem="preco")) == ["Dra. Maria Lima", "Dr. João Souza", "Dr. Sem Agenda"]
    assert buscar(client, ordem="preco")["itens"][0]["preco_centavos"] == 20000


def test_filtro_por_especialidade(client, c):
    assert nomes(buscar(client, especialidade_id=c["pedi"].id)) == ["Dra. Maria Lima"]


def test_filtro_por_unidade(client, c):
    r = buscar(client, unidade_id=c["norte"].id)
    assert nomes(r) == ["Dra. Maria Lima"]
    assert r["itens"][0]["proximo_horario"]["unidade_nome"] == "Unidade Norte"


def test_filtro_por_nome_ignora_acentos_e_maiusculas(client, c):
    assert nomes(buscar(client, nome="joao")) == ["Dr. João Souza"]
    assert set(nomes(buscar(client, nome="cardiologia"))) == {"Dr. João Souza", "Dra. Maria Lima", "Dr. Sem Agenda"}
    assert nomes(buscar(client, nome="PEDIATRIA")) == ["Dra. Maria Lima"]


def test_filtro_por_turno(client, c):
    noite = buscar(client, turno="noite")
    maria = next(i for i in noite["itens"] if i["nome"] == "Dra. Maria Lima")
    inicio = datetime.fromisoformat(maria["proximo_horario"]["inicio"]).astimezone(FUSO_LOCAL)
    assert inicio == local("2026-10-08 18:00")
    joao = next(i for i in noite["itens"] if i["nome"] == "Dr. João Souza")
    assert joao["proximo_horario"] is None
    assert client.get("/api/publico/profissionais", params={"turno": "madrugada"}).status_code == 422


def test_filtro_por_data_desejada(client, c):
    r = buscar(client, data="2026-10-08", nome="joao")
    inicio = datetime.fromisoformat(r["itens"][0]["proximo_horario"]["inicio"]).astimezone(FUSO_LOCAL)
    assert inicio == local("2026-10-14 08:00")


def test_proximo_horario_respeita_consultas_marcadas(client, db, c):
    criar_consulta(db, criar_usuario(db), c["joao"], c["centro"], c["cardio"].tipos[0], local("2026-10-07 08:00"))
    r = buscar(client, nome="joao")
    inicio = datetime.fromisoformat(r["itens"][0]["proximo_horario"]["inicio"]).astimezone(FUSO_LOCAL)
    assert inicio == local("2026-10-07 08:30")


def test_paginacao_de_10_em_10(client, db, c):
    for i in range(12):
        criar_profissional(db, f"Profissional {i:02d}", [c["cardio"]], [c["centro"]])
    p1, p2 = buscar(client), buscar(client, pagina=2)
    assert (len(p1["itens"]), len(p2["itens"]), p1["total"], p1["paginas"]) == (10, 5, 15, 2)


def test_pagina_publica_do_profissional(client, c):
    r = client.get(f"/api/publico/profissionais/{c['maria'].id}")
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["nome"] == "Dra. Maria Lima"
    assert [e["nome"] for e in corpo["especialidades"]] == ["Cardiologia", "Pediatria"]
    assert corpo["especialidades"][0]["tipos"][0]["preco_centavos"] == 30000
    assert {u["nome"] for u in corpo["unidades"]} == {"Unidade Centro", "Unidade Norte"}
    assert corpo["biografia"] == "Atende adultos."
    assert "nota_media" in corpo


def test_busca_com_200_profissionais_responde_em_menos_de_1_segundo(client, db, c):
    for i in range(200):
        nome = f"Profissional Carga {i:03d}"
        prof = Profissional(nome=nome, nome_busca=normalizar(nome), conselho="CRM", registro_numero=str(50000 + i),
                            registro_uf="PA", biografia="", especialidades=[c["cardio"]], unidades=[c["centro"]])
        db.add(prof)
        db.flush()
        db.add(GradeHorario(profissional_id=prof.id, unidade_id=c["centro"].id, dia_semana=i % 6,
                            hora_inicio=time(8), hora_fim=time(12)))
    db.commit()
    buscar(client)  # aquece
    inicio = relogio_real.perf_counter()
    r = buscar(client, nome="cardiologia")
    assert relogio_real.perf_counter() - inicio < 1.0
    assert r["total"] == 203
