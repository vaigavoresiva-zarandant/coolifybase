import json
import os
import requests
import redis
import subprocess
from crewai import Agent, Task, Crew, Process
from crewai.tools import tool


@tool("Herramienta de clonación de repositorios Git")
def tool_clonar_repositorio(repo_url: str, local_path: str) -> str:
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN no está establecido en el entorno")

    authenticated_url = repo_url.replace("https://", f"https://x-access-token:{token}@")
    os.makedirs(local_path, exist_ok=True)
    result = subprocess.run(
        ["git", "clone", authenticated_url, local_path],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return f"ERROR: {result.stderr.strip()}"
    return f"Repositorio clonado con código de salida: {result.returncode}"


@tool("Herramienta de escritura de infraestructura Railway")
def tool_escribir_railway_json(
    service_name: str,
    dockerfile_path: str,
    volume_name: str,
    volume_destination: str,
    output_dir: str,
) -> str:
    template = {
        "$schema": "https://railway.app/railway.schema.json",
        "services": {
            service_name: {
                "build": {"dockerfile": dockerfile_path},
                "watchPatterns": ["./**/*.py", "./requirements.txt"],
                "volumes": [
                    {"source": volume_name, "destination": f"/app/{volume_destination}"}
                ],
            }
        },
    }
    os.makedirs(output_dir, exist_ok=True)
    with open(os.path.join(output_dir, "railway.json"), "w", encoding="utf-8") as f:
        json.dump(template, f, indent=2)
    return f"Archivo railway.json guardado con éxito en {output_dir}"


@tool("Herramienta de Consolidación Git y Apertura de Pull Request")
def tool_consolidar_y_solicitar_pr(
    local_path: str,
    branch_name: str,
    commit_message: str,
    title_pr: str,
    repo_target: str,
) -> str:
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN no está establecido en el entorno")

    current_dir = os.getcwd()
    os.chdir(local_path)
    subprocess.run(["git", "checkout", "-b", branch_name], check=False)
    subprocess.run(["git", "add", "."], check=False)
    subprocess.run(["git", "commit", "-m", commit_message], check=False)
    subprocess.run(["git", "push", "origin", branch_name], check=False)
    os.chdir(current_dir)

    url = f"https://api.github.com/repos/{repo_target}/pulls"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }
    data = {
        "title": title_pr,
        "head": branch_name,
        "base": "main",
    }
    response = requests.post(url, json=data, headers=headers)
    status = response.status_code
    return f"Push ejecutado. Estado de la API de Pull Request en GitHub: {status}"


orquestador_goal = (
    "Supervisar, interceptar y validar flujos de despliegue "
    "e infraestructura automatizada para el entorno CAS."
)
orquestador_backstory = (
    "Eres el cerebro estratégico superior de CoolAppAI. "
    "Dictas las directivas de transformación arquitectónica."
)
orquestador_ceo = Agent(
    role="Orquestador Local CEO",
    goal=orquestador_goal,
    backstory=orquestador_backstory,
    verbose=True,
    allow_delegation=True,
)

ui_especialista_goal = (
    "Diseñar las interfaces frontend reactivas en Marimo aplicando "
    "estrictamente el manual estético de CoolAppAI."
)
ui_especialista_backstory = (
    "Eres el guardián visual de la factoría. Aborreces las llamadas externas "
    "y dominas las tipografías de sistema, el gris antracita y el verde eléctrico."
)
ui_especialista = Agent(
    role="UI Specialist Diseñador",
    goal=ui_especialista_goal,
    backstory=ui_especialista_backstory,
    verbose=True,
    allow_delegation=False,
)

desarrollador_goal = (
    "Ejecutar mutaciones físicas en el sistema de archivos, clonar repositorios "
    "del CAS y escribir configuraciones de Railway."
)
desarrollador_backstory = (
    "Eres la fuerza bruta de ejecución de código en CoolAppAI. Dominas Git, "
    "las APIs de GitHub y los esquemas JSON de infraestructura."
)
desarrollador_devops = Agent(
    role="Desarrollador DevOps de Código",
    goal=desarrollador_goal,
    backstory=desarrollador_backstory,
    tools=[
        tool_clonar_repositorio,
        tool_escribir_railway_json,
        tool_consolidar_y_solicitar_pr,
    ],
    verbose=True,
    allow_delegation=False,
)


def iniciar_bucle_nervioso() -> None:
    r = redis.Redis(host="valkey", port=6379, db=0)
    print("🟢 Motor Cognitivo de CoolAppAI escuchando colas en Valkey...")

    while True:
        tarea_raw = r.brpop("cola_orquestador_maestro")
        if not tarea_raw:
            continue

        _, payload = tarea_raw
        try:
            datos_tarea = json.loads(payload.decode("utf-8"))
        except (ValueError, AttributeError):
            continue

        repo_target = datos_tarea.get("repo_url")
        service_name = datos_tarea.get("service_name", "hermes-framework")
        dockerfile = datos_tarea.get("dockerfile", "Dockerfile.hermes")
        volume_name = datos_tarea.get("volume", "hermes_storage")
        volume_dest = datos_tarea.get("volume_dest", "hermes_storage")
        repo_path = os.path.join("/app/hermes_storage", f"cloned_cas_{service_name}")

        print(f"📥 Tarea recibida: repo={repo_target} service={service_name}")
        tool_clonar_repositorio(repo_target, repo_path)
        tool_escribir_railway_json(
            service_name, dockerfile, volume_name, volume_dest, repo_path
        )

        task_description = (
            f"Clona {repo_target}, genera railway.json descentralizado "
            f"y abre una PR automática para {service_name}."
        )
        task_expected = (
            "Infraestructura local modificada, archivo guardado y Pull Request "
            "abierta con éxito en GitHub."
        )
        task_infra = Task(
            description=task_description,
            expected_output=task_expected,
            agent=desarrollador_devops,
        )

        crew = Crew(
            agents=[
                orquestador_ceo,
                ui_especialista,
                desarrollador_devops,
            ],
            tasks=[task_infra],
            process=Process.sequential,
        )

        crew.kickoff()

        if repo_target:
            tool_consolidar_y_solicitar_pr(
                repo_path,
                f"autodeploy/{service_name}",
                f"Automated infra for {service_name}",
                f"Automated: add railway for {service_name}",
                repo_target,
            )

        r.lpush(
            "cola_ui_marimo",
            json.dumps(
                {
                    "status": "SUCCESS",
                    "service": service_name,
                    "repo": repo_target,
                }
            ),
        )


if __name__ == "__main__":
    iniciar_bucle_nervioso()
