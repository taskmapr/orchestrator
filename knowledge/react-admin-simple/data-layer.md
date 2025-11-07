## Data Layer

- **Fake REST provider**: `dataProvider.tsx` starts with `fakeRestProvider(data, true, 300)` which:
  - Seeds records from `data.tsx`.
  - Enables logging and a 300 ms artificial latency to mimic network calls.

- **Lifecycle hooks**: Wrapped with `withLifecycleCallbacks` to cascade deletes:
  - `beforeDelete` on `posts` fetches related `comments`, issues `deleteMany`, and forces `queryClient.invalidateQueries(['comments'])` to keep caches in sync.

- **Tag search augmentation**: `addTagsSearchSupport` decorates `getList` to handle:
  - Partial pagination metadata for `comments` (`hasNextPage`, `hasPreviousPage`).
  - Custom full-text filtering on `tags` when a `_q` filter is present, using regex matching via `lodash/get` while preserving other filters (e.g., `published`).

- **Upload support**: `addUploadFeature.tsx` intercepts `update('posts')` calls when `pictures` include `File` objects:
  - Converts each file to base64 with `FileReader`.
  - Rewrites `pictures` to objects with `{ src, title }` alongside existing images before delegating.

- **Failure simulation proxy**: A `Proxy` layer (`sometimesFailsDataProvider`) lets the demo emulate API errors:
  - Honors a `session_ended` flag in `localStorage` to throw a 403 `ResponseError`.
  - Rejects `posts` updates when `title === 'f00bar'`, returning a `HttpError` with field-level validation messages.
  - Otherwise forwards calls to the upload-capable provider. Symbol/`then` accesses get ignored to avoid breaking promises.

- **Query client**: `queryClient.ts` exports a singleton `QueryClient` consumed by `<Admin>` and directly queried in components like `PostPreview` to reuse cached records without extra network calls.

- **Seed data (`data.tsx`)**:
  - `posts`: Rich bodies, nested `pictures`, `backlinks`, `notifications`, tag IDs, categories, and flags (e.g., `commentable`).
  - `comments`: Link back to posts, include nested author info, and cover a spread of dates for pagination examples.
  - `tags`: Support multilingual names (`name.en`, `name.fr` once translated), publication flags, and `parent_id` for hierarchy demos.
  - `users`: Provide roles (`admin`, `user`, `user_simple`) plus metadata used by `recordRepresentation` strings.

- **Validators**: `validators.tsx` simply re-exports `react-admin` `required` and `number` validators, offering a central import path for forms.

Together these pieces turn a static dataset into a lifelike backend, enabling the UI to demonstrate optimistic updates, cascading operations, and error handling patterns.

