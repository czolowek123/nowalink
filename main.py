from aiohttp import web, WSMsgType
from pathlib import Path
import json

BASE_DIR = Path(__file__).parent
rooms = {}


async def index(request):
    return web.FileResponse(BASE_DIR / "index.html")


async def websocket(request):
    room_id = request.match_info["room"]

    ws = web.WebSocketResponse()
    await ws.prepare(request)

    users = rooms.setdefault(room_id, set())

    # В комнате разрешены только два пользователя
    if len(users) >= 2:
        await ws.send_json({
            "type": "full",
            "message": "Комната уже занята двумя пользователями"
        })
        await ws.close()
        return ws

    users.add(ws)

    # Сообщаем первому пользователю, что второй вошёл
    if len(users) == 2:
        for user in users:
            if user != ws and not user.closed:
                await user.send_json({
                    "type": "joined"
                })

    try:
        async for message in ws:

            if message.type == WSMsgType.TEXT:
                try:
                    data = json.loads(message.data)
                except json.JSONDecodeError:
                    continue

                # Передача WebRTC-сигналов второму пользователю
                if data.get("type") == "signal":
                    for user in users:
                        if user != ws and not user.closed:
                            await user.send_json({
                                "type": "signal",
                                "data": data.get("data")
                            })

            elif message.type == WSMsgType.ERROR:
                print("Ошибка WebSocket:", ws.exception())

    finally:
        users.discard(ws)

        if not users:
            rooms.pop(room_id, None)

    return ws


app = web.Application()

app.router.add_get("/", index)
app.router.add_get("/ws/{room}", websocket)

if __name__ == "__main__":
    print("NovaLink запущен")
    print("Открой в браузере: http://localhost:8080")

    web.run_app(
        app,
        host="0.0.0.0",
        port=8080
    )
