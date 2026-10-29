"""Erros de domínio. A camada web/API traduz cada um para o status HTTP adequado."""


class ErroDominio(Exception):
    status_code = 400

    def __init__(self, mensagem: str):
        super().__init__(mensagem)
        self.mensagem = mensagem


class RegraNegocio(ErroDominio):
    status_code = 422


class Conflito(ErroDominio):
    status_code = 409


class NaoEncontrado(ErroDominio):
    status_code = 404


class SemPermissao(ErroDominio):
    status_code = 403


class NaoAutenticado(ErroDominio):
    status_code = 401
