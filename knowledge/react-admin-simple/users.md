## Users Resource

- **Registration**: `users/index.tsx` exports CRUD components, sets `PeopleIcon`, and defines `recordRepresentation` as `name (role)`.

### Permission Model
- Relies heavily on `authProvider.canAccess` logic:
  - Roles (`admin`, `user`, `default`) gate access to `users`, `users.role`, `users.id`, and `posts.authors`.
  - Components use `useCanAccess` (async) to tailor UI before render, and `<CanAccess>` wrappers for inline enforcement.

### UserList
- Applies `getUserFilters` to include a `role` filter only when the viewer can access `users.role`.
- Default filter sets `role: 'user'` on load.
- Responsive layout toggles between `SimpleList` (mobile) and `DataTable` (desktop).
- Desktop table expands rows with `UserEditEmbedded`, letting admins edit names inline without navigation.
- Bulk actions limited to `BulkDeleteWithConfirmButton`.
- `Aside` component (see below) renders alongside the list for supplementary copy.

### UserCreate
- Gate-keeps the security tab based on `useCanAccess({ action: 'edit', resource: 'users.role' })`.
- Uses `useUnique()` to enforce unique names within the data provider, plus custom async validator (`isValidName`) rejecting "Admin".
- Toolbar showcases permission-aware "Save and add another" button: only rendered when `batch_create` is allowed.
- Form runs in `mode="onBlur"` and warns on unsaved changes.

### UserEdit
- Shares the same permission checks for the role field as the create form.
- Custom toolbar combines default save with `DeleteWithConfirmButton`.
- Overrides form submission (`onSubmit={newSave}`) to simulate server-side validation errors when name === "test".
- Wraps the form in `<Edit>` with `Aside` and `EditActions` (clone/show shortcuts).

### UserShow
- Mirrors the summary/security tabs, hiding the role tab when disallowed.
- Includes `<Aside />` inside the show view for contextual information.

### Aside
- `Aside.tsx` is a styled div providing descriptive text about app users; it collapses on smaller breakpoints using Material's `styled` API.

### Embedded Edit
- `UserEditEmbedded.tsx` reuses the `Edit` component inline:
  - Receives the parent record via `useRecordContext`.
  - Uses `SimpleForm` with default role `user` and required `name` input.
  - Disables the custom title by passing a single space to `title`.

The users resource demonstrates how to blend role-based access control, inline editing, async validators, and custom toolbars into cohesive admin flows.

