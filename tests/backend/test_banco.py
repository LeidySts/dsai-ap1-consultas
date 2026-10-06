from sqlalchemy import text


def test_banco_de_teste_e_postgresql(db):
    assert "PostgreSQL" in db.execute(text("select version()")).scalar_one()
