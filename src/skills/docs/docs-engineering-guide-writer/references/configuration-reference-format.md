# Configuration Reference Format (Section 5)

Group parameters by module. For each parameter:

| Column | What to include |
|--------|----------------|
| Parameter | Exact config key, in backticks |
| Type | Type annotation using the project's type system (e.g., `float`, `int`, `list[str]`, `bool` for Python; `number`, `string[]` for TypeScript) |
| Default | Actual default value from code |
| Valid Range / Options | Numeric range or allowed enum values |
| Effect | Precise behavioral description — what changes when this value is modified |

For parameters where the effect is non-obvious (e.g., a threshold that changes routing behavior), include a short explanatory note below the table row.
