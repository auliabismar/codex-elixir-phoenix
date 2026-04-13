defmodule MyAppWeb.LiveHelpers do
  import Phoenix.LiveView

  def mount(socket) do
    {:ok, assign(socket, loading: false)}
  end

  def handle_event("validate", params, socket) do
    {:noreply, socket}
  end

  def handle_event("submit", params, socket) do
    {:noreply, socket}
  end
end