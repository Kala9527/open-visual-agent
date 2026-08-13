# Contributing

Thanks for helping improve Open Visual Agent.

Good first contributions:

- Add prompt packs for a real workflow.
- Add provider-specific setup notes.
- Improve Docker, deployment, or screenshots.
- Add examples for Cursor, Codex, Claude Code, or MCP workflows.
- Add tests around provider response parsing.

Before opening a PR:

```bash
python -m compileall backend src scripts agent_cli_scripts
cd frontend
npm run typecheck
npm run build
```

Never include real API keys, generated media, private logs, or local database files.
