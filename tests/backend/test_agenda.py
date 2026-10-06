"""Spec: agenda-e-disponibilidade."""
from datetime import date, datetime

import pytest

from app.agenda.models import Feriado
from app.core.tempo import FUSO_LOCAL, Relogio
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

SEG = "2026-10-12"  # segunda-feira


@pytest.fixture
def c(db):
    """Profissional com grade seg 08:00–12:00 na Unidade Centro; agora = segunda anterior."""
    Relogio.atual = local("2026-10-05 08:00")
    usuario = criar_usuario(db, "profissional")
    centro, norte = criar_unidade(db, "Unidade Centro"), criar_unidade(db, "Unidade Norte", "08:00", "18:00")
    esp = criar_especialidade(db, tipos=(("Consulta", 30, 20000), ("Primeira consulta", 45, 30000)))
    prof = criar_profissional(db, especialidades=[esp], unidades=[centro, norte], usuario=usuario)
    criar_faixa(db, prof, centro, 0, "08:00", "12:00")
    return {
        "prof": prof, "usuario": usuario, "centro": centro, "norte": norte,
        "tipo30": esp.tipos[0], "tipo45": esp.tipos[1],
    }


def hhmm(iso: str) -> str:
    return datetime.fromisoformat(iso).astimezone(FUSO_LOCAL).strftime("%H:%M")


def livres(client, c, tipo="tipo30", de=SEG, ate=SEG):
    r = client.get(
        f"/api/publico/profissionais/{c['prof'].id}/horarios-livres",
        params={"tipo_consulta_id": c[tipo].id, "de": de, "ate": ate},
    )
    assert r.status_code == 200, r.text
    return [hhmm(h["inicio"]) for h in r.json()]


def nova_faixa(client, c, cab, unidade="norte", dia=1, inicio="08:00", fim="12:00"):
    return client.post(
        f"/api/profissionais/{c['prof'].id}/grade",
        headers=cab,
        json={"unidade_id": c[unidade].id, "dia_semana": dia, "hora_inicio": inicio, "hora_fim": fim},
    )


def novo_bloqueio(client, c, inicio, fim, motivo="Congresso"):
    return client.post(
        f"/api/profissionais/{c['prof'].id}/bloqueios",
        headers=auth(c["usuario"]),
        json={"inicio": local(inicio).isoformat(), "fim": local(fim).isoformat(), "motivo": motivo},
    )


# ---------- grade ----------

def test_profissional_define_a_propria_grade(client, c):
    assert nova_faixa(client, c, auth(c["usuario"])).status_code == 201


def test_grade_nao_se_sobrepoe_mesmo_em_outra_unidade(client, c):
    r = nova_faixa(client, c, auth(c["usuario"]), dia=0, inicio="11:00", fim="14:00")
    assert r.status_code == 422
    assert "sobrepõe" in r.json()["detail"]


def test_grade_encostada_nao_e_sobreposicao(client, c):
    assert nova_faixa(client, c, auth(c["usuario"]), dia=0, inicio="12:00", fim="14:00").status_code == 201


def test_grade_fica_dentro_do_horario_da_unidade(client, c):
    r = nova_faixa(client, c, auth(c["usuario"]), dia=2, inicio="07:00", fim="10:00")
    assert r.status_code == 422
    assert "horário da unidade" in r.json()["detail"]


def test_grade_em_dia_que_a_unidade_nao_abre(client, c):
    assert nova_faixa(client, c, auth(c["usuario"]), dia=6).status_code == 422


def test_profissional_nao_altera_grade_de_outro(client, db, c):
    assert nova_faixa(client, c, auth(criar_usuario(db, "profissional"))).status_code == 403


def test_admin_define_grade_de_qualquer_profissional(client, db, c):
    assert nova_faixa(client, c, auth(criar_usuario(db, "admin"))).status_code == 201


# ---------- horários livres ----------

def test_horarios_em_passos_da_duracao_do_tipo(client, c):
    assert livres(client, c) == ["08:00", "08:30", "09:00", "09:30", "10:00", "10:30", "11:00", "11:30"]
    assert livres(client, c, "tipo45") == ["08:00", "08:45", "09:30", "10:15", "11:00"]


def test_intervalo_maximo_de_31_dias(client, c):
    url = f"/api/publico/profissionais/{c['prof'].id}/horarios-livres"
    ok = client.get(url, params={"tipo_consulta_id": c["tipo30"].id, "de": "2026-10-06", "ate": "2026-11-05"})
    longo = client.get(url, params={"tipo_consulta_id": c["tipo30"].id, "de": "2026-10-06", "ate": "2026-11-06"})
    assert ok.status_code == 200
    assert longo.status_code == 422 and longo.json()["detail"] == "O intervalo máximo é de 31 dias."


def test_sem_horarios_em_feriado_nacional(client, db, c):
    db.add(Feriado(data=date(2026, 10, 12), nome="Nossa Senhora Aparecida"))
    db.commit()
    assert livres(client, c) == []


def test_feriado_da_unidade_so_afeta_aquela_unidade(client, db, c):
    db.add(Feriado(data=date(2026, 10, 12), nome="Aniversário", unidade_id=c["norte"].id))
    db.commit()
    assert len(livres(client, c)) == 8
    db.add(Feriado(data=date(2026, 10, 12), nome="Aniversário", unidade_id=c["centro"].id))
    db.commit()
    assert livres(client, c) == []


def test_bloqueio_remove_horarios(client, c):
    assert novo_bloqueio(client, c, f"{SEG} 09:00", f"{SEG} 10:15").status_code == 201
    assert livres(client, c) == ["08:00", "08:30", "10:30", "11:00", "11:30"]


def test_consulta_marcada_ocupa_horario_e_cancelada_libera(client, db, c):
    consulta = criar_consulta(db, criar_usuario(db), c["prof"], c["centro"], c["tipo45"], local(f"{SEG} 10:00"))
    assert livres(client, c) == ["08:00", "08:30", "09:00", "09:30", "11:00", "11:30"]
    consulta.status = "cancelada_paciente"
    db.commit()
    assert len(livres(client, c)) == 8


def test_nunca_no_passado_nem_com_menos_de_2h(client, c):
    Relogio.atual = local(f"{SEG} 08:30")
    assert livres(client, c) == ["10:30", "11:00", "11:30"]
    Relogio.atual = local("2026-10-13 08:00")
    assert livres(client, c) == []


def test_tipo_de_outra_especialidade_e_recusado(client, db, c):
    outra = criar_especialidade(db, "Pediatria")
    r = client.get(
        f"/api/publico/profissionais/{c['prof'].id}/horarios-livres",
        params={"tipo_consulta_id": outra.tipos[0].id, "de": SEG, "ate": SEG},
    )
    assert r.status_code == 422


# ---------- bloqueios e feriados ----------

def test_bloqueio_que_colide_com_consulta_devolve_409_com_a_lista(client, db, c):
    consulta = criar_consulta(db, criar_usuario(db), c["prof"], c["centro"], c["tipo30"], local(f"{SEG} 09:00"))
    r = novo_bloqueio(client, c, f"{SEG} 08:00", f"{SEG} 12:00", "Férias")
    assert r.status_code == 409
    assert [x["id"] for x in r.json()["consultas"]] == [consulta.id]


def test_somente_admin_cadastra_feriado(client, db, c):
    corpo = {"data": "2026-11-15", "nome": "Proclamação da República"}
    assert client.post("/api/feriados", json=corpo, headers=auth(c["usuario"])).status_code == 403
    assert client.post("/api/feriados", json=corpo, headers=auth(criar_usuario(db, "admin"))).status_code == 201
