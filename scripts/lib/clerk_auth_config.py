"""Read/write `[clerk]` section of `~/.synapse/config.toml`.

Shared file with `[telemetry]` (T8) — we only own the `[clerk*]` tables; on
save we MERGE clerk tables into the existing file content rather than
rewriting the whole file. (Hand-rolled TOML; stdlib only.)

Schema:

    [clerk]
    auth = "pat"   # "pat" or "app"

    [clerk.pat]
    token_env = "SYNAPSE_CLERK_TOKEN"

    [clerk.app]
    app_id = "..."
    installation_id = "..."
    private_key_path = "~/.synapse/clerk.pem"

`load()` returns defaults when the file is absent. App-mode config raises
`ValueError` if any of `app_id`, `installation_id`, `private_key_path` is
missing — clerk auth fails loudly rather than silently degrading.
"""
from __future__ import annotations

import os
import pathlib
import tomllib
from dataclasses import dataclass, field
from typing import Literal

CONFIG_NAME = "config.toml"
SYNAPSE_DIR_NAME = ".synapse"

DEFAULT_TOKEN_ENV = "SYNAPSE_CLERK_TOKEN"


def _home_synapse() -> pathlib.Path:
    return pathlib.Path(os.path.expanduser("~")) / SYNAPSE_DIR_NAME


def config_path() -> pathlib.Path:
    """Per-machine clerk-auth config — same file as `[telemetry]`."""
    return _home_synapse() / CONFIG_NAME


@dataclass
class PatConfig:
    token_env: str = DEFAULT_TOKEN_ENV


@dataclass
class AppConfig:
    app_id: str
    installation_id: str
    private_key_path: pathlib.Path


@dataclass
class ClerkAuthConfig:
    auth: Literal["pat", "app"] = "pat"
    pat: PatConfig = field(default_factory=PatConfig)
    app: AppConfig | None = None


def _expand(p: str) -> pathlib.Path:
    return pathlib.Path(os.path.expanduser(str(p)))


def load(path: pathlib.Path | None = None) -> ClerkAuthConfig:
    p = pathlib.Path(path) if path is not None else config_path()
    cfg = ClerkAuthConfig()
    if not p.exists():
        return cfg
    try:
        data = tomllib.loads(p.read_text())
    except (OSError, tomllib.TOMLDecodeError):
        return cfg

    clerk = data.get("clerk", {})
    if not isinstance(clerk, dict):
        return cfg

    auth = clerk.get("auth", "pat")
    if auth not in ("pat", "app"):
        auth = "pat"
    cfg.auth = auth  # type: ignore[assignment]

    pat_section = clerk.get("pat")
    if isinstance(pat_section, dict):
        cfg.pat = PatConfig(
            token_env=str(pat_section.get("token_env", DEFAULT_TOKEN_ENV)),
        )

    app_section = clerk.get("app")
    if isinstance(app_section, dict):
        # App config: parse if any of the required fields present, validate strict.
        has_any = any(k in app_section for k in
                      ("app_id", "installation_id", "private_key_path"))
        if has_any or auth == "app":
            missing = [k for k in ("app_id", "installation_id", "private_key_path")
                       if not str(app_section.get(k, "")).strip()]
            if missing:
                if auth == "app":
                    raise ValueError(
                        f"[clerk.app] missing required field(s): {', '.join(missing)}"
                    )
                # Auth=pat, partial app block — silently ignore (user staging app cfg).
            else:
                cfg.app = AppConfig(
                    app_id=str(app_section["app_id"]).strip(),
                    installation_id=str(app_section["installation_id"]).strip(),
                    private_key_path=_expand(str(app_section["private_key_path"])),
                )

    if cfg.auth == "app" and cfg.app is None:
        raise ValueError("[clerk] auth='app' but [clerk.app] section is missing")

    return cfg


# ---------------------------------------------------------------------------
# Save (merge-aware: we don't own the whole file)
# ---------------------------------------------------------------------------

def _quote(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _clerk_block(cfg: ClerkAuthConfig) -> str:
    lines: list[str] = []
    lines.append("[clerk]")
    lines.append(f"auth = {_quote(cfg.auth)}")

    lines.append("")
    lines.append("[clerk.pat]")
    lines.append(f"token_env = {_quote(cfg.pat.token_env)}")

    if cfg.app is not None:
        lines.append("")
        lines.append("[clerk.app]")
        lines.append(f"app_id = {_quote(cfg.app.app_id)}")
        lines.append(f"installation_id = {_quote(cfg.app.installation_id)}")
        lines.append(f"private_key_path = {_quote(str(cfg.app.private_key_path))}")

    return "\n".join(lines) + "\n"


def _strip_existing_clerk(text: str) -> str:
    """Remove all top-level [clerk...] sections, preserving everything else."""
    lines = text.splitlines()
    out: list[str] = []
    in_clerk = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            header = stripped
            if header == "[clerk]" or header.startswith("[clerk."):
                in_clerk = True
                continue
            else:
                in_clerk = False
                out.append(line)
                continue
        if not in_clerk:
            out.append(line)
    while out and out[-1].strip() == "":
        out.pop()
    return ("\n".join(out) + "\n") if out else ""


def save(cfg: ClerkAuthConfig, path: pathlib.Path) -> None:
    p = pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    existing = ""
    if p.exists():
        try:
            existing = p.read_text()
        except OSError:
            existing = ""
    head = _strip_existing_clerk(existing)
    body = _clerk_block(cfg)
    if head:
        result = head.rstrip("\n") + "\n\n" + body
    else:
        result = body
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(result)
    os.replace(tmp, p)
