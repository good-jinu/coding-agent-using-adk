"""Test script for the Project Planning Agent."""

import sys
import os
import pytest

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from multi_agent_system.core.base_agent import BaseMultiAgent
from multi_agent_system.core.models import ProjectPlan, TechnologyStack, ProjectRequirement


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
        # Validate input
        if not self.validate_input(input_data):
            raise ValueError("Invalid input data")

        # Return mock project plan
        mock_requirements = [
            ProjectRequirement(
                id="FR001",
                type="functional",
                description="User authentication system",
                priority="high",
                category="security"
            ),
            ProjectRequirement(
                id="FR002",
                type="functional",
                description="Task management functionality",
                priority="high",
                category="core"
            )
        ]
        
        mock_tech_stack = TechnologyStack(
            primary_language="Python",
            frameworks=["FastAPI", "Pydantic"],
            databases=["PostgreSQL"],
            tools=["Docker", "Git"],
            justification="Modern stack for web applications"
        )
        
        mock_project_plan = ProjectPlan(
            project_name="Task Management System",
            description="A web application for task management",
            project_type="web_application",
            target_users=["end users", "team members"],
            requirements=mock_requirements,
            technology_stack=mock_tech_stack,
            complexity_assessment={"level": "medium", "score": 6, "effort_estimate_days": 30},
            scope_definition={"in_scope": {}, "out_of_scope": {}},
            estimated_timeline_days=30,
            key_assumptions=[],
            success_criteria=[],
            risks_and_mitigation=[]
        )
        
        return {
            "project_plan": mock_project_plan.model_dump(),
            "analysis_summary": {"project_type": "web_application"},
            "complexity_assessment": {"level": "medium", "score": 6},
            "technology_recommendations": mock_tech_stack.model_dump(),
            "scope_definition": {},
        }

    def validate_input(self, input_data):
        """Validate input data."""
        return isinstance(input_data, dict) and "description" in input_data

    def format_output(self, result):
        """Format output."""
        return result


def test_project_planning_agent_creation():
    """Test that the project planning agent can be created."""
    agent = MockProjectPlanningAgent()
    assert agent.agent_name == "ProjectPlanningAgent"
    assert agent.description == "Mock agent for project planning"


def test_project_planning_agent_input_validation():
    """Test project planning agent input validation."""
    agent = MockProjectPlanningAgent()
    
    # Valid input
    valid_input = {"description": "Test project"}
    assert agent.validate_input(valid_input) is True
    
    # Invalid inputs
    assert agent.validate_input({}) is False
    assert agent.validate_input({"other_field": "value"}) is False
    assert agent.validate_input("not_a_dict") is False


def test_project_planning_agent_execution():
    """Test project planning agent execution."""
    agent = MockProjectPlanningAgent()
    
    input_data = {
        "description": "Create a web application for task management",
        "workflow_id": "test-workflow-001",
    }
    
    result = agent.execute(input_data)
    
    # Check that result contains expected keys
    assert "project_plan" in result
    assert "analysis_summary" in result
    assert "complexity_assessment" in result
    assert "technology_recommendations" in result
    
    # Check project plan structure
    project_plan = result["project_plan"]
    assert project_plan["project_name"] == "Task Management System"
    assert project_plan["project_type"] == "web_application"
    assert len(project_plan["requirements"]) > 0


def test_project_planning_agent_format_output():
    """Test project planning agent output formatting."""
    agent = MockProjectPlanningAgent()
    
    mock_result = {"test": "data"}
    formatted = agent.format_output(mock_result)
    assert formatted == mock_result
