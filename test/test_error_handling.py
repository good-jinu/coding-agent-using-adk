#!/usr/bin/env python3
"""Test script for workflow error handling."""

import sys
import logging
from typing import Dict, Any

# Add the project root to Python path
sys.path.insert(0, ".")

from multi_agent_system.core import (
    BaseMultiAgent,
    MultiAgentCoordinator,
    get_global_data_store,
    AgentExecutionError,
)

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class FailingAgent(BaseMultiAgent):
    """Mock agent that always fails for testing error handling."""

    def __init__(self):
        super().__init__(
            name="FailingAgent",
            description="Mock agent that always fails",
            instruction="Always fail for testing purposes",
        )

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute and fail."""
        logger.info("Executing FailingAgent - about to fail")
        raise AgentExecutionError("FailingAgent", "Intentional failure for testing")

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data."""
        return True

    def format_output(self, result: Any) -> Dict[str, Any]:
        """Format output."""
        return result


class SuccessfulAgent(BaseMultiAgent):
    """Mock agent that always succeeds."""

    def __init__(self):
        super().__init__(
            name="SuccessfulAgent",
            description="Mock agent that always succeeds",
            instruction="Always succeed for testing purposes",
        )

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute successfully."""
        logger.info("Executing SuccessfulAgent")
        return {"status": "success", "message": "Agent executed successfully"}

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data."""
        return True

    def format_output(self, result: Any) -> Dict[str, Any]:
        """Format output."""
        return result


def test_error_handling():
    """Test workflow error handling and recovery."""
    logger.info("Testing error handling")

    # Create a new coordinator for this test
    coordinator = MultiAgentCoordinator()
    data_store = get_global_data_store()
    data_store.clear_data()

    # Create agents - one that fails and one that succeeds
    # Make the failing agent critical by naming it like a critical agent
    class CriticalFailingAgent(BaseMultiAgent):
        def __init__(self):
            super().__init__(
                name="ProjectPlanningAgent",  # Critical agent name
                description="Critical agent that fails",
                instruction="Fail critically",
            )

        def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
            logger.info("Executing CriticalFailingAgent - about to fail")
            raise AgentExecutionError(
                "ProjectPlanningAgent", "Critical failure for testing"
            )

        def validate_input(self, input_data: Dict[str, Any]) -> bool:
            return True

        def format_output(self, result: Any) -> Dict[str, Any]:
            return result

    failing_agent = CriticalFailingAgent()
    successful_agent = SuccessfulAgent()

    # Register agents
    coordinator.register_agent(failing_agent, dependencies=[])
    coordinator.register_agent(successful_agent, dependencies=["ProjectPlanningAgent"])

    logger.info("Registered agents with failing dependency")

    # Execute workflow - should fail due to failing agent
    result = coordinator.execute_workflow("Test error handling")

    logger.info(f"Workflow result: {result.to_dict()}")

    # Verify the workflow failed as expected
    assert not result.success, (
        "Workflow should have failed due to critical agent failure but didn't"
    )
    logger.info("Workflow failed as expected due to critical failing agent")
    assert "ProjectPlanningAgent" in result.failed_agents, (
        "Critical agent not marked as failed"
    )
    logger.info("Critical agent correctly marked as failed")


def test_retry_mechanism():
    """Test the retry mechanism for failed agents."""
    logger.info("Testing retry mechanism")

    class SometimesFailingAgent(BaseMultiAgent):
        """Agent that fails first few times then succeeds."""

        def __init__(self):
            super().__init__(
                name="SometimesFailingAgent",
                description="Agent that fails first few times",
                instruction="Fail first few times then succeed",
            )
            self._attempt_count = 0

        @property
        def attempt_count(self):
            return self._attempt_count

        @attempt_count.setter
        def attempt_count(self, value):
            self._attempt_count = value

        def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
            """Execute with conditional failure."""
            self.attempt_count += 1
            logger.info(f"SometimesFailingAgent attempt {self.attempt_count}")

            if self.attempt_count < 3:  # Fail first 2 attempts
                raise AgentExecutionError(
                    "SometimesFailingAgent", f"Failure on attempt {self.attempt_count}"
                )

            return {"status": "success", "attempt": self.attempt_count}

        def validate_input(self, input_data: Dict[str, Any]) -> bool:
            return True

        def format_output(self, result: Any) -> Dict[str, Any]:
            return result

    # Create coordinator with retry settings and separate registry
    from multi_agent_system.core.agent_registry import AgentRegistry
    from multi_agent_system.core.data_store import SharedDataStore

    retry_registry = AgentRegistry()
    retry_data_store = SharedDataStore()
    coordinator = MultiAgentCoordinator(
        registry=retry_registry,
        data_store=retry_data_store,
        max_retries=3,
        retry_delay=0.1,
    )

    # Create and register agent
    sometimes_failing_agent = SometimesFailingAgent()
    coordinator.register_agent(sometimes_failing_agent, dependencies=[])

    logger.info("Testing agent that fails first 2 attempts")

    # Execute workflow - should succeed after retries
    result = coordinator.execute_workflow("Test retry mechanism")

    logger.info(f"Workflow result: {result.to_dict()}")

    assert result.success, "Workflow should have succeeded after retries"
    logger.info("Workflow succeeded after retries as expected")
