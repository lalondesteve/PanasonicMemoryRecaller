from sanic import Request, Sanic, response
from .component import (
    get_edit,
    get_html,
    get_index,
    projector_card,
    edit_card,
    add_projector_button,
)
from htpy import div
from .models import PanasonicProjector
from tortoise import Tortoise
from .memory import recall_memory


def create_app():
    app = Sanic("PanasonicMemoryRecaller")

    # app.static("/", "static/index.html", name="index")
    app.static("/static/", "static/")

    @app.listener("before_server_start")
    async def init_orm(_):
        await Tortoise.init(
            db_url="sqlite://db/db.sqlite3", modules={"models": ["app.models"]}
        )
        await Tortoise.generate_schemas()

    @app.signal("ws.update.last_message")
    async def update_projector_message(context):
        print(context)

    @app.get("/")
    async def index(_):
        return response.html(str(get_html(get_index())))

    @app.get("/edit")
    async def edit(_):
        return response.html(str(get_html(get_edit())))

    @app.route("/projectors", methods=["get", "post"])
    async def projectors(request: Request):
        if request.method == "POST":
            data = request.form
            if data:
                p = await PanasonicProjector.get(id=data.get("id"))
                p.name = str(data.get("name"))
                p.ip = str(data.get("ip"))
                await p.save()

        projectors = await PanasonicProjector.all()
        return response.html(
            str(div("#cards")[(projector_card(projector) for projector in projectors)])
        )

    @app.post("/projector/recall")
    async def mem(request: Request):
        data = request.form
        if data:
            projector = await PanasonicProjector.get(id=data.get("id"))
            mem = int(data.get("memory"))
            if mem and isinstance(mem, int):
                await recall_memory(mem, projector=projector, request=request)

        return response.HTTPResponse(status=204)

    @app.route("/projector-edit", methods=["get", "post", "delete"])
    async def projector_edit(request: Request):
        if request.method == "POST":
            await PanasonicProjector.create()
        elif request.method == "DELETE":
            id = request.args.get("id")
            p = await PanasonicProjector.get(id=id)
            await p.delete()

        projectors = await PanasonicProjector.all()
        page = div("#edit")[
            add_projector_button(), (edit_card(vp) for vp in projectors)
        ]
        return response.html(str(page))

    return app
