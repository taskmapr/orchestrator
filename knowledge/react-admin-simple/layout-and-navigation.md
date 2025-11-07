## Layout & Navigation

### Global Shell
- `index.tsx` wraps `<Admin>` with `React.StrictMode` and TaskMapr's `<HighlightProvider>`, ensuring overlays can highlight elements across the app.
- `layout={Layout}` overrides the default admin shell with a custom composition defined in `Layout.tsx`.

### Custom Layout Component (`Layout.tsx`)
- Defines `MyAppBar` extending `<AppBar>` to render `<TitlePortal>` (for dynamic page titles) and `<InspectorButton>` (react-admin dev tool).
- `MyMenu` limits visible resources (posts, comments, tags, users) and assigns keyboard shortcuts like `g>p` for quick navigation.
- Wraps children in `<Layout appBar={MyAppBar} menu={MyMenu}>` and appends `<ReactQueryDevtools>` anchored bottom-left with `initialIsOpen={false}`.

### Routing Extensions
- `CustomRouteNoLayout` (used for `/custom`, `/custom1`) demonstrates unauthenticated layout pages:
  - Calls `useGetList` to show post counts.
  - Displays a loader while pending and simple totals afterward.
- `CustomRouteLayout` (used for `/custom2`, `/custom3`) keeps the admin chrome:
  - Calls `useAuthenticated()` to require login before rendering.
  - Fetches posts with pagination/sorting and feeds the results into `<DataTable>` for quick read-only access.
  - Renders `<Title>` to keep the admin page title consistent.
- `CustomRoutes` wiring in `index.tsx` illustrates both `noLayout` and standard layout flavors, each with their own route elements.

### Navigation Patterns
- `Menu.ResourceItem` keyboard shortcuts bubble to the root, enabling command palette-like jumps (e.g., press `g` then `p`).
- `ReferenceManyCount`, `ReferenceField`, and `LinkToRelatedPost` components in resource screens provide contextual navigation between posts and comments.

This setup showcases how to customize the admin chrome while mixing layout-bound and standalone pages, giving agents a clear map of navigation behavior throughout the simple example.

