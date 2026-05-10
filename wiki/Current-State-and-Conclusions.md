# Current State & Conclusions (2026-05-10)

> Repository reality check based on verified files and code paths.
> This page summarizes what is currently true, what is drifting, and what to improve first.

---

## Verified Current State

### Runtime and bots

- Active runtime bot layer is centered on **Dorothy + Elphaba** (`runtime/bot/`).
- API services and routers also map to Dorothy/Elphaba and symmetric operation:
  - `runtime/api/elphaba_service.py`
  - `runtime/api/routers/elphaba.py`
  - `runtime/api/routers/symmetric.py`
- The Flutter UI currently exposes a unified hub surface (`desktop_shell/lib/pages/unified_hub_page.dart`).

### State durability and resilience

- **StateWAL is integrated**:
  - State hydration at startup: `runtime/app.py` (`state_wal.hydrate`)
  - Periodic persistence in gateway poll loop: `runtime/connectors/binance_gateway.py` (`state_wal.persist`)
- Operational resilience features are present in docs and code paths (immortal startup scripts, ops protocol endpoints).

### Configuration baseline

- Default API port is aligned at **8000** in runtime settings (`PECUNATOR_API_PORT` default).

### Security handling

- `CHART_IMG_API_KEY` in VMO is sourced from environment (`os.environ.get(...)`), not hardcoded in source.

---

## Documentation Drift Detected

Several wiki sections still describe a topology that does not match current runtime reality:

- References to active Masha/Thusnelda runtime stack in architecture/module map pages.
- Mentions of `runtime/modules/bots/*` as canonical active bot layer while active runtime entry paths are under `runtime/bot/` for Dorothy/Elphaba.
- Some docs still imply module composition that differs from actual `runtime/api/` and `desktop_shell/lib/pages/` structure.

---

## Sadistic Critique (Technical)

1. **The system improved in resilience, but docs are lagging behind architecture.**
   - Strong operational controls exist, but wiki trust drops when the map diverges from code.
2. **Startup still performs auto-update (`git pull`) in engine boot.**
   - This introduces operational unpredictability in production-like contexts.
3. **Repository narrative is split between old 3-bot model and current symmetric Dorothy/Elphaba model.**
   - This slows onboarding and increases wrong assumptions in maintenance tasks.

---

## Conclusions

- The repo has meaningful new features and resilience gains.
- The main current weakness is not capability, but **consistency between implementation and documentation**.
- Performance/efficiency work should now prioritize **operational predictability** and **documentation-code parity**.

---

## Improvement Plan (Highest Impact First)

1. **Remove boot-time auto-update from `runtime/main.py`**
   - Keep updates as explicit operator action or external supervisor task.
2. **Normalize wiki architecture pages to current Dorothy/Elphaba reality**
   - Update `Arquitectura` and `Mapa-de-Modulos` first.
3. **Unify canonical bot import layer and document it clearly**
   - Explicitly mark `runtime/bot/` vs `runtime/modules/bots/` status.
4. **Create a recurring doc parity check in PR reviews**
   - If runtime/api/bot topology changes, wiki architecture pages must be updated in the same PR.

---

## Sources (verified on 2026-05-10)

- `runtime/app.py`
- `runtime/connectors/binance_gateway.py`
- `runtime/main.py`
- `runtime/core/settings.py`
- `runtime/api/`
- `runtime/api/routers/`
- `runtime/bot/`
- `desktop_shell/lib/pages/`
- `runtime/modules/vmo.py`
