#!/usr/bin/env python3
"""Integration test showing workflow execution with error recovery."""

import sys
import logging
from typing import Dict, Any

# Add the project root to Python path
sys.path.insert(0, ".")

from multi_agent_system.core import (
    BaseMultiAgent,
    MultiAgentCoordinator,
    AgentExecutionError,
)
from multi_agent_system.core.agent_registry import AgentRegistry
from multi_agent_system.core.data_store import SharedDataStore

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ReliableAgent(BaseMultiAgent):
    """Mock agent that always succeeds."""

    def __init__(self, name: str):
        super().__init__(
            name=name,
            description=f"Reliable agent {name}",
            instruction="Always succeed",
        )

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"Executing {self.agent_name} - success")
        return {"status": "success", "agent": self.agent_name}

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        return True

    def format_output(self, result: Any) -> Dict[str, Any]:
        return result


class RecoverableAgent(BaseMultiAgent):
    """Mock agent that fails first time but can be skipped."""

    def __init__(self):
        super().__init__(
            name="CodeRefinementAgent",  # Optional agent
            description="Agent that can be skipped if it fails",
            instruction="Fail first time, can be skipped",
        )
        self._attempt_count = 0

    @property
    def attempt_count(self):
        return self._attempt_count

    @attempt_count.setter
    def attempt_count(self, value):
        self._attempt_count = value

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        self.attempt_count += 1
        logger.info(f"Executing {self.agent_name} - attempt {self.attempt_count}")

        # Always fail to test recovery
        raise AgentExecutionError(
            self.agent_name, "Refinement process failed - optimization not possible"
        )

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        return True

    def format_output(self, result: Any) -> Dict[str, Any]:
        return result


def test_workflow_with_recovery():
    """Test a complete workflow with error recovery."""
    logger.info("Testing workflow execution with error recovery")

    # Create a new coordinator with its own registry and data store for isolation
    registry = AgentRegistry()
    data_store = SharedDataStore()
    coordinator = MultiAgentCoordinator(registry=registry, data_store=data_store)

    # Create agents
    planning_agent = ReliableAgent("ProjectPlanningAgent")
    design_agent = ReliableAgent("ModuleDesignAgent")
    recoverable_agent = RecoverableAgent()  # This will fail but can be skipped
    implementation_agent = ReliableAgent("CodeImplementationAgent")

    # Register agents with dependencies
    coordinator.register_agent(planning_agent, dependencies=[])
    coordinator.register_agent(design_agent, dependencies=["ProjectPlanningAgent"])
    coordinator.register_agent(recoverable_agent, dependencies=["ModuleDesignAgent"])
    coordinator.register_agent(
        implementation_agent, dependencies=["CodeRefinementAgent"]
    )

    logger.info("Registered agents for workflow with recovery test")

    # Add progress callback to monitor recovery
    recovery_events = []

    def progress_callback(workflow_state):
        if workflow_state.failed_agents:
            recovery_events.append(
                {
                    "failed_agents": workflow_state.failed_agents.copy(),
                    "status": workflow_state.status,
                    "current_agent": workflow_state.current_agent,
                }
            )

    coordinator.add_progress_callback(progress_callback)

    # Execute workflow
    logger.info("Starting workflow execution with expected recovery")
    result = coordinator.execute_workflow("Test project with recoverable failure")

    logger.info(f"Workflow result: {result.to_dict()}")

    # Check results
    assert result.success, (
        f"Workflow should have succeeded with recovery: {result.error_message}"
    )
    logger.info("✓ Workflow completed successfully despite agent failure")

    # Verify that the recoverable agent failed but workflow continued
    assert "CodeRefinementAgent" in result.failed_agents, (
        "Expected recoverable agent to fail"
    )
    logger.info("✓ Recoverable agent correctly failed and was handled")

    # Check that other agents completed
    expected_completed = [
        "ProjectPlanningAgent",
        "ModuleDesignAgent",
        "CodeImplementationAgent",
    ]
    for agent_name in expected_completed:
        assert agent_name in result.completed_agents, (
            f"{agent_name} should have completed"
        )
        logger.info(f"✓ {agent_name} completed successfully")

    # Check recovery events
    assert recovery_events, "No recovery events were captured"
    logger.info(f"✓ Recovery events captured: {len(recovery_events)}")
    for event in recovery_events:
        logger.info(f"  Recovery event: {event}")


def test_user_intervention_workflow():
    """Test workflow that requires user intervention."""
    logger.info("Testing workflow with user intervention requirement")

    # Create coordinator with separate registry
    from multi_agent_system.core.agent_registry import AgentRegistry
    from multi_agent_system.core.data_store import SharedDataStore

    intervention_registry = AgentRegistry()
    intervention_data_store = SharedDataStore()
    coordinator = MultiAgentCoordinator(
        registry=intervention_registry, data_store=intervention_data_store
    )

    # Create a critical failing agent
    class CriticalFailingAgent(BaseMultiAgent):
        def __init__(self):
            super().__init__(
                name="ProjectPlanningAgent",  # Critical agent
                description="Critical agent that requires intervention",
                instruction="Fail critically",
            )

        def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
            raise AgentExecutionError(
                "ProjectPlanningAgent",
                "Critical configuration error - manual setup required",
            )

        def validate_input(self, input_data: Dict[str, Any]) -> bool:
            return True

        def format_output(self, result: Any) -> Dict[str, Any]:
            return result

    critical_agent = CriticalFailingAgent()
    coordinator.register_agent(critical_agent, dependencies=[])

    # Execute workflow (should fail and require intervention)
    result = coordinator.execute_workflow("Test project requiring intervention")

    # Check that workflow failed appropriately
    assert not result.success, "Workflow should have failed and required intervention"
    logger.info("✓ Workflow correctly failed due to critical agent failure")

    # Check for user intervention requests
    intervention_requests = coordinator.get_user_intervention_requests()
    assert intervention_requests, "No user intervention request was created"
    logger.info(
        f"✓ User intervention request created: {len(intervention_requests)} requests"
    )

    # Show intervention details
    for request in intervention_requests:
        logger.info(f"  Intervention for: {request.get('agent_name')}")
        logger.info(f"  Error: {request.get('error_message')}")
        logger.info(f"  Suggested actions: {request.get('suggested_actions', [])}")
