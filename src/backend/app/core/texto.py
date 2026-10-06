import unicodedata


def normalizar(texto: str) -> str:
    """Minúsculas e sem acentos, para busca ("João" -> "joao")."""
    sem_acento = unicodedata.normalize("NFKD", texto or "").encode("ascii", "ignore").decode()
    return " ".join(sem_acento.lower().split())
