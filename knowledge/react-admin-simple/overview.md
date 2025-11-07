## React-Admin Simple Example Overview

- **Purpose**: Demonstrates a full CRUD admin built with `react-admin`, backed by an in-memory Fake REST data provider and enhanced with TaskMapr integration hooks.
- **Entry point**: `index.tsx` mounts `<Admin>` inside a `HighlightProvider`, wires providers (`authProvider`, `dataProvider`, `i18nProvider`, `queryClient`), registers four resources (`posts`, `comments`, `tags`, `users`), and declares several custom routes rendered with or without the admin layout.
- **Layout**: `Layout.tsx` wraps the standard `<Layout>` with a custom app bar (`<TitlePortal>`, `<InspectorButton>`), a trimmed menu with keyboard shortcuts, and the React Query Devtools floating button.
- **TaskMapr overlay**: `TaskMaprOverlay` (from `taskmaprIntegration.tsx`) instantiates the TaskMapr client using either `VITE_TASKMAPR_ENDPOINT` or a local fallback, then renders the overlay bundle so the admin UI can be orchestrated externally.
- **Styling**: Global styles come from `assets/app.css` plus the TaskMapr overlay package stylesheet imported at the root.
- **Providers and utilities**:
  - `authProvider.tsx` supports three identities (`login`, `user`, `admin`) and role-based `canAccess` checks that gate fields/actions.
  - `dataProvider.tsx` layers lifecycle callbacks, tag search helpers, file uploads, and failure simulation on top of `ra-data-fakerest` seeded by `data.tsx`.
  - `i18nProvider.tsx` bootstraps Polyglot translations with English default and lazy-loaded French copy.
  - `queryClient.ts` exposes the shared React Query client passed to `<Admin>`.
- **Resources**:
  - `posts`: Rich CRUD flows with responsive tables, quick filters, inline editors, bulk actions, nested arrays, dynamic tag filtering, and embedded user creation.
  - `comments`: Card-based or list renderings, post preview dialogs, quick-create flows, and relation-aware exports.
  - `tags`: Hierarchical explorer, translatable forms, and cross-linked post listings.
  - `users`: Permission-aware forms/lists, embedded editing, custom toolbars, and uniqueness validation.
- **Custom routes**: `/custom`, `/custom1` render `CustomRouteNoLayout`; `/custom2`, `/custom3` render `CustomRouteLayout`, showcasing protected pages inside/outside the admin chrome.
- **Data model**: `data.tsx` seeds posts, comments, tags (with parent/child relationships and multilingual fields), and users with roles and permissions referenced throughout the UI.

Use this document as a map before diving into deeper breakdowns in the companion markdown files.

