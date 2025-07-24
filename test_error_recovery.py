#!/usr/bin/env python3
"""Test script for enhanced error handling and recovery mechanisms."""

import sys
import logging
from typing import Dict, Any
import time

# Add the project root to Python path
sys.path.insert(0, '.')

from multi_agent_system.core import (
    BaseMultiAgent, MultiAgentCoordinator, WorkflowResult, RecoveryResult,
    AgentExecutionError, get_global_data_store
)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TransientFailureAgent(BaseMultiAgent):
    """Mock agent that fails with transient errors."""
    
    def __init__(self):
        super().__init__(
            name="TransientFailureAgent",
            description="Agent that fails with transient errors",
            instruction="Simulate transient failures"
        )
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute and fail with transient error."""
        logger.info("Executing TransientFailureAgent - simulating timeout")
        raise AgentExecutionError("TransientFailureAgent", "Connection timeout - temporary network issue")
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        return True
    
    def format_output(self, result: Any) -> Dict[str, Any]:
        return result


class ComplexityFailureAgent(BaseMultiAgent):
    """Mock agent that fails due to complexity issues."""
    
    def __init__(self):
        super().__init__(
            name="ComplexityFailureAgent",
            description="Agent that fails due to complexity",
            instruction="Simulate complexity failures"
        )
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute and fail with complexity error."""
        logger.info("Executing ComplexityFailureAgent - simulating complexity error")
        raise AgentExecutionError("ComplexityFailureAgent", "Task too complex to process in current configuration")
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        return True
    
    def format_output(self, result: Any) -> Dict[str, Any]:
        return result


class CriticalFailureAgent(BaseMultiAgent):
    """Mock agent that fails critically and requires user intervention."""
    
    def __init__(self):
        super().__init__(
            name="ProjectPlanningAgent",  # Critical agent name
            description="Critical agent that fails",
            instruction="Simulate critical failures"
        )
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute and fail critically."""
        logger.info("Executing CriticalFailureAgent - simulating critical failure")
        raise AgentExecutionError("ProjectPlanningAgent", "Critical system error - unable to process project requirements")
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        return True
    
    def format_output(self, result: Any) -> Dict[str, Any]:
        return result


class OptionalFailureAgent(BaseMultiAgent):
    """Mock agent that can be skipped if it fails."""
    
    def __init__(self):
        super().__init__(
            name="CodeRefinementAgent",  # Optional agent name
            description="Optional agent that can be skipped",
            instruction="Simulate optional agent failure"
        )
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute and fail."""
        logger.info("Executing OptionalFailureAgent - simulating failure")
        raise AgentExecutionError("CodeRefinementAgent", "Refinement process failed - code optimization not possible")
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        return True
    
    def format_output(self, result: Any) -> Dict[str, Any]:
        return result


def test_transient_error_detection():
    """Test detection of transient errors."""
    logger.info("Testing transient error detection")
    
    try:
        coordinator = MultiAgentCoordinator()
        
        # Test various error types
        transient_errors = [
            Exception("Connection timeout occurred"),
            Exception("Network connection failed"),
            Exception("Service temporarily unavailable"),
            Exception("Rate limit exceeded - try again later"),
            Exception("Quota exceeded for this request")
        ]
        
        non_transient_errors = [
            Exception("Invalid input format"),
            Exception("Authentication failed"),
            Exception("File not found"),
            Exception("Syntax error in code")
        ]
        
        # Test transient error detection
        for error in transient_errors:
            is_transient = coordinator._is_transient_error(error)
            if is_transient:
                logger.info(f"✓ Correctly identified transient error: {error}")
            else:
                logger.error(f"✗ Failed to identify transient error: {error}")
                return False
        
        # Test non-transient error detection
        for error in non_transient_errors:
            is_transient = coordinator._is_transient_error(error)
            if not is_transient:
                logger.info(f"✓ Correctly identified non-transient error: {error}")
            else:
                logger.error(f"✗ Incorrectly identified non-transient error as transient: {error}")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"Test failed with exception: {e}")
        return False


def test_recovery_strategies():
    """Test different recovery strategies."""
    logger.info("Testing recovery strategies")
    
    try:
        coordinator = MultiAgentCoordinator()
        data_store = get_global_data_store()
        data_store.clear_data()
        
        # Test transient error recovery
        transient_agent = TransientFailureAgent()
        coordinator.register_agent(transient_agent, dependencies=[])
        
        transient_error = AgentExecutionError("TransientFailureAgent", "Connection timeout - temporary network issue")
        recovery_result = coordinator._attempt_recovery("TransientFailureAgent", transient_error)
        
        if recovery_result.success and recovery_result.strategy == "retry":
            logger.info("✓ Transient error recovery strategy works correctly")
        else:
            logger.error(f"✗ Transient error recovery failed: {recovery_result.to_dict()}")
            return False
        
        # Test complexity error recovery
        complexity_error = AgentExecutionError("ComplexityFailureAgent", "Task too complex to process")
        recovery_result = coordinator._attempt_recovery("ComplexityFailureAgent", complexity_error)
        
        logger.info(f"Complexity error recovery result: {recovery_result.to_dict()}")
        
        # Test optional agent skipping
        optional_error = AgentExecutionError("CodeRefinementAgent", "Refinement failed")
        recovery_result = coordinator._attempt_recovery("CodeRefinementAgent", optional_error)
        
        if recovery_result.success and recovery_result.strategy == "skip":
            logger.info("✓ Optional agent skipping works correctly")
        else:
            logger.error(f"✗ Optional agent skipping failed: {recovery_result.to_dict()}")
            return False
        
        # Test critical agent failure requiring user intervention
        critical_error = AgentExecutionError("ProjectPlanningAgent", "Critical system error")
        recovery_result = coordinator._attempt_recovery("ProjectPlanningAgent", critical_error)
        
        if not recovery_result.success and recovery_result.requires_user_intervention:
            logger.info("✓ Critical agent failure correctly requires user intervention")
        else:
            logger.error(f"✗ Critical agent failure handling failed: {recovery_result.to_dict()}")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_rollback_mechanism():
    """Test rollback mechanism."""
    logger.info("Testing rollback mechanism")
    
    try:
        coordinator = MultiAgentCoordinator()
        data_store = get_global_data_store()
        data_store.clear_data()
        
        # Create a mock workflow state
        from multi_agent_system.core.models import WorkflowState, WorkflowStatus
        workflow_state = WorkflowState(
            workflow_id="test-rollback",
            status=WorkflowStatus.IN_PROGRESS,
            completed_agents=["Agent1", "Agent2"],
            failed_agents=[]
        )
        coordinator._current_workflow = workflow_state
        
        # Create a rollback point
        rollback_point = coordinator._create_rollback_point("Agent3")
        
        if rollback_point and "timestamp" in rollback_point:
            logger.info("✓ Rollback point created successfully")
        else:
            logger.error("✗ Failed to create rollback point")
            return False
        
        # Simulate some changes to the workflow state
        workflow_state.completed_agents.append("Agent3")
        workflow_state.failed_agents.append("Agent4")
        
        # Attempt rollback
        try:
            coordinator._restore_to_rollback_point(rollback_point)
            logger.info("✓ Rollback restoration completed without errors")
        except Exception as e:
            logger.error(f"✗ Rollback restoration failed: {e}")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_user_intervention():
    """Test user intervention mechanisms."""
    logger.info("Testing user intervention mechanisms")
    
    try:
        coordinator = MultiAgentCoordinator()
        data_store = get_global_data_store()
        data_store.clear_data()
        
        # Create a mock workflow
        from multi_agent_system.core.models import WorkflowState, WorkflowStatus
        workflow_state = WorkflowState(
            workflow_id="test-intervention",
            status=WorkflowStatus.IN_PROGRESS
        )
        coordinator._current_workflow = workflow_state
        
        # Simulate a critical failure requiring user intervention
        critical_error = AgentExecutionError("ProjectPlanningAgent", "Critical system error")
        recovery_result = RecoveryResult(
            success=False,
            strategy="user_intervention",
            message="All automated recovery strategies failed",
            requires_user_intervention=True,
            error_details="Critical system error"
        )
        
        # Request user intervention
        coordinator._request_user_intervention("ProjectPlanningAgent", critical_error, recovery_result)
        
        # Check if intervention request was created
        intervention_requests = coordinator.get_user_intervention_requests()
        
        if intervention_requests:
            logger.info(f"✓ User intervention request created: {len(intervention_requests)} requests")
            
            # Test intervention resolution
            intervention_id = "test-intervention-1"
            resolution_success = coordinator.resolve_user_intervention(
                intervention_id, 
                "retry", 
                {"modified_input": "simplified project description"}
            )
            
            if resolution_success:
                logger.info("✓ User intervention resolution works correctly")
            else:
                logger.error("✗ User intervention resolution failed")
                return False
        else:
            logger.error("✗ No user intervention request was created")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_suggested_actions():
    """Test suggested user actions generation."""
    logger.info("Testing suggested user actions")
    
    try:
        coordinator = MultiAgentCoordinator()
        
        # Test suggestions for different agents and errors
        test_cases = [
            ("ProjectPlanningAgent", Exception("Invalid project description"), "project description"),
            ("ModuleDesignAgent", Exception("Architecture too complex"), "architecture"),
            ("CodeImplementationAgent", Exception("Missing dependencies"), "dependencies"),
            ("TestingAgent", Exception("Connection timeout"), "timeout")
        ]
        
        for agent_name, error, expected_keyword in test_cases:
            suggestions = coordinator._get_suggested_user_actions(agent_name, error)
            
            if suggestions and len(suggestions) > 0:
                logger.info(f"✓ Generated {len(suggestions)} suggestions for {agent_name}")
                
                # Check if suggestions contain relevant keywords
                suggestions_text = " ".join(suggestions).lower()
                if expected_keyword in suggestions_text:
                    logger.info(f"✓ Suggestions contain relevant keyword '{expected_keyword}'")
                else:
                    logger.warning(f"⚠ Suggestions may not be specific enough for {agent_name}")
            else:
                logger.error(f"✗ No suggestions generated for {agent_name}")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"Test failed with exception: {e}")
        return False


if __name__ == "__main__":
    logger.info("Running enhanced error handling and recovery tests")
    
    tests = [
        test_transient_error_detection,
        test_recovery_strategies,
        test_rollback_mechanism,
        test_user_intervention,
        test_suggested_actions
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_func in tests:
        try:
            if test_func():
                passed_tests += 1
                logger.info(f"✓ {test_func.__name__} PASSED")
            else:
                logger.error(f"✗ {test_func.__name__} FAILED")
        except Exception as e:
            logger.error(f"✗ {test_func.__name__} FAILED with exception: {e}")
    
    logger.info(f"\nTest Results: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        logger.info("All error handling and recovery tests passed!")
        sys.exit(0)
    else:
        logger.error("Some error handling and recovery tests failed!")
        sys.exit(1)