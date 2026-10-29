"""Ponto de entrada da aplicação: `uvicorn app.main:app`."""

from pathlib import Path
from urllib.parse import quote

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.api.routes import router as api_router
from app.config import get_settings
from app.errors import ErroDominio, NaoAutenticado
from app.web.routes import router as web_router

BASE = Path(__file__).parent


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="2.0.0",
        description="Agendamento de partidas de futebol suíço: times, arenas, partidas e classificação.",
        debug=settings.debug,
    )
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.secret_key,
        session_cookie="partidas_sessao",
        same_site="lax",
        https_only=settings.cookie_seguro,
        max_age=60 * 60 * 24 * 14,
    )
    app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")
    app.include_router(api_router)
    app.include_router(web_router)

    @app.exception_handler(ErroDominio)
    async def erro_dominio(request: Request, exc: ErroDominio):
        if request.url.path.startswith("/api/"):
            return JSONResponse({"detail": exc.mensagem}, status_code=exc.status_code)
        if isinstance(exc, NaoAutenticado):
            destino = request.url.path if request.method == "GET" else "/"
            return RedirectResponse(f"/entrar?proximo={quote(destino)}", status_code=303)
        # Nas telas, erros que escaparam das rotas viram aviso e voltam para a página anterior.
        request.session.setdefault("avisos", []).append(["erro", exc.mensagem])
        voltar = request.headers.get("referer") or "/"
        return RedirectResponse(voltar, status_code=303)

    @app.get("/saude", include_in_schema=False)
    def saude():
        return {"status": "ok"}

    return app


app = create_app()
