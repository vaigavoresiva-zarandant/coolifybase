# Despliegue en Railway para CoolAppAI

Pasos rápidos para desplegar los servicios locales definidos en este repositorio usando los `railway.json` por carpeta.

1) Requisitos
- Tener instalado Railway CLI y autenticado (railway login).

2) Pocketbase
- Carpeta: `pocketbase-env`
- Archivo: `pocketbase-env/railway.json`
- Volumen persistente: `pb_data` -> `/app/pb_data`
- Comando: ejecutar `railway up` dentro de `pocketbase-env` o crear un nuevo proyecto y subir con `railway init`.

3) Valkey
- Carpeta: `valkey-env`
- Archivo: `valkey-env/railway.json`
- Volumen persistente: `valkey_data` -> `/app/valkey_data`

4) Hermes (Agentes)
- Carpeta: `hermes-env`
- Archivo: `hermes-env/railway.json`
- Dockerfile: `hermes-env/Dockerfile.hermes`
- Volumen persistente: `hermes_storage` -> `/app/hermes_storage`
- Si los paquetes no están en PyPI, `Dockerfile.hermes` intenta instalar desde GitHub.

5) Frontend Marimo
- Raíz: `railway.json` y `Dockerfile.marimo`.
- Construir la imagen definida en `Dockerfile.marimo` y exponer el puerto 8080.

6) Variables de entorno y secretos
- `GITHUB_TOKEN` es requerido para `hermes-env/init_agents.py` si se usa la clonación autenticada.

7) Notas y restricciones (Jun 2026)
- Nixpacks está PROHIBIDO; usar Dockerfiles personalizados o imágenes base oficiales.

8) Comandos útiles
 - desde cada carpeta de servicio, entrar en la carpeta y ejecutar: `railway up`
 - comandos de build Docker (opcional):
   - `docker build -f Dockerfile.marimo -t coolappai-marimo .`
   - `docker build -f hermes-env/Dockerfile.hermes -t coolappai-hermes ./hermes-env`
