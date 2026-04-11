# API Pagination

## Key Points
- Prefer cursor pagination for mutable datasets and offset pagination for simple admin lists.
- Return pagination metadata with every paged response.
- Enforce a maximum page size at the boundary.
