#!/usr/bin/env python3
"""Test script for workflow orchestration functionality."""

import sys
import logging
from typing import Dict, Any

# Add the project root to Python path
sys.path.insert(0, ".")

from multi_agent_system.core import (
    BaseMultiAgent,
    MultiAgentCoordinator,
    get_global_registry,
    get_global_data_store,
)

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class MockProjectPlanningAgent(BaseMultiAgent):
    """Mock project planning agent for testing."""

    def __init__(self):
        super().__init__(
            name="ProjectPlanningAgent",
            description="Mock agent for project planning",
            instruction="Create a project plan from user input",
        )

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute project planning."""
        logger.info("Executing ProjectPlanningAgent")

        # Simulate project planning logic
        project_plan = {
            "project_name": "Test Project",
            "description": "A test project for workflow orchestration",
            "requirements": ["Requirement 1", "Requirement 2"],
            "scope": "Test scope",
            "estimated_complexity": "medium",
            "target_language": "python",
            "framework_preferences": ["pytest", "pydantic"],
        }

        return project_plan

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data."""
        return "project_context" in input_data

    def format_output(self, result: Any) -> Dict[str, Any]:
        """Format output."""
        return result


class MockModuleDesignAgent(BaseMultiAgent):
    """Mock module design agent for testing."""

    def __init__(self):
        super().__init__(
            name="ModuleDesignAgent",
            description="Mock agent for module design",
            instruction="Create module structure from project plan",
        )

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute module design."""
        logger.info("Executing ModuleDesignAgent")

        # Simulate module design logic
        module_structure = {
            "modules": [
                {
                    "name": "core",
                    "purpose": "Core functionality",
                    "public_interface": ["main_function"],
                    "dependencies": [],
                    "estimated_complexity": 5,
                    "file_path": "src/core.py",
                },
                {
                    "name": "utils",
                    "purpose": "Utility functions",
                    "public_interface": ["helper_function"],
                    "dependencies": [],
                    "estimated_complexity": 3,
                    "file_path": "src/utils.py",
                },
            ],
            "interfaces": [
                {
                    "name": "CoreInterface",
                    "methods": ["main_function"],
                    "properties": [],
                    "description": "Core interface",
                }
            ],
            "dependencies": {"core": [], "utils": []},
            "architecture_pattern": "layered",
        }

        return module_structure

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data."""
        return "project_plan" in input_data

    def format_output(self, result: Any) -> Dict[str, Any]:
        """Format output."""
        return result


def setup_workflow(coordinator: MultiAgentCoordinator):
    """Helper function to register agents for tests."""
    registry = get_global_registry()
    data_store = get_global_data_store()

    # Clear any existing data
    data_store.clear_data()
    registry.clear_agents()

    # Create mock agents
    planning_agent = MockProjectPlanningAgent()
    design_agent = MockModuleDesignAgent()

    # Register agents with dependencies
    coordinator.register_agent(planning_agent, dependencies=[])
    coordinator.register_agent(design_agent, dependencies=["ProjectPlanningAgent"])
    logger.info(f"Registered agents: {registry.list_agents()}")


def test_workflow_orchestration():
    """Test the workflow orchestration functionality."""
    logger.info("Starting workflow orchestration test")

    # Use a new coordinator for this test to ensure isolation
    coordinator = MultiAgentCoordinator()
    setup_workflow(coordinator)

    # Validate workflow setup
    validation_result = coordinator.validate_workflow_setup()
    logger.info(f"Workflow validation: {validation_result}")
    assert validation_result["valid"], (
        f"Workflow validation failed: {validation_result['errors']}"
    )

    # Test execution order
    execution_order = coordinator.get_agent_execution_order()
    logger.info(f"Execution order: {execution_order}")
    assert execution_order == ["ProjectPlanningAgent", "ModuleDesignAgent"]

    # Execute workflow
    logger.info("Starting workflow execution")
    result = coordinator.execute_workflow(
        "Create a simple Python project with core and utility modules"
    )

    logger.info(f"Workflow result: {result.to_dict()}")

    # Check results
    assert result.success, f"Workflow failed: {result.error_message}"
    logger.info("Workflow executed successfully!")

    # Verify data was stored correctly
    data_store = coordinator.data_store
    project_context = data_store.get_project_context()
    assert project_context.project_plan is not None, "Project plan was not created"
    assert project_context.module_structure is not None, (
        "Module structure was not created"
    )

    logger.info(f"Project name: {project_context.project_plan.project_name}")
    logger.info(f"Number of modules: {len(project_context.module_structure.modules)}")


def test_progress_monitoring():
    """Test workflow progress monitoring."""
    logger.info("Testing progress monitoring")

    progress_updates = []

    def progress_callback(workflow_state):
        """Callback to capture progress updates."""
        progress_info = {
            "status": workflow_state.status,
            "current_agent": workflow_state.current_agent,
            "completed_agents": workflow_state.completed_agents.copy(),
            "progress_percentage": workflow_state.get_progress_percentage(
                2
            ),  # 2 agents total
        }
        progress_updates.append(progress_info)
        logger.info(f"Progress update: {progress_info}")

    # Use a new coordinator for this test to ensure isolation
    coordinator = MultiAgentCoordinator()
    setup_workflow(coordinator)
    coordinator.add_progress_callback(progress_callback)

    # Execute workflow
    coordinator.execute_workflow("Test progress monitoring")

    logger.info(f"Total progress updates: {len(progress_updates)}")
    for i, update in enumerate(progress_updates):
        logger.info(f"Update {i + 1}: {update}")

    assert len(progress_updates) > 0, "Progress callback was not called"
