"""
CoolAppAI Marimo frontend — UI reactiva siguiendo la guía de estilo.
"""
try:
    import marimo as mo
except Exception:
    # Stub mínimo para edición y pruebas fuera del entorno Marimo
    class _State:
        def __init__(self, v=None):
            self.value = v

        def set(self, v):
            self.value = v

    class _UI:
        @staticmethod
        def div(*a, **k):
            return ""

        @staticmethod
        def h1(t, **k):
            return ""

        @staticmethod
        def button(t, **k):
            return ""

        @staticmethod
        def iframe(src="", **k):
            return f"<iframe src='{src}'></iframe>"

    mo = type(
    "M",
    (),
    {
        "state": lambda v=None: _State(v),
        "ui": _UI(),
        "run": lambda ui, **kw: print("Marimo stub run"),
    },
)

SELECTED = mo.state(None)

SERVICES = [
    {"name": "PocketBase", "alias": "pocketbase", "port": 8090},
    {"name": "Valkey", "alias": "valkey", "port": 8080},
    {"name": "Hermes Framework", "alias": "hermes-framework", "port": 8000},
]


def select_service(alias: str, port: int):
    # Guardar como alias:port
    SELECTED.set(f"{alias}:{port}")


def render_service_card(svc):
    # Estilos siguiendo la guía (fondo antracita, acento verde al seleccionar)
    is_active = False
    if SELECTED.value and isinstance(SELECTED.value, str):
        is_active = SELECTED.value.startswith(svc["alias"] + ":")

    border = "1px solid #222428"
    if is_active:
        border = "2px solid #00FF66"

    return mo.ui.div(
        mo.ui.h1(svc["name"], style={"color": "#FFFFFF"}),
        mo.ui.button("Abrir", _onclick=lambda: select_service(svc["alias"], svc["port"])),
        style={
            "background": "#1A1B26",
            "border": border,
            "padding": "12px",
            "borderRadius": "8px",
            "width": "220px",
            "margin": "8px",
        },
    )


def mock_log_stream(callback):
    # Simula un flujo de logs; en producción esto consumiría mensajes de Valkey/Redis
    import threading
    import time

    def worker():
        i = 0
        while True:
            i += 1
            msg = f"[valkey] queue-status: pending={i % 5} running={(i % 3)}"
            callback(msg)
            time.sleep(3)

    t = threading.Thread(target=worker, daemon=True)
    t.start()


def build_ui():
    font_family = (
        "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
    )
    mono_family = "ui-monospace, SFMono-Regular, Consolas, 'Liberation Mono', Menlo, monospace"

    header = mo.ui.div(
        mo.ui.h1(
            "CoolAppAI",
            style={
                "fontFamily": font_family,
                "color": "#FFFFFF",
                "margin": "0",
            },
        ),
        style={
            "background": "#12131C",
            "padding": "18px 24px",
            "borderBottom": "1px solid #17171C",
        },
    )

    # Left sidebar with services and clusters
    service_cards = [render_service_card(s) for s in SERVICES]
    clusters = [
        "CSP (Coolify Studio Production)",
        "CSStaging (Coolify Studio Staging)",
        "CAP (Coolify Agent Production)",
        "CAS (Coolify Agent Staging)",
    ]
    cluster_items = [
        mo.ui.div(c, style={"color": "#A9B2C3", "marginBottom": "6px"}) for c in clusters
    ]
    cluster_list = mo.ui.div(*cluster_items, style={"marginTop": "12px"})

    sidebar = mo.ui.div(
        mo.ui.h1("Infra Core", style={"color": "#00FF66"}),
        *service_cards,
        mo.ui.h1("Clusters", style={"color": "#00FF66", "marginTop": "12px"}),
        cluster_list,
        style={"width": "260px", "padding": "18px", "background": "#12131C", "borderRight": "1px solid #17171C"},
    )

    # Central area with iframe (reactive to SELECTED)
    if SELECTED.value:
        parts = SELECTED.value.split(":")
        alias = parts[0]
        port = parts[1] if len(parts) > 1 else "80"
        iframe_src = f"http://{alias}:{port}"
        iframe_el = mo.ui.iframe(src=iframe_src, width="100%", height="600px")
    else:
        iframe_el = mo.ui.div(
            "Seleccione un servicio en el panel izquierdo.", style={"color": "#A9B2C3", "padding": "24px"}
        )

    # Terminal logs (mocked)
    logs = []

    def append_log(msg):
        logs.append(msg)

    mock_log_stream(append_log)

    log_block = mo.ui.div(
        "\n".join(logs),
        style={
            "fontFamily": mono_family,
            "color": "#A9B2C3",
            "padding": "12px",
            "background": "#0F1014",
            "height": "120px",
            "overflow": "auto",
        },
    )

    log_view = mo.ui.div(mo.ui.h1("Logs", style={"color": "#FFFFFF"}), log_block)

    main_area = mo.ui.div(iframe_el, log_view, style={"flex": "1", "padding": "18px"})

    layout = mo.ui.div(
        header,
        mo.ui.div(sidebar, main_area, style={"display": "flex", "minHeight": "calc(100vh - 72px)"}),
        style={"background": "#12131C", "minHeight": "100vh"},
    )

    return layout


if __name__ == "__main__":
    ui = build_ui()
    try:
        mo.run(ui, host="0.0.0.0", port=2718)
    except Exception:
        print("Marimo no disponible; UI renderizada estáticamente.")
        print(ui)
