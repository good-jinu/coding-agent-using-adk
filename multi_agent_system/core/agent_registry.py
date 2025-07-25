"""Agent registration and discovery system."""

from typing import Dict, List, Optional, Type
import logging
from .base_agent import BaseMultiAgent

logger = logging.getLogger(__name__)


class AgentRegistry:
    """
    Registry for managing agent registration and discovery.

    Provides centralized management of available agents and their capabilities.
    """

    def __init__(self):
        """Initialize the agent registry."""
        self._agents: Dict[str, BaseMultiAgent] = {}
        self._agent_types: Dict[str, Type[BaseMultiAgent]] = {}
        self._dependencies: Dict[str, List[str]] = {}

    def register_agent(
        self, agent: BaseMultiAgent, dependencies: Optional[List[str]] = None
    ) -> None:
        """
        Register an agent with the registry.

        Args:
            agent: Agent instance to register
            dependencies: List of agent names this agent depends on

        Raises:
            ValueError: If agent name already exists
        """
        if agent.agent_name in self._agents:
            raise ValueError(f"Agent {agent.agent_name} is already registered")

        self._agents[agent.agent_name] = agent
        self._agent_types[agent.agent_name] = type(agent)
        self._dependencies[agent.agent_name] = dependencies or []

        logger.info(f"Registered agent: {agent.agent_name}")

    def unregister_agent(self, agent_name: str) -> None:
        """
        Unregister an agent from the registry.

        Args:
            agent_name: Name of agent to unregister

        Raises:
            KeyError: If agent name not found
        """
        if agent_name not in self._agents:
            raise KeyError(f"Agent {agent_name} not found in registry")

        del self._agents[agent_name]
        del self._agent_types[agent_name]
        del self._dependencies[agent_name]

        logger.info(f"Unregistered agent: {agent_name}")

    def get_agent(self, agent_name: str) -> BaseMultiAgent:
        """
        Get an agent by name.

        Args:
            agent_name: Name of the agent

        Returns:
            Agent instance

        Raises:
            KeyError: If agent name not found
        """
        if agent_name not in self._agents:
            raise KeyError(f"Agent {agent_name} not found in registry")

        return self._agents[agent_name]

    def get_agent_type(self, agent_name: str) -> Type[BaseMultiAgent]:
        """
        Get the type of an agent by name.

        Args:
            agent_name: Name of the agent

        Returns:
            Agent class type

        Raises:
            KeyError: If agent name not found
        """
        if agent_name not in self._agent_types:
            raise KeyError(f"Agent {agent_name} not found in registry")

        return self._agent_types[agent_name]

    def get_agent_dependencies(self, agent_name: str) -> List[str]:
        """
        Get the dependencies of an agent.

        Args:
            agent_name: Name of the agent

        Returns:
            List of agent names this agent depends on

        Raises:
            KeyError: If agent name not found
        """
        if agent_name not in self._dependencies:
            raise KeyError(f"Agent {agent_name} not found in registry")

        return self._dependencies[agent_name].copy()

    def list_agents(self) -> List[str]:
        """
        Get list of all registered agent names.

        Returns:
            List of agent names
        """
        return list(self._agents.keys())

    def clear_agents(self) -> None:
        """Clear all agents from the registry."""
        self._agents.clear()
        self._agent_types.clear()
        self._dependencies.clear()
        logger.info("All agents cleared from the registry")

    def get_agent_info(self, agent_name: str) -> Dict[str, str]:
        """
        Get information about an agent.

        Args:
            agent_name: Name of the agent

        Returns:
            Dictionary with agent information

        Raises:
            KeyError: If agent name not found
        """
        agent = self.get_agent(agent_name)
        info = agent.get_agent_info()
        info["dependencies"] = self.get_agent_dependencies(agent_name)
        return info

    def get_execution_order(self) -> List[str]:
        """
        Get the execution order of agents based on dependencies.

        Returns:
            List of agent names in execution order

        Raises:
            ValueError: If circular dependencies are detected
        """
        # Topological sort to determine execution order
        visited = set()
        temp_visited = set()
        result = []

        def visit(agent_name: str):
            if agent_name in temp_visited:
                raise ValueError(
                    f"Circular dependency detected involving agent {agent_name}"
                )

            if agent_name not in visited:
                temp_visited.add(agent_name)

                # Visit dependencies first
                for dep in self._dependencies.get(agent_name, []):
                    if dep not in self._agents:
                        raise ValueError(
                            f"Dependency {dep} for agent {agent_name} not found"
                        )
                    visit(dep)

                temp_visited.remove(agent_name)
                visited.add(agent_name)
                result.append(agent_name)

        # Visit all agents
        for agent_name in self._agents:
            if agent_name not in visited:
                visit(agent_name)

        return result

    def validate_dependencies(self) -> bool:
        """
        Validate that all agent dependencies are satisfied.

        Returns:
            True if all dependencies are valid

        Raises:
            ValueError: If invalid dependencies are found
        """
        for agent_name, deps in self._dependencies.items():
            for dep in deps:
                if dep not in self._agents:
                    raise ValueError(
                        f"Agent {agent_name} depends on {dep} which is not registered"
                    )

        # Check for circular dependencies
        try:
            self.get_execution_order()
        except ValueError as e:
            raise ValueError(f"Dependency validation failed: {e}")

        return True


# Global registry instance
_global_registry = AgentRegistry()


def get_global_registry() -> AgentRegistry:
    """Get the global agent registry instance."""
    return _global_registry
