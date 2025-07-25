"""
Multi-Agent Coding System

A comprehensive multi-agent system that automates the entire software development
lifecycle from planning to implementation and testing.
"""

from typing import Dict, Any, Optional
from .core.root_agent import create_root_agent
from .core.coordinator import MultiAgentCoordinator
from .core.agent_registry import get_global_registry

# Create the root agent instance for ADK compatibility
root_agent = create_root_agent()

__version__ = "0.1.0"


class MultiAgentSystem:
    """
    Main entry point for the multi-agent system.

    Provides a simplified interface for executing the complete multi-agent workflow.
    """

    def __init__(self):
        """Initialize the multi-agent system."""
        self.coordinator = MultiAgentCoordinator()
        self.root_agent = root_agent

    def execute_workflow(
        self, project_description: str, workflow_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute the complete multi-agent workflow.

        Args:
            project_description: Description of the software project to develop
            workflow_id: Optional workflow ID

        Returns:
            Dictionary containing workflow results and output artifacts
        """
        # Prepare input for the root agent
        input_data = {"description": project_description, "workflow_id": workflow_id}

        # Execute the workflow using the root agent
        return self.root_agent.execute(input_data)

    def get_available_agents(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about all available agents.

        Returns:
            Dictionary mapping agent names to their information
        """
        registry = get_global_registry()
        agents_info = {}

        for agent_name in registry.list_agents():
            agents_info[agent_name] = registry.get_agent_info(agent_name)

        return agents_info

    def get_workflow_progress(self) -> Optional[Dict[str, Any]]:
        """
        Get current workflow progress information.

        Returns:
            Dictionary with progress information or None if no active workflow
        """
        return self.root_agent.get_workflow_progress()

    def cancel_workflow(self) -> bool:
        """
        Cancel the currently running workflow.

        Returns:
            True if workflow was cancelled, False if no active workflow
        """
        return self.root_agent.cancel_workflow()
