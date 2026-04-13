defmodule MyAppWeb.Components.Modal do
  use MyAppWeb, :component

  attr :show, :boolean, default: false
  attr :title, :string, default: ""
  slot :inner_block, required: true

  def modal(assigns) do
    ~H"""
    <div class={"modal", hidden: !@show} phx-click-away="close">
      <div class="modal-content">
        <h2><%= @title %></h2>
        <%= render_slot(@inner_block) %>
      </div>
    </div>
    """
  end
end