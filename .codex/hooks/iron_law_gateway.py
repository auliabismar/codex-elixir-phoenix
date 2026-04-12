import importlib
import json
import sys
from pathlib import Path

# Story 4.1: Iron Law Gateway Entrypoint
# Contract: IRON LAW VIOLATION: {Reasoning}. Require: {Prescribed Correction}.

WRITE_TOOL_NAMES = {
    "apply_patch",
    "replace_file_content",
    "write_to_file",
}

TOOL_NAME_KEYS = ("tool", "tool_name", "toolName")
PARAMETER_CONTAINER_KEYS = ("parameters", "tool_input", "toolInput", "toolArgs")
TARGET_FILE_KEYS = (
    "AbsolutePath",
    "TargetFile",
    "filePath",
    "file_path",
    "path",
    "target_file",
)
WRITE_HINT_KEYS = (
    "content",
    "input",
    "new_content",
    "new_str",
    "old_str",
    "patch",
    "replacement",
)
PATCH_TARGET_PREFIXES = (
    "*** Add File: ",
    "*** Delete File: ",
    "*** Update File: ",
)


class IronLawGateway:
    """
    Independent gateway for intercepting tool use and enforcing Iron Law constraints.
    Designed for < 500ms latency.
    """

    def __init__(self):
        # Register rule modules here in subsequent stories.
        # Format: {"module": "module_name", "description": "Human name"}
        self.rule_registry = [
            {"module": "check_float_money", "name": "Float Money Detector"},
            {"module": "block_string_to_atom", "name": "Dynamic Atom Protector"},
        ]

    def _violation(self, reasoning: str, correction: str) -> None:
        print(
            f"IRON LAW VIOLATION: {reasoning}. Require: {correction}.",
            file=sys.stderr,
        )
        sys.exit(1)

    def _extract_tool_name(self, payload: dict) -> str | None:
        for key in TOOL_NAME_KEYS:
            tool_name = payload.get(key)
            if isinstance(tool_name, str) and tool_name.strip():
                return tool_name.strip().lower()
        return None

    def _extract_parameters(self, payload: dict) -> dict | None:
        for key in PARAMETER_CONTAINER_KEYS:
            raw_params = payload.get(key)
            if raw_params is None:
                continue

            if isinstance(raw_params, dict):
                return raw_params

            if isinstance(raw_params, str) and raw_params.strip():
                try:
                    parsed = json.loads(raw_params)
                except json.JSONDecodeError:
                    self._violation(
                        "Malformed tool parameters",
                        "Provide a valid JSON object for the write arguments",
                    )

                if isinstance(parsed, dict):
                    return parsed

                self._violation(
                    "Unsupported tool parameter shape",
                    "Provide write arguments as a JSON object",
                )

            self._violation(
                "Unsupported tool parameter shape",
                "Provide structured write arguments",
            )

        if any(key in payload for key in TARGET_FILE_KEYS + WRITE_HINT_KEYS):
            return payload

        return None

    def _looks_like_write_operation(self, tool_name: str, params: dict | None) -> bool:
        if tool_name in WRITE_TOOL_NAMES:
            return True

        if not isinstance(params, dict):
            return False

        return any(key in params for key in WRITE_HINT_KEYS)

    def _extract_patch_targets(self, patch_text: str) -> list[str]:
        targets = []

        for line in patch_text.splitlines():
            for prefix in PATCH_TARGET_PREFIXES:
                if line.startswith(prefix):
                    target = line.removeprefix(prefix).strip()
                    if target:
                        targets.append(target)
                    break

        return targets

    def _extract_target_files(self, tool_name: str, params: dict) -> list[str]:
        if tool_name == "apply_patch":
            for key in ("input", "patch", "content"):
                patch_text = params.get(key)
                if isinstance(patch_text, str) and patch_text.strip():
                    return self._extract_patch_targets(patch_text)
            return []

        for key in TARGET_FILE_KEYS:
            target_file = params.get(key)
            if isinstance(target_file, str) and target_file.strip():
                return [target_file]

        return []

    def run(self):
        """Parse payload, filter for Elixir writes, and dispatch to rules."""
        try:
            # Read from stdin (Codex hook contract)
            raw_input = sys.stdin.read()
            if not raw_input:
                # No payload - nothing to check
                sys.exit(0)

            payload = json.loads(raw_input)
        except json.JSONDecodeError:
            print(
                "IRON LAW VIOLATION: Malformed hook payload. Require: Valid JSON from stdin.",
                file=sys.stderr,
            )
            sys.exit(1)
        except Exception as e:
            print(
                f"IRON LAW VIOLATION: Unexpected hook error: {str(e)}. Require: Stable execution environment.",
                file=sys.stderr,
            )
            sys.exit(1)

        # Validate basic structure
        if not isinstance(payload, dict):
            self._violation(
                "Unsupported hook payload shape",
                "Provide a structured JSON object payload",
            )

        tool = self._extract_tool_name(payload)
        if not tool:
            self._violation(
                "Missing tool name in hook payload",
                "Include the triggering tool identifier",
            )

        params = self._extract_parameters(payload)
        if not self._looks_like_write_operation(tool, params):
            sys.exit(0)

        if params is None:
            self._violation(
                "Missing write parameters in hook payload",
                "Provide structured target metadata for write operations",
            )

        target_files = self._extract_target_files(tool, params)
        if not target_files:
            self._violation(
                "Missing target file for write operation",
                "Provide a concrete file target before execution",
            )

        if not any(Path(target_file).suffix in [".ex", ".exs"] for target_file in target_files):
            sys.exit(0)

        # Add current directory to path for dynamic imports
        script_dir = str(Path(__file__).parent.absolute())
        if script_dir not in sys.path:
            sys.path.insert(0, script_dir)

        # Registry Dispatcher
        for rule_config in self.rule_registry:
            try:
                module_name = rule_config.get("module")
                if not module_name:
                    continue

                # Import rule module
                rule_module = importlib.import_module(module_name)
                
                # Dispatch check: check(tool_name, params, targets)
                violation = rule_module.check(tool, params, target_files)
                
                if violation:
                    self._violation(
                        violation.get("reasoning", "Unknown reasoning"),
                        violation.get("correction", "Unknown correction")
                    )

            except ImportError:
                print(
                    f"IRON LAW VIOLATION: Missing rule module {rule_config.get('module')}. Require: All registered rules present.",
                    file=sys.stderr,
                )
                sys.exit(1)
            except Exception as e:
                print(
                    f"IRON LAW VIOLATION: Gateway execution error in {rule_config.get('module')}: {str(e)}. Require: Bug-free rule implementation.",
                    file=sys.stderr,
                )
                sys.exit(1)

        # Allow if no rules blocked the write
        sys.exit(0)


if __name__ == "__main__":
    gateway = IronLawGateway()
    gateway.run()
