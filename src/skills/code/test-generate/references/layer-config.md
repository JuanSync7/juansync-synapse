# Config-Layer Test Patterns

## Definition

Config-layer tests verify pydantic / dataclass model behavior: field validation,
cross-field constraints, default value resolution, and `model_validator(mode="after")`
rules. They do **not** test pydantic itself — only the constraints your code declares.

---

## Field-Level Tests

**Type coercion and required vs optional**

```python
def test_port_coerced_from_string():
    cfg = ServerConfig(port="8080")
    assert cfg.port == 8080  # str -> int coercion

def test_missing_required_field_raises():
    with pytest.raises(ValidationError) as exc:
        ServerConfig()
    assert any(e["loc"] == ("host",) for e in exc.value.errors())
```

**Default values**

```python
def test_timeout_default():
    cfg = ServerConfig(host="localhost")
    assert cfg.timeout == 30
```

**Alias handling**

```python
def test_alias_population():
    cfg = ServerConfig.model_validate({"server_host": "localhost"})
    assert cfg.host == "localhost"
```

**Frozen / immutability**

```python
def test_frozen_model_rejects_mutation():
    cfg = FrozenConfig(name="x")
    with pytest.raises(ValidationError):
        cfg.name = "y"
```

---

## Cross-Field Validators

Test `@model_validator(mode="after")` rules through the public constructor, not the
validator method directly.

```python
def test_fast_mode_requires_short_timeout():
    with pytest.raises(ValidationError) as exc:
        PipelineConfig(mode="fast", timeout=60)
    errors = exc.value.errors()
    assert any("timeout" in str(e["loc"]) for e in errors)

def test_fast_mode_valid_timeout():
    cfg = PipelineConfig(mode="fast", timeout=10)
    assert cfg.timeout == 10
```

---

## Discriminator Unions

One test per branch of `Annotated[Union[A, B], Field(discriminator="type")]`.

```python
def test_discriminator_selects_local_store():
    cfg = StoreConfig.model_validate({"type": "local", "path": "/tmp"})
    assert isinstance(cfg, LocalStoreConfig)

def test_discriminator_selects_s3_store():
    cfg = StoreConfig.model_validate({"type": "s3", "bucket": "my-bucket"})
    assert isinstance(cfg, S3StoreConfig)

def test_unknown_discriminator_raises():
    with pytest.raises(ValidationError):
        StoreConfig.model_validate({"type": "gcs", "bucket": "x"})
```

---

## Validation Error Shape

Assert `loc` and `type`, not just that a `ValidationError` was raised.

```python
def test_negative_workers_error_shape():
    with pytest.raises(ValidationError) as exc:
        WorkerConfig(count=-1)
    err = exc.value.errors()[0]
    assert err["loc"] == ("count",)
    assert err["type"] == "greater_than"
```

---

## Environment Variable Loading

Use `monkeypatch.setenv` for `pydantic_settings.BaseSettings`.

```python
def test_settings_from_env(monkeypatch):
    monkeypatch.setenv("APP_HOST", "prod.example.com")
    monkeypatch.setenv("APP_PORT", "9090")
    settings = AppSettings()
    assert settings.host == "prod.example.com"
    assert settings.port == 9090
```

---

## Round-Trip

`model_validate(model_dump())` must reproduce the same model.

```python
def test_round_trip():
    original = PipelineConfig(mode="batch", timeout=120, workers=4)
    restored = PipelineConfig.model_validate(original.model_dump())
    assert restored == original
```

---

## Default Value Freshness

`Field(default_factory=...)` ensures mutable defaults are independent across instances.

```python
def test_mutable_default_not_shared():
    a = CollectionConfig()
    b = CollectionConfig()
    a.tags.append("x")
    assert "x" not in b.tags
```

---

## Schema Export

Only test schema shape if it is consumed externally (e.g., passed to a UI or stored).

```python
def test_schema_has_required_properties():
    schema = PipelineConfig.model_json_schema()
    assert "mode" in schema["properties"]
    assert "timeout" in schema["required"]
```

---

## Anti-Patterns

- **Do not** call `_validate_cross_fields` directly — test through the constructor.
- **Do not** test that pydantic raises on wrong types in general — only your constraints.
- **Do not** mock the model under test; construct it with real inputs.
- **Do not** patch pydantic internals to suppress validation for convenience.

---

## Full Example

```python
# tests/config/test_pipeline_config.py
import pytest
from pydantic import ValidationError
from myapp.config import PipelineConfig  # mode, timeout, workers

class TestPipelineConfig:
    def test_fast_mode_rejects_long_timeout(self):
        with pytest.raises(ValidationError) as exc:
            PipelineConfig(mode="fast", timeout=60, workers=2)
        assert any("timeout" in str(e["loc"]) for e in exc.value.errors())

    def test_fast_mode_accepts_short_timeout(self):
        cfg = PipelineConfig(mode="fast", timeout=20, workers=2)
        assert cfg.timeout == 20

    def test_default_workers(self):
        cfg = PipelineConfig(mode="batch", timeout=120)
        assert cfg.workers == 1

    def test_round_trip(self):
        cfg = PipelineConfig(mode="batch", timeout=120, workers=4)
        assert PipelineConfig.model_validate(cfg.model_dump()) == cfg
```
