"""Test script for the Test Planning Agent."""

import sys
import os
import pytest

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from multi_agent_system.core.base_agent import BaseMultiAgent
from multi_agent_system.core.models import TestPlan, TestCase, TestType


class MockProjectPlanningAgent(BaseMultiAgent):
    """Mock project planning agent for testing."""

    def __init__(self):
        super().__init__(
            name="ProjectPlanningAgent",
            description="Mock agent for project planning",
            instruction="Create a project plan from user input",
        )

    def execute(self, input_data):
        """Execute project planning with mock data."""
        return {
            "project_plan": {
                "project_name": "Test Project",
                "description": "A test project",
                "project_type": "web_application",
                "requirements": [
                    {"id": "FR001", "type": "functional", "description": "User authentication", "priority": "high", "category": "security"},
                    {"id": "FR002", "type": "functional", "description": "Task management", "priority": "high", "category": "core"}
                ],
                "technology_stack": {
                    "primary_language": "Python",
                    "frameworks": ["FastAPI"],
                    "databases": ["PostgreSQL"],
                    "tools": ["Docker"]
                },
                "complexity_assessment": {"level": "medium", "score": 5},
                "estimated_timeline_days": 30
            }
        }

    def validate_input(self, input_data):
        """Validate input data."""
        return isinstance(input_data, dict) and "description" in input_data

    def format_output(self, result):
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

    def execute(self, input_data):
        """Execute module design with mock data."""
        return {
            "module_structure": {
                "modules": [
                    {
                        "name": "auth_module",
                        "purpose": "Authentication and authorization",
                        "public_interface": ["authenticate", "authorize"],
                        "dependencies": [],
                        "estimated_complexity": 3,
                        "file_path": "src/auth/auth_module.py"
                    },
                    {
                        "name": "task_module",
                        "purpose": "Task management functionality",
                        "public_interface": ["create_task", "update_task", "delete_task"],
                        "dependencies": ["auth_module"],
                        "estimated_complexity": 5,
                        "file_path": "src/tasks/task_module.py"
                    }
                ],
                "interfaces": [
                    {
                        "name": "AuthInterface",
                        "methods": ["authenticate", "authorize"],
                        "properties": ["current_user"],
                        "description": "Authentication interface"
                    }
                ],
                "dependencies": {
                    "auth_module": [],
                    "task_module": ["auth_module"]
                },
                "architecture_pattern": "Layered Architecture"
            }
        }

    def validate_input(self, input_data):
        """Validate input data."""
        return isinstance(input_data, dict) and "project_plan" in input_data

    def format_output(self, result):
        """Format output."""
        return result


class MockTestPlanningAgent(BaseMultiAgent):
    """Mock test planning agent for testing."""

    def __init__(self):
        super().__init__(
            name="TestPlanningAgent",
            description="Mock agent for test planning",
            instruction="Create test plans from project plan and module structure",
        )

    def execute(self, input_data):
        """Execute test planning with mock data."""
        # Validate input
        if not self.validate_input(input_data):
            raise ValueError("Invalid input data")

        # Create mock test cases
        mock_unit_test = TestCase(
            name="test_authenticate_success",
            description="Test successful authentication",
            input_data={"username": "testuser", "password": "testpass"},
            expected_output={"authenticated": True},
            test_type=TestType.UNIT,
            module_name="auth_module"
        )
        
        mock_integration_test = TestCase(
            name="test_auth_integration",
            description="Test authentication integration",
            input_data={"module": "auth_module", "dependency": "database"},
            expected_output={"integration_success": True},
            test_type=TestType.INTEGRATION,
            module_name="auth_module"
        )
        
        # Create mock test plans
        mock_test_plans = [
            TestPlan(
                module_name="auth_module",
                unit_tests=[mock_unit_test],
                integration_tests=[mock_integration_test],
                e2e_tests=[]
            )
        ]
        
        # Create mock integration test plan
        mock_integration_plan = TestPlan(
            module_name="system_integration",
            unit_tests=[],
            integration_tests=[mock_integration_test],
            e2e_tests=[]
        )
        
        # Create mock e2e test plan
        mock_e2e_test = TestCase(
            name="test_user_login_workflow",
            description="End-to-end test for user login workflow",
            input_data={"workflow": "User Login", "steps": ["visit_login", "enter_credentials", "submit"]},
            expected_output={"workflow_completed": True},
            test_type=TestType.E2E,
            module_name="end_to_end"
        )
        
        mock_e2e_plan = TestPlan(
            module_name="end_to_end",
            unit_tests=[],
            integration_tests=[],
            e2e_tests=[mock_e2e_test]
        )
        
        return {
            "test_plans": [plan.model_dump() for plan in mock_test_plans],
            "integration_test_plan": mock_integration_plan.model_dump(),
            "e2e_test_plan": mock_e2e_plan.model_dump(),
            "test_analysis": {"testable_requirements": [], "critical_paths": []},
            "test_strategy": {
                "approach": "Comprehensive testing",
                "test_pyramid": {
                    "unit_tests": "70%",
                    "integration_tests": "20%",
                    "e2e_tests": "10%"
                }
            },
            "test_recommendations": ["Increase code coverage", "Add performance tests"],
            "coverage_analysis": {
                "total_test_cases": 3,
                "unit_test_count": 1,
                "integration_test_count": 1,
                "e2e_test_count": 1
            },
            "test_metadata": {
                "total_test_cases": 3
            }
        }

    def validate_input(self, input_data):
        """Validate input data."""
        return (isinstance(input_data, dict) and 
                "project_plan" in input_data and 
                "module_structure" in input_data)

    def format_output(self, result):
        """Format output."""
        return result


def test_test_planning_agent_creation():
    """Test that the test planning agent can be created."""
    agent = MockTestPlanningAgent()
    assert agent.agent_name == "TestPlanningAgent"
    assert agent.description == "Mock agent for test planning"


def test_test_planning_agent_input_validation():
    """Test test planning agent input validation."""
    agent = MockTestPlanningAgent()
    
    # Valid input
    valid_input = {
        "project_plan": {"project_name": "Test"},
        "module_structure": {"modules": []}
    }
    assert agent.validate_input(valid_input) is True
    
    # Invalid inputs
    assert agent.validate_input({}) is False
    assert agent.validate_input({"project_plan": {}}) is False
    assert agent.validate_input({"module_structure": {}}) is False
    assert agent.validate_input("not_a_dict") is False


def test_test_planning_agent_execution():
    """Test test planning agent execution."""
    agent = MockTestPlanningAgent()
    
    # First create a mock project plan
    planning_agent = MockProjectPlanningAgent()
    planning_input = {"description": "Test project"}
    planning_result = planning_agent.execute(planning_input)
    project_plan = planning_result["project_plan"]
    
    # Then create a mock module structure
    design_agent = MockModuleDesignAgent()
    design_input = {"project_plan": project_plan}
    design_result = design_agent.execute(design_input)
    module_structure = design_result["module_structure"]
    
    # Now test the test planning agent
    test_input = {
        "project_plan": project_plan,
        "module_structure": module_structure,
        "workflow_id": "test-workflow-003",
    }
    
    result = agent.execute(test_input)
    
    # Check that result contains expected keys
    assert "test_plans" in result
    assert "integration_test_plan" in result
    assert "e2e_test_plan" in result
    assert "test_analysis" in result
    assert "test_strategy" in result
    assert "test_recommendations" in result
    assert "coverage_analysis" in result
    assert "test_metadata" in result
    
    # Check test plans
    assert len(result["test_plans"]) > 0
    assert "integration_test_plan" in result
    assert "e2e_test_plan" in result
    
    # Check test metadata
    assert result["test_metadata"]["total_test_cases"] > 0


def test_test_planning_agent_format_output():
    """Test test planning agent output formatting."""
    agent = MockTestPlanningAgent()
    
    mock_result = {"test": "data"}
    formatted = agent.format_output(mock_result)
    assert formatted == mock_result
