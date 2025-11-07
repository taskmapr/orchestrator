## Tags Resource

- **Registration**: `tags/index.tsx` wires up CRUD components and declares `recordRepresentation: 'name.en'` for consistent labeling.

### TagList
- Driven by `ListBase` with a high `perPage` (1000) to load the full tree at once.
- Renders `ListActions` alongside a `Card` containing a collapsible hierarchy built by `Tree` and `SubTree` helpers.
- `Tree` splits nodes into roots (`parent_id` undefined) and resolves children on demand.
- `SubTree` manages expansion state (`openChildren`) to display nested lists with `ExpandMore`/`ExpandLess` icons and attaches `EditButton` actions.

### TagCreate
- `Create` + `SimpleFormConfigurable` providing a streamlined, translatable form.
- `TranslatableInputs` enables editing `name` in English and French, enforcing `required()` validation.
- Redirects to `list` after creation to refresh the tree.

### TagEdit
- Combines two pieces of UI:
  1. Standard `Edit` form mirroring the create layout with `TranslatableInputs` and `warnWhenUnsavedChanges`.
  2. A nested `List` wrapped in `ResourceContextProvider value="posts"` filtering posts by the current tag ID (`filter={{ tags: [id] }}`) and rendering a `DataTable` with edit links.
- Demonstrates cross-resource embedding inside a single screen.

### TagShow
- Minimal `Show` view using `SimpleShowLayout`, `TranslatableFields`, and a `BooleanField` for the `published` flag.

### Data Considerations
- `data.tsx` seeds tags with mixed `published` values and parent/child relationships (e.g., "Sport" → "Parkour", "Crossfit"), which the tree UI surfaces.
- Multilingual structure is `{ name: { en: string, fr?: string } }`; French copy loads dynamically when the locale switches.

Tags provide examples of hierarchical navigation, translation-friendly forms, and cross-resource dashboards that aggregate related records.

