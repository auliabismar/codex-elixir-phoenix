# LiveView Forms

## Overview
LiveView provides form handling with optimistic UI and real-time feedback.

## Basic Form Pattern
```elixir
def render(assigns) do
  ~H"""
  <.form for={@form} phx-submit="save">
    <.input field={@form[:name]} label="Name" />
    <.input field={@form[:email]} label="Email" />
    <button>Save</button>
  </.form>
  """
end

def handle_event("save", %{"user" => user_params}, socket) do
  case Accounts.create_user(user_params) do
    {:ok, _user} ->
      {:noreply, put_flash(socket, :info, "Created!")}

    {:error, changeset} ->
      {:noreply, assign(socket, form: to_form(changeset))}
  end
end
```

## Key PhX Events
- `phx-change` - Form field change
- `phx-submit` - Form submission
- `phx-feedback-for` - Validation feedback
- `phx-auto-recover` - Auto recovery on crash