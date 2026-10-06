"""Spec: agendamento — cancelar, remarcar, transições de status e histórico."""
import pytest

from app.agendamento.models import Consulta, HistoricoStatus
from app.agendamento.service import TRANSICOES, mudar_status
from app.core.erros import RegraViolada
from app.core.tempo import Relogio
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
    Relogio.atual = local("2026-10-05 08:00")
    centro = criar_unidade(db)
    esp = criar_especialidade(db, tipos=(("Consulta", 30, 25000),))
    prof = criar_profissional(db, especialidades=[esp], unidades=[centro])
    criar_faixa(db, prof, centro, 0)
    paciente = criar_usuario(db, nome="Maria Paciente")
    consulta = criar_consulta(db, paciente, prof, centro, esp.tipos[0], local(f"{SEG} 09:00"))
    return {"prof": prof, "centro": centro, "tipo": esp.tipos[0], "paciente": paciente, "consulta": consulta,
            "recepcao": criar_usuario(db, "recepcao")}


def cancelar(client, c, usuario=None):
    return client.post(f"/api/consultas/{c['consulta'].id}/cancelar", headers=auth(usuario or c["paciente"]))


def remarcar(client, c, inicio, usuario=None, consulta_id=None):
    return client.post(
        f"/api/consultas/{consulta_id or c['consulta'].id}/remarcar",
        json={"inicio": local(inicio).isoformat()},
        headers=auth(usuario or c["paciente"]),
    )


def test_paciente_cancela_com_mais_de_24h(client, c):
    r = cancelar(client, c)
    assert r.status_code == 200 and r.json()["status"] == "cancelada_paciente"


def test_paciente_nao_cancela_com_menos_de_24h_mas_a_recepcao_sim(client, c):
    Relogio.atual = local("2026-10-11 10:00")
    r = cancelar(client, c)
    assert r.status_code == 422
    assert "menos de 24 horas" in r.json()["detail"]
    r = cancelar(client, c, c["recepcao"])
    assert r.status_code == 200 and r.json()["status"] == "cancelada_clinica"


def test_paciente_nao_cancela_consulta_de_outro(client, db, c):
    assert cancelar(client, c, criar_usuario(db, nome="Intruso")).status_code == 404


def test_cancelar_duas_vezes_e_transicao_invalida(client, c):
    assert cancelar(client, c).status_code == 200
    assert cancelar(client, c, c["recepcao"]).status_code == 422


def test_cancelamento_libera_o_horario(client, c):
    cancelar(client, c)
    r = client.get(f"/api/publico/profissionais/{c['prof'].id}/horarios-livres",
                   params={"tipo_consulta_id": c["tipo"].id, "de": SEG, "ate": SEG})
    assert len(r.json()) == 8


def test_remarcar_cancela_a_original_e_marca_a_nova(client, db, c):
    r = remarcar(client, c, f"{SEG} 10:00")
    assert r.status_code == 201, r.text
    nova = db.get(Consulta, r.json()["id"])
    db.refresh(c["consulta"])
    assert c["consulta"].status == "cancelada_paciente"
    assert nova.status == "marcada" and nova.remarcacoes == 1 and nova.consulta_origem_id == c["consulta"].id


def test_remarcar_para_horario_invalido_mantem_a_original(client, db, c):
    outro = criar_usuario(db, nome="Outro")
    criar_consulta(db, outro, c["prof"], c["centro"], c["tipo"], local(f"{SEG} 10:00"))
    r = remarcar(client, c, f"{SEG} 10:00")
    assert r.status_code == 409
    db.refresh(c["consulta"])
    assert c["consulta"].status == "marcada"
    assert db.query(HistoricoStatus).filter_by(consulta_id=c["consulta"].id).count() == 0


def test_remarcar_para_o_proprio_horario_e_possivel(client, c):
    """A original é cancelada antes, então o mesmo horário volta a ficar livre."""
    assert remarcar(client, c, f"{SEG} 09:00").status_code == 201


def test_no_maximo_2_remarcacoes(client, c):
    r1 = remarcar(client, c, f"{SEG} 10:00")
    r2 = remarcar(client, c, f"{SEG} 10:30", consulta_id=r1.json()["id"])
    assert r2.status_code == 201 and r2.json()["remarcacoes"] == 2
    assert r2.json()["pode_remarcar"] is False
    r3 = remarcar(client, c, f"{SEG} 11:00", consulta_id=r2.json()["id"])
    assert r3.status_code == 422
    assert r3.json()["detail"] == "Esta consulta já foi remarcada 2 vezes."


def test_paciente_nao_remarca_com_menos_de_24h(client, c):
    Relogio.atual = local("2026-10-11 10:00")
    assert remarcar(client, c, f"{SEG} 10:00").status_code == 422
    assert remarcar(client, c, f"{SEG} 10:00", usuario=c["recepcao"]).status_code == 201


def test_historico_registra_quem_quando_de_e_para(client, db, c):
    cancelar(client, c)
    r = client.get(f"/api/consultas/{c['consulta'].id}/historico", headers=auth(c["paciente"]))
    assert r.status_code == 200
    ultimo = r.json()[-1]
    assert (ultimo["de_status"], ultimo["para_status"], ultimo["usuario_id"]) == (
        "marcada", "cancelada_paciente", c["paciente"].id)
    assert ultimo["em"].startswith("2026-10-05")


@pytest.mark.parametrize("atual,novo", [
    ("marcada", "realizada"), ("marcada", "em_atendimento"), ("realizada", "marcada"),
    ("cancelada_paciente", "marcada"), ("faltou", "confirmada"), ("confirmada", "cancelada_paciente"),
])
def test_transicoes_invalidas_sao_recusadas(db, c, atual, novo):
    consulta = c["consulta"]
    consulta.status = atual
    with pytest.raises(RegraViolada) as erro:
        mudar_status(db, consulta, novo, c["recepcao"])
    assert erro.value.status_code == 422


def test_fluxo_valido_de_status(db, c):
    consulta = c["consulta"]
    for novo in ("confirmada", "em_atendimento", "realizada"):
        assert novo in TRANSICOES[consulta.status]
        mudar_status(db, consulta, novo, c["recepcao"])
    db.commit()
    assert consulta.status == "realizada"
    assert db.query(HistoricoStatus).filter_by(consulta_id=consulta.id).count() == 3
