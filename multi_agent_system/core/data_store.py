"""Shared data store for inter-agent communication."""

from typing import Dict, Any, List, Optional
import json
import logging
from datetime import datetime
from pathlib import Path
import threading
from .models import (
    ProjectContext,
    AgentOutput,
    WorkflowState,
    ProjectPlan,
    ModuleStructure,
    TestingPlan,
    CodeArtifact,
    TestingResult,
)

logger = logging.getLogger(__name__)


class SharedDataStore:
    """
    Shared data store for inter-agent communication and state management.

    Provides thread-safe storage and retrieval of project data, agent outputs,
    and workflow state information.
    """

    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize the shared data store.

        Args:
            storage_path: Optional path for persistent storage
        """
        self._lock = threading.RLock()
        self._project_context = ProjectContext()
        self._agent_outputs: Dict[str, List[AgentOutput]] = {}
        self._workflow_history: List[Dict[str, Any]] = []
        self._storage_path = Path(storage_path) if storage_path else None

        if self._storage_path:
            self._storage_path.mkdir(parents=True, exist_ok=True)
            self._load_from_storage()

    def store_agent_output(
        self,
        agent_name: str,
        output_type: str,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Store output from an agent.

        Args:
            agent_name: Name of the agent producing the output
            output_type: Type of output (e.g., 'project_plan', 'module_structure')
            data: The actual output data
            metadata: Optional metadata about the output
        """
        with self._lock:
            output = AgentOutput(
                agent_name=agent_name,
                output_type=output_type,
                data=data,
                metadata=metadata or {},
            )

            if agent_name not in self._agent_outputs:
                self._agent_outputs[agent_name] = []

            self._agent_outputs[agent_name].append(output)

            # Update project context based on output type
            self._update_project_context(output_type, data)

            # Log the storage operation
            self._log_operation(
                "store_output",
                {
                    "agent_name": agent_name,
                    "output_type": output_type,
                    "timestamp": datetime.now().isoformat(),
                },
            )

            logger.info(f"Stored output from agent {agent_name} of type {output_type}")

            if self._storage_path:
                self._save_to_storage()

    def get_agent_output(
        self, agent_name: str, output_type: Optional[str] = None
    ) -> List[AgentOutput]:
        """
        Get outputs from a specific agent.

        Args:
            agent_name: Name of the agent
            output_type: Optional filter by output type

        Returns:
            List of agent outputs
        """
        with self._lock:
            if agent_name not in self._agent_outputs:
                return []

            outputs = self._agent_outputs[agent_name]

            if output_type:
                outputs = [
                    output for output in outputs if output.output_type == output_type
                ]

            return outputs.copy()

    def get_latest_agent_output(
        self, agent_name: str, output_type: Optional[str] = None
    ) -> Optional[AgentOutput]:
        """
        Get the latest output from a specific agent.

        Args:
            agent_name: Name of the agent
            output_type: Optional filter by output type

        Returns:
            Latest agent output or None if not found
        """
        outputs = self.get_agent_output(agent_name, output_type)
        return outputs[-1] if outputs else None

    def get_agent_input(self, agent_name: str) -> Dict[str, Any]:
        """
        Get input data for an agent based on the current project context.

        Args:
            agent_name: Name of the agent requesting input

        Returns:
            Dictionary containing relevant input data for the agent
        """
        with self._lock:
            input_data = {
                "project_context": self._project_context.model_dump(),
                "timestamp": datetime.now().isoformat(),
            }

            # Add agent-specific input data based on agent type
            if agent_name == "ProjectPlanningAgent":
                # Project planning agent gets minimal context
                input_data["previous_outputs"] = []
            elif agent_name == "ModuleDesignAgent":
                # Module design agent needs project plan
                if self._project_context.project_plan:
                    input_data["project_plan"] = (
                        self._project_context.project_plan.model_dump()
                    )
            elif agent_name == "TestPlanningAgent":
                # Test planning agent needs module structure
                if self._project_context.module_structure:
                    input_data["module_structure"] = (
                        self._project_context.module_structure.model_dump()
                    )
            elif agent_name == "CodeImplementationAgent":
                # Code implementation agent needs both module structure and test plans
                if self._project_context.module_structure:
                    input_data["module_structure"] = (
                        self._project_context.module_structure.model_dump()
                    )
                input_data["test_plans"] = [
                    tp.model_dump() for tp in self._project_context.test_plans
                ]
            elif agent_name == "TestingAgent":
                # Testing agent needs code artifacts and test plans
                input_data["code_artifacts"] = [
                    ca.model_dump() for ca in self._project_context.code_artifacts
                ]
                input_data["test_plans"] = [
                    tp.model_dump() for tp in self._project_context.test_plans
                ]
            elif agent_name == "CodeRefinementAgent":
                # Refinement agent needs test results and code artifacts
                input_data["test_results"] = [
                    tr.model_dump() for tr in self._project_context.test_results
                ]
                input_data["code_artifacts"] = [
                    ca.model_dump() for ca in self._project_context.code_artifacts
                ]

            return input_data

    def get_project_context(self) -> ProjectContext:
        """
        Get the complete project context.

        Returns:
            Current project context
        """
        with self._lock:
            return self._project_context.model_copy(deep=True)

    def update_workflow_state(self, workflow_state: WorkflowState) -> None:
        """
        Update the workflow state.

        Args:
            workflow_state: New workflow state
        """
        with self._lock:
            self._project_context.workflow_state = workflow_state
            self._project_context.update_timestamp()

            self._log_operation(
                "update_workflow_state",
                {
                    "workflow_id": workflow_state.workflow_id,
                    "status": workflow_state.status,
                    "current_agent": workflow_state.current_agent,
                    "timestamp": datetime.now().isoformat(),
                },
            )

            if self._storage_path:
                self._save_to_storage()

    def get_workflow_state(self) -> Optional[WorkflowState]:
        """
        Get the current workflow state.

        Returns:
            Current workflow state or None if not set
        """
        with self._lock:
            return self._project_context.workflow_state

    def get_workflow_history(self) -> List[Dict[str, Any]]:
        """
        Get the workflow execution history.

        Returns:
            List of workflow history entries
        """
        with self._lock:
            return self._workflow_history.copy()

    def clear_data(self) -> None:
        """Clear all stored data."""
        with self._lock:
            self._project_context = ProjectContext()
            self._agent_outputs.clear()
            self._workflow_history.clear()

            logger.info("Cleared all data from shared data store")

            if self._storage_path:
                self._save_to_storage()

    def _update_project_context(self, output_type: str, data: Dict[str, Any]) -> None:
        """
        Update project context based on agent output.

        Args:
            output_type: Type of output
            data: Output data
        """
        try:
            if output_type == "project_plan":
                self._project_context.project_plan = ProjectPlan(**data)
            elif output_type == "module_structure":
                self._project_context.module_structure = ModuleStructure(**data)
            elif output_type == "test_plan":
                test_plan = TestingPlan(**data)
                # Replace existing test plan for the same module or add new one
                existing_index = None
                for i, tp in enumerate(self._project_context.test_plans):
                    if tp.module_name == test_plan.module_name:
                        existing_index = i
                        break

                if existing_index is not None:
                    self._project_context.test_plans[existing_index] = test_plan
                else:
                    self._project_context.test_plans.append(test_plan)
            elif output_type == "code_artifact":
                code_artifact = CodeArtifact(**data)
                # Replace existing artifact for the same module or add new one
                existing_index = None
                for i, ca in enumerate(self._project_context.code_artifacts):
                    if ca.module_name == code_artifact.module_name:
                        existing_index = i
                        break

                if existing_index is not None:
                    self._project_context.code_artifacts[existing_index] = code_artifact
                else:
                    self._project_context.code_artifacts.append(code_artifact)
            elif output_type == "test_results":
                if isinstance(data, list):
                    test_results = [TestingResult(**result) for result in data]
                    self._project_context.test_results.extend(test_results)
                else:
                    test_result = TestingResult(**data)
                    self._project_context.test_results.append(test_result)

            self._project_context.update_timestamp()

        except Exception as e:
            logger.error(
                f"Failed to update project context for output type {output_type}: {e}"
            )

    def _log_operation(self, operation: str, details: Dict[str, Any]) -> None:
        """
        Log an operation to the workflow history.

        Args:
            operation: Operation name
            details: Operation details
        """
        entry = {
            "operation": operation,
            "details": details,
            "timestamp": datetime.now().isoformat(),
        }
        self._workflow_history.append(entry)

    def _save_to_storage(self) -> None:
        """Save data to persistent storage."""
        if not self._storage_path:
            return

        try:
            # Save project context
            context_file = self._storage_path / "project_context.json"
            with open(context_file, "w") as f:
                json.dump(self._project_context.model_dump(), f, indent=2, default=str)

            # Save agent outputs
            outputs_file = self._storage_path / "agent_outputs.json"
            serializable_outputs = {}
            for agent_name, outputs in self._agent_outputs.items():
                serializable_outputs[agent_name] = [output.model_dump() for output in outputs]

            with open(outputs_file, "w") as f:
                json.dump(serializable_outputs, f, indent=2, default=str)

            # Save workflow history
            history_file = self._storage_path / "workflow_history.json"
            with open(history_file, "w") as f:
                json.dump(self._workflow_history, f, indent=2, default=str)

        except Exception as e:
            logger.error(f"Failed to save data to storage: {e}")

    def _load_from_storage(self) -> None:
        """Load data from persistent storage."""
        if not self._storage_path:
            return

        try:
            # Load project context
            context_file = self._storage_path / "project_context.json"
            if context_file.exists():
                with open(context_file, "r") as f:
                    context_data = json.load(f)
                    self._project_context = ProjectContext(**context_data)

            # Load agent outputs
            outputs_file = self._storage_path / "agent_outputs.json"
            if outputs_file.exists():
                with open(outputs_file, "r") as f:
                    outputs_data = json.load(f)
                    for agent_name, outputs in outputs_data.items():
                        self._agent_outputs[agent_name] = [
                            AgentOutput(**output) for output in outputs
                        ]

            # Load workflow history
            history_file = self._storage_path / "workflow_history.json"
            if history_file.exists():
                with open(history_file, "r") as f:
                    self._workflow_history = json.load(f)

            logger.info("Loaded data from persistent storage")

        except Exception as e:
            logger.error(f"Failed to load data from storage: {e}")


# Global data store instance
_global_data_store = SharedDataStore()


def get_global_data_store() -> SharedDataStore:
    """Get the global shared data store instance."""
    return _global_data_store
