import os
import sys
import threading
import time
from typing import Any, cast

# Ensure the local Marimo package in marimo-env is importable when running from
# the monorepo root.
ROOT_DIR = os.path.dirname(__file__)
LOCAL_MARIMO_PATH = os.path.join(ROOT_DIR, "marimo-env")
if LOCAL_MARIMO_PATH not in sys.path:
    sys.path.insert(0, LOCAL_MARIMO_PATH)

import marimo as mo

COLOR_BACKGROUND = "#12131C"
COLOR_SURFACE = "#1A1B26"
COLOR_ACCENT = "#00FF66"
COLOR_TEXT = "#FFFFFF"
COLOR_SECONDARY = "#A9B2C3"
COLOR_BORDER = "#222428"

SERVICES = [
    {
        "name": "PocketBase",
        "host": "pocketbase",
        "port": 8090,
        "description": "Vault de estado, credenciales cifradas y tokens GitHub.",
    },
    {
        "name": "Valkey",
        "host": "valkey",
        "port": 8080,
        "description": "Broker de memoria central para colas y flujo de mensajes.",
    },
    {
        "name": "Hermes Framework",
        "host": "hermes-framework",
        "port": 8000,
        "description": "Motor cognitivo de agentes y orquestación CrewAI.",
    },
]

SELECTED = cast(mo.State[dict], mo.state(None))
LOG_LINES = mo.state([])
STREAM_RUNNING = mo.state(False)


def append_log(message: str) -> None:
    current = LOG_LINES.value or []
    current = current[-50:]
    current.append(message)
    LOG_LINES.set(current)


def start_valkey_log_stream() -> None:
    if STREAM_RUNNING.value:
        return

    STREAM_RUNNING.set(True)

    def worker() -> None:
        counter = 0
        while True:
            counter += 1
            payload = {
                "event": "cola_orquestador_maestro",
                "pending": counter % 5,
                "running": counter % 3,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            }
            append_log(
                f"[valkey] {payload['timestamp']} - pending={payload['pending']} running={payload['running']}"
            )
            time.sleep(3)

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()


def select_service(host: str, port: int) -> None:
    SELECTED.set({"host": host, "port": port})


def render_service_card(service: dict) -> Any:
    active = SELECTED.value and SELECTED.value.get("host") == service["host"]
    return mo.ui.div(
        mo.ui.h1(service["name"], style={"color": COLOR_TEXT, "margin": "0 0 8px 0"}),
        mo.ui.div(
            service["description"],
            style={
                "color": COLOR_SECONDARY,
                "fontSize": "13px",
                "marginBottom": "12px",
            },
        ),
        mo.ui.button(
            "Abrir",
            _onclick=lambda: select_service(service["host"], service["port"]),
            style={
                "background": COLOR_ACCENT,
                "color": COLOR_BACKGROUND,
                "border": "none",
                "padding": "10px 14px",
                "borderRadius": "999px",
                "cursor": "pointer",
            },
        ),
        style={
            "background": COLOR_SURFACE,
            "border": (
                f"2px solid {COLOR_ACCENT}" if active else f"1px solid {COLOR_BORDER}"
            ),
            "borderRadius": "18px",
            "padding": "18px",
            "marginBottom": "14px",
            "width": "100%",
            "boxSizing": "border-box",
        },
    )


def build_ui() -> Any:
    start_valkey_log_stream()

    header = mo.ui.div(
        mo.ui.h1(
            "CoolAppAI", style={"color": COLOR_TEXT, "margin": "0", "fontSize": "30px"}
        ),
        mo.ui.div(
            "Factoría autónoma multi-servicio dibujada en un Canvas de control.",
            style={"color": COLOR_SECONDARY, "marginTop": "8px", "lineHeight": "1.6"},
        ),
        style={
            "padding": "24px 32px",
            "background": COLOR_BACKGROUND,
            "borderBottom": f"1px solid {COLOR_BORDER}",
        },
    )

    service_cards = [render_service_card(service) for service in SERVICES]
    cluster_summary = mo.ui.div(
        mo.ui.h1(
            "Entornos",
            style={"color": COLOR_ACCENT, "fontSize": "16px", "margin": "0 0 12px 0"},
        ),
        *[
            mo.ui.div(cluster, style={"color": COLOR_SECONDARY, "marginBottom": "8px"})
            for cluster in [
                "CSP - Coolify Studio Production",
                "CSStaging - Coolify Studio Staging",
                "CAP - Coolify Agent Production",
                "CAS - Coolify Agent Staging",
            ]
        ],
        style={"padding": "18px", "borderRadius": "18px", "background": COLOR_SURFACE},
    )

    sidebar = mo.ui.div(
        mo.ui.h1(
            "Canvas de Servicios",
            style={"color": COLOR_ACCENT, "margin": "0 0 18px 0", "fontSize": "18px"},
        ),
        *service_cards,
        cluster_summary,
        style={
            "width": "280px",
            "padding": "24px",
            "background": COLOR_BACKGROUND,
            "borderRight": f"1px solid {COLOR_BORDER}",
        },
    )

    if SELECTED.value:
        selected = SELECTED.value
        iframe_src = f"http://{selected['host']}:{selected['port']}"
        iframe_card = mo.ui.div(
            mo.ui.h1(
                f"{selected['host']}",
                style={"color": COLOR_TEXT, "margin": "0 0 12px 0"},
            ),
            mo.ui.div(
                f"Navegando en el host privado interno: {iframe_src}",
                style={"color": COLOR_SECONDARY, "marginBottom": "16px"},
            ),
            mo.ui.iframe(
                src=iframe_src,
                width="100%",
                height="620px",
                style={"border": f"1px solid {COLOR_BORDER}", "borderRadius": "16px"},
            ),
        )
    else:
        iframe_card = mo.ui.div(
            "Seleccione un servicio para abrir su panel interno.",
            style={"color": COLOR_SECONDARY, "padding": "32px", "textAlign": "center"},
        )

    logs = LOG_LINES.value or []
    log_panel = mo.ui.div(
        mo.ui.h1(
            "Terminal de Valkey", style={"color": COLOR_TEXT, "margin": "0 0 12px 0"}
        ),
        mo.ui.div(
            "\n".join(logs[-12:]),
            style={
                "background": "#0F1014",
                "color": COLOR_SECONDARY,
                "fontFamily": "ui-monospace, SFMono-Regular, Consolas, monospace",
                "padding": "16px",
                "borderRadius": "16px",
                "whiteSpace": "pre-wrap",
                "height": "180px",
                "overflow": "auto",
            },
        ),
        style={"marginTop": "20px"},
    )

    content = mo.ui.div(
        sidebar,
        mo.ui.div(
            iframe_card,
            log_panel,
            style={
                "display": "flex",
                "flexDirection": "column",
                "gap": "20px",
                "flex": "1",
                "padding": "24px",
            },
        ),
        style={"display": "flex", "minHeight": "calc(100vh - 96px)"},
    )

    return mo.ui.div(
        header, content, style={"background": COLOR_BACKGROUND, "minHeight": "100vh"}
    )


if __name__ == "__main__":
    mo.run(build_ui(), host="0.0.0.0", port=2718)
