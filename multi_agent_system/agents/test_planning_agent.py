"""Test Planning Agent implementation."""

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

from ..core.base_agent import BaseMultiAgent, AgentExecutionError, ValidationError
from ..core.models import TestPlan, TestCase, TestType
from ..core.data_store import get_global_data_store

logger = logging.getLogger(__name__)


class TestPlanningAgent(BaseMultiAgent):
    """
    Agent responsible for creating comprehensive test plans based on project plans
    and module structures, including unit, integration, and end-to-end tests.
    """

    def __init__(self):
        """Initialize the Test Planning Agent."""
        super().__init__(
            name="TestPlanningAgent",
            description="Creates comprehensive test strategies and plans for all project modules",
            instruction="""
You are an expert test architect and quality assurance specialist. Your role is to create 
comprehensive, systematic test plans that ensure software quality and reliability.

**Your Core Responsibilities:**

1. **Test Strategy Design**: Create comprehensive testing strategies covering all aspects
2. **Test Case Generation**: Generate detailed test cases for unit, integration, and e2e testing
3. **Test Data Planning**: Design test data sets including edge cases and boundary conditions
4. **Coverage Analysis**: Ensure complete test coverage of functionality and requirements
5. **Test Automation Planning**: Design tests suitable for automated execution

**Testing Approach:**

1. **Analyze Requirements**: Extract testable requirements from project plans and module designs
2. **Identify Test Scenarios**: Create test scenarios covering normal, edge, and error cases
3. **Design Test Cases**: Create detailed test cases with inputs, expected outputs, and assertions
4. **Plan Test Data**: Design comprehensive test data including boundary conditions
5. **Organize Test Suites**: Group tests logically by module, functionality, and test type

**Test Types and Coverage:**

**Unit Tests:**
- Test individual functions and methods in isolation
- Cover all public interfaces and edge cases
- Include positive and negative test scenarios
- Test error handling and exception cases

**Integration Tests:**
- Test module-to-module interactions
- Verify interface contracts and data flow
- Test external system integrations
- Validate end-to-end workflows

**End-to-End Tests:**
- Test complete user workflows and scenarios
- Validate business requirements fulfillment
- Test system behavior under realistic conditions
- Include performance and load considerations

**Test Design Principles:**
- **Comprehensive Coverage**: Test all requirements and edge cases
- **Maintainable Tests**: Create clear, readable, and maintainable test code
- **Independent Tests**: Ensure tests can run independently and in any order
- **Deterministic Results**: Tests should produce consistent, predictable results
- **Fast Execution**: Design tests for quick feedback cycles

**Test Case Structure:**
Each test case should include:
- Clear, descriptive name indicating what is being tested
- Detailed description of the test scenario
- Specific input data and parameters
- Expected output and behavior
- Assertions and validation criteria
- Setup and teardown requirements

**Quality Assurance Focus:**
- Ensure tests validate business requirements
- Include security and performance considerations
- Plan for accessibility and usability testing
- Consider cross-platform and browser compatibility
- Include regression testing strategies

Always create thorough, practical test plans that provide confidence in software quality.
            """,
        )

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute test planning based on project plan and module structure.

        Args:
            input_data: Dictionary containing project plan and module structure

        Returns:
            Dictionary containing comprehensive test plans
        """
        try:
            self.log_execution_start(input_data)

            # Get project plan and module structure
            project_plan = self._get_project_plan(input_data)
            module_structure = self._get_module_structure(input_data)

            if not project_plan:
                raise ValidationError(
                    self.agent_name, "project_plan", "Project plan is required"
                )
            if not module_structure:
                raise ValidationError(
                    self.agent_name, "module_structure", "Module structure is required"
                )

            # Analyze requirements for testing
            test_analysis = self._analyze_requirements_for_testing(
                project_plan, module_structure
            )

            # Generate test plans for each module
            test_plans = []
            modules = module_structure.get("modules", [])

            for module in modules:
                module_test_plan = self._create_module_test_plan(
                    module, project_plan, module_structure, test_analysis
                )
                test_plans.append(module_test_plan)

            # Create integration test plan
            integration_test_plan = self._create_integration_test_plan(
                modules, project_plan, module_structure, test_analysis
            )

            # Create end-to-end test plan
            e2e_test_plan = self._create_e2e_test_plan(
                project_plan, module_structure, test_analysis
            )

            # Generate test strategy and recommendations
            test_strategy = self._generate_test_strategy(project_plan, module_structure)
            test_recommendations = self._generate_test_recommendations(
                test_plans, test_analysis
            )

            # Create comprehensive output
            output = {
                "test_plans": [plan.model_dump() for plan in test_plans],
                "integration_test_plan": integration_test_plan.model_dump(),
                "e2e_test_plan": e2e_test_plan.model_dump(),
                "test_analysis": test_analysis,
                "test_strategy": test_strategy,
                "test_recommendations": test_recommendations,
                "coverage_analysis": self._analyze_test_coverage(
                    test_plans, integration_test_plan, e2e_test_plan
                ),
                "test_metadata": {
                    "agent_name": self.agent_name,
                    "timestamp": datetime.now().isoformat(),
                    "version": "1.0",
                    "total_test_cases": sum(
                        len(plan.get_all_tests()) for plan in test_plans
                    )
                    + len(integration_test_plan.get_all_tests())
                    + len(e2e_test_plan.get_all_tests()),
                },
            }

            self.log_execution_end(output)
            return output

        except Exception as e:
            self.log_error(e, "Test planning execution failed")
            raise AgentExecutionError(self.agent_name, str(e), e)

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate input data for test planning.

        Args:
            input_data: Input data to validate

        Returns:
            True if input is valid, False otherwise
        """
        try:
            # Check if input is a dictionary
            if not isinstance(input_data, dict):
                self.logger.error("Input data must be a dictionary")
                return False

            # Check for project plan and module structure (either in input or data store)
            project_plan = input_data.get("project_plan")
            module_structure = input_data.get("module_structure")

            if not project_plan or not module_structure:
                # Try to get from data store
                try:
                    data_store = get_global_data_store()
                    if not project_plan:
                        stored_plan = data_store.get_agent_output(
                            "ProjectPlanningAgent"
                        )
                        if not stored_plan:
                            self.logger.error(
                                "Project plan not found in input or data store"
                            )
                            return False

                    if not module_structure:
                        stored_structure = data_store.get_agent_output(
                            "ModuleDesignAgent"
                        )
                        if not stored_structure:
                            self.logger.error(
                                "Module structure not found in input or data store"
                            )
                            return False
                except Exception:
                    self.logger.error(
                        "Could not retrieve required data from data store"
                    )
                    return False

            return True

        except Exception as e:
            self.logger.error(f"Input validation error: {e}")
            return False

    def format_output(self, result: Any) -> Dict[str, Any]:
        """
        Format the test planning result for next agent.

        Args:
            result: Raw execution result

        Returns:
            Formatted output dictionary
        """
        if isinstance(result, dict):
            return result

        # If result is not a dict, wrap it
        return {
            "test_plans": result,
            "agent": self.agent_name,
            "timestamp": datetime.now().isoformat(),
        }

    def _get_project_plan(self, input_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get project plan from input data or data store."""
        # First try to get from input
        project_plan = input_data.get("project_plan")
        if project_plan:
            return project_plan

        # Try to get from data store
        try:
            data_store = get_global_data_store()
            stored_output = data_store.get_agent_output("ProjectPlanningAgent")
            if stored_output and "project_plan" in stored_output:
                return stored_output["project_plan"]
        except Exception as e:
            self.logger.warning(f"Could not retrieve project plan from data store: {e}")

        return None

    def _get_module_structure(
        self, input_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Get module structure from input data or data store."""
        # First try to get from input
        module_structure = input_data.get("module_structure")
        if module_structure:
            return module_structure

        # Try to get from data store
        try:
            data_store = get_global_data_store()
            stored_output = data_store.get_agent_output("ModuleDesignAgent")
            if stored_output and "module_structure" in stored_output:
                return stored_output["module_structure"]
        except Exception as e:
            self.logger.warning(
                f"Could not retrieve module structure from data store: {e}"
            )

        return None

    def _analyze_requirements_for_testing(
        self, project_plan: Dict[str, Any], module_structure: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze project requirements to identify testing needs.

        Args:
            project_plan: Project plan data
            module_structure: Module structure data

        Returns:
            Dictionary containing test analysis
        """
        analysis = {
            "testable_requirements": [],
            "critical_paths": [],
            "edge_cases": [],
            "integration_points": [],
            "performance_requirements": [],
            "security_requirements": [],
            "user_workflows": [],
            "error_scenarios": [],
        }

        # Analyze requirements for testability
        requirements = project_plan.get("requirements", [])
        for req in requirements:
            if self._is_testable_requirement(req):
                analysis["testable_requirements"].append(req)

            if req.get("category") == "performance":
                analysis["performance_requirements"].append(req)
            elif "security" in req.get("description", "").lower():
                analysis["security_requirements"].append(req)

        # Identify critical paths from module dependencies
        dependencies = module_structure.get("dependencies", {})
        analysis["critical_paths"] = self._identify_critical_paths(dependencies)

        # Identify integration points
        analysis["integration_points"] = self._identify_integration_points(
            module_structure
        )

        # Extract user workflows
        analysis["user_workflows"] = self._extract_user_workflows(project_plan)

        # Identify edge cases and error scenarios
        analysis["edge_cases"] = self._identify_edge_cases(
            project_plan, module_structure
        )
        analysis["error_scenarios"] = self._identify_error_scenarios(
            project_plan, module_structure
        )

        return analysis

    def _is_testable_requirement(self, requirement: Dict[str, Any]) -> bool:
        """Check if a requirement is testable."""
        description = requirement.get("description", "").lower()

        # Requirements that are typically testable
        testable_indicators = [
            "should",
            "must",
            "will",
            "can",
            "allow",
            "enable",
            "provide",
            "create",
            "update",
            "delete",
            "display",
            "calculate",
            "validate",
            "authenticate",
            "authorize",
            "send",
            "receive",
            "process",
        ]

        return any(indicator in description for indicator in testable_indicators)

    def _identify_critical_paths(
        self, dependencies: Dict[str, List[str]]
    ) -> List[List[str]]:
        """Identify critical paths through module dependencies."""
        paths = []

        # Find modules with no dependencies (entry points)
        entry_points = [module for module, deps in dependencies.items() if not deps]

        # Find modules with no dependents (exit points)
        all_deps = set()
        for deps in dependencies.values():
            all_deps.update(deps)
        exit_points = [
            module for module in dependencies.keys() if module not in all_deps
        ]

        # Create paths from entry to exit points
        for entry in entry_points:
            for exit in exit_points:
                path = self._find_path(entry, exit, dependencies)
                if path:
                    paths.append(path)

        return paths[:5]  # Limit to top 5 critical paths

    def _find_path(
        self, start: str, end: str, dependencies: Dict[str, List[str]]
    ) -> Optional[List[str]]:
        """Find a path from start to end module."""
        if start == end:
            return [start]

        visited = set()
        queue = [(start, [start])]

        while queue:
            current, path = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)

            # Find modules that depend on current
            for module, deps in dependencies.items():
                if current in deps and module not in visited:
                    new_path = path + [module]
                    if module == end:
                        return new_path
                    queue.append((module, new_path))

        return None

    def _identify_integration_points(
        self, module_structure: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Identify integration points between modules."""
        integration_points = []
        dependencies = module_structure.get("dependencies", {})

        for module, deps in dependencies.items():
            for dep in deps:
                integration_points.append(
                    {"from_module": module, "to_module": dep, "type": "dependency"}
                )

        return integration_points

    def _extract_user_workflows(
        self, project_plan: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract user workflows from project requirements."""
        workflows = []
        requirements = project_plan.get("requirements", [])

        # Common workflow patterns
        workflow_patterns = [
            {
                "name": "User Registration",
                "steps": ["visit_signup", "enter_details", "verify_email", "login"],
                "requirements": ["authentication", "user", "email"],
            },
            {
                "name": "Task Management",
                "steps": [
                    "login",
                    "create_task",
                    "assign_task",
                    "update_status",
                    "complete_task",
                ],
                "requirements": ["task", "create", "update", "assign"],
            },
            {
                "name": "Data Processing",
                "steps": [
                    "upload_data",
                    "validate_data",
                    "process_data",
                    "generate_report",
                ],
                "requirements": ["upload", "process", "validate", "report"],
            },
        ]

        for pattern in workflow_patterns:
            # Check if requirements match this workflow pattern
            req_text = " ".join(
                [req.get("description", "") for req in requirements]
            ).lower()
            if all(keyword in req_text for keyword in pattern["requirements"]):
                workflows.append(pattern)

        return workflows[:3]  # Limit to top 3 workflows

    def _identify_edge_cases(
        self, project_plan: Dict[str, Any], module_structure: Dict[str, Any]
    ) -> List[str]:
        """Identify edge cases to test."""
        edge_cases = [
            "Empty input data",
            "Maximum input size",
            "Invalid data types",
            "Null/undefined values",
            "Concurrent access",
            "Network timeouts",
            "Database connection failures",
            "Memory limitations",
            "Invalid user permissions",
            "Malformed requests",
        ]

        # Add project-specific edge cases based on requirements
        requirements = project_plan.get("requirements", [])
        for req in requirements:
            description = req.get("description", "").lower()
            if "email" in description:
                edge_cases.append("Invalid email formats")
            if "password" in description:
                edge_cases.append("Weak password validation")
            if "file" in description or "upload" in description:
                edge_cases.append("Large file uploads")
                edge_cases.append("Unsupported file types")

        return edge_cases[:12]  # Limit to 12 edge cases

    def _identify_error_scenarios(
        self, project_plan: Dict[str, Any], module_structure: Dict[str, Any]
    ) -> List[str]:
        """Identify error scenarios to test."""
        error_scenarios = [
            "Invalid authentication credentials",
            "Unauthorized access attempts",
            "Server internal errors",
            "Database query failures",
            "External API unavailability",
            "Input validation failures",
            "Resource not found errors",
            "Timeout exceptions",
            "Insufficient permissions",
            "Data corruption scenarios",
        ]

        return error_scenarios[:10]  # Limit to 10 error scenarios

    def _create_module_test_plan(
        self,
        module: Dict[str, Any],
        project_plan: Dict[str, Any],
        module_structure: Dict[str, Any],
        test_analysis: Dict[str, Any],
    ) -> TestPlan:
        """Create a test plan for a specific module."""
        module_name = module.get("name", "")

        # Generate unit tests
        unit_tests = self._generate_unit_tests(module, test_analysis)

        # Generate integration tests for this module
        integration_tests = self._generate_module_integration_tests(
            module, module_structure, test_analysis
        )

        return TestPlan(
            module_name=module_name,
            unit_tests=unit_tests,
            integration_tests=integration_tests,
            e2e_tests=[],  # E2E tests are handled separately
        )

    def _generate_unit_tests(
        self, module: Dict[str, Any], test_analysis: Dict[str, Any]
    ) -> List[TestCase]:
        """Generate unit tests for a module."""
        unit_tests = []
        module_name = module.get("name", "")
        public_interface = module.get("public_interface", [])

        for i, method in enumerate(public_interface[:6], 1):  # Limit to 6 methods
            # Parse method signature
            method_name = method.split("(")[0] if "(" in method else method

            # Generate positive test case
            positive_test = TestCase(
                name=f"test_{method_name}_success",
                description=f"Test successful execution of {method_name}",
                input_data=self._generate_test_input(method, "positive"),
                expected_output=self._generate_expected_output(method, "positive"),
                test_type=TestType.UNIT,
                module_name=module_name,
            )
            unit_tests.append(positive_test)

            # Generate negative test case
            negative_test = TestCase(
                name=f"test_{method_name}_invalid_input",
                description=f"Test {method_name} with invalid input",
                input_data=self._generate_test_input(method, "negative"),
                expected_output=self._generate_expected_output(method, "negative"),
                test_type=TestType.UNIT,
                module_name=module_name,
            )
            unit_tests.append(negative_test)

        # Add edge case tests
        for edge_case in test_analysis["edge_cases"][
            :3
        ]:  # Limit to 3 edge cases per module
            edge_test = TestCase(
                name=f"test_{module_name}_edge_case_{edge_case.replace(' ', '_').lower()}",
                description=f"Test {module_name} with edge case: {edge_case}",
                input_data={"edge_case": edge_case},
                expected_output={"handled": True, "error": None},
                test_type=TestType.UNIT,
                module_name=module_name,
            )
            unit_tests.append(edge_test)

        return unit_tests

    def _generate_test_input(self, method: str, test_type: str) -> Dict[str, Any]:
        """Generate test input data for a method."""
        method_name = method.split("(")[0] if "(" in method else method

        if test_type == "positive":
            # Generate valid input based on method name
            if "create" in method_name.lower():
                return {"data": {"name": "test_item", "status": "active"}}
            elif "get" in method_name.lower():
                return {"id": "test_id_123"}
            elif "update" in method_name.lower():
                return {"id": "test_id_123", "data": {"status": "updated"}}
            elif "delete" in method_name.lower():
                return {"id": "test_id_123"}
            elif "authenticate" in method_name.lower():
                return {"username": "testuser", "password": "testpass123"}
            else:
                return {"param": "valid_value"}
        else:  # negative
            # Generate invalid input
            if "create" in method_name.lower():
                return {"data": None}
            elif "get" in method_name.lower():
                return {"id": ""}
            elif "update" in method_name.lower():
                return {"id": None, "data": {}}
            elif "delete" in method_name.lower():
                return {"id": "nonexistent_id"}
            elif "authenticate" in method_name.lower():
                return {"username": "", "password": ""}
            else:
                return {"param": None}

    def _generate_expected_output(self, method: str, test_type: str) -> Any:
        """Generate expected output for a method."""
        method_name = method.split("(")[0] if "(" in method else method

        if test_type == "positive":
            if "create" in method_name.lower():
                return {"id": "generated_id", "status": "created"}
            elif "get" in method_name.lower():
                return {"id": "test_id_123", "data": "retrieved_data"}
            elif "update" in method_name.lower():
                return {"id": "test_id_123", "status": "updated"}
            elif "delete" in method_name.lower():
                return {"success": True}
            elif "authenticate" in method_name.lower():
                return {"authenticated": True, "token": "auth_token"}
            else:
                return {"result": "success"}
        else:  # negative
            return {"error": "Invalid input", "success": False}

    def _generate_module_integration_tests(
        self,
        module: Dict[str, Any],
        module_structure: Dict[str, Any],
        test_analysis: Dict[str, Any],
    ) -> List[TestCase]:
        """Generate integration tests for a module."""
        integration_tests = []
        module_name = module.get("name", "")
        dependencies = module.get("dependencies", [])

        # Test integration with each dependency
        for dep in dependencies[:3]:  # Limit to 3 dependencies
            integration_test = TestCase(
                name=f"test_{module_name}_integration_with_{dep}",
                description=f"Test integration between {module_name} and {dep}",
                input_data={
                    "module": module_name,
                    "dependency": dep,
                    "action": "integrate",
                },
                expected_output={"integration_success": True, "data_flow": "verified"},
                test_type=TestType.INTEGRATION,
                module_name=module_name,
            )
            integration_tests.append(integration_test)

        return integration_tests

    def _create_integration_test_plan(
        self,
        modules: List[Dict[str, Any]],
        project_plan: Dict[str, Any],
        module_structure: Dict[str, Any],
        test_analysis: Dict[str, Any],
    ) -> TestPlan:
        """Create integration test plan for the entire system."""
        integration_tests = []

        # Test critical paths
        for path in test_analysis["critical_paths"][:3]:  # Limit to 3 critical paths
            path_test = TestCase(
                name=f"test_critical_path_{'_to_'.join(path)}",
                description=f"Test critical path: {' -> '.join(path)}",
                input_data={"path": path, "test_data": "sample_data"},
                expected_output={"path_success": True, "data_integrity": True},
                test_type=TestType.INTEGRATION,
                module_name="system_integration",
            )
            integration_tests.append(path_test)

        # Test integration points
        for integration_point in test_analysis["integration_points"][:5]:  # Limit to 5
            integration_test = TestCase(
                name=f"test_integration_{integration_point['from_module']}_to_{integration_point['to_module']}",
                description=f"Test integration from {integration_point['from_module']} to {integration_point['to_module']}",
                input_data=integration_point,
                expected_output={"integration_verified": True},
                test_type=TestType.INTEGRATION,
                module_name="system_integration",
            )
            integration_tests.append(integration_test)

        return TestPlan(
            module_name="system_integration",
            unit_tests=[],
            integration_tests=integration_tests,
            e2e_tests=[],
        )

    def _create_e2e_test_plan(
        self,
        project_plan: Dict[str, Any],
        module_structure: Dict[str, Any],
        test_analysis: Dict[str, Any],
    ) -> TestPlan:
        """Create end-to-end test plan."""
        e2e_tests = []

        # Test user workflows
        for workflow in test_analysis["user_workflows"]:
            workflow_test = TestCase(
                name=f"test_e2e_{workflow['name'].lower().replace(' ', '_')}",
                description=f"End-to-end test for {workflow['name']} workflow",
                input_data={"workflow": workflow["name"], "steps": workflow["steps"]},
                expected_output={"workflow_completed": True, "all_steps_passed": True},
                test_type=TestType.E2E,
                module_name="end_to_end",
            )
            e2e_tests.append(workflow_test)

        # Test error scenarios
        for error_scenario in test_analysis["error_scenarios"][:3]:  # Limit to 3
            error_test = TestCase(
                name=f"test_e2e_error_{error_scenario.lower().replace(' ', '_')}",
                description=f"End-to-end test for error scenario: {error_scenario}",
                input_data={"error_scenario": error_scenario},
                expected_output={"error_handled": True, "graceful_degradation": True},
                test_type=TestType.E2E,
                module_name="end_to_end",
            )
            e2e_tests.append(error_test)

        return TestPlan(
            module_name="end_to_end",
            unit_tests=[],
            integration_tests=[],
            e2e_tests=e2e_tests,
        )

    def _generate_test_strategy(
        self, project_plan: Dict[str, Any], module_structure: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate overall test strategy."""
        complexity = project_plan.get("complexity_assessment", {}).get(
            "level", "medium"
        )

        strategy = {
            "approach": "Comprehensive multi-layer testing",
            "test_pyramid": {
                "unit_tests": "70% - Fast, isolated tests for individual components",
                "integration_tests": "20% - Module interaction and API contract tests",
                "e2e_tests": "10% - Critical user journey and workflow tests",
            },
            "automation_level": "High"
            if complexity in ["high", "very_high"]
            else "Medium",
            "test_environments": ["development", "staging", "production"],
            "ci_cd_integration": True,
            "performance_testing": complexity in ["high", "very_high"],
            "security_testing": True,
            "accessibility_testing": "web" in project_plan.get("project_type", ""),
            "cross_browser_testing": "web" in project_plan.get("project_type", ""),
        }

        return strategy

    def _generate_test_recommendations(
        self, test_plans: List[TestPlan], test_analysis: Dict[str, Any]
    ) -> List[str]:
        """Generate test recommendations."""
        recommendations = []

        total_tests = sum(len(plan.get_all_tests()) for plan in test_plans)

        # Test count recommendations
        if total_tests > 100:
            recommendations.append("Consider test parallelization for faster execution")
        elif total_tests < 20:
            recommendations.append("Consider adding more comprehensive test coverage")

        # Coverage recommendations
        recommendations.extend(
            [
                "Implement code coverage tracking with minimum 80% threshold",
                "Use test-driven development (TDD) approach for new features",
                "Implement continuous integration with automated test execution",
                "Create test data factories for consistent test data generation",
                "Implement proper test isolation and cleanup procedures",
            ]
        )

        # Project-specific recommendations
        if test_analysis["performance_requirements"]:
            recommendations.append(
                "Implement performance testing with load and stress tests"
            )

        if test_analysis["security_requirements"]:
            recommendations.append("Include security testing with penetration testing")

        recommendations.extend(
            [
                "Document test cases with clear acceptance criteria",
                "Implement test reporting and metrics tracking",
                "Regular test maintenance and refactoring",
                "Consider mutation testing for test quality validation",
            ]
        )

        return recommendations

    def _analyze_test_coverage(
        self, test_plans: List[TestPlan], integration_plan: TestPlan, e2e_plan: TestPlan
    ) -> Dict[str, Any]:
        """Analyze test coverage across all test plans."""
        total_unit_tests = sum(len(plan.unit_tests) for plan in test_plans)
        total_integration_tests = sum(
            len(plan.integration_tests) for plan in test_plans
        ) + len(integration_plan.integration_tests)
        total_e2e_tests = len(e2e_plan.e2e_tests)
        total_tests = total_unit_tests + total_integration_tests + total_e2e_tests

        coverage_analysis = {
            "total_test_cases": total_tests,
            "unit_test_count": total_unit_tests,
            "integration_test_count": total_integration_tests,
            "e2e_test_count": total_e2e_tests,
            "test_distribution": {
                "unit_percentage": round(
                    (total_unit_tests / total_tests * 100) if total_tests > 0 else 0, 1
                ),
                "integration_percentage": round(
                    (total_integration_tests / total_tests * 100)
                    if total_tests > 0
                    else 0,
                    1,
                ),
                "e2e_percentage": round(
                    (total_e2e_tests / total_tests * 100) if total_tests > 0 else 0, 1
                ),
            },
            "coverage_quality": "Good" if total_tests >= 30 else "Needs Improvement",
            "pyramid_compliance": self._check_test_pyramid_compliance(
                total_unit_tests, total_integration_tests, total_e2e_tests
            ),
        }

        return coverage_analysis

    def _check_test_pyramid_compliance(
        self, unit_count: int, integration_count: int, e2e_count: int
    ) -> Dict[str, Any]:
        """Check if test distribution follows the test pyramid principle."""
        total = unit_count + integration_count + e2e_count
        if total == 0:
            return {"compliant": False, "reason": "No tests defined"}

        unit_percentage = unit_count / total * 100
        integration_percentage = integration_count / total * 100
        e2e_percentage = e2e_count / total * 100

        # Ideal test pyramid: 70% unit, 20% integration, 10% e2e
        compliant = (
            unit_percentage >= 60  # At least 60% unit tests
            and integration_percentage <= 30  # At most 30% integration tests
            and e2e_percentage <= 20  # At most 20% e2e tests
        )

        return {
            "compliant": compliant,
            "unit_percentage": round(unit_percentage, 1),
            "integration_percentage": round(integration_percentage, 1),
            "e2e_percentage": round(e2e_percentage, 1),
            "recommendation": "Good test pyramid distribution"
            if compliant
            else "Consider rebalancing test distribution",
        }
