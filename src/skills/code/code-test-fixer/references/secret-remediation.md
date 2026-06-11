# Secret Remediation Playbook

Loaded at [SURFACE-SECRETS]. Every detect-secrets finding is `requires-human-review`.
This skill never deletes secret strings, rewrites history, or commits any change in this node.

---

## 1. Why Secrets Are Never Auto-Fixed

**Rotation, not deletion, is the correct response.** Removing the string from HEAD does not
invalidate the credential. The secret remains live and exploitable until rotated at the
provider or service layer.

**Git history retains the secret.** Unless the repo's full history is rewritten, the string
lives in every prior commit. History rewrite (`git filter-branch`, `git filter-repo`, BFG) is
a destructive operation that rewrites SHAs, breaks forks, and requires coordination with every
contributor who has cloned the repo. That decision belongs to a human with repository authority.

**Secret types have different rotation procedures.** An AWS access key, a JWT signing key, and
a database password each have a distinct revocation and rotation path. Generic find-and-delete
logic cannot know which path applies.

---

## 2. Per-Finding `requires-human-review` Entry

For every detect-secrets finding, append one entry to `requires_human_review` with:

- `category`: `secret`
- `file`: path relative to repo root
- `line`: line number reported by detect-secrets
- `secret_type`: detected type (see section 3 for canonical labels)
- `rotation_ref`: the relevant subsection from section 3
- `history_rewrite_required`: `yes` if the branch has ever been merged to a public branch
  (main, develop, release); `no` if the finding was caught pre-merge on a feature branch only
- `reason`: human-readable note, e.g. `"AWS access key detected — rotate via IAM before merge"`

Example entry (Python dict form, matching LintIssue shape):

```python
{
    "category": "secret",
    "file": "src/config/settings.py",
    "line": 42,
    "secret_type": "aws_access_key",
    "rotation_ref": "section-3-aws-access-key",
    "history_rewrite_required": "yes",
    "reason": "AWS access key detected — rotate via IAM; history rewrite required (reached main)",
}
```

---

## 3. Rotation Playbook by Credential Type

### AWS Access Key (`aws_access_key`)

1. Log in to the AWS IAM console.
2. Locate the key under IAM > Users > Security credentials.
3. Deactivate and delete the exposed key immediately.
4. Generate a new key pair for the same IAM user or role.
5. Update all deployment secrets stores (AWS Secrets Manager, Parameter Store, CI environment
   variables) with the new key.
6. Verify no active workloads reference the old key before confirming deletion.

### GitHub Personal Access Token (`github_token` / `github_pat`)

1. Navigate to github.com/settings/tokens.
2. Revoke the exposed token immediately.
3. Generate a replacement token with the minimum required scopes.
4. Update the token in all CI/CD secrets (GitHub Actions secrets, external CI vaults).
5. Audit recent API calls against the token if the exposure window is unknown.

### Private SSH Key (`private_key`)

1. Identify all servers where the corresponding public key appears in `authorized_keys`.
2. Remove the public key from `authorized_keys` on every server before regenerating.
3. Generate a new keypair (`ssh-keygen -t ed25519`).
4. Deploy the new public key to all target servers.
5. Update any key references in deployment configs, bastion configs, and CI secrets.

### Database Password (`db_password`)

1. Rotate the password at the database layer (ALTER USER / provider console).
2. Update the connection string in the application secrets manager (Vault, AWS Secrets Manager,
   environment variable store).
3. Restart or redeploy dependent services to pick up the new connection string.
4. Confirm old password is no longer accepted before closing the incident.

### Generic API Key (`generic_api_key` / `high_entropy_string`)

1. Identify the provider by inspecting the key format and surrounding code context.
2. Follow the provider's documented key rotation or revocation flow.
3. Update the replacement key in the application secrets store.
4. If the provider cannot be identified, treat as a high-severity finding and escalate to
   the security team before merging.

### JWT Signing Key (`jwt_signing_key` / `secret_key`)

1. Generate a new signing key using a cryptographically secure method appropriate for the
   algorithm (e.g., `openssl rand -base64 64` for HS256).
2. Deploy the new key to the application secrets store.
3. Invalidate all outstanding tokens: either force a global re-login or rotate to a new key ID
   (`kid`) and expire the old one after a short grace period.
4. Remove or rotate any refresh tokens that were signed with the old key.

---

## 4. detect-secrets Baseline Interaction

If `.secrets.baseline` exists in the repo, detect-secrets only surfaces findings that are **not
already listed in the baseline**. Baseline entries are pre-approved known findings (or false
positives) reviewed by a human.

This skill does not modify `.secrets.baseline`. If a new finding turns out to be a false
positive, the human reviewer updates the baseline:

```
detect-secrets scan --update .secrets.baseline
```

The updated baseline is committed separately by the reviewer, outside the scope of this skill.

---

## 5. What This Skill MUST NEVER Do

- Delete the secret string from the working tree.
- Run `git filter-branch`, `git filter-repo`, or BFG Repo Cleaner.
- Add the file containing the secret to `.gitignore` — the file is already committed and
  `.gitignore` does not remove tracked files from history.
- Add `# pragma: allowlist secret` to suppress a finding without a corresponding
  `requires-human-review` entry and explicit human sign-off.
- Commit any change as part of [SURFACE-SECRETS] — this node is output-only.

---

## 6. Output Contract

Each detect-secrets finding produces exactly one entry in `requires_human_review` with:

- `category=secret`
- File, line, and detected secret type
- Rotation playbook reference (section 3 subsection)
- `history_rewrite_required` indicator

The [OPEN-PR] node renders all `category=secret` entries in a dedicated **Secrets Requiring
Human Review** section of the PR body, separate from other `requires-human-review` items.
The PR label `requires-human-review` is applied unconditionally when any secret finding exists.
