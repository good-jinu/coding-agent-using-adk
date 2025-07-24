"""Multi-agent workflow coordination and orchestration."""

import uuid
import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from enum import Enum

from .base_agent import BaseMultiAgent, AgentExecutionError
from .agent_registry import AgentRegistry, get_global_registry
from .data_store import SharedDataStore, get_global_data_store
from .models import WorkflowState, WorkflowStatus

logger = logging.getLogger(__name__)


class WorkflowResult:
    """Result of workflow execution."""
    
    def __init__(self, workflow_id: str, success: bool, error_message: Optional[str] = None):
        self.workflow_id = workflow_id
        self.success = success
        self.error_message = error_message
        self.completed_agents: List[str] = []
        self.failed_agents: List[str] = []
        self.execution_time: Optional[float] = None
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
    
    def add_completed_agent(self, agent_name: str) -> None:
        """Add an agent to the completed list."""
        if agent_name not in self.completed_agents:
            self.completed_agents.append(agent_name)
    
    def add_failed_agent(self, agent_name: str) -> None:
        """Add an agent to the failed list."""
        if agent_name not in self.failed_agents:
            self.failed_agents.append(agent_name)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "workflow_id": self.workflow_id,
            "success": self.success,
            "error_message": self.error_message,
            "completed_agents": self.completed_agents,
            "failed_agents": self.failed_agents,
            "execution_time": self.execution_time,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None
        }


class MultiAgentCoordinator:
    """
    Coordinator for multi-agent workflow orchestration.
    
    Manages agent execution sequencing, dependency resolution, error handling,
    and workflow state tracking.
    """
    
    def __init__(self, 
                 registry: Optional[AgentRegistry] = None,
                 data_store: Optional[SharedDataStore] = None,
                 max_retries: int = 3,
                 retry_delay: float = 1.0):
        """
        Initialize the multi-agent coordinator.
        
        Args:
            registry: Agent registry instance (uses global if None)
            data_store: Shared data store instance (uses global if None)
            max_retries: Maximum number of retries for failed agents
            retry_delay: Delay between retries in seconds
        """
        self.registry = registry or get_global_registry()
        self.data_store = data_store or get_global_data_store()
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # Workflow state tracking
        self._current_workflow: Optional[WorkflowState] = None
        self._progress_callbacks: List[Callable[[WorkflowState], None]] = []
        
        logger.info("MultiAgentCoordinator initialized")
    
    def register_agent(self, agent: BaseMultiAgent, dependencies: Optional[List[str]] = None) -> None:
        """
        Register an agent with the coordinator.
        
        Args:
            agent: Agent instance to register
            dependencies: List of agent names this agent depends on
        """
        self.registry.register_agent(agent, dependencies)
        logger.info(f"Registered agent {agent.agent_name} with coordinator")
    
    def add_progress_callback(self, callback: Callable[[WorkflowState], None]) -> None:
        """
        Add a callback function to be called on workflow progress updates.
        
        Args:
            callback: Function to call with workflow state updates
        """
        self._progress_callbacks.append(callback)
    
    def execute_workflow(self, initial_input: str, workflow_id: Optional[str] = None) -> WorkflowResult:
        """
        Execute the complete multi-agent workflow.
        
        Args:
            initial_input: Initial input for the workflow (project description)
            workflow_id: Optional workflow ID (generates one if None)
            
        Returns:
            WorkflowResult containing execution details
            
        Raises:
            ValueError: If no agents are registered or dependencies are invalid
        """
        # Generate workflow ID if not provided
        if workflow_id is None:
            workflow_id = str(uuid.uuid4())
        
        # Initialize workflow result
        result = WorkflowResult(workflow_id, success=False)
        result.start_time = datetime.now()
        
        try:
            # Validate agent dependencies
            if not self.registry.list_agents():
                raise ValueError("No agents registered for workflow execution")
            
            self.registry.validate_dependencies()
            
            # Get execution order based on dependencies
            execution_order = self.registry.get_execution_order()
            logger.info(f"Workflow {workflow_id} execution order: {execution_order}")
            
            # Initialize workflow state
            workflow_state = WorkflowState(
                workflow_id=workflow_id,
                status=WorkflowStatus.IN_PROGRESS,
                start_time=datetime.now()
            )
            
            self._current_workflow = workflow_state
            self.data_store.update_workflow_state(workflow_state)
            self._notify_progress_callbacks(workflow_state)
            
            # Store initial input in data store
            self.data_store.store_agent_output(
                agent_name="user",
                output_type="initial_input",
                data={"description": initial_input, "workflow_id": workflow_id}
            )
            
            # Execute agents in order
            for agent_name in execution_order:
                try:
                    success = self._execute_agent_with_retry(agent_name, workflow_state)
                    if success:
                        workflow_state.mark_agent_completed(agent_name)
                        result.add_completed_agent(agent_name)
                        logger.info(f"Agent {agent_name} completed successfully")
                    else:
                        workflow_state.mark_agent_failed(agent_name, f"Agent {agent_name} failed after {self.max_retries} retries")
                        result.add_failed_agent(agent_name)
                        logger.error(f"Agent {agent_name} failed after maximum retries")
                        
                        # Decide whether to continue or abort workflow
                        if self._should_abort_workflow(agent_name, workflow_state):
                            raise AgentExecutionError(agent_name, "Critical agent failure, aborting workflow")
                
                except Exception as e:
                    workflow_state.mark_agent_failed(agent_name, str(e))
                    result.add_failed_agent(agent_name)
                    logger.error(f"Agent {agent_name} execution failed: {e}")
                    
                    if self._should_abort_workflow(agent_name, workflow_state):
                        raise
                
                # Update workflow state and notify callbacks
                workflow_state.current_agent = None
                self.data_store.update_workflow_state(workflow_state)
                self._notify_progress_callbacks(workflow_state)
            
            # Mark workflow as completed
            workflow_state.status = WorkflowStatus.COMPLETED
            workflow_state.end_time = datetime.now()
            result.success = True
            
            logger.info(f"Workflow {workflow_id} completed successfully")
            
        except Exception as e:
            # Mark workflow as failed
            if self._current_workflow:
                self._current_workflow.status = WorkflowStatus.FAILED
                self._current_workflow.error_message = str(e)
                self._current_workflow.end_time = datetime.now()
                self.data_store.update_workflow_state(self._current_workflow)
                self._notify_progress_callbacks(self._current_workflow)
            
            result.error_message = str(e)
            logger.error(f"Workflow {workflow_id} failed: {e}")
        
        finally:
            # Calculate execution time
            result.end_time = datetime.now()
            if result.start_time:
                result.execution_time = (result.end_time - result.start_time).total_seconds()
            
            # Update final workflow state
            if self._current_workflow:
                self.data_store.update_workflow_state(self._current_workflow)
                self._notify_progress_callbacks(self._current_workflow)
            
            self._current_workflow = None
        
        return result
    
    def _execute_agent_with_retry(self, agent_name: str, workflow_state: WorkflowState) -> bool:
        """
        Execute an agent with retry logic.
        
        Args:
            agent_name: Name of the agent to execute
            workflow_state: Current workflow state
            
        Returns:
            True if agent executed successfully, False otherwise
        """
        agent = self.registry.get_agent(agent_name)
        retry_count = 0
        
        while retry_count <= self.max_retries:
            try:
                # Update workflow state
                workflow_state.current_agent = agent_name
                self.data_store.update_workflow_state(workflow_state)
                self._notify_progress_callbacks(workflow_state)
                
                logger.info(f"Executing agent {agent_name} (attempt {retry_count + 1}/{self.max_retries + 1})")
                
                # Get input data for the agent
                input_data = self.data_store.get_agent_input(agent_name)
                
                # Validate input
                if not agent.validate_input(input_data):
                    raise AgentExecutionError(agent_name, "Input validation failed")
                
                # Execute the agent
                agent.log_execution_start(input_data)
                output = agent.execute(input_data)
                agent.log_execution_end(output)
                
                # Format and store output
                formatted_output = agent.format_output(output)
                
                # Determine output type based on agent name
                output_type = self._get_output_type_for_agent(agent_name)
                
                self.data_store.store_agent_output(
                    agent_name=agent_name,
                    output_type=output_type,
                    data=formatted_output,
                    metadata={"retry_count": retry_count, "execution_time": datetime.now().isoformat()}
                )
                
                return True
                
            except Exception as e:
                retry_count += 1
                agent.log_error(e, f"Execution attempt {retry_count}")
                
                if retry_count <= self.max_retries:
                    logger.warning(f"Agent {agent_name} failed (attempt {retry_count}), retrying in {self.retry_delay}s: {e}")
                    import time
                    time.sleep(self.retry_delay)
                else:
                    logger.error(f"Agent {agent_name} failed after {self.max_retries + 1} attempts: {e}")
                    # Call handle_agent_failure for recovery mechanisms
                    self.handle_agent_failure(agent_name, e)
                    return False
        
        return False
    
    def _get_output_type_for_agent(self, agent_name: str) -> str:
        """
        Get the expected output type for an agent.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Expected output type string
        """
        # Map agent names to their expected output types
        output_type_mapping = {
            "ProjectPlanningAgent": "project_plan",
            "ModuleDesignAgent": "module_structure",
            "TestPlanningAgent": "test_plan",
            "CodeImplementationAgent": "code_artifact",
            "TestingAgent": "test_results",
            "CodeRefinementAgent": "code_artifact"
        }
        
        return output_type_mapping.get(agent_name, "generic_output")
    
    def _should_abort_workflow(self, failed_agent: str, workflow_state: WorkflowState) -> bool:
        """
        Determine if workflow should be aborted due to agent failure.
        
        Args:
            failed_agent: Name of the failed agent
            workflow_state: Current workflow state
            
        Returns:
            True if workflow should be aborted
        """
        # Critical agents that should abort the workflow if they fail
        critical_agents = {
            "ProjectPlanningAgent",
            "ModuleDesignAgent"
        }
        
        # Abort if critical agent fails
        if failed_agent in critical_agents:
            return True
        
        # Abort if too many agents have failed
        failure_threshold = 0.5  # 50% of agents
        total_agents = len(self.registry.list_agents())
        failed_count = len(workflow_state.failed_agents)
        
        if failed_count / total_agents > failure_threshold:
            return True
        
        return False
    
    def _notify_progress_callbacks(self, workflow_state: WorkflowState) -> None:
        """
        Notify all registered progress callbacks.
        
        Args:
            workflow_state: Current workflow state
        """
        for callback in self._progress_callbacks:
            try:
                callback(workflow_state)
            except Exception as e:
                logger.error(f"Progress callback failed: {e}")
    
    def handle_agent_failure(self, agent_name: str, error: Exception) -> None:
        """
        Handle agent execution failures with recovery mechanisms.
        
        Args:
            agent_name: Name of the failed agent
            error: Exception that caused the failure
        """
        logger.error(f"Handling failure for agent {agent_name}: {error}")
        
        if self._current_workflow:
            self._current_workflow.mark_agent_failed(agent_name, str(error))
            self.data_store.update_workflow_state(self._current_workflow)
            self._notify_progress_callbacks(self._current_workflow)
        
        # Trigger recovery mechanisms
        recovery_result = self._attempt_recovery(agent_name, error)
        
        if not recovery_result.success:
            logger.error(f"Recovery failed for agent {agent_name}: {recovery_result.message}")
            # Check if user intervention is needed
            if recovery_result.requires_user_intervention:
                self._request_user_intervention(agent_name, error, recovery_result)
    
    def get_workflow_progress(self) -> Optional[Dict[str, Any]]:
        """
        Get current workflow progress information.
        
        Returns:
            Dictionary with progress information or None if no active workflow
        """
        if not self._current_workflow:
            return None
        
        total_agents = len(self.registry.list_agents())
        progress_percentage = self._current_workflow.get_progress_percentage(total_agents)
        
        return {
            "workflow_id": self._current_workflow.workflow_id,
            "status": self._current_workflow.status,
            "current_agent": self._current_workflow.current_agent,
            "completed_agents": self._current_workflow.completed_agents,
            "failed_agents": self._current_workflow.failed_agents,
            "progress_percentage": progress_percentage,
            "start_time": self._current_workflow.start_time.isoformat() if self._current_workflow.start_time else None,
            "total_agents": total_agents
        }
    
    def cancel_workflow(self) -> bool:
        """
        Cancel the currently running workflow.
        
        Returns:
            True if workflow was cancelled, False if no active workflow
        """
        if not self._current_workflow:
            return False
        
        self._current_workflow.status = WorkflowStatus.CANCELLED
        self._current_workflow.end_time = datetime.now()
        self.data_store.update_workflow_state(self._current_workflow)
        self._notify_progress_callbacks(self._current_workflow)
        
        logger.info(f"Workflow {self._current_workflow.workflow_id} cancelled")
        return True
    
    def get_agent_execution_order(self) -> List[str]:
        """
        Get the execution order of registered agents based on dependencies.
        
        Returns:
            List of agent names in execution order
        """
        return self.registry.get_execution_order()
    
    def validate_workflow_setup(self) -> Dict[str, Any]:
        """
        Validate the current workflow setup.
        
        Returns:
            Dictionary with validation results
        """
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "agent_count": len(self.registry.list_agents()),
            "execution_order": []
        }
        
        try:
            # Check if agents are registered
            if not self.registry.list_agents():
                validation_result["valid"] = False
                validation_result["errors"].append("No agents registered")
                return validation_result
            
            # Validate dependencies
            self.registry.validate_dependencies()
            
            # Get execution order
            execution_order = self.registry.get_execution_order()
            validation_result["execution_order"] = execution_order
            
            # Check for recommended agents
            recommended_agents = {
                "ProjectPlanningAgent",
                "ModuleDesignAgent", 
                "TestPlanningAgent",
                "CodeImplementationAgent",
                "TestingAgent"
            }
            
            registered_agents = set(self.registry.list_agents())
            missing_agents = recommended_agents - registered_agents
            
            if missing_agents:
                validation_result["warnings"].append(f"Missing recommended agents: {list(missing_agents)}")
            
        except Exception as e:
            validation_result["valid"] = False
            validation_result["errors"].append(str(e))
        
        return validation_result
    
    def _attempt_recovery(self, agent_name: str, error: Exception) -> 'RecoveryResult':
        """
        Attempt to recover from agent failure using various strategies.
        
        Args:
            agent_name: Name of the failed agent
            error: Exception that caused the failure
            
        Returns:
            RecoveryResult indicating success/failure and next steps
        """
        logger.info(f"Attempting recovery for failed agent {agent_name}")
        
        # Strategy 1: Check if this is a transient error that can be retried
        if self._is_transient_error(error):
            logger.info(f"Detected transient error for {agent_name}, will be handled by retry mechanism")
            return RecoveryResult(success=True, strategy="retry", message="Transient error, retry will handle")
        
        # Strategy 2: Try alternative execution approach
        alternative_result = self._try_alternative_approach(agent_name, error)
        if alternative_result.success:
            return alternative_result
        
        # Strategy 3: Attempt partial rollback and recovery
        rollback_result = self._attempt_partial_rollback(agent_name, error)
        if rollback_result.success:
            # Even if rollback succeeds, critical agents still need user intervention
            # since the original problem hasn't been resolved
            if not self._can_skip_agent(agent_name):
                logger.warning(f"Rollback succeeded for critical agent {agent_name}, but user intervention still required")
                return RecoveryResult(
                    success=False,
                    strategy="rollback_with_intervention",
                    message=f"Rollback succeeded but critical agent {agent_name} still requires user intervention",
                    requires_user_intervention=True,
                    error_details=str(error)
                )
            return rollback_result
        
        # Strategy 4: Check if workflow can continue without this agent
        if self._can_skip_agent(agent_name):
            logger.warning(f"Skipping non-critical agent {agent_name} and continuing workflow")
            return RecoveryResult(success=True, strategy="skip", message=f"Skipped non-critical agent {agent_name}")
        
        # Strategy 5: Request user intervention
        logger.error(f"All recovery strategies failed for {agent_name}, requiring user intervention")
        return RecoveryResult(
            success=False, 
            strategy="user_intervention", 
            message="All automated recovery strategies failed",
            requires_user_intervention=True,
            error_details=str(error)
        )
    
    def _is_transient_error(self, error: Exception) -> bool:
        """
        Determine if an error is transient and likely to succeed on retry.
        
        Args:
            error: Exception to analyze
            
        Returns:
            True if error appears to be transient
        """
        transient_error_indicators = [
            "timeout", "connection", "network", "temporary", "temporarily", "rate limit",
            "service unavailable", "unavailable", "too many requests", "quota exceeded"
        ]
        
        error_message = str(error).lower()
        return any(indicator in error_message for indicator in transient_error_indicators)
    
    def _try_alternative_approach(self, agent_name: str, error: Exception) -> 'RecoveryResult':
        """
        Try an alternative execution approach for the failed agent.
        
        Args:
            agent_name: Name of the failed agent
            error: Original error
            
        Returns:
            RecoveryResult indicating success/failure
        """
        logger.info(f"Trying alternative approach for agent {agent_name}")
        
        # For now, this is a placeholder for future alternative strategies
        # Could include: different model parameters, alternative prompts, etc.
        
        # Example: Try with reduced complexity or different parameters
        if "complexity" in str(error).lower() or "too complex" in str(error).lower():
            logger.info(f"Attempting simplified approach for {agent_name}")
            # This would require agent-specific logic to reduce complexity
            return RecoveryResult(
                success=False, 
                strategy="alternative_approach", 
                message="Alternative approach not yet implemented for this error type"
            )
        
        return RecoveryResult(
            success=False, 
            strategy="alternative_approach", 
            message="No alternative approach available for this error type"
        )
    
    def _attempt_partial_rollback(self, agent_name: str, error: Exception) -> 'RecoveryResult':
        """
        Attempt to rollback to a previous stable state and recover.
        
        Args:
            agent_name: Name of the failed agent
            error: Original error
            
        Returns:
            RecoveryResult indicating success/failure
        """
        logger.info(f"Attempting partial rollback for agent {agent_name}")
        
        if not self._current_workflow:
            return RecoveryResult(
                success=False, 
                strategy="rollback", 
                message="No active workflow to rollback"
            )
        
        # Create a rollback point
        rollback_point = self._create_rollback_point(agent_name)
        
        try:
            # Attempt to restore to previous state
            self._restore_to_rollback_point(rollback_point)
            
            # Clear the failed agent's output if it exists
            self._clear_agent_output(agent_name)
            
            logger.info(f"Successfully rolled back state for agent {agent_name}")
            return RecoveryResult(
                success=True, 
                strategy="rollback", 
                message=f"Successfully rolled back to state before {agent_name} execution"
            )
            
        except Exception as rollback_error:
            logger.error(f"Rollback failed for agent {agent_name}: {rollback_error}")
            return RecoveryResult(
                success=False, 
                strategy="rollback", 
                message=f"Rollback failed: {rollback_error}"
            )
    
    def _can_skip_agent(self, agent_name: str) -> bool:
        """
        Determine if an agent can be skipped without breaking the workflow.
        
        Args:
            agent_name: Name of the agent to potentially skip
            
        Returns:
            True if agent can be safely skipped
        """
        # Define non-critical agents that can be skipped
        optional_agents = {
            "CodeRefinementAgent",  # Can skip if initial code is acceptable
            "TestingAgent"  # Can skip if manual testing is acceptable (not recommended)
        }
        
        # Critical agents that cannot be skipped
        critical_agents = {
            "ProjectPlanningAgent",
            "ModuleDesignAgent",
            "CodeImplementationAgent"
        }
        
        if agent_name in critical_agents:
            return False
        
        if agent_name in optional_agents:
            return True
        
        # For unknown agents, be conservative and don't skip
        return False
    
    def _create_rollback_point(self, agent_name: str) -> Dict[str, Any]:
        """
        Create a rollback point before agent execution.
        
        Args:
            agent_name: Name of the agent about to execute
            
        Returns:
            Dictionary containing rollback state information
        """
        if not self._current_workflow:
            return {}
        
        rollback_point = {
            "timestamp": datetime.now().isoformat(),
            "agent_name": agent_name,
            "workflow_state": self._current_workflow.dict() if self._current_workflow else None,
            "project_context": self.data_store.get_project_context().dict(),
            "completed_agents": self._current_workflow.completed_agents.copy() if self._current_workflow else [],
            "failed_agents": self._current_workflow.failed_agents.copy() if self._current_workflow else []
        }
        
        # Store rollback point in data store for persistence
        self.data_store.store_agent_output(
            agent_name="system",
            output_type="rollback_point",
            data=rollback_point,
            metadata={"created_for_agent": agent_name}
        )
        
        return rollback_point
    
    def _restore_to_rollback_point(self, rollback_point: Dict[str, Any]) -> None:
        """
        Restore system state to a previous rollback point.
        
        Args:
            rollback_point: Rollback point data
        """
        if not rollback_point:
            raise ValueError("Invalid rollback point")
        
        logger.info(f"Restoring to rollback point created at {rollback_point.get('timestamp')}")
        
        # Restore workflow state
        if rollback_point.get("workflow_state") and self._current_workflow:
            workflow_data = rollback_point["workflow_state"]
            self._current_workflow.completed_agents = workflow_data.get("completed_agents", [])
            self._current_workflow.failed_agents = workflow_data.get("failed_agents", [])
            self._current_workflow.current_agent = workflow_data.get("current_agent")
            
        # Note: Project context restoration would require more sophisticated
        # state management and could be implemented based on specific needs
        
        logger.info("Rollback restoration completed")
    
    def _clear_agent_output(self, agent_name: str) -> None:
        """
        Clear the output of a specific agent from the data store.
        
        Args:
            agent_name: Name of the agent whose output should be cleared
        """
        # This would require extending the data store with a clear method
        # For now, we'll log the intent
        logger.info(f"Clearing output for agent {agent_name}")
        # TODO: Implement actual output clearing in data store
    
    def _request_user_intervention(self, agent_name: str, error: Exception, recovery_result: 'RecoveryResult') -> None:
        """
        Request user intervention for unrecoverable errors.
        
        Args:
            agent_name: Name of the failed agent
            error: Original error
            recovery_result: Result of recovery attempts
        """
        logger.critical(f"User intervention required for agent {agent_name}")
        
        intervention_request = {
            "timestamp": datetime.now().isoformat(),
            "agent_name": agent_name,
            "error_message": str(error),
            "recovery_attempts": recovery_result.strategy,
            "recovery_message": recovery_result.message,
            "workflow_id": self._current_workflow.workflow_id if self._current_workflow else None,
            "suggested_actions": self._get_suggested_user_actions(agent_name, error)
        }
        
        # Store intervention request
        self.data_store.store_agent_output(
            agent_name="system",
            output_type="user_intervention_request",
            data=intervention_request,
            metadata={"requires_user_action": True}
        )
        
        # Notify callbacks about intervention requirement
        if self._current_workflow:
            self._current_workflow.status = WorkflowStatus.FAILED
            self._current_workflow.error_message = f"User intervention required for agent {agent_name}: {error}"
            self._notify_progress_callbacks(self._current_workflow)
        
        logger.info(f"User intervention request created for agent {agent_name}")
    
    def _get_suggested_user_actions(self, agent_name: str, error: Exception) -> List[str]:
        """
        Get suggested actions for user intervention.
        
        Args:
            agent_name: Name of the failed agent
            error: Original error
            
        Returns:
            List of suggested actions for the user
        """
        suggestions = []
        error_message = str(error).lower()
        
        # General suggestions
        suggestions.append("Review the error message and agent logs for more details")
        suggestions.append("Check if the input data format is correct")
        
        # Agent-specific suggestions
        if agent_name == "ProjectPlanningAgent":
            suggestions.extend([
                "Verify the project description is clear and detailed",
                "Check if the requested technology stack is supported",
                "Consider simplifying the project scope"
            ])
        elif agent_name == "ModuleDesignAgent":
            suggestions.extend([
                "Review the project plan for completeness",
                "Check if the architecture requirements are feasible",
                "Consider breaking down complex modules"
            ])
        elif agent_name == "CodeImplementationAgent":
            suggestions.extend([
                "Verify the module design is complete and valid",
                "Check if all required dependencies are available",
                "Review test plans for implementation guidance"
            ])
        
        # Error-specific suggestions
        if "timeout" in error_message:
            suggestions.append("Consider increasing timeout limits or simplifying the task")
        elif "memory" in error_message or "resource" in error_message:
            suggestions.append("Try reducing the scope or complexity of the current task")
        elif "permission" in error_message or "access" in error_message:
            suggestions.append("Check file system permissions and access rights")
        
        return suggestions
    
    def get_user_intervention_requests(self) -> List[Dict[str, Any]]:
        """
        Get all pending user intervention requests.
        
        Returns:
            List of user intervention requests
        """
        # Get intervention requests from data store
        system_outputs = self.data_store.get_agent_output("system", "user_intervention_request")
        return [output.data for output in system_outputs]
    
    def resolve_user_intervention(self, intervention_id: str, user_action: str, user_input: Optional[Dict[str, Any]] = None) -> bool:
        """
        Resolve a user intervention request.
        
        Args:
            intervention_id: ID of the intervention request
            user_action: Action taken by user ("retry", "skip", "modify", "abort")
            user_input: Optional additional input from user
            
        Returns:
            True if intervention was resolved successfully
        """
        logger.info(f"Resolving user intervention {intervention_id} with action: {user_action}")
        
        try:
            # Store the user's resolution
            resolution = {
                "intervention_id": intervention_id,
                "user_action": user_action,
                "user_input": user_input or {},
                "resolved_at": datetime.now().isoformat()
            }
            
            self.data_store.store_agent_output(
                agent_name="system",
                output_type="user_intervention_resolution",
                data=resolution
            )
            
            # Handle different user actions
            if user_action == "retry":
                return self._handle_user_retry(intervention_id, user_input)
            elif user_action == "skip":
                return self._handle_user_skip(intervention_id)
            elif user_action == "modify":
                return self._handle_user_modify(intervention_id, user_input)
            elif user_action == "abort":
                return self._handle_user_abort(intervention_id)
            else:
                logger.error(f"Unknown user action: {user_action}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to resolve user intervention {intervention_id}: {e}")
            return False
    
    def _handle_user_retry(self, intervention_id: str, user_input: Optional[Dict[str, Any]]) -> bool:
        """Handle user's decision to retry a failed agent."""
        logger.info(f"User requested retry for intervention {intervention_id}")
        # Implementation would depend on specific retry requirements
        return True
    
    def _handle_user_skip(self, intervention_id: str) -> bool:
        """Handle user's decision to skip a failed agent."""
        logger.info(f"User requested skip for intervention {intervention_id}")
        # Implementation would mark agent as skipped and continue workflow
        return True
    
    def _handle_user_modify(self, intervention_id: str, user_input: Optional[Dict[str, Any]]) -> bool:
        """Handle user's decision to modify input and retry."""
        logger.info(f"User requested modify for intervention {intervention_id}")
        # Implementation would update input data and retry
        return True
    
    def _handle_user_abort(self, intervention_id: str) -> bool:
        """Handle user's decision to abort the workflow."""
        logger.info(f"User requested abort for intervention {intervention_id}")
        if self._current_workflow:
            self._current_workflow.status = WorkflowStatus.CANCELLED
            self._current_workflow.end_time = datetime.now()
        return True


class RecoveryResult:
    """Result of a recovery attempt."""
    
    def __init__(self, success: bool, strategy: str, message: str, 
                 requires_user_intervention: bool = False, error_details: Optional[str] = None):
        self.success = success
        self.strategy = strategy
        self.message = message
        self.requires_user_intervention = requires_user_intervention
        self.error_details = error_details
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "success": self.success,
            "strategy": self.strategy,
            "message": self.message,
            "requires_user_intervention": self.requires_user_intervention,
            "error_details": self.error_details
        }


# Global coordinator instance
_global_coordinator = MultiAgentCoordinator()


def get_global_coordinator() -> MultiAgentCoordinator:
    """Get the global multi-agent coordinator instance."""
    return _global_coordinator