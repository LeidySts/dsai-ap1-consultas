"""Spec: cadastro-e-login — cadastro de paciente."""
import pytest

from app.auth.models import Usuario
from app.auth.service import cpf_valido

CPF_OK = "529.982.247-25"


def dados(**extra):
    base = {
        "nome": "Maria Silva",
        "email": "maria@teste.com",
        "cpf": CPF_OK,
        "data_nascimento": "1990-05-10",
        "telefone": "91988887777",
        "senha": "segura123",
    }
    return {**base, **extra}


def test_paciente_se_cadastra_com_todos_os_campos(client, db):
    r = client.post("/api/auth/cadastro", json=dados())
    assert r.status_code == 201
    assert r.json()["perfil"] == "paciente"
    usuario = db.query(Usuario).one()
    assert usuario.cpf == "52998224725"
    assert str(usuario.data_nascimento) == "1990-05-10"


@pytest.mark.parametrize("campo", ["nome", "email", "cpf", "data_nascimento", "telefone", "senha"])
def test_campos_obrigatorios(client, campo):
    corpo = dados()
    del corpo[campo]
    assert client.post("/api/auth/cadastro", json=corpo).status_code == 422


def test_email_unico(client):
    client.post("/api/auth/cadastro", json=dados())
    r = client.post("/api/auth/cadastro", json=dados(cpf="111.444.777-35", email="MARIA@teste.com"))
    assert r.status_code == 409
    assert r.json()["detail"] == "Este e-mail já está cadastrado."


def test_cpf_unico(client):
    client.post("/api/auth/cadastro", json=dados())
    r = client.post("/api/auth/cadastro", json=dados(email="outra@teste.com"))
    assert r.status_code == 409
    assert r.json()["detail"] == "Este CPF já está cadastrado."


def test_cpf_com_digito_verificador_errado_e_recusado(client):
    r = client.post("/api/auth/cadastro", json=dados(cpf="529.982.247-26"))
    assert r.status_code == 422
    assert r.json()["detail"] == "CPF inválido."


@pytest.mark.parametrize("cpf,valido", [("52998224725", True), ("11144477735", True), ("11111111111", False), ("123", False)])
def test_validacao_de_cpf(cpf, valido):
    assert cpf_valido(cpf) is valido


@pytest.mark.parametrize("senha", ["curta1", "somenteletras", "1234567890"])
def test_senha_fraca_e_recusada(client, senha):
    r = client.post("/api/auth/cadastro", json=dados(senha=senha))
    assert r.status_code == 422
    assert "mínimo 8 caracteres" in r.json()["detail"]


def test_senha_guardada_com_hash_bcrypt(client, db):
    client.post("/api/auth/cadastro", json=dados())
    usuario = db.query(Usuario).one()
    assert usuario.senha_hash != "segura123"
    assert usuario.senha_hash.startswith("$2")
