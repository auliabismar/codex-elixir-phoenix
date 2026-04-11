# Elixir Basics

## Overview
Core Elixir language concepts and idioms.

## Data Types
```elixir
# Atoms
:ok
:error

# Tuples
{:ok, "data"}
{:error, "msg"}

# Lists
[1, 2, 3]
[head | tail]

# Maps
%{key: "value"}
%{"key" => "value"}

# Structs
%User{name: "Alice"}
```

## Pattern Matching
```elixir
def process({:ok, data}) do
  data
end

def process({:error, reason}) do
  {:error, reason}
end
```

## Pipe Operator
```elixir
data
|> transform()
|> filter()
|> validate()
```

## Sigils
```elixir
~r/regex/       # Regex
~w[word list]a  # Word list (atoms)
~D[2024-01-01]  # Date
~U[2024-01-01 12:00:00Z]  # UTC DateTime