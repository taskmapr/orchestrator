## Posts Resource

- **Registration**: `posts/index.tsx` exports the resource config used by `<Resource name="posts" {...posts} />`, mapping list/create/edit/show components, setting `BookIcon`, and `recordRepresentation: 'title'`.

### PostList
- Responsive list switches between:
  - `InfiniteList` + `SimpleList` on small screens (`useMediaQuery`).
  - `List` with a dense `DataTable` on larger viewports.
- **Filters**: Combines `SearchInput`, a pre-filled `TextInput`, and a custom `QuickFilter` chip translating label keys.
- **Bulk actions**: Adds `ResetViewsButton` alongside default delete/export buttons.
- **Exporter**: Serializes posts with flattened backlink URLs via `jsonexport` and `downloadCSV`.
- **Row behavior**: `rowClick` returns `'edit'` for commentable posts, else `'show'`.
- **Expand panel**: `PostPanel` injects `record.body` as raw HTML for in-row previews.
- **Columns**: Mix of fields (`DateField`, `BooleanField`, `ReferenceManyCount`, `ReferenceArrayField` with tag chips) and action buttons.

### PostCreate
- Uses `Create` + `SimpleFormConfigurable` with custom toolbar buttons that demonstrate different redirect/reset flows.
- Default values for `average_note` and `published_at` via `useMemo`.
- Integrates `RichTextInput`, file upload for PDFs, array inputs for backlinks and authors, and `CanAccess` to gate the authors section.
- `DependantInput` hides the average note field until `title` has a value.
- `CreateUser` dialog leverages `useCreateSuggestionContext` to add users on the fly and returns the new record to the parent input.

### PostEdit
- Wrapper `Edit` supplies custom `EditActions` (clone/show/create shortcuts) and warns on unsaved changes.
- `TabbedForm` divides content into Summary, Body, Miscellaneous, and Comments tabs.
  - Summary: Editable `title`, `teaser`, notification checkboxes, `ImageInput`, and authors array (permission-gated).
  - Body: `RichTextInput`.
  - Miscellaneous: `TagReferenceInput` with dynamic published filter, backlinks, publish date, category picker with `CreateCategory` dialog, numeric and boolean fields, nested array inputs for pictures.
  - Comments: `ReferenceManyField` with `DataTable` plus inline `EditButton`.
- Demonstrates inline array editing, `FormDataConsumer`, and `CanAccess` wrappers for field-level permissions.

### PostShow
- Wraps `ShowView` driven by `useShowController` to share controller state.
- `TabbedShowLayout` mirrors edit tabs, with conditional teaser display based on record title.
- Displays tags using locale-aware `ReferenceArrayField` + `ChipField`, includes `InPlaceEditor` for `views`, and shows comment counts via `ReferenceManyCount`.
- `CreateRelatedComment` clones a comment to bootstrap a related record.

### Supporting Components
- `PostTitle`: Localized title template for headers.
- `ResetViewsButton`: Uses `useUpdateMany` with `undoable` mutation mode to reset selected posts' view counts and notify the user.
- `TagReferenceInput`: Custom reference array selector that toggles a `published` filter, supports creating tags from a dialog, and resets the field when filter switches.

Use this summary to locate advanced CRUD patterns, permission gating, dynamic form behavior, and auxiliary helpers used throughout the posts resource.

