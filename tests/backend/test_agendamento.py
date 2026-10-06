"""Spec: agendamento — marcar, regras do paciente, concorrência, minhas consultas."""
import threading
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

from app.agendamento.models import Consulta, HistoricoStatus
from app.core.tempo import Relogio
from app.main import app
from apoio import (
    auth,
    criar_consulta,
    criar_especialidade,
    criar_faixa,
    criar_profissional,
    criar_unidade,
    criar_usuario,
    local,
)

SEG = "2026-10-12"


@pytest.fixture
def c(db):
    """Agora = seg 05/10 08:00. Profissional atende seg e ter 08:00–12:00 na Unidade Centro."""
    Relogio.atual = local("2026-10-05 08:00")
    centro = criar_unidade(db)
    esp = criar_especialidade(db, tipos=(("Consulta", 30, 25000),))
    prof = criar_profissional(db, especialidades=[esp], unidades=[centro])
    outro = criar_profissional(db, "Dra. Outra", especialidades=[esp], unidades=[centro])
    for p in (prof, outro):
        criar_faixa(db, p, centro, 0)
        criar_faixa(db, p, centro, 1)
    return {"prof": prof, "outro": outro, "centro": centro, "tipo": esp.tipos[0],
            "paciente": criar_usuario(db, nome="Maria Paciente"), "recepcao": criar_usuario(db, "recepcao")}


def pedido(c, inicio, prof="prof", **extra):
    return {"profissional_id": c[prof].id, "unidade_id": c["centro"].id, "tipo_consulta_id": c["tipo"].id,
            "inicio": local(inicio).isoformat(), **extra}


def marcar(client, c, inicio, usuario=None, **extra):
    return client.post("/api/consultas", json=pedido(c, inicio, **extra), headers=auth(usuario or c["paciente"]))


def test_paciente_marca_horario_livre(client, db, c):
    r = marcar(client, c, f"{SEG} 09:00")
    assert r.status_code == 201, r.text
    corpo = r.json()
    assert corpo["status"] == "marcada"
    assert corpo["preco_centavos"] == 25000 and corpo["forma_pagamento"] == "particular"
    assert corpo["profissional"]["id"] == c["prof"].id
    hist = db.query(HistoricoStatus).one()
    assert (hist.de_status, hist.para_status, hist.usuario_id) == (None, "marcada", c["paciente"].id)


def test_horario_fora_da_grade_ou_ocupado_devolve_409(client, c):
    assert marcar(client, c, f"{SEG} 13:00").status_code == 409
    assert marcar(client, c, f"{SEG} 09:10").status_code == 409  # não é um início válido
    assert marcar(client, c, f"{SEG} 09:00").status_code == 201
    outro = marcar(client, c, f"{SEG} 09:00", usuario=c["recepcao"], paciente_id=criar_paciente(c).id)
    assert outro.status_code == 409
    assert outro.json()["detail"] == "Horário não está mais disponível."


def criar_paciente(c):
    from app.core.db import SessionLocal

    with SessionLocal() as s:
        return criar_usuario(s, nome="Outro Paciente")


def test_dois_pedidos_simultaneos_so_um_e_aceito(c):
    pacientes = [c["paciente"], criar_paciente(c)]
    barreira = threading.Barrier(2)
    respostas = []

    def tentar(paciente):
        cliente = TestClient(app)
        barreira.wait()
        r = cliente.post("/api/consultas", json=pedido(c, f"{SEG} 10:00"), headers=auth(paciente))
        respostas.append(r.status_code)

    threads = [threading.Thread(target=tentar, args=(p,)) for p in pacientes]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert sorted(respostas) == [201, 409]


def test_indice_unico_impede_duas_consultas_ativas_no_mesmo_inicio(db, c):
    from sqlalchemy.exc import IntegrityError

    criar_consulta(db, c["paciente"], c["prof"], c["centro"], c["tipo"], local(f"{SEG} 10:00"))
    with pytest.raises(IntegrityError):
        criar_consulta(db, criar_usuario(db), c["prof"], c["centro"], c["tipo"], local(f"{SEG} 10:00"))
    db.rollback()


def test_paciente_nao_tem_consultas_sobrepostas(client, c):
    assert marcar(client, c, f"{SEG} 09:00").status_code == 201
    r = marcar(client, c, f"{SEG} 09:00", prof="outro")
    assert r.status_code == 422
    assert r.json()["detail"] == "Você já tem uma consulta neste horário."


def test_maximo_de_3_consultas_futuras_marcadas(client, c):
    for hora in ("08:00", "09:00", "10:00"):
        assert marcar(client, c, f"{SEG} {hora}").status_code == 201
    r = marcar(client, c, f"{SEG} 11:00")
    assert r.status_code == 422
    assert r.json()["detail"] == "Limite de 3 consultas futuras marcadas atingido."


def test_tres_faltas_em_90_dias_bloqueiam_a_web_mas_nao_a_recepcao(client, db, c):
    for dias in (60, 30, 7):
        criar_consulta(db, c["paciente"], c["outro"], c["centro"], c["tipo"],
                       local("2026-10-05 09:00") - timedelta(days=dias), status="faltou")
    r = marcar(client, c, f"{SEG} 09:00")
    assert r.status_code == 422
    assert "3 faltas" in r.json()["detail"]
    r = marcar(client, c, f"{SEG} 09:00", usuario=c["recepcao"], paciente_id=c["paciente"].id)
    assert r.status_code == 201


def test_faltas_espalhadas_alem_de_90_dias_nao_bloqueiam(client, db, c):
    for dias in (150, 100, 7):
        criar_consulta(db, c["paciente"], c["outro"], c["centro"], c["tipo"],
                       local("2026-10-05 09:00") - timedelta(days=dias), status="faltou")
    assert marcar(client, c, f"{SEG} 09:00").status_code == 201


def test_bloqueio_por_faltas_acaba_depois_de_30_dias(client, db, c):
    for dias in (40, 38, 35):
        criar_consulta(db, c["paciente"], c["outro"], c["centro"], c["tipo"],
                       local("2026-10-05 09:00") - timedelta(days=dias), status="faltou")
    assert marcar(client, c, f"{SEG} 09:00").status_code == 201


def test_recepcao_marca_em_nome_de_paciente(client, db, c):
    r = marcar(client, c, f"{SEG} 09:00", usuario=c["recepcao"], paciente_id=c["paciente"].id)
    assert r.status_code == 201
    consulta = db.query(Consulta).one()
    assert consulta.paciente_id == c["paciente"].id and consulta.criado_por_id == c["recepcao"].id
    assert marcar(client, c, f"{SEG} 10:00", usuario=c["recepcao"]).status_code == 422  # sem paciente


def test_profissional_nao_marca(client, db, c):
    assert marcar(client, c, f"{SEG} 09:00", usuario=criar_usuario(db, "profissional")).status_code == 403


def test_minhas_consultas_separa_proximas_e_passadas(client, db, c):
    passada = criar_consulta(db, c["paciente"], c["prof"], c["centro"], c["tipo"], local("2026-09-28 09:00"),
                             status="realizada")
    marcar(client, c, f"{SEG} 09:00")
    r = client.get("/api/consultas/minhas", headers=auth(c["paciente"]))
    assert r.status_code == 200
    corpo = r.json()
    assert [x["id"] for x in corpo["passadas"]] == [passada.id]
    assert len(corpo["proximas"]) == 1
    proxima = corpo["proximas"][0]
    assert proxima["pode_cancelar"] is True and proxima["pode_remarcar"] is True
    assert corpo["passadas"][0]["pode_cancelar"] is False


def test_minhas_consultas_nao_permite_cancelar_com_menos_de_24h(client, db, c):
    criar_consulta(db, c["paciente"], c["prof"], c["centro"], c["tipo"], local("2026-10-06 07:30"))
    proxima = client.get("/api/consultas/minhas", headers=auth(c["paciente"])).json()["proximas"][0]
    assert proxima["pode_cancelar"] is False and proxima["pode_remarcar"] is False
