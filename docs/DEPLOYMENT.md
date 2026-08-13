# Deployment

Open Visual Agent is a split FastAPI + Vue app.

## Local

```bat
copy .env.example .env
setup_env.bat
start.bat
```

In another terminal:

```bat
cd frontend
npm install
npm run dev
```

Open http://127.0.0.1:5177.

## Docker Compose

```bash
cp .env.example .env
docker compose up --build
```

Frontend: http://127.0.0.1:5177
Backend docs: http://127.0.0.1:8007/docs

## Production Notes

- Do not commit `.env`, generated media, SQLite databases, logs, or local build output.
- Put provider API keys in platform secrets.
- Set `VITE_API_BASE_URL` to the public backend URL if frontend and backend are on different hosts.
- Use persistent storage only for `outputs/` and the SQLite database if you want to keep history.
