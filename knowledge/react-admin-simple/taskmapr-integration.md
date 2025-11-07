## TaskMapr Integration

- **Overlay Provider**: `index.tsx` imports `HighlightProvider` from `@taskmapr/ui-overlay` and wraps the entire admin tree, enabling TaskMapr to highlight UI components for guided automations.

- **Overlay Component (`taskmaprIntegration.tsx`)**:
  - Exposes `TaskMaprOverlay`, a lightweight component rendered once beneath `<Admin>`.
  - Calls `useTaskMaprActionHandlers()` to retrieve default action callbacks (navigation, form filling, etc.).
  - Resolves `agentEndpoint` from `VITE_TASKMAPR_ENDPOINT` or defaults to `http://localhost:8000/api/taskmapr/orchestrate`, matching the orchestrator FastAPI endpoint.
  - Invokes `useTaskMaprClientInstance` with the endpoint and action handlers, then renders the returned `<Overlay />` component supplied by the TaskMapr UI package.

- **Styling**: `index.tsx` imports `@taskmapr/ui-overlay/taskmapr-overlay.css`, ensuring the overlay renders correctly without additional setup.

- **Runtime Expectations**:
  - The overlay package manages its own portals and isolation, so no explicit DOM container is needed.
  - Action handlers can be extended to interop with admin events; the example uses defaults, but the orchestrator could override them if necessary.
  - When the orchestrator is offline, the overlay still mounts but remote actions will fail gracefully until the agent endpoint responds.

Use this reference when wiring the simple example into the broader TaskMapr orchestration flow or when debugging overlay-related behaviors.

