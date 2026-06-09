"""Hermes + CrewAI orchestration script for CoolAppAI.

This script implements three agent profiles (Orquestador, UI Specialist, Developer)
and listens to a Redis queue to trigger repository cloning, railway.json writes
and automated PR creation.
"""

import os
import json
import time
import requests
import subprocess
from typing import Optional

import redis


def clonar_repositorio(repo_url, local_path):
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN no está establecido en el entorno")
    authenticated_url = repo_url.replace("https://", f"https://x-access-token:{token}@")
    return os.system(f"git clone {authenticated_url} {local_path}")


def escribir_railway_json(service_name, dockerfile_path, volume_name, volume_destination, output_dir):
    template = {
        "$schema": "https://railway.app/railway.schema.json",
        "services": {
            service_name: {
                "build": {"dockerfile": dockerfile_path},
                "watchPatterns": ["./**/*.py", "./requirements.txt"],
                "volumes": [{"source": volume_name, "destination": f"/app/{volume_destination}"}],
            }
        },
    }
    os.makedirs(output_dir, exist_ok=True)
    with open(os.path.join(output_dir, "railway.json"), "w") as f:
        json.dump(template, f, indent=2)


def consolidar_y_solicitar_pr(local_path, branch_name, commit_message, title_pr, repo_target):
    current_dir = os.getcwd()
    os.chdir(local_path)
    os.system(f"git checkout -b {branch_name}")
    os.system("git add .")
    os.system(f'git commit -m "{commit_message}"')
    os.system(f"git push origin {branch_name}")
    os.chdir(current_dir)

    url = f"https://api.github.com/repos/{repo_target}/pulls"
    headers = {
        "Authorization": f"token {os.getenv('GITHUB_TOKEN')}",
        "Accept": "application/vnd.github.v3+json",
    }
    data = {"title": title_pr, "head": branch_name, "base": "main"}
    return requests.post(url, json=data, headers=headers)


class DesarrolladorAgent:
    def __init__(self, workspace: str = "/app/hermes_storage/workspace"):
        self.workspace = workspace
        os.makedirs(self.workspace, exist_ok=True)

    def preparar_repositorio(self, repo_url: str, name: Optional[str] = None):
        name = name or repo_url.rstrip("/\n").split("/")[-1].replace(".git", "")
        local_path = os.path.join(self.workspace, name)
        if os.path.exists(local_path):
            subprocess.run(["git", "-C", local_path, "pull"], check=False)
        else:
            clonar_repositorio(repo_url, local_path)

        # Instalar dependencias si existe requirements.txt o pyproject
        req_txt = os.path.join(local_path, "requirements.txt")
        pyproject = os.path.join(local_path, "pyproject.toml")
        if os.path.exists(req_txt):
            cmd = ["pip", "install", "-r", req_txt]
            subprocess.run(cmd, check=False)
        elif os.path.exists(pyproject):
            cmd = ["pip", "install", "."]
            subprocess.run(cmd, cwd=local_path, check=False)


class UIEspecialista:
    def disenar_ui(self, spec: dict) -> dict:
        # Construye sugerencias de UI para el diseñador Marimo basadas en la spec
        # Devuelve metadatos que el desarrollador puede usar (p.ej. nombre de servicio y puerto)
        ui_meta = {"title": f"UI para {spec.get('service', 'unknown')}", "port": spec.get("port", 8080)}
        return ui_meta


class Orquestador:
    def __init__(self, redis_url: str = "redis://redis:6379/0"):
        self.r = redis.from_url(redis_url)
        self.dev = DesarrolladorAgent()
        self.ui = UIEspecialista()

    def loop(self):
        # Escucha la cola 'cola_orquestador_maestro' y procesa mensajes
        while True:
            item = self.r.brpop("cola_orquestador_maestro", timeout=5)
            if not item:
                time.sleep(1)
                continue

            _, payload = item
            try:
                data = json.loads(payload)
            except Exception:
                continue

            repo = data.get("repo_url")
            service_name = data.get("service_name", "hermes-framework")
            dockerfile = data.get("dockerfile", "Dockerfile.hermes")
            volume = data.get("volume", "hermes_storage")
            volume_dest = data.get("volume_dest", "hermes_storage")
            target_repo = data.get("repo_target")

            # 1) Clonar y preparar repo
            self.dev.preparar_repositorio(repo)

            # 2) Solicitar diseño UI
            ui_meta = self.ui.disenar_ui({"service": service_name, "port": data.get("port", 8000)})

            # 3) Escribir railway.json en subcarpeta del repo clonado
            local_name = repo.rstrip("/\n").split("/")[-1].replace(".git", "")
            out_dir = os.path.join(self.dev.workspace, local_name)
            escribir_railway_json(service_name, dockerfile, volume, volume_dest, out_dir)

            # 4) Consolidar cambios y solicitar PR
            branch = f"autodeploy/{service_name}"
            commit_msg = "Add railway.json for automated deployment"
            title = f"Automated: add railway for {service_name}"
            if target_repo:
                consolidar_y_solicitar_pr(out_dir, branch, commit_msg, title, target_repo)


def main():
    orchestrator = Orquestador(redis_url=os.getenv("REDIS_URL", "redis://redis:6379/0"))
    orchestrator.loop()


if __name__ == "__main__":
    main()
