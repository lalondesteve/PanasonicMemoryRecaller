import asyncio
from json import loads

from sanic import Request, Sanic, Websocket, response
from .component import (
    get_html,
    get_index,
    projector_card,
    edit_card,
    add_projector_button,
)
from htpy import div
from .models import PanasonicProjector
from tortoise import Tortoise
from .memory import recall_memory, power_on, power_off

WSCLIENTS: set[asyncio.Queue] = set()


def create_app():
    app = Sanic("PanasonicMemoryRecaller")
    app.static("/static/", "static/")

    @app.listener("before_server_start")
    async def init_orm(_):
        await Tortoise.init(
            db_url="sqlite://db/db.sqlite3", modules={"models": ["app.models"]}
        )
        await Tortoise.generate_schemas()

    @app.signal("ws.broadcast.message")
    async def ws_broadcast(message):
        print("signal received", message)
        if message == "last_message":
            projectors = await PanasonicProjector.all()
            message = str(
                div("#cards", hx_swap_oob="true")[
                    (projector_card(projector) for projector in projectors)
                ]
            )
        for queue in WSCLIENTS:
            queue.put_nowait(message)

    @app.get("/")
    async def index(_):
        return response.html(str(get_html(get_index())))

    async def ws_receive_loop(ws: Websocket) -> None:
        while True:
            data = await ws.recv()
            if data:
                await ws_broadcast(loads(data))
            await asyncio.sleep(0.01)

    @app.websocket("/ws")
    async def ws_connect(request, ws: Websocket):
        queue = asyncio.Queue()
        WSCLIENTS.add(queue)
        task_name = f"receiver:{request.id}"
        request.app.add_task(ws_receive_loop(ws), name=task_name)
        await ws.send(str(div("#test-swap", hx_swap_oob="true")["You got swapped"]))
        try:
            while True:
                message = await queue.get()
                await ws.send(message)
        finally:
            await request.app.cancel_task(task_name)
            request.app.purge_tasks()

    @app.route("/projectors", methods=["get", "post"])
    async def get_post_projectors(request: Request):
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

    @app.get("/projectors/power-on")
    async def get_power_on(request: Request):
        projectors = await PanasonicProjector.all()
        for projector in projectors:
            await power_on(projector=projector, request=request)
        return response.HTTPResponse(status=204)

    @app.get("/projectors/power-off")
    async def get_power_off(request: Request):
        projectors = await PanasonicProjector.all()
        for projector in projectors:
            await power_off(projector=projector, request=request)
        return response.HTTPResponse(status=204)

    @app.get("/projectors/recall/<mem>")
    async def recall_all(request: Request, mem: int):
        projectors = await PanasonicProjector.all()
        for projector in projectors:
            await recall_memory(mem, projector=projector, request=request)
        return response.HTTPResponse(status=204)

    @app.post("/projector/recall")
    async def memory(request: Request):
        if data := request.form:
            _id = data.get("id")
            mem = data.get("memory")
            if _id and mem:
                projector = await PanasonicProjector.get(id=data.get("id"))
                await recall_memory(int(mem), projector=projector, request=request)

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
