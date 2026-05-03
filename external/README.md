# external

Externally-owned submodule slot — empty in the framework distribution. Adopters add multi-artifact suites here as git submodules:

```bash
git submodule add <url> external/<suite-name>
```

Each suite owns its own structure (typically `skills/`, `agents/`, `protocols/`). `scripts/install.sh` discovers artifacts in `external/` automatically alongside `src/` and `synapse/`.
