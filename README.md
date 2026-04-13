# Codex Elixir Phoenix

An AI-assisted development framework for Elixir and Phoenix projects. Provides intelligent skills, reference docs, and guardrails for building robust Phoenix applications.

## Overview

Codex Elixir Phoenix is a plugin for [Claude Code](https://claude.com/claude-code) that brings specialized Elixir/Phoenix development capabilities to your AI assistant. It includes:

- **Skills**: Specialized commands for common Phoenix development tasks
- **Reference Docs**: Comprehensive documentation for Elixir, Phoenix, Ecto, LiveView, Oban, and more
- **Guardrails**: Built-in patterns for data protection, architectural constraints, and best practices
- **Evaluation Suite**: Testing infrastructure for validating code quality and compliance

## Requirements

- [Claude Code](https://claude.com/claude-code) (latest)
- Elixir & Phoenix (for running generated code)
- Python 3.10+ (for evaluation harness)

## Installation

### Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/codex-elixir-phoenix.git
cd codex-elixir-phoenix

# Inject into your Phoenix project
./setup.sh /path/to/your/phoenix app
```

Or on Windows:

```powershell
.\setup.ps1 C:\path\to\your\phoenix-app
```

This copies the `.codex` directory into your Phoenix project, making all skills and references available.

### Manual Installation

Copy the `.codex` directory to your Phoenix project root:

```bash
cp -r .codex /path/to/your/phoenix-app/
```

## Available Skills

| Skill | Command | Description |
|-------|---------|-------------|
| **Intro** | `codex $phx-intro` | Interactive Phoenix tutorial for new users |
| **Plan** | `codex $phx-plan` | Generate feature plans with Elixir code examples |
| **Work** | `codex $phx-work` | Execute implementation tasks with verification |
| **Verify** | `codex $phx-verify` | Run verification and compilation checks |
| **Review** | `codex $phx-review` | Perform semantic code reviews |
| **Compound** | `codex $phx-compound` | Multi-file orchestration and refactoring |
| **Full** | `codex $phx-full` | Complete autonomous development workflow |

### Usage

Once installed in your Phoenix project, invoke skills through Claude Code:

```
You: Implement a user authentication system with LiveView
Claude: I'll use the phx-work skill to build this feature. Let me start with planning...
```

## Reference Documentation

The framework includes comprehensive reference docs in `.codex/references/`:

### Core Topics
- **Elixir Basics** - Language fundamentals, modules, functions
- **OTP** - Supervisors, GenServers, Applications
- **Mix** - Tasks, dependencies, configuration

### Web Frameworks
- **Phoenix** - Controllers, views, routing, plugs
- **LiveView** - Components, forms, async operations, JS interop

### Data Layer
- **Ecto** - Schemas, changesets, queries, associations, preloads
- **Phoenix Contexts** - Domain-driven design patterns

### Background Jobs
- **Oban** - Workers, queues, recurring jobs, testing

### API Development
- **REST APIs** - JSON serialization, OpenAPI, versioning, pagination
- **Webhooks** - Security, idempotency, error handling

### Testing
- **ExUnit** - Unit and integration testing
- **LiveView Testing** - Component and integration tests
- **Mox** - Mocking patterns

## Guardrails

Codex includes built-in "Iron Law" patterns that ensure code quality:

- **Data Type Protection** - Prevent accidental data leakage
- **Architectural Guardrails** - Enforce context boundaries
- **Background Job Idempotency** - Safe retry mechanisms
- **Input Validation** - Schema validation and sanitization

## Evaluation Suite

The project includes a comprehensive test harness for validating code quality:

```bash
cd tests
pytest
```

### Benchmarking

Run quality benchmarks to compare outputs:

```bash
pytest tests/benchmarks/test_quality_benchmarks.py
```

Output is generated in `tests/benchmarks/output/`.

## Project Structure

```
codex-elixir-phoenix/
├── .codex/                    # Main Codex plugin
│   ├── skills/                # Available skills
│   │   ├── phx-intro/        # Interactive tutorial
│   │   ├── phx-plan/         # Planning skill
│   │   ├── phx-work/         # Implementation skill
│   │   ├── phx-verify/      # Verification skill
│   │   ├── phx-review/       # Review skill
│   │   ├── phx-compound/     # Refactoring skill
│   │   └── phx-full/         # Full workflow
│   ├── references/           # Documentation
│   │   ├── elixir-basics.md
│   │   ├── phoenix/
│   │   ├── liveview/
│   │   ├── ecto/
│   │   ├── oban/
│   │   └── ...
│   └── hooks/               # Iron Law enforcement
├── tests/                   # Evaluation suite
│   └── benchmarks/          # Quality benchmarking
├── setup.sh                 # Unix installation script
├── setup.ps1               # Windows installation script
└── README.md
```

## License

MIT

## Acknowledgments

This project was inspired by [oliver-kriska/claude-elixir-phoenix](https://github.com/oliver-kriska/claude-elixir-phoenix), which provided the foundational concept for AI-assisted Phoenix development.

## Contributing

Contributions welcome! Please open an issue or PR on GitHub.