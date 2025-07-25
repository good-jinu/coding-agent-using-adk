# Multi-Agent System for Software Development

This repository contains a comprehensive multi-agent system designed for automated software development. The system orchestrates multiple specialized agents to handle different phases of the software development lifecycle, from planning to implementation and testing.

## System Architecture

The multi-agent system is built with a modular architecture consisting of the following core components:

### Core Components

1. **RootAgent**: The main entry point and coordinator for the multi-agent system, managing the complete software development lifecycle.

2. **AgentRegistry**: Manages agent registration, discovery, and dependency resolution. Ensures agents are executed in the correct order based on their dependencies.

3. **MultiAgentCoordinator**: Orchestrates the execution of multiple agents, handles errors and recovery strategies, and tracks workflow progress.

4. **SharedDataStore**: Provides thread-safe storage and retrieval of project data, agent outputs, and workflow state information. Facilitates communication between agents.

5. **BaseMultiAgent**: Abstract base class for all agents in the system, providing standardized interfaces for execution, validation, and output formatting.

### Data Models

The system uses Pydantic models to represent various aspects of the software development process:

- **ProjectContext**: Central data model that holds all project-related information
- **ProjectPlan**: Represents the overall project plan and requirements
- **ModuleStructure**: Defines the software architecture and module structure
- **TestPlan**: Contains test strategies and plans for modules
- **CodeArtifact**: Represents implemented code
- **TestResult**: Contains test execution results
- **WorkflowState**: Tracks the state of workflow execution

## Workflow Process

The multi-agent system follows a structured workflow:

1. **Project Planning**: The ProjectPlanningAgent analyzes requirements and creates a detailed project plan.
2. **Module Design**: The ModuleDesignAgent designs the software architecture and module structure based on the project plan.
3. **Test Planning**: The TestPlanningAgent creates comprehensive test strategies and plans based on the module structure.
4. **Code Implementation**: The CodeImplementationAgent implements code based on the module structure and test plans.
5. **Testing**: The TestingAgent executes tests and validates the implementation.
6. **Code Refinement**: The CodeRefinementAgent refines and optimizes code quality based on test results.

## Error Handling and Recovery

The system implements sophisticated error handling and recovery mechanisms:

1. **Retry Logic**: Automatically retries failed agent executions with configurable retry counts and delays.
2. **Recovery Strategies**:
   - Transient error detection
   - Alternative execution approaches
   - Partial rollback and recovery
   - Non-critical agent skipping
   - User intervention requests

## Key Features

- **Dependency-Based Execution**: Agents are executed in the correct order based on their dependencies.
- **Thread-Safe Data Sharing**: Secure communication between agents through the shared data store.
- **Progress Tracking**: Comprehensive tracking of workflow progress and agent status.
- **Persistent Storage**: Optional persistent storage of workflow state and agent outputs.
- **User Intervention**: Support for requesting user intervention when automated recovery fails.

## Usage

To use the multi-agent system, create a RootAgent instance and provide a project description:

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

## Extending the System

The system can be extended by creating new agent types that inherit from BaseMultiAgent and implementing the required methods:

- `execute`: Implement the agent's main functionality
- `validate_input`: Validate input data structure and content
- `format_output`: Format execution result for the next agent in the pipeline

Register new agents with the AgentRegistry to include them in the workflow.