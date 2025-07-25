# Codebase Agent

A comprehensive framework for automated software development and code analysis using multi-agent systems and LLM-powered agents.

## 🌟 Overview

Codebase Agent is a powerful tool designed to streamline and automate various aspects of the software development lifecycle. It consists of two main components:

1. **Multi-Agent System**: A modular architecture that orchestrates multiple specialized agents to handle different phases of software development, from planning to implementation and testing.

2. **Code Analysis Agent**: An LLM-powered agent that analyzes code repositories to provide insights into structure, dependencies, design patterns, and recommendations for improvement.

## ✨ Features

### 🤖 Multi-Agent System

- **Modular Architecture**: Built with a flexible, modular design that allows for easy extension and customization.
- **Workflow Orchestration**: Coordinates multiple agents to execute complex software development workflows.
- **Dependency-Based Execution**: Ensures agents are executed in the correct order based on their dependencies.
- **Error Handling and Recovery**: Implements sophisticated error handling with retry logic and recovery strategies.
- **Thread-Safe Data Sharing**: Secure communication between agents through a shared data store.
- **Progress Tracking**: Comprehensive tracking of workflow progress and agent status.

### 📊 Code Analysis

- **Repository Analysis**: Analyzes code repositories to provide insights into structure and design.
- **Dependency Mapping**: Identifies and maps dependencies between components.
- **Design Pattern Recognition**: Detects common design patterns used in the codebase.
- **Complexity Assessment**: Evaluates code complexity and provides scores for individual files.
- **Improvement Recommendations**: Suggests practical improvements to enhance code quality.

## 📖 Usage

### Multi-Agent System

To use the multi-agent system for software development:

```python
from multi_agent_system.core.root_agent import create_root_agent

# Create the root agent
root_agent = create_root_agent()

# Execute the workflow with a project description
result = root_agent.execute({
    "description": "Create a web application for task management with user authentication"
})

# Access the results
print(f"Workflow success: {result['success']}")
print(f"Completed agents: {result['completed_agents']}")
print(f"Deliverables: {result['deliverables']}")
```

### Code Analysis Agent

To analyze a code repository:

```python
from code_analysis_agent.agent import analyze_directory

# Specify the directory to analyze
target_directory = "/path/to/your/project"

# Generate analysis prompt
analysis_prompt = analyze_directory(target_directory)

# Use the prompt with the code_analysis_agent
# (Implementation depends on how you're interfacing with the LLM)
```

## 🚀 Installation

### Prerequisites

- Python 3.13 or higher
- Dependencies listed in pyproject.toml

### Installation Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/good-jinu/coding-agent-using-adk.git
   cd codebase-agent
   ```

2. Install the package using uv:
   ```bash
   uv sync
   ```

## 🗂️ Project Structure

```
codebase-agent/
├── code_analysis_agent/       # Code analysis component
│   ├── __init__.py
│   └── agent.py               # Main code analysis agent implementation
├── multi_agent_system/        # Multi-agent system for software development
│   ├── README.md              # Documentation for multi-agent system
│   ├── __init__.py
│   └── core/                  # Core components of multi-agent system
│       ├── __init__.py
│       ├── agent_registry.py  # Agent registration and discovery
│       ├── base_agent.py      # Base class for all agents
│       ├── coordinator.py     # Workflow orchestration
│       ├── data_store.py      # Shared data storage
│       ├── models.py          # Data models
│       └── root_agent.py      # Main entry point for the system
├── test/                      # Test suite
│   ├── test_error_handling.py
│   ├── test_error_recovery.py
│   ├── test_workflow_orchestration.py
│   └── test_workflow_with_recovery.py
├── pyproject.toml             # Project metadata and dependencies
└── run_all_tests.py           # Script to run all tests
```

## 🛠️ Development

### Multi-Agent System

The multi-agent system follows a structured workflow:

1. **Project Planning**: Analyzes requirements and creates a detailed project plan.
2. **Module Design**: Designs the software architecture and module structure.
3. **Test Planning**: Creates comprehensive test strategies and plans.
4. **Code Implementation**: Implements code based on the module structure and test plans.
5. **Testing**: Executes tests and validates the implementation.
6. **Code Refinement**: Refines and optimizes code quality based on test results.

To extend the system, create new agent types that inherit from `BaseMultiAgent` and implement the required methods:

- `execute`: Implement the agent's main functionality
- `validate_input`: Validate input data structure and content
- `format_output`: Format execution result for the next agent in the pipeline

Register new agents with the `AgentRegistry` to include them in the workflow.

### Code Analysis Agent

The code analysis agent uses Google's ADK (Agent Development Kit) and LLM (Gemini 2.5 Flash model) to analyze code repositories. It provides:

- File-level analysis: Purpose, key components, dependencies, complexity
- Directory structure analysis: File distribution, organization
- Project-level analysis: Architecture patterns, design patterns, technologies

## 🧪 Testing

Run all tests with:

```bash
uv run python run_all_tests.py
```

Or run individual test files:

```bash
uv run python test/test_error_handling.py
uv run python test/test_workflow_orchestration.py
```
