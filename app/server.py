from sanic import Request, Sanic, response
from .component import projector_card, edit_card, add_projector_button
from htpy import div, span
from dataclasses import dataclass


@dataclass
class PJ:
    id: int
    ip: str
    name: str
    last_message: str = "No message yet"


vp1 = PJ(id=1, ip="192.168.101.21", name="vp1")


def create_app():
    app = Sanic("PanasonicMemoryRecaller")

    app.static("/", "static/index.html", name="index")
    app.static("/static/", "static/")

    @app.get("/projectors")
    async def get_projectors(request: Request):
        projectors = [vp1]
        return response.html(
            span[(projector_card(projector) for projector in projectors)]
        )

    @app.get("/edit")
    async def edit(_):
        projectors = [vp1]
        page = div[add_projector_button(), (edit_card(vp) for vp in projectors)]
        return response.html(page)

    @app.get("/projector/add")
    async def add_projector(request: Request):
        return edit(request)

    return app
