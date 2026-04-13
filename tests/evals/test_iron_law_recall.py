import pytest

import iron_law_gateway

# Story 7.1: The 52-Test Pytest Iron Law Evaluation Suite

# DEFINITION OF MALICIOUS VARIANTS (52 TOTAL)
# -------------------------------------------

VARIANTS_BY_RULE = {
    "check_float_money": [
        {"name": "money_float_direct", "tool": "write_to_file", "params": {"TargetFile": "lib/app/schema.ex", "CodeContent": "field :price, :float"}},
        {"name": "money_float_patch", "tool": "apply_patch", "params": {"patch": "*** Update File: lib/app/schema.ex\n+  field :balance, :float"}},
        {"name": "money_float_whitespace", "tool": "write_to_file", "params": {"TargetFile": "lib/app/schema.ex", "CodeContent": "add    :cost   ,    :float"}},
        {"name": "money_float_parens", "tool": "write_to_file", "params": {"TargetFile": "lib/app/schema.ex", "CodeContent": "modify(:total, :float)"}},
        {"name": "money_float_multiline", "tool": "write_to_file", "params": {"TargetFile": "lib/app/schema.ex", "CodeContent": "field(\n  :subtotal,\n  :float\n)"}},
        {"name": "money_float_mixed_case", "tool": "write_to_file", "params": {"TargetFile": "lib/app/schema.ex", "CodeContent": "field :FEES, :float"}},
        {"name": "money_float_nested_field", "tool": "write_to_file", "params": {"TargetFile": "lib/app/schema.ex", "CodeContent": "field :transaction_amount, :float"}},
        {"name": "money_float_migration_add", "tool": "write_to_file", "params": {"TargetFile": "priv/repo/migrations/1.exs", "CodeContent": "add :price, :float"}},
        {"name": "money_float_migration_modify", "tool": "write_to_file", "params": {"TargetFile": "priv/repo/migrations/1.exs", "CodeContent": "modify :balance, :float"}},
        {"name": "money_float_with_comment", "tool": "write_to_file", "params": {"TargetFile": "lib/app/schema.ex", "CodeContent": "field :price, # comment\n :float"}},
    ],
    "block_string_to_atom": [
        {"name": "dynamic_atom_variable", "tool": "write_to_file", "params": {"TargetFile": "lib/app/util.ex", "CodeContent": "String.to_atom(some_var)"}},
        {"name": "dynamic_atom_interpolation", "tool": "write_to_file", "params": {"TargetFile": "lib/app/util.ex", "CodeContent": 'String.to_atom("user_#{id}")'}},
        {"name": "dynamic_atom_pipe", "tool": "write_to_file", "params": {"TargetFile": "lib/app/util.ex", "CodeContent": 'some_str |> String.to_atom()'}},
        {"name": "dynamic_atom_multiline", "tool": "write_to_file", "params": {"TargetFile": "lib/app/util.ex", "CodeContent": 'String.to_atom(\n  "prefix_" <> suffix\n)'}},
        {"name": "dynamic_atom_within_list", "tool": "write_to_file", "params": {"TargetFile": "lib/app/util.ex", "CodeContent": "[String.to_atom(v) for v <- list]"}},
        {"name": "dynamic_atom_apply", "tool": "write_to_file", "params": {"TargetFile": "lib/app/util.ex", "CodeContent": 'apply(String, :to_atom, [dynamic_string])'}},
        {"name": "dynamic_atom_in_function", "tool": "write_to_file", "params": {"TargetFile": "lib/app/util.ex", "CodeContent": "def map_atom(s), do: String.to_atom(s)"}},
        {"name": "dynamic_atom_with_options", "tool": "write_to_file", "params": {"TargetFile": "lib/app/util.ex", "CodeContent": "String.to_atom(x)"}},
        {"name": "dynamic_atom_concatenation", "tool": "write_to_file", "params": {"TargetFile": "lib/app/util.ex", "CodeContent": 'String.to_atom("fixed" <> dynamic)'}},
        {"name": "dynamic_atom_nested", "tool": "write_to_file", "params": {"TargetFile": "lib/app/util.ex", "CodeContent": "Enum.map(inputs, &String.to_atom/1)"}},
    ],
    "check_liveview_assign_new": [
        {"name": "assign_new_repo_all", "tool": "write_to_file", "params": {"TargetFile": "lib/app_web/live/page_live.ex", "CodeContent": 'def mount(_, _, socket) do\n  assign_new(socket, :users, fn -> Repo.all(User) end)\nend'}},
        {"name": "assign_new_repo_get", "tool": "write_to_file", "params": {"TargetFile": "lib/app_web/live/page_live.ex", "CodeContent": 'def mount(_, _, socket) do\n  assign_new(socket, :user, fn -> Repo.get(User, 1) end)\nend'}},
        {"name": "assign_new_custom_fetch", "tool": "write_to_file", "params": {"TargetFile": "lib/app_web/live/page_live.ex", "CodeContent": 'def mount(_, _, socket) do\n  assign_new(socket, :data, fn -> Accounts.get_user!(1) end)\nend'}},
        {"name": "assign_new_datetime", "tool": "write_to_file", "params": {"TargetFile": "lib/app_web/live/page_live.ex", "CodeContent": 'def mount(_, _, socket) do\n  assign_new(socket, :now, fn -> DateTime.utc_now() end)\nend'}},
        {"name": "assign_new_rand", "tool": "write_to_file", "params": {"TargetFile": "lib/app_web/live/page_live.ex", "CodeContent": 'def mount(_, _, socket) do\n  assign_new(socket, :val, fn -> :rand.uniform() end)\nend'}},
        {"name": "assign_new_uuid", "tool": "write_to_file", "params": {"TargetFile": "lib/app_web/live/page_live.ex", "CodeContent": 'def mount(_, _, socket) do\n  assign_new(socket, :id, fn -> UUID.uuid4() end)\nend'}},
        {"name": "assign_new_capture_syntax", "tool": "write_to_file", "params": {"TargetFile": "lib/app_web/live/page_live.ex", "CodeContent": 'def mount(_, _, socket) do\n  assign_new(socket, :stats, &fetch_stats/0)\nend'}},
        {"name": "assign_new_tuple_syntax", "tool": "write_to_file", "params": {"TargetFile": "lib/app_web/live/page_live.ex", "CodeContent": 'def mount(_, _, socket) do\n  assign_new(socket, :data, {MyModule, :get_data, []})\nend'}},
        {"name": "assign_new_multiline_callback", "tool": "write_to_file", "params": {"TargetFile": "lib/app_web/live/page_live.ex", "CodeContent": 'def mount(_, _, socket) do\n  assign_new(socket, :res, fn ->\n    Repo.one(query)\n  end)\nend'}},
        {"name": "assign_new_helper_search", "tool": "write_to_file", "params": {"TargetFile": "lib/app_web/live/page_live.ex", "CodeContent": 'def mount(_, _, socket) do\n  assign_new(socket, :list, fn -> search_products(q) end)\nend'}},
        {"name": "assign_new_complex_volatile", "tool": "write_to_file", "params": {"TargetFile": "lib/app_web/live/page_live.ex", "CodeContent": 'def mount(_, _, socket) do\n  assign_new(socket, :x, fn -> Enum.random([1, 2]) end)\nend'}},
        {"name": "assign_new_time", "tool": "write_to_file", "params": {"TargetFile": "lib/app_web/live/page_live.ex", "CodeContent": 'def mount(_, _, socket) do\n  assign_new(socket, :t, fn -> Time.utc_now() end)\nend'}},
    ],
    "require_connected_mount": [
        {"name": "connected_mount_repo_missing_guard", "tool": "write_to_file", "params": {"TargetFile": "lib/app_web/live/user_live.ex", "CodeContent": "def mount(_params, _session, socket) do\n  users = Repo.all(User)\n  {:ok, assign(socket, users: users)}\nend"}},
        {"name": "connected_mount_pubsub_missing_guard", "tool": "write_to_file", "params": {"TargetFile": "lib/app_web/live/user_live.ex", "CodeContent": "def mount(_, _, socket) do\n  PubSub.subscribe(App.PubSub, \"topic\")\n  {:ok, socket}\nend"}},
        {"name": "connected_mount_fetch_missing_guard", "tool": "write_to_file", "params": {"TargetFile": "lib/app_web/live/user_live.ex", "CodeContent": "def mount(_, _, s) do\n  data = Accounts.list_users()\n  {:ok, assign(s, data: data)}\nend"}},
        {"name": "connected_mount_multiline", "tool": "write_to_file", "params": {"TargetFile": "lib/app_web/live/user_live.ex", "CodeContent": "def mount(\n  _params,\n  _session,\n  socket\n) do\n  Repo.get(U, 1)\n  {:ok, socket}\nend"}},
        {"name": "connected_mount_with_whitespace", "tool": "write_to_file", "params": {"TargetFile": "lib/app_web/live/user_live.ex", "CodeContent": "def mount(  p  ,  s  ,  sock  ) do\n  Search.load_all()\n  {:ok, sock}\nend"}},
        {"name": "connected_mount_different_socket_name", "tool": "write_to_file", "params": {"TargetFile": "lib/app_web/live/user_live.ex", "CodeContent": "def mount(_, _, skt) do\n  Repo.all(X)\n  {:ok, skt}\nend"}},
        {"name": "connected_mount_complex_body", "tool": "write_to_file", "params": {"TargetFile": "lib/app_web/live/user_live.ex", "CodeContent": "def mount(_, _, socket) do\n  if true do\n    Repo.all(Z)\n  end\n  {:ok, socket}\nend"}},
        {"name": "connected_mount_nested_module", "tool": "write_to_file", "params": {"TargetFile": "lib/app_web/live/user_live.ex", "CodeContent": "def mount(_, _, socket) do\n  App.Context.get_item(1)\n  {:ok, socket}\nend"}},
        {"name": "connected_mount_search_helper", "tool": "write_to_file", "params": {"TargetFile": "lib/app_web/live/user_live.ex", "CodeContent": "def mount(_, _, socket) do\n  paginate_items(params)\n  {:ok, socket}\nend"}},
        {"name": "connected_mount_mixed_calls", "tool": "write_to_file", "params": {"TargetFile": "lib/app_web/live/user_live.ex", "CodeContent": "def mount(_, _, socket) do\n  Repo.get(X, 1)\n  PubSub.subscribe(T, \"t\")\n  {:ok, socket}\nend"}},
    ],
    "require_oban_idempotency": [
        {"name": "oban_worker_missing_unique", "tool": "write_to_file", "params": {"TargetFile": "lib/app/workers/job.ex", "CodeContent": "use Oban.Worker, queue: :events"}},
        {"name": "oban_worker_empty_unique", "tool": "write_to_file", "params": {"TargetFile": "lib/app/workers/job.ex", "CodeContent": "use Oban.Worker, unique: []"}},
        {"name": "oban_worker_missing_keys", "tool": "write_to_file", "params": {"TargetFile": "lib/app/workers/job.ex", "CodeContent": "use Oban.Worker, unique: [period: 60]"}},
        {"name": "oban_worker_multiline", "tool": "write_to_file", "params": {"TargetFile": "lib/app/workers/job.ex", "CodeContent": "use Oban.Worker,\n  queue: :default"}},
        {"name": "oban_worker_with_comment", "tool": "write_to_file", "params": {"TargetFile": "lib/app/workers/job.ex", "CodeContent": "use Oban.Worker # missing unique"}},
        {"name": "oban_worker_no_opts", "tool": "write_to_file", "params": {"TargetFile": "lib/app/workers/job.ex", "CodeContent": "use Oban.Worker"}},
        {"name": "oban_worker_other_opts", "tool": "write_to_file", "params": {"TargetFile": "lib/app/workers/job.ex", "CodeContent": "use Oban.Worker, max_attempts: 10"}},
        {"name": "oban_worker_patch_missing", "tool": "apply_patch", "params": {"patch": "*** Update File: lib/app/workers/job.ex\n+use Oban.Worker, queue: :low"}},
        {"name": "oban_worker_broken_unique", "tool": "write_to_file", "params": {"TargetFile": "lib/app/workers/job.ex", "CodeContent": "use Oban.Worker, unique: [key: :id]"}},
        {"name": "oban_worker_malformed_keys", "tool": "write_to_file", "params": {"TargetFile": "lib/app/workers/job.ex", "CodeContent": "use Oban.Worker, unique: [keys: :id]"}},
    ],
}


def _registered_rule_modules():
    return [rule["module"] for rule in iron_law_gateway.IronLawGateway().rule_registry]


def _build_malicious_variants():
    registered_modules = _registered_rule_modules()
    missing_coverage = [module for module in registered_modules if module not in VARIANTS_BY_RULE]
    extra_coverage = [module for module in VARIANTS_BY_RULE if module not in registered_modules]

    assert not missing_coverage, f"Missing eval coverage for registered rules: {missing_coverage}"
    assert not extra_coverage, f"Eval coverage exists for unregistered rules: {extra_coverage}"

    variants = []
    for module_name in registered_modules:
        for variant in VARIANTS_BY_RULE[module_name]:
            variants.append({**variant, "rule_module": module_name})

    assert len(variants) == 52, f"Expected 52 malicious variants, found {len(variants)}"
    return variants


MALICIOUS_VARIANTS = _build_malicious_variants()

SAFE_VARIANTS = [
    {"name": "safe_price_field", "tool": "write_to_file", "params": {"TargetFile": "lib/app/schema.ex", "CodeContent": "field :price, :decimal"}},
    {"name": "safe_atom_literal", "tool": "write_to_file", "params": {"TargetFile": "lib/app/util.ex", "CodeContent": 'String.to_atom("fixed")'}},
    {"name": "safe_atom_apply_literal", "tool": "write_to_file", "params": {"TargetFile": "lib/app/util.ex", "CodeContent": 'apply(String, :to_atom, ["fixed"])'}},
    {"name": "safe_assign_new", "tool": "write_to_file", "params": {"TargetFile": "lib/app_web/live/page_live.ex", "CodeContent": 'assign_new(socket, :val, fn -> 123 end)'}},
    {"name": "safe_connected_mount", "tool": "write_to_file", "params": {"TargetFile": "lib/app_web/live/user_live.ex", "CodeContent": "def mount(_, _, socket) do\n  if connected?(socket) do\n    Repo.all(User)\n  end\n  {:ok, socket}\nend"}},
    {"name": "safe_oban_worker", "tool": "write_to_file", "params": {"TargetFile": "lib/app/workers/job.ex", "CodeContent": "use Oban.Worker, unique: [keys: [:id], period: 60]"}},
]

def test_registered_rules_have_eval_coverage():
    """Every registered rule should contribute variants to the recall suite."""
    assert {variant["rule_module"] for variant in MALICIOUS_VARIANTS} == set(_registered_rule_modules())


@pytest.mark.parametrize("variant", MALICIOUS_VARIANTS, ids=[variant["name"] for variant in MALICIOUS_VARIANTS])
def test_recall_blocking(payload_runner, variant):
    """Ensure all malicious variants are blocked (Recall)."""
    # Use realistic Codex payload structure
    payload = {
        "tool": variant["tool"],
        "parameters": variant["params"]
    }
    
    exit_code, stdout, stderr = payload_runner(payload)
    
    assert exit_code == 1, f"Expected {variant['name']} to be blocked, but it was allowed."
    assert "IRON LAW VIOLATION" in stderr
    # Verify it wasn't blocked just because of malformed payload
    assert "Missing write parameters" not in stderr

@pytest.mark.parametrize("variant", SAFE_VARIANTS, ids=[variant["name"] for variant in SAFE_VARIANTS])
def test_precision_allowing(payload_runner, variant):
    """Ensure legitimate code is allowed (Precision)."""
    payload = {
        "tool": variant["tool"],
        "parameters": variant["params"]
    }

    exit_code, stdout, stderr = payload_runner(payload)
    
    assert exit_code == 0, f"Expected {variant['name']} to be allowed, but it was blocked: {stderr}"
