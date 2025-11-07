## Authentication & Internationalization

### Auth Provider (`authProvider.tsx`)
- **Identities**:
  - `login` / `password`: Default identity (`John Doe`) with full access inferred from absence of a role.
  - `user` / `password`: Stores role `user`, surfaces different avatar/name.
  - `admin` / `password`: Stores role `admin` with elevated rights.
- **Storage contract**: Persists `login`, `user`, `avatar`, optional `role`, and a `not_authenticated` flag in `localStorage`.
- **Login flow**: Recognizes the three demo users, resets auth flags, and resolves immediately; invalid credentials set `not_authenticated` and reject after a 1 s timeout for UX feedback.
- **Logout**: Clears stored identity, marks `not_authenticated`, and resolves.
- **Session checks**:
  - `checkError`: Rejects on HTTP 401/403 to trigger logouts.
  - `checkAuth`: Rejects when `not_authenticated` is present, otherwise resolves (keeping the demo logged in by default).
  - `getIdentity`: Returns the stored identity or the `DEFAULT_IDENTITY` fallback when no login is recorded.
- **Access Control**:
  - Strategy dispatches by role (`admin`, `user`, `default`).
  - Role-specific deny lists for `resource` and `action` pairs provide coarse-grained authorization.
  - Used extensively via `useCanAccess` / `<CanAccess>` to show/hide inputs, filters, bulk actions, and tabs.

### Internationalization (`i18nProvider.tsx`)
- Wraps `polyglotI18nProvider`, seeding English (`en`) strings from `i18n/en.ts`.
- Lazily loads French translations from `i18n/fr.ts` when the locale switches to `fr`, returning a promise for Polyglot to resolve.
- Exposes available locales to the language switcher: English and Français.
- Translations cover resource labels, custom actions (`post.action.save_and_add`, `simple.action.resetViews`), plus the sample TaskMapr copy pulled into components.

### Practical Notes
- Components rely on `useTranslate` to render localized labels (e.g., quick filters, dialogs, chips).
- Custom validators/messages use translation keys (`ra.validation.minLength`) so backend errors surface in the active language.
- Access control integrates directly with UI elements—compare post author sections (`CanAccess action="edit" resource="posts.authors"`) versus user role fields (`resource="users.role"`).

Together, these providers simulate multi-role authentication and multilingual UX, enabling the agent to reason about conditional UI rendering and message catalog usage across the example app.

