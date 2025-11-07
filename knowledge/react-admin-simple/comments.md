## Comments Resource

- **Registration**: `comments/index.tsx` maps CRUD components and `ChatBubbleIcon` into the resource config consumed by `<Resource name="comments" {...comments} />`.

### CommentList
- Built with `ListBase` to control pagination (6 per page by default) and supply context to custom children.
- `ListToolbar` attaches filters: global search and a `ReferenceInput` for `post_id`.
- `exporter` fetches related posts before exporting, rewrites `author_name` and `post_title`, and streams CSV via `jsonexport` / `downloadCSV`.
- Adaptive rendering:
  - `CommentGrid`: Material cards laid out in a responsive `Grid`, showing author avatar, body preview with ellipsis, related post link, and edit/show actions.
  - `CommentMobileList`: Compact `SimpleList` for narrow screens.
- `Pagination` exposes 6/9/12 rows-per-page switches.

### CommentCreate
- Simple `Create` + `SimpleFormConfigurable` layout targeting a modal-like width (30 em on large screens).
- Captures `post_id` via `PostReferenceInput`, enforces a 10-character minimum on author names, defaults `created_at` to `now`, and allows multiline bodies.

### CommentEdit
- Uses `useEditController` and `EditContextProvider` to manually assemble the page:
  - Top toolbar includes `ShowButton` and a `CreateButton` for posts.
  - Main content is a `Card` with `SimpleForm`, enabling unsaved-change warnings.
  - `ReferenceInput` for `post_id` supplies `AutocompleteInput` with custom `optionText`, `matchSuggestion`, quick-create dialog (`CreatePost`), and display of `title - id` pairs.
  - `LinkToRelatedPost` leverages `useCreatePath` to navigate to the associated post edit view.
  - Validates author name/body lengths (`minLength(10)`).

### CommentShow
- slimmed-down `Show` leveraging the new `RecordField` API to render labeled values.
- Prefetches the related post (via `meta.prefetch`) and wraps the record in a `Stack` for spacing.

### Supporting Components
- `PostReferenceInput`: Hybrid selector that offers quick-create and modal preview for posts.
  - Uses `useWatch` to detect the current selection, toggles a dialog for previews using `PostPreview`, and resets on closure.
- `PostPreview`: Reads the cached `getOne` result directly from `react-query` to avoid extra data fetches when previewing.
- `PostQuickCreate` & `PostQuickCreateCancelButton`: Provide a modal form for creating a minimal post (title + teaser) and returning the new choice to the parent input with error notifications on failure.

The comments resource highlights relation management, quick creation flows, and responsive card/table layouts tailored for content moderation scenarios.

