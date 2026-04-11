# Ecto Associations

## Key Points
- Use `belongs_to`, `has_one`, `has_many`, and `many_to_many` to describe relationships in schemas.
- Preload associations before rendering them outside the Repo boundary.
- Pair association definitions with `cast_assoc/3` only when nested writes are part of the contract.

## Example
```elixir
schema "posts" do
  belongs_to :author, MyApp.Accounts.User
  many_to_many :tags, MyApp.Blog.Tag, join_through: "posts_tags"
end
```
