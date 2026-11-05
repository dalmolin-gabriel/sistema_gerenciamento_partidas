"""Foto principal da arena.

Toda foto enviada é padronizada para 16:9 e salva em duas larguras (1600 e 800 px) em WebP.
Na tela, o navegador escolhe a versão certa e ajusta o corte ao tamanho do card
(object-fit: cover), respeitando o ponto de foco escolhido pelo dono.
"""

import io
import secrets
import warnings
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.errors import RegraNegocio
from app.models import Arena, Usuario
from app.services import arenas as arenas_service

TAMANHO_MAXIMO = 8 * 1024 * 1024           # 8 MB
LARGURAS = (1600, 800)
PROPORCAO = (16, 9)
MINIMO = (800, 450)                        # menor que isso fica borrado no card
FORMATOS_ACEITOS = {"JPEG", "PNG", "WEBP"}
FOCOS = {"topo": 0, "centro": 50, "base": 100}
Image.MAX_IMAGE_PIXELS = 50_000_000        # barra "bombas" de descompressão


def pasta_fotos() -> Path:
    pasta = Path(get_settings().fotos_dir)
    pasta.mkdir(parents=True, exist_ok=True)
    return pasta


def _abrir(conteudo: bytes) -> Image.Image:
    if not conteudo:
        raise RegraNegocio("Escolha uma foto para enviar.")
    if len(conteudo) > TAMANHO_MAXIMO:
        raise RegraNegocio("A foto passa de 8 MB. Envie uma versão menor.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            img = Image.open(io.BytesIO(conteudo))
            formato = img.format
            img.load()
    except (UnidentifiedImageError, Image.DecompressionBombError, Image.DecompressionBombWarning, OSError):
        raise RegraNegocio("Esse arquivo não é uma foto válida. Use JPG, PNG ou WebP.")
    if formato not in FORMATOS_ACEITOS:
        raise RegraNegocio("Formato não aceito. Use JPG, PNG ou WebP.")
    # Fotos de celular vêm "deitadas" com a rotação no EXIF: aplica antes de cortar.
    img = ImageOps.exif_transpose(img)
    if img.width < MINIMO[0] or img.height < MINIMO[1]:
        raise RegraNegocio(f"A foto é pequena demais ({img.width}×{img.height}). Use pelo menos 1600 px de largura.")
    return img.convert("RGB")


def _apagar_arquivos(nome: str | None) -> None:
    if nome:
        for largura in LARGURAS:
            (pasta_fotos() / f"{nome}-{largura}.webp").unlink(missing_ok=True)


def salvar(db: Session, usuario: Usuario, arena_id: int, conteudo: bytes, foco: str = "centro") -> Arena:
    arena = arenas_service.obter(db, arena_id)
    arenas_service._garantir_dono(arena, usuario)
    img = _abrir(conteudo)
    foco_pct = FOCOS.get(foco, 50)

    # Nome novo a cada envio: o navegador não fica mostrando a foto antiga do cache.
    nome = f"arena-{arena.id}-{secrets.token_hex(4)}"
    pasta = pasta_fotos()
    for largura in LARGURAS:
        altura = largura * PROPORCAO[1] // PROPORCAO[0]
        corte = ImageOps.fit(img, (largura, altura), method=Image.Resampling.LANCZOS,
                             centering=(0.5, foco_pct / 100))
        # Salvar sem passar exif= descarta os metadados (inclusive a localização GPS).
        corte.save(pasta / f"{nome}-{largura}.webp", "WEBP", quality=80, method=4)

    antiga = arena.foto
    arena.foto, arena.foto_foco = nome, foco_pct
    db.commit()
    _apagar_arquivos(antiga)
    return arena


def definir_foco(db: Session, usuario: Usuario, arena_id: int, foco: str) -> Arena:
    arena = arenas_service.obter(db, arena_id)
    arenas_service._garantir_dono(arena, usuario)
    if foco not in FOCOS:
        raise RegraNegocio("Escolha topo, centro ou base.")
    arena.foto_foco = FOCOS[foco]
    db.commit()
    return arena


def remover(db: Session, usuario: Usuario, arena_id: int) -> Arena:
    arena = arenas_service.obter(db, arena_id)
    arenas_service._garantir_dono(arena, usuario)
    antiga, arena.foto, arena.foto_foco = arena.foto, None, 50
    db.commit()
    _apagar_arquivos(antiga)
    return arena
