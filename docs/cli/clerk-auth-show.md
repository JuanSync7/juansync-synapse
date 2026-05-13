# cortex clerk auth show

Print the active clerk auth configuration. Token values are never displayed.

## Usage

```
cortex clerk auth show [--json]
```

## Output (PAT mode, default)

```
clerk auth config: /home/me/.synapse/config.toml
  auth     = 'pat'
  pat.token_env = 'SYNAPSE_CLERK_TOKEN'  (value NOT shown for security)
  app: (not configured)
```

## Output (App mode)

```
clerk auth config: /home/me/.synapse/config.toml
  auth     = 'app'
  pat.token_env = 'SYNAPSE_CLERK_TOKEN'  (value NOT shown for security)
  app.app_id          = '12345'
  app.installation_id = '67890'
  app.private_key_path = /home/me/.synapse/clerk.pem
```

## JSON

```
cortex clerk auth show --json
```

```json
{
  "auth": "pat",
  "config_path": "/home/me/.synapse/config.toml",
  "pat": { "token_env": "SYNAPSE_CLERK_TOKEN" },
  "app": null
}
```

## Security

This command **never** prints token values, private key contents, or environment-variable values. It only reports the *names* of env vars (PAT mode) and the *paths* of key files (App mode). To verify auth actually works end-to-end, use [`clerk auth probe`](clerk-auth-probe.md).
