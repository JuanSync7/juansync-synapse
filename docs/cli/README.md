# CLI Reference

Per-command documentation for the `cortex` dispatcher. Run `./cortex help <command>` to view any of these from the terminal.

## Commands

| Command | Doc | Description |
|---------|-----|-------------|
| [install](install.md) | Install synapses to Claude Code |
| [codex](codex.md) | Install synapses to Codex CLI |
| [gemini](gemini.md) | Install synapses to Gemini CLI |
| [agents](agents.md) | Install agent definitions |
| [identity](identity.md) | Install identity files |
| [list](list.md) | List installed synapses |
| [available](available.md) | Show all available synapses |
| [pathway](pathway.md) | Manage pathway bundles |
| [scaffold](scaffold.md) | Create a new synapse |
| [validate](validate.md) | Run structural checks |
| [sync](sync.md) | Sync registries and READMEs |
| [audit](audit.md) | Companion artifact audit |
| [doctor](doctor.md) | Scan installed.lock for 7 finding categories |
| [doctor symlinks](doctor-symlinks.md) | Legacy broken-symlink check (now a subcommand) |
| [drift](drift.md) | Resolve drift (show, stash, restore, adopt, ignore, list-stashes) |
| [clean](clean.md) | Remove all installed symlinks |
| [check-links](check-links.md) | Validate markdown links |
| [reorganize](reorganize.md) | Domain-based artifact reorganization |
| [clerk](clerk.md) | External submodule bump automation (overview) |
| [clerk bump-externals](clerk-bump-externals.md) | Detect upstream tags; open bump PRs |
| [clerk status](clerk-status.md) | Summarize `~/.synapse/clerk_state.toml` |
| [clerk doctor](clerk-doctor.md) | Clerk-self checks (state, auth, .gitmodules) |
| [clerk auth](clerk-auth.md) | Manage clerk auth (PAT / GitHub App) — overview |
| [clerk auth show](clerk-auth-show.md) | Print auth config (no token values) |
| [clerk auth set-mode](clerk-auth-set-mode.md) | Switch between PAT and App, persist config |
| [clerk auth probe](clerk-auth-probe.md) | Exercise the active auth adapter |
| [telemetry](telemetry.md) | Lifecycle event emission (overview, sinks, opt-out) |
| [telemetry status](telemetry-status.md) | Show telemetry config and file size |
| [telemetry rotate](telemetry-rotate.md) | Gzip events.jsonl and truncate |
| [telemetry emit](telemetry-emit.md) | Emit a single event (used by hooks) |
