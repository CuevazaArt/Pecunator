# Production Readiness Audit

> Repository re-audit date: **2026-05-10**  
> Scope: repository contents, runtime entrypoints, CI configuration, wiki-visible operating surface.  
> Goal: verify which previously requested hardening items were already addressed, and identify what still blocks a production-grade hub.

---

## Executive verdict

**Pecunator is closer to production than before, but the hub is still not production-ready.**

Several important hardening items **were addressed** since the earlier critique:

- `StateWAL` is now integrated into bootstrap and gateway polling.
- `CHART_IMG_API_KEY` is read from the environment instead of being hardcoded.
- Backend and desktop default API port are now aligned on **8000**.
- Symmetric deployment already includes rollback logic.
- API authentication is enabled by default with a local bearer token.
- A filesystem kill switch (`PANIC.lock`) exists and is checked in bot loops.

However, there are still **high-impact operational blockers** that should be resolved before treating the hub as production-safe.

---

## What was already addressed

| Area | Current status | Evidence |
|---|---|---|
| Crash-safe gateway state | **Addressed** | `runtime/app.py` hydrates `StateStore`; `runtime/connectors/binance_gateway.py` persists snapshots every poll cycle |
| Chart-IMG secret handling | **Addressed** | `runtime/modules/vmo.py` reads `CHART_IMG_API_KEY` from the environment |
| Port mismatch | **Addressed** | `runtime/core/settings.py` and `desktop_shell/lib/config/app_config.dart` both default to port `8000` |
| Symmetric rollback | **Addressed** | `runtime/api/routers/symmetric.py` deletes/rolls back failed paired deployment |
| Local API auth default | **Addressed** | `runtime/api/auth.py` generates and enforces `runtime/data/api.token` |
| OOB panic check | **Partially addressed** | `runtime/bot/_base_runner.py` calls `check_panic_lock()` each cycle |

---

## Open blockers

### 1) CI gate still allows broken tests to merge

In `.github/workflows/ci-gate.yml`, the Python test step still swallows failures:

```yaml
pytest runtime/tests/ -v --tb=short -x || echo "::warning::Some tests failed"
```

This means the workflow can continue even when tests fail, which defeats the point of a required merge gate.

**Production risk:** broken runtime code can pass branch protection and ship unnoticed.  
**Priority:** Critical.

---

### 2) The engine still performs `git pull` on startup

`runtime/main.py` still calls `_auto_update()` before starting the API, and `_auto_update()` runs:

```python
["git", "pull", "--ff-only"]
```

This is not a safe production deployment pattern.

**Production risk:**

- the running node can change code at boot without operator approval,
- a bad push can be deployed automatically,
- version drift becomes harder to audit,
- recovery and rollback stay implicit instead of controlled.

**Priority:** Critical.

---

### 3) Runtime artifacts are still committed into the repository

Tracked runtime output is still present in Git, including:

- `backend.log.1`
- `backend.log.2`
- `backend.log.3`
- `desktop_shell/analyze_out.txt`
- `data/vmo/vmo_cache.db`
- `runtime/data/vmo/vmo_cache.db`
- multiple files under `runtime/data/vmo_captures/`

The `.gitignore` file blocks new runtime output, but already tracked artifacts remain in history and in the branch.

**Production risk:** repository noise, accidental disclosure of runtime behavior, bloated diffs, polluted releases.  
**Priority:** High.

---

### 4) `PANIC.lock` ignores the configured data directory

The panic sentinel path in `runtime/bot/_panic.py` is still derived from `__file__`:

```python
_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
```

If `PECUNATOR_DATA_DIR` is changed, the rest of the runtime can move to a custom data directory, but the panic lock still points to the default package-relative location.

**Production risk:** the operator may create `PANIC.lock` in the configured runtime directory and assume the bots will stop, while the bots keep running.  
**Priority:** High.

---

### 5) The desktop shell still hardcodes its engine base URL

`desktop_shell/lib/pages/home_shell.dart` still uses:

```dart
static const _engineBase = 'http://127.0.0.1:8000';
```

At the same time, `desktop_shell/lib/config/app_config.dart` already exposes centralized host/port defaults.

**Production risk:** if the backend port or host changes, the UI can silently point to the wrong endpoint.  
**Priority:** High.

---

### 6) The desktop shell still shows a hardcoded version string

The AppBar still displays:

```dart
Text('v2.6.1', ...)
```

That version is not dynamically sourced from the backend or a shared version constant.

**Production risk:** operators see the wrong version during incident response, release verification, and rollback checks.  
**Priority:** Medium.

---

### 7) Alerts are still local-only

`runtime/core/alert_dispatcher.py` currently stores alerts in memory, logs them, and optionally writes `alerts.log`. There is no active external delivery channel yet.

**Production risk:** a fuse trip, orphan condition, or degraded gateway can happen while nobody is watching the local console.  
**Priority:** Medium.

---

## Validation snapshot

### Python tests

Current repository test run:

- **184 passed**
- **9 skipped**
- runtime + e2e suite finished successfully

### Python lint

`ruff` still reports existing repository issues, including:

- a syntax error in `runtime/api/sandbox.py`,
- unused imports and undefined names,
- multiple long lines and whitespace violations.

This audit did **not** fix those code issues; it documents the current state.

### Flutter analyze

Flutter tooling was not available in the current sandbox session, so desktop analysis could not be re-run from this environment.

---

## Minimum path to production

1. **Fix the CI gate** so failed tests fail the workflow.
2. **Remove startup self-update** from `runtime/main.py`.
3. **Clean tracked runtime artifacts** from Git and keep them ignored.
4. **Bind `PANIC.lock` to `data_dir()`** so the kill switch follows configured runtime storage.
5. **Use `AppConfig.buildEngineUrl()` in the desktop shell** instead of a duplicated constant.
6. **Expose a real version source** shared by backend and UI.
7. **Add at least one external alert channel** for critical events.
8. **Reduce existing lint debt** until the repository can enforce lint cleanly in CI.

---

## Bottom line

The repository shows meaningful hardening progress, especially around **state recovery**, **secret handling**, **symmetric safety**, and **default API authentication**.

But the hub should still be treated as **pre-production / operator-controlled hardening stage**, not as a fully production-ready operating surface, until the blockers above are closed.
