"""Test script for the Module Design Agent."""

import sys
import os
import pytest

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from multi_agent_system.core.base_agent import BaseMultiAgent
from multi_agent_system.core.models import ModuleStructure, Module, Interface


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
                "requirements": [],
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
        # Validate input
        if not self.validate_input(input_data):
            raise ValueError("Invalid input data")

        # Create mock modules
        mock_modules = [
            Module(
                name="auth_module",
                purpose="Authentication and authorization",
                public_interface=["authenticate", "authorize"],
                dependencies=[],
                estimated_complexity=3,
                file_path="src/auth/auth_module.py"
            ),
            Module(
                name="task_module",
                purpose="Task management functionality",
                public_interface=["create_task", "update_task", "delete_task"],
                dependencies=["auth_module"],
                estimated_complexity=5,
                file_path="src/tasks/task_module.py"
            )
        ]
        
        # Create mock interfaces
        mock_interfaces = [
            Interface(
                name="AuthInterface",
                methods=["authenticate", "authorize"],
                properties=["current_user"],
                description="Authentication interface"
            ),
            Interface(
                name="TaskInterface",
                methods=["create_task", "update_task", "delete_task"],
                properties=[],
                description="Task management interface"
            )
        ]
        
        # Create mock dependencies
        mock_dependencies = {
            "auth_module": [],
            "task_module": ["auth_module"]
        }
        
        # Create mock module structure
        mock_module_structure = ModuleStructure(
            modules=mock_modules,
            interfaces=mock_interfaces,
            dependencies=mock_dependencies,
            architecture_pattern="Layered Architecture"
        )
        
        return {
            "module_structure": mock_module_structure.model_dump(),
            "design_analysis": {"project_type": "web_application"},
            "architecture_pattern": "Layered Architecture",
            "validation_result": {"is_valid": True, "errors": [], "warnings": []},
            "design_recommendations": ["Use dependency injection", "Implement proper error handling"]
        }

    def validate_input(self, input_data):
        """Validate input data."""
        return isinstance(input_data, dict) and "project_plan" in input_data

    def format_output(self, result):
        """Format output."""
        return result


def test_module_design_agent_creation():
    """Test that the module design agent can be created."""
    agent = MockModuleDesignAgent()
    assert agent.agent_name == "ModuleDesignAgent"
    assert agent.description == "Mock agent for module design"


def test_module_design_agent_input_validation():
    """Test module design agent input validation."""
    agent = MockModuleDesignAgent()
    
    # Valid input
    valid_input = {"project_plan": {"project_name": "Test"}}
    assert agent.validate_input(valid_input) is True
    
    # Invalid inputs
    assert agent.validate_input({}) is False
    assert agent.validate_input({"other_field": "value"}) is False
    assert agent.validate_input("not_a_dict") is False


def test_module_design_agent_execution():
    """Test module design agent execution."""
    agent = MockModuleDesignAgent()
    
    # First create a mock project plan
    planning_agent = MockProjectPlanningAgent()
    planning_input = {"description": "Test project"}
    planning_result = planning_agent.execute(planning_input)
    project_plan = planning_result["project_plan"]
    
    # Now test the module design agent
    design_input = {"project_plan": project_plan, "workflow_id": "test-workflow-002"}
    
    result = agent.execute(design_input)
    
    # Check that result contains expected keys
    assert "module_structure" in result
    assert "design_analysis" in result
    assert "architecture_pattern" in result
    assert "validation_result" in result
    assert "design_recommendations" in result
    
    # Check module structure
    module_structure = result["module_structure"]
    assert len(module_structure["modules"]) > 0
    assert len(module_structure["interfaces"]) > 0
    assert len(module_structure["dependencies"]) > 0
    assert module_structure["architecture_pattern"] == "Layered Architecture"
    
    # Check validation result
    validation_result = result["validation_result"]
    assert validation_result["is_valid"] is True


def test_module_design_agent_format_output():
    """Test module design agent output formatting."""
    agent = MockModuleDesignAgent()
    
    mock_result = {"test": "data"}
    formatted = agent.format_output(mock_result)
    assert formatted == mock_result
