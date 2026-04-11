# Ecto Transactions

## Key Points
- Wrap related writes in `Repo.transaction/1` when consistency matters.
- Return `{:ok, value}` or `{:error, reason}` from transaction callbacks for predictable rollbacks.
- Keep transaction bodies short and free of network calls.
