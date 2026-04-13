defmodule MyAppWeb.UserLive do
  use MyAppWeb, :live_view
  def render(assigns) do
    ~H"""
    <div id="user-hook" phx-hook="UserHook"></div>
    """
  end
end
