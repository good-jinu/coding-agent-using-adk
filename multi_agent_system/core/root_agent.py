"""Root agent implementation for the multi-agent system."""

from typing import Dict, Any, Optional
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters
from dotenv import load_dotenv
import logging

from .base_agent import BaseMultiAgent, AgentExecutionError, ValidationError
from .coordinator import MultiAgentCoordinator
from .agent_registry import get_global_registry, AgentRegistry
from .data_store import get_global_data_store, SharedDataStore


load_dotenv()

GEMINI_MODEL = "gemini-2.5-flash"
logger = logging.getLogger(__name__)


class RootAgent(BaseMultiAgent):
    """
    Root agent that orchestrates the entire multi-agent coding workflow.

    This agent serves as the main entry point and coordinator for the multi-agent system,
    managing the complete software development lifecycle from planning to implementation.
    """

    # Pydantic model fields
    coordinator: MultiAgentCoordinator = {"default_factory": MultiAgentCoordinator}
    registry: AgentRegistry = {"default_factory": get_global_registry}
    data_store: SharedDataStore = {"default_factory": get_global_data_store}

    def __init__(self, **data):
        """Initialize the root agent."""
        # Set default values for the RootAgent
        data.setdefault("name", "RootAgent")
        data.setdefault(
            "description",
            "Orchestrates multi-agent software development workflows from planning to implementation",
        )
        data.setdefault(
            "instruction",
            """
You are the root coordinator for a comprehensive multi-agent software development system. 
Your primary responsibility is to orchestrate the complete software development lifecycle 
through specialized agents working in coordination.

**Your Core Responsibilities:**

1. **Requirements Analysis**: Parse and understand user project descriptions
2. **Workflow Orchestration**: Coordinate specialized agents in the correct sequence
3. **Progress Monitoring**: Track workflow execution and handle issues
4. **Quality Assurance**: Ensure deliverables meet requirements
5. **Communication**: Provide clear status updates and final results

**Available Specialized Agents:**
- ProjectPlanningAgent: Creates detailed project plans and requirements analysis
- ModuleDesignAgent: Designs software architecture and module structure
- TestPlanningAgent: Creates comprehensive test strategies and plans
- CodeImplementationAgent: Implements code based on designs and specifications
- TestingAgent: Executes tests and validates implementation
- CodeRefinementAgent: Refines and optimizes code quality

**Workflow Process:**
1. Analyze the user's project description and extract requirements
2. Initialize and configure the multi-agent coordinator
3. Execute agents in proper dependency order
4. Handle failures with appropriate recovery strategies
5. Validate deliverables and ensure quality standards
6. Provide comprehensive final results

**Key Principles:**
- Maintain clear communication throughout the process
- Ensure proper error handling and recovery
- Follow software development best practices
- Provide actionable feedback and recommendations
- Deliver high-quality, production-ready code

Always approach each project systematically, ensuring all phases of development
are properly executed and integrated.
            """,
        )
        super().__init__(**data)

        logger.info("RootAgent initialized successfully")

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the complete multi-agent workflow.

        Args:
            input_data: Dictionary containing project description and configuration

        Returns:
            Dictionary containing workflow results and deliverables
        """
        try:
            self.log_execution_start(input_data)

            # Extract project description
            project_description = input_data.get("description", "")
            workflow_id = input_data.get("workflow_id")

            if not project_description:
                raise ValidationError(
                    self.agent_name, "description", "Project description is required"
                )

            # Validate workflow setup
            validation_result = self.coordinator.validate_workflow_setup()
            if not validation_result["valid"]:
                raise AgentExecutionError(
                    self.agent_name,
                    f"Workflow validation failed: {validation_result['errors']}",
                )

            # Execute the workflow
            self.logger.info(
                f"Starting workflow execution for project: {project_description[:100]}..."
            )
            result = self.coordinator.execute_workflow(project_description, workflow_id)

            # Collect deliverables
            deliverables = self._collect_deliverables(result.workflow_id)

            # Format final output
            output = {
                "success": result.success,
                "workflow_id": result.workflow_id,
                "completed_agents": result.completed_agents,
                "failed_agents": result.failed_agents,
                "execution_time": result.execution_time,
                "error_message": result.error_message,
                "deliverables": deliverables,
                "summary": self._generate_workflow_summary(result, deliverables),
            }

            self.log_execution_end(output)
            return output

        except Exception as e:
            self.log_error(e, "Workflow execution failed")
            raise AgentExecutionError(self.agent_name, str(e), e)

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate input data for the root agent.

        Args:
            input_data: Input data to validate

        Returns:
            True if input is valid, False otherwise
        """
        try:
            # Check required fields
            if not isinstance(input_data, dict):
                self.logger.error("Input data must be a dictionary")
                return False

            # Check for project description
            description = input_data.get("description")
            if not description or not isinstance(description, str):
                self.logger.error(
                    "Project description is required and must be a string"
                )
                return False

            if len(description.strip()) < 10:
                self.logger.error(
                    "Project description must be at least 10 characters long"
                )
                return False

            # Validate optional workflow_id
            workflow_id = input_data.get("workflow_id")
            if workflow_id is not None and not isinstance(workflow_id, str):
                self.logger.error("Workflow ID must be a string if provided")
                return False

            return True

        except Exception as e:
            self.logger.error(f"Input validation error: {e}")
            return False

    def format_output(self, result: Any) -> Dict[str, Any]:
        """
        Format the execution result for output.

        Args:
            result: Raw execution result

        Returns:
            Formatted output dictionary
        """
        if isinstance(result, dict):
            return result

        # If result is not a dict, wrap it
        return {
            "result": result,
            "agent": self.agent_name,
            "timestamp": self.data_store.get_current_timestamp(),
        }

    def get_workflow_progress(self) -> Optional[Dict[str, Any]]:
        """Get current workflow progress."""
        return self.coordinator.get_workflow_progress()

    def cancel_workflow(self) -> bool:
        """Cancel the currently running workflow."""
        return self.coordinator.cancel_workflow()

    def _collect_deliverables(self, workflow_id: str) -> Dict[str, Any]:
        """
        Collect all deliverables produced by the workflow.

        Args:
            workflow_id: ID of the completed workflow

        Returns:
            Dictionary containing all workflow deliverables
        """
        try:
            project_context = self.data_store.get_project_context()

            deliverables = {}

            # Collect outputs from each agent
            agent_outputs = [
                ("project_plan", "ProjectPlanningAgent"),
                ("module_structure", "ModuleDesignAgent"),
                ("test_plan", "TestPlanningAgent"),
                ("code_artifacts", "CodeImplementationAgent"),
                ("test_results", "TestingAgent"),
                ("refined_code", "CodeRefinementAgent"),
            ]

            for deliverable_name, agent_name in agent_outputs:
                try:
                    output = self.data_store.get_agent_output(agent_name)
                    if output:
                        deliverables[deliverable_name] = output
                except Exception as e:
                    self.logger.warning(
                        f"Could not collect {deliverable_name} from {agent_name}: {e}"
                    )

            # Add project context if available
            if project_context:
                deliverables["project_context"] = project_context.dict()

            return deliverables

        except Exception as e:
            self.logger.error(f"Failed to collect deliverables: {e}")
            return {"error": f"Failed to collect deliverables: {str(e)}"}

    def _generate_workflow_summary(
        self, result, deliverables: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive summary of the workflow execution.

        Args:
            result: Workflow execution result
            deliverables: Collected deliverables

        Returns:
            Dictionary containing workflow summary
        """
        summary = {
            "status": "completed" if result.success else "failed",
            "total_agents": len(result.completed_agents) + len(result.failed_agents),
            "successful_agents": len(result.completed_agents),
            "failed_agents": len(result.failed_agents),
            "execution_time_seconds": result.execution_time,
            "deliverables_count": len(
                [d for d in deliverables.values() if d is not None]
            ),
            "key_deliverables": list(deliverables.keys()),
        }

        # Add recommendations based on results
        recommendations = []

        if result.failed_agents:
            recommendations.append(
                f"Review and address failures in: {', '.join(result.failed_agents)}"
            )

        if "test_results" in deliverables:
            recommendations.append("Review test results and ensure all tests pass")

        if "code_artifacts" in deliverables:
            recommendations.append("Conduct code review before deployment")

        summary["recommendations"] = recommendations

        return summary


# Create the root agent instance
def create_root_agent() -> RootAgent:
    """
    Factory function to create a root agent instance.

    Returns:
        Configured RootAgent instance
    """
    return RootAgent()


# For backward compatibility, create a simple LlmAgent version
def create_simple_root_agent() -> LlmAgent:
    """
    Create a simple LlmAgent-based root agent for basic usage.

    Returns:
        LlmAgent configured as root agent
    """
    return LlmAgent(
        model=GEMINI_MODEL,
        name="MultiAgentSystemController",
        description="Controls and orchestrates the multi-agent software development workflow",
        instruction="""
You are the controller for a multi-agent software development system. Your role is to:

1. Understand the user's project requirements and goals
2. Coordinate the execution of specialized agents in the proper sequence
3. Ensure the complete software development lifecycle is properly managed
4. Handle any errors or issues that arise during the development process
5. Provide clear summaries and status updates on the development progress

When given a project description, you will:
- Parse and analyze the requirements
- Determine which specialized agents to activate
- Coordinate the workflow between planning, design, implementation, and testing agents
- Ensure all outputs are properly integrated
- Provide a final summary of the completed project

Always maintain a structured approach to software development, following best practices
and ensuring high-quality code output.
        """,
        tools=[
            MCPToolset(
                connection_params=StdioServerParameters(
                    command="npx",
                    args=[
                        "-y",
                        "@modelcontextprotocol/server-filesystem",
                        "/",  # Root access for file operations
                    ],
                ),
            )
        ],
    )
