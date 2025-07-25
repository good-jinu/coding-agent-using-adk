"""Shared data models for the multi-agent system."""

from typing import List, Dict, Any, Optional
from pydantic import field_validator, BaseModel, Field
from datetime import datetime
from enum import Enum


class ProjectComplexity(str, Enum):
    """Project complexity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class RequirementType(str, Enum):
    """Types of project requirements."""

    FUNCTIONAL = "functional"
    NON_FUNCTIONAL = "non_functional"
    TECHNICAL = "technical"


class RequirementPriority(str, Enum):
    """Priority levels for requirements."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class UnitTestType(str, Enum):
    """Types of tests."""

    UNIT = "unit"
    INTEGRATION = "integration"
    E2E = "e2e"
    PERFORMANCE = "performance"


# Aliases for backward compatibility
TestType = UnitTestType
TestingType = UnitTestType


class UnitTestStatus(str, Enum):
    """Test execution status."""

    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    SKIPPED = "skipped"


# Aliases for backward compatibility
TestStatus = UnitTestStatus
TestingStatus = UnitTestStatus


class WorkflowStatus(str, Enum):
    """Workflow execution status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ProjectRequirement(BaseModel):
    """Individual project requirement."""

    id: str = Field(..., description="Unique requirement identifier")
    type: RequirementType = Field(..., description="Type of requirement")
    description: str = Field(..., description="Requirement description")
    priority: RequirementPriority = Field(..., description="Requirement priority")
    category: str = Field(..., description="Requirement category")
    acceptance_criteria: List[str] = Field(
        default_factory=list, description="Acceptance criteria for the requirement"
    )

    @field_validator("description")
    @classmethod
    def validate_description(cls, v):
        if not v or not v.strip():
            raise ValueError("Requirement description cannot be empty")
        return v.strip()


class TechnologyStack(BaseModel):
    """Technology stack recommendation."""

    primary_language: str = Field(..., description="Primary programming language")
    frameworks: List[str] = Field(
        default_factory=list, description="Recommended frameworks"
    )
    databases: List[str] = Field(
        default_factory=list, description="Recommended databases"
    )
    tools: List[str] = Field(
        default_factory=list, description="Development and deployment tools"
    )
    justification: str = Field(..., description="Justification for technology choices")


class ProjectPlan(BaseModel):
    """Project planning data model."""

    project_name: str = Field(..., description="Name of the project")
    description: str = Field(..., description="Detailed project description")
    project_type: str = Field(..., description="Type of project")
    target_users: List[str] = Field(
        default_factory=list, description="Target user groups"
    )
    requirements: List[ProjectRequirement] = Field(
        default_factory=list, description="List of project requirements"
    )
    technology_stack: TechnologyStack = Field(
        ..., description="Recommended technology stack"
    )
    complexity_assessment: Dict[str, Any] = Field(
        default_factory=dict, description="Project complexity assessment"
    )
    scope_definition: Dict[str, Any] = Field(
        default_factory=dict, description="Project scope definition"
    )
    estimated_timeline_days: int = Field(..., description="Estimated timeline in days")
    key_assumptions: List[str] = Field(
        default_factory=list, description="Key project assumptions"
    )
    success_criteria: List[str] = Field(
        default_factory=list, description="Project success criteria"
    )
    risks_and_mitigation: List[Dict[str, str]] = Field(
        default_factory=list, description="Identified risks and mitigation strategies"
    )
    created_at: datetime = Field(
        default_factory=datetime.now, description="Creation timestamp"
    )

    @field_validator("project_name")
    @classmethod
    def validate_project_name(cls, v):
        if not v or not v.strip():
            raise ValueError("Project name cannot be empty")
        return v.strip()

    @field_validator("estimated_timeline_days")
    @classmethod
    def validate_timeline(cls, v):
        if v <= 0:
            raise ValueError("Estimated timeline must be positive")
        return v


class Interface(BaseModel):
    """Interface definition for modules."""

    name: str = Field(..., description="Interface name")
    methods: List[str] = Field(
        default_factory=list, description="List of method signatures"
    )
    properties: List[str] = Field(
        default_factory=list, description="List of properties"
    )
    description: str = Field("", description="Interface description")


class Module(BaseModel):
    """Module definition."""

    name: str = Field(..., description="Module name")
    purpose: str = Field(..., description="Module purpose and responsibility")
    public_interface: List[str] = Field(
        default_factory=list, description="Public interface methods"
    )
    dependencies: List[str] = Field(
        default_factory=list, description="List of module dependencies"
    )
    estimated_complexity: int = Field(
        1, ge=1, le=10, description="Complexity score (1-10)"
    )
    file_path: Optional[str] = Field(
        None, description="Expected file path for the module"
    )

    @field_validator("name")
    @classmethod
    def validate_module_name(cls, v):
        if not v or not v.strip():
            raise ValueError("Module name cannot be empty")
        return v.strip()


class ModuleStructure(BaseModel):
    """Module structure and architecture definition."""

    modules: List[Module] = Field(default_factory=list, description="List of modules")
    interfaces: List[Interface] = Field(
        default_factory=list, description="List of interfaces"
    )
    dependencies: Dict[str, List[str]] = Field(
        default_factory=dict, description="Module dependency graph"
    )
    architecture_pattern: str = Field("", description="Architecture pattern used")
    created_at: datetime = Field(
        default_factory=datetime.now, description="Creation timestamp"
    )

    def get_module_by_name(self, name: str) -> Optional[Module]:
        """Get a module by name."""
        for module in self.modules:
            if module.name == name:
                return module
        return None

    def validate_dependencies(self) -> bool:
        """Validate that all dependencies exist."""
        module_names = {module.name for module in self.modules}
        for module_name, deps in self.dependencies.items():
            if module_name not in module_names:
                return False
            for dep in deps:
                if dep not in module_names:
                    return False
        return True


class UnitTestCase(BaseModel):
    """Test case definition."""

    name: str = Field(..., description="Test case name")
    description: str = Field(..., description="Test case description")
    input_data: Dict[str, Any] = Field(
        default_factory=dict, description="Test input data"
    )
    expected_output: Any = Field(None, description="Expected test output")
    test_type: TestType = Field(..., description="Type of test")
    module_name: str = Field(..., description="Target module name")

    @field_validator("name")
    @classmethod
    def validate_test_name(cls, v):
        if not v or not v.strip():
            raise ValueError("Test case name cannot be empty")
        return v.strip()


# Aliases for backward compatibility
TestCase = UnitTestCase
TestingCase = UnitTestCase


class UnitTestPlan(BaseModel):
    """Test planning data model."""

    module_name: str = Field(..., description="Target module name")
    unit_tests: List[TestCase] = Field(
        default_factory=list, description="Unit test cases"
    )
    integration_tests: List[TestCase] = Field(
        default_factory=list, description="Integration test cases"
    )
    e2e_tests: List[TestCase] = Field(
        default_factory=list, description="End-to-end test cases"
    )
    created_at: datetime = Field(
        default_factory=datetime.now, description="Creation timestamp"
    )

    def get_all_tests(self) -> List[TestCase]:
        """Get all test cases combined."""
        return self.unit_tests + self.integration_tests + self.e2e_tests

    def get_tests_by_type(self, test_type: TestType) -> List[TestCase]:
        """Get test cases by type."""
        all_tests = self.get_all_tests()
        return [test for test in all_tests if test.test_type == test_type]


# Aliases for backward compatibility
TestPlan = UnitTestPlan
TestingPlan = UnitTestPlan


class CodeArtifact(BaseModel):
    """Generated code artifact."""

    file_path: str = Field(..., description="File path for the code")
    content: str = Field(..., description="Code content")
    language: str = Field(..., description="Programming language")
    module_name: str = Field(..., description="Associated module name")
    dependencies: List[str] = Field(
        default_factory=list, description="Code dependencies"
    )
    created_at: datetime = Field(
        default_factory=datetime.now, description="Creation timestamp"
    )

    @field_validator("file_path")
    @classmethod
    def validate_file_path(cls, v):
        if not v or not v.strip():
            raise ValueError("File path cannot be empty")
        return v.strip()


class UnitTestResult(BaseModel):
    """Test execution result."""

    test_name: str = Field(..., description="Name of the executed test")
    status: TestStatus = Field(..., description="Test execution status")
    execution_time: float = Field(0.0, ge=0, description="Execution time in seconds")
    error_message: Optional[str] = Field(
        None, description="Error message if test failed"
    )
    coverage_percentage: float = Field(
        0.0, ge=0, le=100, description="Code coverage percentage"
    )
    module_name: str = Field(..., description="Target module name")
    created_at: datetime = Field(
        default_factory=datetime.now, description="Execution timestamp"
    )


# Aliases for backward compatibility
TestResult = UnitTestResult
TestingResult = UnitTestResult


class WorkflowState(BaseModel):
    """Workflow execution state."""

    workflow_id: str = Field(..., description="Unique workflow identifier")
    status: WorkflowStatus = Field(
        WorkflowStatus.PENDING, description="Current workflow status"
    )
    current_agent: Optional[str] = Field(None, description="Currently executing agent")
    completed_agents: List[str] = Field(
        default_factory=list, description="List of completed agents"
    )
    failed_agents: List[str] = Field(
        default_factory=list, description="List of failed agents"
    )
    start_time: Optional[datetime] = Field(None, description="Workflow start time")
    end_time: Optional[datetime] = Field(None, description="Workflow end time")
    error_message: Optional[str] = Field(
        None, description="Error message if workflow failed"
    )

    def mark_agent_completed(self, agent_name: str) -> None:
        """Mark an agent as completed."""
        if agent_name not in self.completed_agents:
            self.completed_agents.append(agent_name)
        if agent_name in self.failed_agents:
            self.failed_agents.remove(agent_name)

    def mark_agent_failed(self, agent_name: str, error_message: str) -> None:
        """Mark an agent as failed."""
        if agent_name not in self.failed_agents:
            self.failed_agents.append(agent_name)
        self.error_message = error_message

    def get_progress_percentage(self, total_agents: int) -> float:
        """Calculate workflow progress percentage."""
        if total_agents == 0:
            return 0.0
        return (len(self.completed_agents) / total_agents) * 100


class AgentOutput(BaseModel):
    """Standard agent output format."""

    agent_name: str = Field(
        ..., description="Name of the agent that produced this output"
    )
    output_type: str = Field(
        ..., description="Type of output (e.g., 'project_plan', 'module_structure')"
    )
    data: Dict[str, Any] = Field(..., description="Actual output data")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
    created_at: datetime = Field(
        default_factory=datetime.now, description="Creation timestamp"
    )

    @field_validator("agent_name")
    @classmethod
    def validate_agent_name(cls, v):
        if not v or not v.strip():
            raise ValueError("Agent name cannot be empty")
        return v.strip()


class ProjectContext(BaseModel):
    """Complete project context containing all data."""

    project_plan: Optional[ProjectPlan] = Field(
        None, description="Project planning data"
    )
    module_structure: Optional[ModuleStructure] = Field(
        None, description="Module structure data"
    )
    test_plans: List[TestPlan] = Field(
        default_factory=list, description="Test plans for all modules"
    )
    code_artifacts: List[CodeArtifact] = Field(
        default_factory=list, description="Generated code artifacts"
    )
    test_results: List[TestResult] = Field(
        default_factory=list, description="Test execution results"
    )
    workflow_state: Optional[WorkflowState] = Field(
        None, description="Current workflow state"
    )
    created_at: datetime = Field(
        default_factory=datetime.now, description="Creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.now, description="Last update timestamp"
    )

    def update_timestamp(self) -> None:
        """Update the last modified timestamp."""
        self.updated_at = datetime.now()

    def get_test_plan_for_module(self, module_name: str) -> Optional[TestPlan]:
        """Get test plan for a specific module."""
        for test_plan in self.test_plans:
            if test_plan.module_name == module_name:
                return test_plan
        return None

    def get_code_artifact_for_module(self, module_name: str) -> Optional[CodeArtifact]:
        """Get code artifact for a specific module."""
        for artifact in self.code_artifacts:
            if artifact.module_name == module_name:
                return artifact
        return None
