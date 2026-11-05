"""Foto principal da arena: validação, padronização e exibição."""

import io

import pytest
from PIL import Image

from app.config import get_settings


@pytest.fixture(autouse=True)
def pasta_temporaria(tmp_path, monkeypatch):
    monkeypatch.setenv("FOTOS_DIR", str(tmp_path))
    get_settings.cache_clear()
    yield tmp_path
    get_settings.cache_clear()


def _imagem(largura=2000, altura=1500, formato="JPEG", exif_gps=False) -> bytes:
    img = Image.new("RGB", (largura, altura), (30, 140, 60))
    buf = io.BytesIO()
    extra = {}
    if exif_gps:
        exif = Image.Exif()
        exif[0x8825] = {1: "S", 2: (28.0, 40.0, 0.0)}  # GPSInfo
        extra["exif"] = exif
    img.save(buf, formato, **extra)
    return buf.getvalue()


def _enviar(cliente, arena_id, conteudo, foco="centro", nome="foto.jpg"):
    return cliente.put(f"/api/v1/arenas/{arena_id}/foto", files={"foto": (nome, conteudo)}, data={"foco": foco})


def test_foto_padronizada_em_16x9_nas_duas_larguras(cenario, pasta_temporaria):
    r = _enviar(cenario["dono"], cenario["arena"]["id"], _imagem(3000, 4000))  # foto em pé, de celular
    assert r.status_code == 200, r.text
    url = r.json()["foto_url"]
    nome = url.rsplit("/", 1)[1].removesuffix("-1600.webp")
    for largura in (1600, 800):
        with Image.open(pasta_temporaria / f"{nome}-{largura}.webp") as img:
            assert img.format == "WEBP"
            assert img.size == (largura, largura * 9 // 16)


def test_remove_localizacao_gps(cenario, pasta_temporaria):
    _enviar(cenario["dono"], cenario["arena"]["id"], _imagem(exif_gps=True))
    arquivo = next(pasta_temporaria.glob("*-1600.webp"))
    with Image.open(arquivo) as img:
        assert 0x8825 not in img.getexif()


def test_so_o_dono_envia(cenario):
    assert _enviar(cenario["gabriel"], cenario["arena"]["id"], _imagem()).status_code == 403


@pytest.mark.parametrize("conteudo, trecho", [
    (b"isto nao e uma imagem", "não é uma foto válida"),
    (_imagem(600, 400), "pequena demais"),
    (_imagem(formato="GIF"), "Formato não aceito"),
    (b"", "Escolha uma foto"),
])
def test_recusa_arquivos_invalidos(cenario, conteudo, trecho):
    r = _enviar(cenario["dono"], cenario["arena"]["id"], conteudo)
    assert r.status_code == 422
    assert trecho in r.json()["detail"]


def test_recusa_acima_de_8mb(cenario, monkeypatch):
    from app.services import fotos
    monkeypatch.setattr(fotos, "TAMANHO_MAXIMO", 1000)
    r = _enviar(cenario["dono"], cenario["arena"]["id"], _imagem())
    assert r.status_code == 422 and "8 MB" in r.json()["detail"]


def test_trocar_apaga_a_antiga_e_remover_limpa(cenario, pasta_temporaria):
    dono, aid = cenario["dono"], cenario["arena"]["id"]
    _enviar(dono, aid, _imagem())
    primeira = sorted(p.name for p in pasta_temporaria.iterdir())
    _enviar(dono, aid, _imagem())
    segunda = sorted(p.name for p in pasta_temporaria.iterdir())
    assert len(segunda) == 2 and not set(primeira) & set(segunda)
    assert dono.delete(f"/api/v1/arenas/{aid}/foto").status_code == 204
    assert list(pasta_temporaria.iterdir()) == []
    assert dono.get(f"/api/v1/arenas/{aid}").json()["foto_url"] is None


def test_foto_aparece_no_quadro_grande_com_o_foco(cenario, cliente):
    aid = cenario["arena"]["id"]
    r = cenario["dono"].post(f"/arenas/{aid}/foto", files={"foto": ("campo.jpg", _imagem())}, data={"foco": "base"})
    assert "Foto atualizada" in r.text
    inicio = cliente.get("/").text
    assert 'class="vitrine-slide com-foto"' in inicio
    assert "--foco: 100%" in inicio and "-800.webp 800w" in inicio
    assert 'class="capa-arena"' in cliente.get(f"/arenas/{aid}").text


def test_mudar_so_o_enquadramento(cenario, db):
    aid = cenario["arena"]["id"]
    dono = cenario["dono"]
    dono.post(f"/arenas/{aid}/foto", files={"foto": ("campo.jpg", _imagem())})
    r = dono.post(f"/arenas/{aid}/foto", data={"foco": "topo"})
    assert "Enquadramento atualizado" in r.text
    assert "--foco: 0%" in r.text
