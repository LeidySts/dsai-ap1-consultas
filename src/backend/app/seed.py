"""Dados de demonstração. Uso: `python -m app.seed`.

Idempotente: se o admin de demonstração já existe, não faz nada.
Os dados de base ficam em app/dados/demo.json.
"""
import json
import random
from datetime import date, datetime, time, timedelta
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agenda.models import Feriado, GradeHorario
from app.agenda.service import carregar_dados_agenda, gerar_horarios, hoje_local
from app.agendamento.models import Consulta, HistoricoStatus
from app.auth.models import Usuario
from app.clinicas.models import Especialidade, Profissional, TipoConsulta, Unidade
from app.core.db import SessionLocal
from app.core.seguranca import hash_senha
from app.core.tempo import FUSO_LOCAL, agora_utc
from app.core.texto import normalizar

ARQUIVO = Path(__file__).parent / "dados" / "demo.json"
TOTAL_PROFISSIONAIS = 48
TOTAL_PACIENTES = 100
TURNOS = {"manha": (time(8), time(12)), "tarde": (time(13), time(17)), "noite": (time(18), time(21))}


def gerar_cpf(rng: random.Random) -> str:
    base = [rng.randint(0, 9) for _ in range(9)]
    for tamanho in (9, 10):
        soma = sum(d * (tamanho + 1 - i) for i, d in enumerate(base[:tamanho]))
        base.append((soma * 10) % 11 % 10)
    return "".join(map(str, base))


def _nome(rng: random.Random, dados: dict) -> str:
    return f"{rng.choice(dados['nomes'])} {rng.choice(dados['sobrenomes'])} {rng.choice(dados['sobrenomes'])}"


def _criar_cadastros(db: Session, dados: dict, rng: random.Random):
    unidades = []
    for u in dados["unidades"]:
        unidade = Unidade(
            **{**u, "abertura": time.fromisoformat(u["abertura"]), "fechamento": time.fromisoformat(u["fechamento"])},
            nome_busca=normalizar(u["nome"]),
        )
        unidades.append(unidade)
    especialidades = []
    for e in dados["especialidades"]:
        especialidade = Especialidade(nome=e["nome"], nome_busca=normalizar(e["nome"]))
        especialidade.tipos = [TipoConsulta(nome=n, duracao_min=d, preco_centavos=p) for n, d, p in e["tipos"]]
        especialidades.append(especialidade)
    db.add_all(unidades + especialidades)
    for data, nome in dados["feriados_nacionais"]:
        db.add(Feriado(data=date.fromisoformat(data), nome=nome))
    db.flush()
    return unidades, especialidades


def _criar_usuarios(db: Session, dados: dict, rng: random.Random):
    senha_hash = hash_senha(dados["senha_demo"])
    demo = {}
    for u in dados["usuarios_demo"]:
        usuario = Usuario(
            nome=u["nome"], email=u["email"], perfil=u["perfil"], senha_hash=senha_hash, telefone="91990000000",
            cpf=gerar_cpf(rng) if u["perfil"] == "paciente" else None,
            data_nascimento=date(1988, 3, 14) if u["perfil"] == "paciente" else None,
        )
        db.add(usuario)
        demo[u["perfil"]] = usuario
    pacientes = [demo["paciente"]]
    cpfs = {demo["paciente"].cpf}
    for i in range(TOTAL_PACIENTES - 1):
        cpf = gerar_cpf(rng)
        while cpf in cpfs:
            cpf = gerar_cpf(rng)
        cpfs.add(cpf)
        paciente = Usuario(
            nome=_nome(rng, dados), email=f"paciente{i + 1:03d}@demo.com", perfil="paciente", senha_hash=senha_hash,
            cpf=cpf, telefone=f"9198{rng.randint(1000000, 9999999)}",
            data_nascimento=date(rng.randint(1950, 2015), rng.randint(1, 12), rng.randint(1, 28)),
        )
        db.add(paciente)
        pacientes.append(paciente)
    db.flush()
    return demo, pacientes


def _criar_profissionais(db: Session, dados: dict, rng: random.Random, unidades, especialidades, medico_demo):
    profissionais = []
    for i in range(TOTAL_PROFISSIONAIS):
        if i == 0:
            nome, esps, unis = medico_demo.nome, especialidades[:2], unidades[:2]
        else:
            nome = ("Dr. " if rng.random() < 0.5 else "Dra. ") + _nome(rng, dados)
            # garante ao menos 4 profissionais por especialidade
            esps = [especialidades[i % len(especialidades)]]
            if rng.random() < 0.25:
                esps.append(rng.choice([e for e in especialidades if e not in esps]))
            unis = rng.sample(unidades, rng.choice([1, 1, 2]))
        profissional = Profissional(
            usuario_id=medico_demo.id if i == 0 else None, nome=nome, nome_busca=normalizar(nome), conselho="CRM",
            registro_numero=str(10000 + i), registro_uf="PA", biografia=rng.choice(dados["biografias"]),
            especialidades=esps, unidades=unis,
        )
        db.add(profissional)
        db.flush()
        for dia in sorted(rng.sample(range(6), rng.randint(3, 5))):
            opcoes = [
                (u, turno) for u in unis for turno, (ini, fim) in TURNOS.items()
                if dia in u.dias_funcionamento and u.abertura <= ini and fim <= u.fechamento
            ]
            if not opcoes:
                continue
            for unidade, turno in rng.sample(opcoes, min(len(opcoes), rng.choice([1, 1, 2]))):
                ini, fim = TURNOS[turno]
                ja = [g for g in profissional_grade(db, profissional.id) if g.dia_semana == dia]
                if any(ini < g.hora_fim and g.hora_inicio < fim for g in ja):
                    continue
                db.add(GradeHorario(profissional_id=profissional.id, unidade_id=unidade.id, dia_semana=dia,
                                    hora_inicio=ini, hora_fim=fim))
                db.flush()
        profissionais.append(profissional)
    return profissionais


def profissional_grade(db: Session, profissional_id: int) -> list[GradeHorario]:
    return list(db.scalars(select(GradeHorario).where(GradeHorario.profissional_id == profissional_id)))


def _registrar(db: Session, consulta: Consulta, autor: Usuario, quando: datetime) -> None:
    db.add(HistoricoStatus(consulta_id=consulta.id, de_status=None, para_status="marcada", usuario_id=autor.id,
                           em=quando))
    if consulta.status != "marcada":
        db.add(HistoricoStatus(consulta_id=consulta.id, de_status="marcada", para_status=consulta.status,
                               usuario_id=autor.id, em=consulta.fim))


def _criar_consultas(db: Session, rng: random.Random, profissionais, pacientes, recepcao):
    agora = agora_utc()
    hoje = hoje_local()
    ocupacao: dict[int, list[tuple[datetime, datetime]]] = {p.id: [] for p in pacientes}
    futuras = {p.id: 0 for p in pacientes}
    faltas = {p.id: 0 for p in pacientes}

    def livre_para(paciente, inicio, fim):
        return all(not (inicio < f and i < fim) for i, f in ocupacao[paciente.id])

    # futuras: a partir dos horários livres reais dos próximos 14 dias
    agendas = carregar_dados_agenda(db, [p.id for p in profissionais], hoje, hoje + timedelta(days=14))
    for prof in profissionais:
        tipo = prof.especialidades[0].tipos[0]
        horarios = list(gerar_horarios(agendas[prof.id], tipo.duracao_min, hoje, hoje + timedelta(days=14), agora))
        for h in rng.sample(horarios, min(len(horarios), 3)):
            candidatos = [p for p in pacientes if futuras[p.id] < 2 and livre_para(p, h.inicio, h.fim)]
            if prof.usuario_id and futuras[pacientes[0].id] < 2 and livre_para(pacientes[0], h.inicio, h.fim):
                candidatos = [pacientes[0]]
            paciente = rng.choice(candidatos)
            consulta = Consulta(paciente_id=paciente.id, profissional_id=prof.id, unidade_id=h.unidade_id,
                                tipo_consulta_id=tipo.id, inicio=h.inicio, fim=h.fim, status="marcada",
                                preco_centavos=tipo.preco_centavos, criado_por_id=paciente.id)
            db.add(consulta)
            db.flush()
            _registrar(db, consulta, paciente, agora - timedelta(days=rng.randint(1, 10)))
            ocupacao[paciente.id].append((h.inicio, h.fim))
            futuras[paciente.id] += 1

    # passadas: nos dias de grade dos últimos 30 dias
    for prof in profissionais:
        tipo = prof.especialidades[0].tipos[0]
        grade = profissional_grade(db, prof.id)
        for _ in range(4):
            if not grade:
                break
            faixa = rng.choice(grade)
            dias_atras = rng.randint(1, 30)
            dia = hoje - timedelta(days=dias_atras)
            while dia.weekday() != faixa.dia_semana:
                dia -= timedelta(days=1)
            inicio = datetime.combine(dia, faixa.hora_inicio, FUSO_LOCAL) + timedelta(
                minutes=tipo.duracao_min * rng.randint(0, 3)
            )
            fim = inicio + timedelta(minutes=tipo.duracao_min)
            sorteio = rng.random()
            status = "realizada" if sorteio < 0.8 else ("cancelada_paciente" if sorteio < 0.9 else "faltou")
            candidatos = [p for p in pacientes if livre_para(p, inicio, fim)]
            if status == "faltou":
                candidatos = [p for p in candidatos if faltas[p.id] == 0]
            paciente = rng.choice(candidatos)
            ocupados_prof = db.scalar(select(Consulta.id).where(Consulta.profissional_id == prof.id,
                                                                Consulta.inicio == inicio))
            if ocupados_prof:
                continue
            consulta = Consulta(paciente_id=paciente.id, profissional_id=prof.id, unidade_id=faixa.unidade_id,
                                tipo_consulta_id=tipo.id, inicio=inicio, fim=fim, status=status,
                                preco_centavos=tipo.preco_centavos, criado_por_id=recepcao.id)
            db.add(consulta)
            db.flush()
            _registrar(db, consulta, recepcao, inicio - timedelta(days=7))
            ocupacao[paciente.id].append((inicio, fim))
            faltas[paciente.id] += status == "faltou"


def popular(db: Session, semente: int = 42) -> bool:
    """Cria os dados de demonstração. Devolve False se já existiam."""
    dados = json.loads(ARQUIVO.read_text(encoding="utf-8"))
    admin_email = next(u["email"] for u in dados["usuarios_demo"] if u["perfil"] == "admin")
    if db.scalar(select(Usuario.id).where(Usuario.email == admin_email)):
        return False
    rng = random.Random(semente)
    unidades, especialidades = _criar_cadastros(db, dados, rng)
    demo, pacientes = _criar_usuarios(db, dados, rng)
    profissionais = _criar_profissionais(db, dados, rng, unidades, especialidades, demo["profissional"])
    _criar_consultas(db, rng, profissionais, pacientes, demo["recepcao"])
    db.commit()
    return True


def main() -> None:
    with SessionLocal() as db:
        print("Dados de demonstração criados." if popular(db) else "Dados de demonstração já existem; nada a fazer.")


if __name__ == "__main__":
    main()
