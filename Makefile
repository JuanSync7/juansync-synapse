.PHONY: all init install claude codex codex-project gemini agents list available clean zip reorg check-links tag-stable tag-dev test

all:
	@echo "Usage: make <command> [args...]"
	@echo ""
	@echo "Global:"
	@echo "  make init                 configure git hooks + submodules (first-time)"
	@echo "  make list                 show installed skills"
	@echo "  make available            show all available skills"
	@echo "  make reorg                show artifact placement status"
	@echo "  make check-links          validate relative paths in all .md files"
	@echo ""
	@echo "Claude Code:"
	@echo "  make claude               install all skills + agents to ~/.claude/"
	@echo "  make install              alias for 'make claude'"
	@echo "  make install docs         install src/skills/docs only (adopter)"
	@echo "  make install docs code    install multiple domains"
	@echo "  make agents               install agent definitions only"
	@echo "  make zip                  package all skills as .zip for Claude Desktop"
	@echo "  make zip docs/patch-docs  package one skill"
	@echo "  make clean                remove all installed symlinks (all harnesses)"
	@echo ""
	@echo "Codex CLI:"
	@echo "  make codex                install all skills to ~/.codex/skills/ (global)"
	@echo "  make codex-project        install all skills to .agents/skills/ (project)"
	@echo ""
	@echo "Gemini CLI:"
	@echo "  make gemini               install all skills to ~/.gemini/extensions/ai-synapse/"

init:
	git config core.hooksPath .githooks
	git submodule update --init --recursive
	@echo "Git hooks configured. Submodules initialized."

# make claude → install all skills + agents
claude:
	./scripts/install.sh install all
	./scripts/install.sh agents

# make install           → alias for make claude (backwards compat)
# make install docs      → install src/skills/docs (adopter shortcut)
# make install docs code → install src/skills/docs and src/skills/code
# Framework skills under synapse/ are installed via 'make install' (no args = all).
_INSTALL_TARGETS := $(filter-out install, $(MAKECMDGOALS))
install:
	@if [ -z "$(_INSTALL_TARGETS)" ]; then \
		./scripts/install.sh install all; \
	else \
		./scripts/install.sh install $(addprefix src/skills/,$(_INSTALL_TARGETS)); \
	fi

agents:
	./scripts/install.sh agents

# make codex → install all skills to ~/.codex/skills/ (global)
_CODEX_TARGETS := $(filter-out codex, $(MAKECMDGOALS))
codex:
	@if [ -z "$(_CODEX_TARGETS)" ]; then \
		./scripts/install.sh codex all; \
	else \
		./scripts/install.sh codex $(addprefix src/skills/,$(_CODEX_TARGETS)); \
	fi

# make codex-project → install all skills to .agents/skills/ (project-scoped)
_CODEX_PROJECT_TARGETS := $(filter-out codex-project, $(MAKECMDGOALS))
codex-project:
	@if [ -z "$(_CODEX_PROJECT_TARGETS)" ]; then \
		./scripts/install.sh codex-project all; \
	else \
		./scripts/install.sh codex-project $(addprefix src/skills/,$(_CODEX_PROJECT_TARGETS)); \
	fi

# make gemini → install all skills to ~/.gemini/extensions/ai-synapse/
_GEMINI_TARGETS := $(filter-out gemini, $(MAKECMDGOALS))
gemini:
	@if [ -z "$(_GEMINI_TARGETS)" ]; then \
		./scripts/install.sh gemini all; \
	else \
		./scripts/install.sh gemini $(addprefix src/skills/,$(_GEMINI_TARGETS)); \
	fi

list:
	./scripts/install.sh list

available:
	./scripts/install.sh available

clean:
	./scripts/install.sh clean

# make zip                  → zip all skills
# make zip docs/patch-docs  → zip one skill
_ZIP_TARGETS := $(filter-out zip, $(MAKECMDGOALS))
zip:
	@if [ -z "$(_ZIP_TARGETS)" ]; then \
		./scripts/install.sh zip all; \
	else \
		./scripts/install.sh zip $(addprefix src/skills/,$(_ZIP_TARGETS)); \
	fi

check-links:
	./scripts/check-links.sh

# --- Versioning ---
# tag-stable: promote latest vX.Y.Z-pre.N tag to stable (manual cadence, on main)
# tag-dev:    local dev convenience — print next pre-tag for current diff (no apply)
tag-stable:
	./scripts/tag-stable.sh

tag-dev:
	./scripts/tag-dev.sh

# --- Tests ---
# make test → runs pytest, plus the bash-driven CLI/version tests.
test:
	./scripts/test.sh

# make reorg → show status (for other commands, use ./scripts/reorganize.sh directly)
reorg:
	./scripts/reorganize.sh status

# Prevent Make from erroring on unknown targets passed as install args (e.g. "docs", "code")
%:
	@:
