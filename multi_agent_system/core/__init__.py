"""Core infrastructure for the multi-agent system."""

from .base_agent import BaseMultiAgent, AgentExecutionError, ValidationError
from .agent_registry import AgentRegistry, get_global_registry
from .data_store import SharedDataStore, get_global_data_store
from .coordinator import (
    MultiAgentCoordinator,
    WorkflowResult,
    RecoveryResult,
    get_global_coordinator,
)
from .models import (
    ProjectPlan,
    ModuleStructure,
    Module,
    Interface,
    TestPlan,
    TestCase,
    CodeArtifact,
    TestResult,
    WorkflowState,
    AgentOutput,
    ProjectContext,
    ProjectComplexity,
    TestType,
    TestStatus,
    WorkflowStatus,
)

__all__ = [
    # Base classes
    "BaseMultiAgent",
    "AgentExecutionError",
    "ValidationError",
    # Registry
    "AgentRegistry",
    "get_global_registry",
    # Data store
    "SharedDataStore",
    "get_global_data_store",
    # Coordinator
    "MultiAgentCoordinator",
    "WorkflowResult",
    "RecoveryResult",
    "get_global_coordinator",
    # Data models
    "ProjectPlan",
    "ModuleStructure",
    "Module",
    "Interface",
    "TestPlan",
    "TestCase",
    "CodeArtifact",
    "TestResult",
    "WorkflowState",
    "AgentOutput",
    "ProjectContext",
    # Enums
    "ProjectComplexity",
    "TestType",
    "TestStatus",
    "WorkflowStatus",
]
