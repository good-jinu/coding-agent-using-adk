"""Module Design Agent implementation."""

from typing import Dict, Any, List, Optional, Set
import logging
import re
from datetime import datetime

from ..core.base_agent import BaseMultiAgent, AgentExecutionError, ValidationError
from ..core.models import ModuleStructure, Module, Interface
from ..core.data_store import get_global_data_store

logger = logging.getLogger(__name__)


class ModuleDesignAgent(BaseMultiAgent):
    """
    Agent responsible for analyzing project plans and creating detailed
    module structures with interfaces and dependency management.
    """

    def __init__(self):
        """Initialize the Module Design Agent."""
        super().__init__(
            name="ModuleDesignAgent",
            description="Designs software architecture and module structure based on project plans",
            instruction="""
You are an expert software architect specializing in modular design and system architecture. 
Your role is to analyze project plans and create well-structured, maintainable module architectures.

**Your Core Responsibilities:**

1. **Module Decomposition**: Break down project requirements into logical, cohesive modules
2. **Interface Design**: Define clear interfaces between modules with proper abstraction
3. **Dependency Management**: Create dependency graphs and ensure proper separation of concerns
4. **Architecture Patterns**: Apply appropriate architectural patterns (MVC, layered, microservices, etc.)
5. **Scalability Planning**: Design modules that can scale and evolve independently

**Design Process:**

1. **Analyze Project Plan**: Extract functional requirements and technical constraints
2. **Identify Core Domains**: Group related functionality into logical domains
3. **Define Module Boundaries**: Create modules with single responsibilities and clear purposes
4. **Design Interfaces**: Define public APIs and contracts between modules
5. **Manage Dependencies**: Ensure proper dependency direction and minimize coupling
6. **Validate Architecture**: Check for circular dependencies and architectural violations

**Design Principles:**
- Single Responsibility Principle: Each module should have one reason to change
- Dependency Inversion: Depend on abstractions, not concretions
- Interface Segregation: Create focused, specific interfaces
- Loose Coupling: Minimize dependencies between modules
- High Cohesion: Keep related functionality together

**Module Categories:**
- **Core/Domain**: Business logic and domain models
- **Service/Application**: Application services and use cases
- **Infrastructure**: External integrations, databases, APIs
- **Presentation**: User interfaces and controllers
- **Shared/Common**: Utilities and shared components

**Output Requirements:**
Create a comprehensive module structure that includes:
- Well-defined modules with clear responsibilities
- Public interfaces for each module
- Dependency graph showing module relationships
- Architecture pattern documentation
- Validation of design principles

Always prioritize maintainability, testability, and scalability in your designs.
            """,
        )

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute module design based on project plan.

        Args:
            input_data: Dictionary containing project plan and design parameters

        Returns:
            Dictionary containing module structure and architecture design
        """
        try:
            self.log_execution_start(input_data)

            # Get project plan from input or data store
            project_plan = self._get_project_plan(input_data)
            if not project_plan:
                raise ValidationError(
                    self.agent_name, "project_plan", "Project plan is required"
                )

            # Analyze project requirements for module design
            design_analysis = self._analyze_project_for_design(project_plan)

            # Identify core domains and module boundaries
            domains = self._identify_core_domains(project_plan, design_analysis)

            # Create module structure
            modules = self._create_modules(domains, project_plan, design_analysis)

            # Design interfaces for modules
            interfaces = self._design_module_interfaces(modules, project_plan)

            # Create dependency graph
            dependencies = self._create_dependency_graph(modules, interfaces)

            # Validate architecture
            validation_result = self._validate_architecture(modules, dependencies)

            # Determine architecture pattern
            architecture_pattern = self._determine_architecture_pattern(
                project_plan, modules
            )

            # Create module structure
            module_structure = ModuleStructure(
                modules=modules,
                interfaces=interfaces,
                dependencies=dependencies,
                architecture_pattern=architecture_pattern,
            )

            # Generate detailed output
            output = {
                "module_structure": module_structure.model_dump(),
                "design_analysis": design_analysis,
                "architecture_pattern": architecture_pattern,
                "validation_result": validation_result,
                "design_recommendations": self._generate_design_recommendations(
                    module_structure
                ),
                "design_metadata": {
                    "agent_name": self.agent_name,
                    "timestamp": datetime.now().isoformat(),
                    "version": "1.0",
                },
            }

            self.log_execution_end(output)
            return output

        except Exception as e:
            self.log_error(e, "Module design execution failed")
            raise AgentExecutionError(self.agent_name, str(e), e)

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate input data for module design.

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

            # Check for project plan (either in input or data store)
            project_plan = input_data.get("project_plan")
            if not project_plan:
                # Try to get from data store
                try:
                    data_store = get_global_data_store()
                    stored_plan = data_store.get_agent_output("ProjectPlanningAgent")
                    if not stored_plan:
                        self.logger.error(
                            "Project plan not found in input or data store"
                        )
                        return False
                except Exception:
                    self.logger.error("Could not retrieve project plan from data store")
                    return False

            return True

        except Exception as e:
            self.logger.error(f"Input validation error: {e}")
            return False

    def format_output(self, result: Any) -> Dict[str, Any]:
        """
        Format the module design result for next agent.

        Args:
            result: Raw execution result

        Returns:
            Formatted output dictionary
        """
        if isinstance(result, dict):
            return result

        # If result is not a dict, wrap it
        return {
            "module_structure": result,
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

    def _analyze_project_for_design(
        self, project_plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze project plan to extract design-relevant information.

        Args:
            project_plan: Project plan data

        Returns:
            Dictionary containing design analysis
        """
        analysis = {
            "project_type": project_plan.get("project_type", "general_application"),
            "complexity_level": project_plan.get("complexity_assessment", {}).get(
                "level", "medium"
            ),
            "functional_requirements": [],
            "non_functional_requirements": [],
            "integration_points": [],
            "data_entities": [],
            "user_interactions": [],
            "external_systems": [],
        }

        # Analyze requirements
        requirements = project_plan.get("requirements", [])
        for req in requirements:
            if req.get("type") == "functional":
                analysis["functional_requirements"].append(req)
            else:
                analysis["non_functional_requirements"].append(req)

        # Extract data entities from requirements
        analysis["data_entities"] = self._extract_data_entities(requirements)

        # Extract user interactions
        analysis["user_interactions"] = self._extract_user_interactions(requirements)

        # Extract integration points
        analysis["integration_points"] = self._extract_integration_points(requirements)

        # Extract external systems
        analysis["external_systems"] = self._extract_external_systems(requirements)

        return analysis

    def _extract_data_entities(self, requirements: List[Dict[str, Any]]) -> List[str]:
        """Extract data entities from requirements."""
        entities = set()

        # Common entity patterns
        entity_patterns = [
            r"\b(user|customer|client|account|profile)\b",
            r"\b(task|item|job|work|assignment)\b",
            r"\b(project|workspace|team|group)\b",
            r"\b(order|purchase|transaction|payment)\b",
            r"\b(product|service|item|catalog)\b",
            r"\b(message|notification|alert|email)\b",
            r"\b(report|analytics|dashboard|metric)\b",
            r"\b(file|document|attachment|media)\b",
            r"\b(setting|configuration|preference)\b",
            r"\b(log|audit|history|activity)\b",
        ]

        for req in requirements:
            description = req.get("description", "").lower()
            for pattern in entity_patterns:
                matches = re.findall(pattern, description)
                entities.update(matches)

        return list(entities)[:10]  # Limit to top 10 entities

    def _extract_user_interactions(
        self, requirements: List[Dict[str, Any]]
    ) -> List[str]:
        """Extract user interaction patterns from requirements."""
        interactions = set()

        # Common interaction patterns
        interaction_patterns = [
            r"(?:create|add|new) ([^.!?]+)",
            r"(?:update|edit|modify) ([^.!?]+)",
            r"(?:delete|remove) ([^.!?]+)",
            r"(?:view|display|show) ([^.!?]+)",
            r"(?:search|find|filter) ([^.!?]+)",
            r"(?:login|authenticate|signin)",
            r"(?:upload|download) ([^.!?]+)",
            r"(?:send|receive) ([^.!?]+)",
        ]

        for req in requirements:
            description = req.get("description", "").lower()
            for pattern in interaction_patterns:
                matches = re.findall(pattern, description)
                if matches:
                    if isinstance(matches[0], str):
                        interactions.add(matches[0].strip())
                    else:
                        interactions.add(pattern.split("(")[0])

        return list(interactions)[:8]  # Limit to top 8 interactions

    def _extract_integration_points(
        self, requirements: List[Dict[str, Any]]
    ) -> List[str]:
        """Extract integration points from requirements."""
        integrations = set()

        for req in requirements:
            description = req.get("description", "").lower()
            if any(
                keyword in description
                for keyword in ["integrate", "api", "external", "third-party"]
            ):
                # Extract the integration target
                integration_patterns = [
                    r"integrate with ([^.!?]+)",
                    r"([^.!?]*api[^.!?]*)",
                    r"external ([^.!?]+)",
                    r"third[- ]party ([^.!?]+)",
                ]

                for pattern in integration_patterns:
                    matches = re.findall(pattern, description)
                    integrations.update(
                        [match.strip() for match in matches if match.strip()]
                    )

        return list(integrations)[:6]  # Limit to top 6 integrations

    def _extract_external_systems(
        self, requirements: List[Dict[str, Any]]
    ) -> List[str]:
        """Extract external systems from requirements."""
        systems = set()

        # Common external system patterns
        system_patterns = [
            r"\b(database|db|storage)\b",
            r"\b(email|smtp|mail)\b",
            r"\b(payment|stripe|paypal)\b",
            r"\b(auth|authentication|oauth)\b",
            r"\b(cache|redis|memcached)\b",
            r"\b(queue|messaging|kafka)\b",
            r"\b(search|elasticsearch|solr)\b",
            r"\b(cdn|cloudfront|s3)\b",
        ]

        for req in requirements:
            description = req.get("description", "").lower()
            for pattern in system_patterns:
                matches = re.findall(pattern, description)
                systems.update(matches)

        return list(systems)[:8]  # Limit to top 8 systems

    def _identify_core_domains(
        self, project_plan: Dict[str, Any], analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Identify core business domains for module organization.

        Args:
            project_plan: Project plan data
            analysis: Design analysis data

        Returns:
            List of domain definitions
        """
        domains = []

        # Core domain based on project type
        project_type = analysis["project_type"]

        if project_type in ["web_application", "web_api"]:
            domains.extend(
                [
                    {
                        "name": "authentication",
                        "description": "User authentication and authorization",
                        "entities": ["user", "account", "profile"],
                        "responsibilities": [
                            "login",
                            "signup",
                            "permissions",
                            "sessions",
                        ],
                    },
                    {
                        "name": "core_business",
                        "description": "Core business logic and domain models",
                        "entities": analysis["data_entities"][:5],
                        "responsibilities": analysis["user_interactions"][:5],
                    },
                    {
                        "name": "api",
                        "description": "API endpoints and request handling",
                        "entities": ["request", "response", "endpoint"],
                        "responsibilities": ["routing", "validation", "serialization"],
                    },
                ]
            )

        elif project_type == "cli_tool":
            domains.extend(
                [
                    {
                        "name": "command_processing",
                        "description": "Command line interface and argument processing",
                        "entities": ["command", "argument", "option"],
                        "responsibilities": ["parsing", "validation", "help"],
                    },
                    {
                        "name": "core_logic",
                        "description": "Core tool functionality",
                        "entities": analysis["data_entities"][:3],
                        "responsibilities": analysis["user_interactions"][:3],
                    },
                ]
            )

        elif project_type == "mobile_application":
            domains.extend(
                [
                    {
                        "name": "ui",
                        "description": "User interface components and screens",
                        "entities": ["screen", "component", "navigation"],
                        "responsibilities": ["rendering", "user_input", "navigation"],
                    },
                    {
                        "name": "data",
                        "description": "Data management and persistence",
                        "entities": analysis["data_entities"][:4],
                        "responsibilities": ["storage", "synchronization", "caching"],
                    },
                ]
            )

        # Add common domains based on requirements
        if analysis["integration_points"]:
            domains.append(
                {
                    "name": "integration",
                    "description": "External system integrations",
                    "entities": ["client", "adapter", "connector"],
                    "responsibilities": analysis["integration_points"][:4],
                }
            )

        if analysis["external_systems"]:
            domains.append(
                {
                    "name": "infrastructure",
                    "description": "Infrastructure and external services",
                    "entities": analysis["external_systems"][:4],
                    "responsibilities": ["configuration", "monitoring", "logging"],
                }
            )

        # Add shared/common domain
        domains.append(
            {
                "name": "shared",
                "description": "Shared utilities and common functionality",
                "entities": ["utility", "helper", "constant"],
                "responsibilities": ["validation", "formatting", "error_handling"],
            }
        )

        return domains

    def _create_modules(
        self,
        domains: List[Dict[str, Any]],
        project_plan: Dict[str, Any],
        analysis: Dict[str, Any],
    ) -> List[Module]:
        """
        Create module definitions based on identified domains.

        Args:
            domains: List of domain definitions
            project_plan: Project plan data
            analysis: Design analysis data

        Returns:
            List of Module objects
        """
        modules = []

        for domain in domains:
            # Create main module for the domain
            module_name = f"{domain['name']}_module"

            # Determine module complexity
            complexity = self._calculate_module_complexity(domain, analysis)

            # Create public interface methods
            public_interface = self._generate_public_interface(domain, analysis)

            # Determine dependencies
            dependencies = self._determine_module_dependencies(domain, domains)

            # Determine file path
            file_path = self._generate_file_path(domain, project_plan)

            module = Module(
                name=module_name,
                purpose=domain["description"],
                public_interface=public_interface,
                dependencies=dependencies,
                estimated_complexity=complexity,
                file_path=file_path,
            )

            modules.append(module)

        return modules

    def _calculate_module_complexity(
        self, domain: Dict[str, Any], analysis: Dict[str, Any]
    ) -> int:
        """Calculate complexity score for a module."""
        base_complexity = 3

        # Add complexity based on entities
        entity_count = len(domain.get("entities", []))
        base_complexity += min(3, entity_count // 2)

        # Add complexity based on responsibilities
        responsibility_count = len(domain.get("responsibilities", []))
        base_complexity += min(2, responsibility_count // 3)

        # Adjust based on domain type
        domain_name = domain["name"]
        if domain_name in ["authentication", "integration"]:
            base_complexity += 2  # These are typically more complex
        elif domain_name in ["shared", "infrastructure"]:
            base_complexity += 1  # Moderate complexity

        return min(10, max(1, base_complexity))

    def _generate_public_interface(
        self, domain: Dict[str, Any], analysis: Dict[str, Any]
    ) -> List[str]:
        """Generate public interface methods for a module."""
        interface_methods = []

        domain_name = domain["name"]
        responsibilities = domain.get("responsibilities", [])

        # Generate CRUD operations for data-centric domains
        if domain_name in ["core_business", "data"]:
            entities = domain.get("entities", [])
            for entity in entities[:3]:  # Limit to top 3 entities
                interface_methods.extend(
                    [
                        f"create_{entity}(data: dict) -> {entity.title()}",
                        f"get_{entity}(id: str) -> Optional[{entity.title()}]",
                        f"update_{entity}(id: str, data: dict) -> {entity.title()}",
                        f"delete_{entity}(id: str) -> bool",
                    ]
                )

        # Generate specific methods based on responsibilities
        for responsibility in responsibilities[:4]:  # Limit to top 4
            method_name = responsibility.replace(" ", "_").lower()
            interface_methods.append(f"{method_name}() -> Any")

        # Add common interface methods based on domain type
        if domain_name == "authentication":
            interface_methods.extend(
                [
                    "authenticate(credentials: dict) -> AuthResult",
                    "authorize(user: User, resource: str) -> bool",
                    "logout(session_id: str) -> bool",
                ]
            )
        elif domain_name == "api":
            interface_methods.extend(
                [
                    "handle_request(request: Request) -> Response",
                    "validate_input(data: dict) -> ValidationResult",
                    "serialize_response(data: Any) -> dict",
                ]
            )
        elif domain_name == "integration":
            interface_methods.extend(
                [
                    "connect() -> bool",
                    "send_data(data: dict) -> Result",
                    "receive_data() -> dict",
                ]
            )

        return interface_methods[:8]  # Limit to 8 methods per module

    def _determine_module_dependencies(
        self, domain: Dict[str, Any], all_domains: List[Dict[str, Any]]
    ) -> List[str]:
        """Determine dependencies for a module."""
        dependencies = []
        domain_name = domain["name"]

        # Common dependency patterns
        if domain_name != "shared":
            dependencies.append(
                "shared_module"
            )  # Most modules depend on shared utilities

        if domain_name == "api":
            dependencies.extend(["authentication_module", "core_business_module"])
        elif domain_name == "core_business":
            if any(d["name"] == "authentication" for d in all_domains):
                dependencies.append("authentication_module")
        elif domain_name == "integration":
            dependencies.append("core_business_module")
        elif domain_name == "ui":
            dependencies.extend(["authentication_module", "data_module"])

        return dependencies

    def _generate_file_path(
        self, domain: Dict[str, Any], project_plan: Dict[str, Any]
    ) -> str:
        """Generate file path for a module."""
        domain_name = domain["name"]
        project_type = project_plan.get("project_type", "general_application")

        # Base path structure
        if project_type in ["web_application", "web_api"]:
            base_path = "src"
        elif project_type == "cli_tool":
            base_path = "cli"
        elif project_type == "mobile_application":
            base_path = "app"
        else:
            base_path = "src"

        # Module-specific paths
        if domain_name == "authentication":
            return f"{base_path}/auth/auth_module.py"
        elif domain_name == "core_business":
            return f"{base_path}/core/business_module.py"
        elif domain_name == "api":
            return f"{base_path}/api/api_module.py"
        elif domain_name == "ui":
            return f"{base_path}/ui/ui_module.py"
        elif domain_name == "data":
            return f"{base_path}/data/data_module.py"
        elif domain_name == "integration":
            return f"{base_path}/integrations/integration_module.py"
        elif domain_name == "infrastructure":
            return f"{base_path}/infrastructure/infra_module.py"
        elif domain_name == "shared":
            return f"{base_path}/shared/shared_module.py"
        else:
            return f"{base_path}/{domain_name}/{domain_name}_module.py"

    def _design_module_interfaces(
        self, modules: List[Module], project_plan: Dict[str, Any]
    ) -> List[Interface]:
        """Design interfaces for module communication."""
        interfaces = []

        for module in modules:
            # Create interface for each module
            interface_name = f"{module.name.replace('_module', '').title()}Interface"

            interface = Interface(
                name=interface_name,
                methods=module.public_interface,
                properties=self._generate_interface_properties(module),
                description=f"Interface for {module.purpose}",
            )

            interfaces.append(interface)

        return interfaces

    def _generate_interface_properties(self, module: Module) -> List[str]:
        """Generate interface properties for a module."""
        properties = []

        module_name = module.name
        if "authentication" in module_name:
            properties.extend(
                ["current_user: Optional[User]", "is_authenticated: bool"]
            )
        elif "core_business" in module_name:
            properties.extend(["data_store: DataStore", "validator: Validator"])
        elif "api" in module_name:
            properties.extend(["router: Router", "middleware: List[Middleware]"])
        elif "shared" in module_name:
            properties.extend(["config: Config", "logger: Logger"])

        return properties

    def _create_dependency_graph(
        self, modules: List[Module], interfaces: List[Interface]
    ) -> Dict[str, List[str]]:
        """Create dependency graph for modules."""
        dependencies = {}

        for module in modules:
            dependencies[module.name] = module.dependencies.copy()

        return dependencies

    def _validate_architecture(
        self, modules: List[Module], dependencies: Dict[str, List[str]]
    ) -> Dict[str, Any]:
        """Validate the architecture design."""
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "circular_dependencies": [],
            "orphaned_modules": [],
            "recommendations": [],
        }

        # Check for circular dependencies
        circular_deps = self._detect_circular_dependencies(dependencies)
        if circular_deps:
            validation_result["is_valid"] = False
            validation_result["circular_dependencies"] = circular_deps
            validation_result["errors"].append(
                f"Circular dependencies detected: {circular_deps}"
            )

        # Check for orphaned modules
        all_modules = set(dependencies.keys())
        referenced_modules = set()
        for deps in dependencies.values():
            referenced_modules.update(deps)

        orphaned = (
            all_modules - referenced_modules - {"shared_module"}
        )  # shared_module is expected to be orphaned
        if orphaned:
            validation_result["orphaned_modules"] = list(orphaned)
            validation_result["warnings"].append(
                f"Orphaned modules found: {list(orphaned)}"
            )

        # Check module count
        module_count = len(modules)
        if module_count > 15:
            validation_result["warnings"].append(
                f"High module count ({module_count}). Consider consolidation."
            )
        elif module_count < 3:
            validation_result["warnings"].append(
                f"Low module count ({module_count}). Consider more separation."
            )

        # Generate recommendations
        if validation_result["is_valid"]:
            validation_result["recommendations"].append(
                "Architecture design follows good practices"
            )

        return validation_result

    def _detect_circular_dependencies(
        self, dependencies: Dict[str, List[str]]
    ) -> List[List[str]]:
        """Detect circular dependencies in the module graph."""

        def has_cycle(
            node: str, visited: Set[str], rec_stack: Set[str], path: List[str]
        ) -> Optional[List[str]]:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in dependencies.get(node, []):
                if neighbor not in visited:
                    cycle = has_cycle(neighbor, visited, rec_stack, path)
                    if cycle:
                        return cycle
                elif neighbor in rec_stack:
                    # Found cycle
                    cycle_start = path.index(neighbor)
                    return path[cycle_start:] + [neighbor]

            rec_stack.remove(node)
            path.pop()
            return None

        visited = set()
        cycles = []

        for node in dependencies:
            if node not in visited:
                cycle = has_cycle(node, visited, set(), [])
                if cycle:
                    cycles.append(cycle)

        return cycles

    def _determine_architecture_pattern(
        self, project_plan: Dict[str, Any], modules: List[Module]
    ) -> str:
        """Determine the most appropriate architecture pattern."""
        project_type = project_plan.get("project_type", "general_application")
        complexity = project_plan.get("complexity_assessment", {}).get(
            "level", "medium"
        )
        module_count = len(modules)

        # Determine pattern based on project characteristics
        if project_type == "web_api":
            if complexity in ["high", "very_high"] and module_count > 8:
                return "Clean Architecture (Hexagonal)"
            else:
                return "Layered Architecture"
        elif project_type == "web_application":
            return "Model-View-Controller (MVC)"
        elif project_type == "cli_tool":
            return "Command Pattern"
        elif project_type == "mobile_application":
            return "Model-View-ViewModel (MVVM)"
        elif project_type == "microservice":
            return "Microservices Architecture"
        elif project_type == "data_processing":
            return "Pipeline Architecture"
        else:
            if module_count > 10:
                return "Modular Monolith"
            else:
                return "Layered Architecture"

    def _generate_design_recommendations(
        self, module_structure: ModuleStructure
    ) -> List[str]:
        """Generate design recommendations based on the module structure."""
        recommendations = []

        module_count = len(module_structure.modules)
        dependency_count = sum(
            len(deps) for deps in module_structure.dependencies.values()
        )

        # Module count recommendations
        if module_count > 12:
            recommendations.append(
                "Consider consolidating modules to reduce complexity"
            )
        elif module_count < 4:
            recommendations.append(
                "Consider splitting large modules for better maintainability"
            )

        # Dependency recommendations
        avg_dependencies = dependency_count / module_count if module_count > 0 else 0
        if avg_dependencies > 3:
            recommendations.append(
                "High coupling detected. Consider reducing inter-module dependencies"
            )

        # Architecture-specific recommendations
        pattern = module_structure.architecture_pattern
        if "Clean Architecture" in pattern:
            recommendations.append("Ensure dependency inversion principle is followed")
            recommendations.append("Keep domain logic independent of external concerns")
        elif "MVC" in pattern:
            recommendations.append(
                "Maintain clear separation between Model, View, and Controller"
            )
        elif "Layered" in pattern:
            recommendations.append(
                "Ensure dependencies flow in one direction (top to bottom)"
            )

        # General recommendations
        recommendations.extend(
            [
                "Implement comprehensive unit tests for each module",
                "Document public interfaces and their contracts",
                "Consider using dependency injection for better testability",
                "Implement proper error handling and logging in each module",
            ]
        )

        return recommendations
