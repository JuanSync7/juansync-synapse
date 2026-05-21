# Before/After Example: Small Feature Addition

## Scenario

A developer adds a `rate_limit_window` config parameter to the auth module. The diff touches `src/auth/config.py` (new field) and `src/auth/handler.py` (uses the new field in the response).

## Diff

```diff
--- a/src/auth/config.py
+++ b/src/auth/config.py
@@ -15,6 +15,7 @@ class AuthConfig:
     token_expiry: int = 3600
     refresh_enabled: bool = True
     max_retries: int = 3
+    rate_limit_window: int = 300  # seconds between rate limit resets
```

## Phase 1: Triage

- **Change type:** Feature (new config parameter)
- **Doc impact (from doc-impact-map):** eng-guide (always), .env.example (new config option), README (only if public API — this is internal config, so skip)

## Phase 2: Discovery

`.doc-map.yaml` lookup:
```yaml
docs/auth/AUTH_ENGINEERING_GUIDE.md: [src/auth/]
.env.example: [src/]
```

Result: two docs to patch.

## Phase 3: Patch

### Engineering Guide — Before

```markdown
## Configuration

The auth module is configured via `AuthConfig`:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `token_expiry` | `int` | `3600` | Token lifetime in seconds |
| `refresh_enabled` | `bool` | `True` | Whether token refresh is allowed |
| `max_retries` | `int` | `3` | Max authentication retry attempts |
```

### Engineering Guide — After

```markdown
## Configuration

The auth module is configured via `AuthConfig`:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `token_expiry` | `int` | `3600` | Token lifetime in seconds |
| `refresh_enabled` | `bool` | `True` | Whether token refresh is allowed |
| `max_retries` | `int` | `3` | Max authentication retry attempts |
| `rate_limit_window` | `int` | `300` | Seconds between rate limit resets |
```

**Convention match:** New row follows the existing table format — same column order, same backtick style for parameter names and types, same sentence-case description without period.

### .env.example — Before

```env
# Auth
AUTH_TOKEN_EXPIRY=3600
AUTH_REFRESH_ENABLED=true
AUTH_MAX_RETRIES=3
```

### .env.example — After

```env
# Auth
AUTH_TOKEN_EXPIRY=3600
AUTH_REFRESH_ENABLED=true
AUTH_MAX_RETRIES=3
AUTH_RATE_LIMIT_WINDOW=300
```

**Convention match:** New entry follows the existing naming pattern (`AUTH_` prefix, SCREAMING_SNAKE_CASE), placed after `AUTH_MAX_RETRIES` to mirror the order in `AuthConfig`.

## Bad Patch Example

What a convention-violating patch looks like for the same change:

### Engineering Guide — Bad Patch

```markdown
## Configuration

The auth module is configured via `AuthConfig`:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `token_expiry` | `int` | `3600` | Token lifetime in seconds |
| `refresh_enabled` | `bool` | `True` | Whether token refresh is allowed |
| `max_retries` | `int` | `3` | Max authentication retry attempts |
| rate_limit_window | integer | 300 | Rate limit reset window (in seconds). |
```

**Problems:**
- Missing backticks around parameter name and type (existing rows use backticks)
- `integer` instead of `int` (existing rows use Python type names)
- Description ends with a period (existing rows don't)
- Parenthetical format differs from existing terse descriptions

### .env.example — Bad Patch

```env
# Auth
AUTH_TOKEN_EXPIRY=3600
AUTH_REFRESH_ENABLED=true
AUTH_MAX_RETRIES=3

# Rate limiting
RATE_LIMIT_WINDOW=300
```

**Problems:**
- Added a blank line and new comment section (existing entries have no sub-grouping)
- Missing `AUTH_` prefix (existing entries all use it)
- Different placement breaks the visual grouping

## Phase 4: Summary

```
## Patch Summary

**Diff source:** HEAD~1
**Change type:** feature

## Patched

| Doc | Section | Change |
|-----|---------|--------|
| docs/auth/AUTH_ENGINEERING_GUIDE.md | Configuration | Added `rate_limit_window` row to config table |
| .env.example | Auth | Added `AUTH_RATE_LIMIT_WINDOW=300` |

## Skipped

| Doc | Reason |
|-----|--------|
| README.md | No public API change — rate_limit_window is internal config |
| docs/auth/AUTH_SPEC.md | No new requirement — config addition is implementation detail |
| test-coverage.md | No new test scenarios added in this diff |
```
