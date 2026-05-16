# Fixture — length-floor-abort

Principle sub-type; no voice anchors. Tests T4 / O6: when the only honest rewrite covering the kept set would be under 30% of source length, the agent emits `LENGTH FLOOR ERROR` and refuses to write.

## Kept Claims (input)

```yaml
kept_claims:
  - id: short001
    heading_anchor: core-rule
    text: "All commits must be signed."
    source_lines: [3, 3]
```

(One short kept claim. The remaining 90% of the source is content the human auditor cut. A faithful rewrite of just this one claim would be ~10 words; the source is ~600 words.)

## Original Doc (input)

```markdown
# Commit Signing Policy

## Core Rule
All commits must be signed. This is the single load-bearing rule of this document and the rest is rationale and examples.

## Rationale
Signed commits give us cryptographic provenance for every change that lands in main. Without signing, an attacker who compromises a developer's workstation could push commits that appear to come from that developer, and we would have no way to detect the impersonation after the fact. Signing closes this gap by making each commit verifiable against a known public key. We have evaluated alternative provenance mechanisms (branch protection tied to OIDC identity, signed tags only, GPG keyserver federation) and signing per-commit remains the most robust option for our threat model. The cost is per-developer setup time (15–30 minutes the first time, near-zero thereafter) and a small amount of CI overhead to verify signatures on pull request creation. We accept these costs because the alternative — an unsigned commit graph — is a class of risk we cannot retroactively close.

## Examples

### Example 1: Setting up signing for the first time
A new contributor runs `git config commit.gpgsign true` and configures their GPG key in their git config. They push their first PR and the CI signature-verification job passes. This is the happy path and represents the experience of every contributor after onboarding.

### Example 2: A signed commit fails verification
The CI job reports the signature is invalid. The contributor checks `gpg --list-secret-keys` and discovers their key has expired. They rotate the key, re-sign their last commit with `git commit --amend -S --no-edit`, and force-push to their PR branch. The CI re-runs and passes. This is the most common failure mode and takes about 5 minutes to resolve.

### Example 3: An unsigned commit slips into a PR
A contributor working on a fresh laptop forgets to enable signing. They push a PR with several unsigned commits. The CI signature-verification job blocks the merge. The contributor rebases the branch with signing enabled, force-pushes, and the PR proceeds. This catches the failure at the right point in the workflow — before main is touched.

## Edge cases
Merge commits made through the GitHub web UI are signed by GitHub's web-flow key, not the contributor's key. We accept these as valid signatures because the integrity is anchored in the contributor's authenticated session with GitHub. Commits authored by automated bots use the bot's dedicated signing key, also accepted as valid. Cherry-picks and reverts preserve the original signature where possible and re-sign with the picker's key otherwise — both paths are valid.
```

## Voice Anchors (input)

(absent)

## Expected Behavior

- Output is the single-line string `LENGTH FLOOR ERROR: <n>% of source, floor is 30%` where `<n>` is the agent's measured ratio (well under 30).
- The agent does NOT emit `rewritten_doc`. A truncated rewrite that drops the floor silently → FAIL O6.
- The agent does NOT attempt to pad the rewrite with content not in the kept set to clear the floor — that would introduce extra-claim leakage (FAIL O4).
- The correct call is to refuse loudly so the shrinker can surface the over-compression to the user, who likely cut too many claims in the audit phase.
