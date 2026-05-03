# mypy Strict-Mode Fix Patterns

Loaded at [FIX-MYPY]. Apply in order; prefer the narrowest fix that satisfies mypy.

---

## Missing Return Type

Procedures (no meaningful return): add `-> None`.

```python
# before
def reset_state():
    self._cache.clear()

# after
def reset_state() -> None:
    self._cache.clear()
```

Concrete return: annotate the actual type.

```python
# before
def get_user(user_id: int):
    return db.query(User).get(user_id)

# after
def get_user(user_id: int) -> User:
    return db.query(User).get(user_id)
```

Generic return: use `TypeVar`, not `Any`.

```python
from typing import TypeVar

T = TypeVar("T")

def first(items: list[T]) -> T:
    return items[0]
```

---

## Missing Parameter Type

Annotate based on call sites. If all callers pass `str`, use `str`.

```python
# before
def normalize(value):
    return value.strip().lower()

# after
def normalize(value: str) -> str:
    return value.strip().lower()
```

Heterogeneous call sites — lift to `TypeVar` or `Protocol`.

```python
from typing import Protocol

class Sized(Protocol):
    def __len__(self) -> int: ...

def is_empty(obj: Sized) -> bool:
    return len(obj) == 0
```

---

## `Optional` vs `T | None`

Use `T | None` in all new code (Python 3.10+). Never use `Optional[T]` in new code.

```python
# wrong
from typing import Optional
def find(key: str) -> Optional[str]: ...

# right
def find(key: str) -> str | None: ...
```

For Python < 3.10 compatibility add `from __future__ import annotations` at the top
of the file — the union syntax then works at runtime too.

---

## `Any` Escape Hatch

Reserve `Any` for boundary types only: deserialization entry points, dynamic plugin
loading, third-party libraries without stubs.

```python
import json
from typing import Any

def load_config(path: str) -> dict[str, Any]:   # boundary — raw JSON
    with open(path) as f:
        return json.load(f)                     # Any stops here

def get_timeout(config: dict[str, Any]) -> int: # narrow immediately after
    return int(config["timeout"])
```

Do not propagate `Any` past the first function that can narrow it.

---

## `# type: ignore` Usage

Always specify the error code. Always pair with a commit-message reason.

```python
result = legacy_api.fetch()  # type: ignore[no-any-return]  # legacy_api has no stubs; tracked in #142
```

Bare `# type: ignore` is prohibited — mypy silences all errors on the line, hiding
future regressions.

---

## Generic Containers

Use built-in lowercase generics (Python 3.9+). Import `from __future__ import annotations`
for files that need < 3.9 compatibility at runtime.

```python
# wrong
from typing import List, Dict, Tuple
def process(items: List[str]) -> Dict[str, int]: ...

# right
def process(items: list[str]) -> dict[str, int]: ...
```

Same rule applies to `set[T]`, `tuple[T, ...]`, `frozenset[T]`.

---

## Callable Annotations

```python
from collections.abc import Callable

# no args, returns bool
validator: Callable[[], bool]

# two args, returns None
Handler = Callable[[str, int], None]

def register(handler: Callable[[str], bool]) -> None: ...
```

Use `collections.abc.Callable`, not `typing.Callable`, in new code.

---

## Forward References

Prefer `from __future__ import annotations` over string literals.

```python
# before — string literal forward reference
def clone(self) -> "Node": ...

# after — clean with __future__
from __future__ import annotations

def clone(self) -> Node: ...
```

Use string literals only when `__future__` import is already blocked by another
incompatibility in the same file.

---

## TypedDict for Known Shapes

Replace `dict[str, Any]` with `TypedDict` whenever the shape is fixed.

```python
from typing import TypedDict

# wrong
def build_payload(name: str, retries: int) -> dict[str, Any]: ...

# right
class Payload(TypedDict):
    name: str
    retries: int

def build_payload(name: str, retries: int) -> Payload:
    return {"name": name, "retries": retries}
```

---

## Protocol for Structural Typing

Prefer `Protocol` over `ABC` when you need duck-typing without inheritance.

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class Closeable(Protocol):
    def close(self) -> None: ...

def shutdown(resource: Closeable) -> None:
    resource.close()
```

---

## Common Errors and Fixes

### `Incompatible return value type`

Narrow with `assert isinstance` or split branches.

```python
# mypy: Incompatible return value type (got "str | None", expected "str")
def get_name(user: User) -> str:
    assert isinstance(user.name, str)   # narrow; crash fast on None
    return user.name
```

Or refactor the branch so each path returns the declared type.

### `Argument has incompatible type`

Coerce explicitly at the call site.

```python
# before — passes int where str expected
send_message(user_id)

# after
send_message(str(user_id))
```

If the function signature is wrong, fix the parameter type, not the caller.

### `Need type annotation for variable`

Annotate empty containers at declaration.

```python
# wrong
results = []
mapping = {}

# right
results: list[str] = []
mapping: dict[str, int] = {}
```

### `Returning Any from function declared to return X`

Cast at the producer, or narrow the return value before returning.

```python
from typing import cast

def fetch_name(data: dict[str, Any]) -> str:
    return cast(str, data["name"])   # assert type at boundary
```

If `cast` is hiding a real type mismatch, refactor the producer instead.
