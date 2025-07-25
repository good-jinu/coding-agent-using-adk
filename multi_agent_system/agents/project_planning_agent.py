"""Project Planning Agent implementation."""

from typing import Dict, Any, List
import logging
import re
from datetime import datetime

from ..core.base_agent import BaseMultiAgent, AgentExecutionError, ValidationError
from ..core.models import ProjectPlan, ProjectRequirement, TechnologyStack

logger = logging.getLogger(__name__)


class ProjectPlanningAgent(BaseMultiAgent):
    """
    Agent responsible for analyzing user project descriptions and creating
    structured project plans with requirements, scope, and architecture recommendations.
    """

    def __init__(self):
        """Initialize the Project Planning Agent."""
        super().__init__(
            name="ProjectPlanningAgent",
            description="Analyzes project descriptions and creates comprehensive project plans",
            instruction="""
You are an expert software architect and project manager. Your role is to analyze user project descriptions and create comprehensive, structured project plans.

**Your Responsibilities:**

1. **Requirement Analysis**: Extract and categorize functional and non-functional requirements
2. **Scope Definition**: Define clear project boundaries and deliverables
3. **Technology Recommendations**: Suggest appropriate technology stack based on requirements
4. **Complexity Assessment**: Estimate project complexity and development effort
5. **Architecture Planning**: Recommend high-level architecture patterns

**Analysis Process:**

1. **Parse Project Description**: Extract key information about the project's purpose, features, and constraints
2. **Identify Requirements**: Categorize requirements into functional, non-functional, and technical
3. **Assess Complexity**: Evaluate project complexity based on features, integrations, and technical challenges
4. **Recommend Technology**: Suggest programming languages, frameworks, and tools
5. **Define Scope**: Clearly outline what will and won't be included in the project

**Output Format:**
Create a structured project plan that includes:
- Project overview and objectives
- Detailed requirements list (functional and non-functional)
- Recommended technology stack with justifications
- High-level architecture approach
- Complexity assessment and effort estimation
- Project scope and boundaries
- Key assumptions and constraints

**Key Principles:**
- Be thorough but practical in requirement extraction
- Consider scalability, maintainability, and performance
- Recommend proven technologies appropriate for the project size
- Clearly communicate assumptions and limitations
- Focus on delivering value to the end user

Always provide clear, actionable project plans that serve as a solid foundation for the development process.
            """,
        )

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute project planning based on user description.

        Args:
            input_data: Dictionary containing project description and optional parameters

        Returns:
            Dictionary containing structured project plan
        """
        try:
            self.log_execution_start(input_data)

            # Extract project description
            description = input_data.get("description", "")
            if not description:
                raise ValidationError(
                    self.agent_name, "description", "Project description is required"
                )

            # Analyze the project description
            analysis_result = self._analyze_project_description(description)

            # Extract requirements
            requirements = self._extract_requirements(description, analysis_result)

            # Assess complexity
            complexity_assessment = self._assess_complexity(
                requirements, analysis_result
            )

            # Recommend technology stack
            tech_stack = self._recommend_technology_stack(
                requirements, complexity_assessment
            )

            # Define project scope
            scope_definition = self._define_project_scope(requirements, analysis_result)

            # Create structured project plan
            project_plan = self._create_project_plan(
                description=description,
                analysis=analysis_result,
                requirements=requirements,
                complexity=complexity_assessment,
                tech_stack=tech_stack,
                scope=scope_definition,
            )

            # Generate detailed planning output
            output = {
                "project_plan": project_plan.model_dump(),
                "analysis_summary": analysis_result,
                "complexity_assessment": complexity_assessment,
                "technology_recommendations": tech_stack.model_dump(),
                "scope_definition": scope_definition,
                "planning_metadata": {
                    "agent_name": self.agent_name,
                    "timestamp": datetime.now().isoformat(),
                    "version": "1.0",
                },
            }

            self.log_execution_end(output)
            return output

        except Exception as e:
            self.log_error(e, "Project planning execution failed")
            raise AgentExecutionError(self.agent_name, str(e), e)

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate input data for project planning.

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

            # Check for required description field
            description = input_data.get("description")
            if not description or not isinstance(description, str):
                self.logger.error(
                    "Project description is required and must be a string"
                )
                return False

            # Check minimum description length
            if len(description.strip()) < 20:
                self.logger.error(
                    "Project description must be at least 20 characters long"
                )
                return False

            # Validate optional parameters
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
        Format the project planning result for next agent.

        Args:
            result: Raw execution result

        Returns:
            Formatted output dictionary
        """
        if isinstance(result, dict):
            return result

        # If result is not a dict, wrap it
        return {
            "project_plan": result,
            "agent": self.agent_name,
            "timestamp": datetime.now().isoformat(),
        }

    def _analyze_project_description(self, description: str) -> Dict[str, Any]:
        """
        Analyze the project description to extract key information.

        Args:
            description: User project description

        Returns:
            Dictionary containing analysis results
        """
        analysis = {
            "project_type": self._identify_project_type(description),
            "key_features": self._extract_key_features(description),
            "target_users": self._identify_target_users(description),
            "technical_constraints": self._identify_technical_constraints(description),
            "integration_requirements": self._identify_integrations(description),
            "performance_requirements": self._identify_performance_requirements(
                description
            ),
        }

        return analysis

    def _identify_project_type(self, description: str) -> str:
        """Identify the type of project based on description."""
        description_lower = description.lower()

        # Web application indicators
        if any(
            keyword in description_lower
            for keyword in [
                "web app",
                "website",
                "web application",
                "frontend",
                "backend",
                "api",
                "rest",
                "graphql",
            ]
        ):
            if any(
                keyword in description_lower
                for keyword in ["api", "rest", "graphql", "backend", "server"]
            ):
                return "web_api"
            elif any(
                keyword in description_lower
                for keyword in [
                    "frontend",
                    "ui",
                    "user interface",
                    "react",
                    "vue",
                    "angular",
                ]
            ):
                return "web_frontend"
            else:
                return "web_application"

        # Mobile application indicators
        elif any(
            keyword in description_lower
            for keyword in ["mobile app", "ios", "android", "react native", "flutter"]
        ):
            return "mobile_application"

        # Desktop application indicators
        elif any(
            keyword in description_lower
            for keyword in ["desktop", "gui", "tkinter", "qt", "electron"]
        ):
            return "desktop_application"

        # CLI tool indicators
        elif any(
            keyword in description_lower
            for keyword in ["command line", "cli", "terminal", "script", "automation"]
        ):
            return "cli_tool"

        # Library/SDK indicators
        elif any(
            keyword in description_lower
            for keyword in ["library", "sdk", "package", "module", "framework"]
        ):
            return "library"

        # Data processing indicators
        elif any(
            keyword in description_lower
            for keyword in [
                "data processing",
                "etl",
                "pipeline",
                "analytics",
                "machine learning",
                "ai",
            ]
        ):
            return "data_processing"

        # Microservice indicators
        elif any(
            keyword in description_lower
            for keyword in ["microservice", "service", "distributed", "containerized"]
        ):
            return "microservice"

        else:
            return "general_application"

    def _extract_key_features(self, description: str) -> List[str]:
        """Extract key features from the project description."""
        features = []

        # Common feature patterns
        feature_patterns = [
            r"user(?:s)? can ([^.!?]+)",
            r"should (?:be able to )?([^.!?]+)",
            r"will (?:be able to )?([^.!?]+)",
            r"feature(?:s)? (?:include|includes) ([^.!?]+)",
            r"functionality (?:include|includes) ([^.!?]+)",
            r"(?:need|needs) to ([^.!?]+)",
            r"(?:want|wants) to ([^.!?]+)",
            r"(?:require|requires) ([^.!?]+)",
        ]

        for pattern in feature_patterns:
            matches = re.findall(pattern, description, re.IGNORECASE)
            features.extend([match.strip() for match in matches])

        # Remove duplicates and clean up
        unique_features = []
        for feature in features:
            if feature and len(feature) > 5 and feature not in unique_features:
                unique_features.append(feature)

        return unique_features[:10]  # Limit to top 10 features

    def _identify_target_users(self, description: str) -> List[str]:
        """Identify target users from the project description."""
        users = []

        # Common user patterns
        user_patterns = [
            r"(?:for|target) ([^.!?]*(?:user|customer|client|admin|developer|manager)[^.!?]*)",
            r"([^.!?]*(?:user|customer|client|admin|developer|manager)[^.!?]*) (?:can|will|should)",
            r"designed for ([^.!?]+)",
            r"intended for ([^.!?]+)",
        ]

        for pattern in user_patterns:
            matches = re.findall(pattern, description, re.IGNORECASE)
            users.extend([match.strip() for match in matches])

        # Default users if none found
        if not users:
            project_type = self._identify_project_type(description)
            if project_type in ["web_application", "web_frontend"]:
                users = ["end users", "web users"]
            elif project_type == "web_api":
                users = ["client applications", "developers"]
            elif project_type == "mobile_application":
                users = ["mobile users"]
            elif project_type == "cli_tool":
                users = ["developers", "system administrators"]
            else:
                users = ["end users"]

        return users[:5]  # Limit to top 5 user types

    def _identify_technical_constraints(self, description: str) -> List[str]:
        """Identify technical constraints from the description."""
        constraints = []

        # Look for specific technology mentions
        tech_mentions = re.findall(
            r"(?:using|with|built on|based on) ([^.!?]+)", description, re.IGNORECASE
        )
        constraints.extend([f"Must use {tech.strip()}" for tech in tech_mentions])

        # Look for performance constraints
        perf_patterns = [
            r"(?:fast|quick|real-time|low latency)",
            r"(?:scalable|high performance|high throughput)",
            r"(?:secure|security|authentication|authorization)",
        ]

        for pattern in perf_patterns:
            if re.search(pattern, description, re.IGNORECASE):
                constraints.append(f"Performance requirement: {pattern}")

        return constraints

    def _identify_integrations(self, description: str) -> List[str]:
        """Identify required integrations from the description."""
        integrations = []

        # Common integration patterns
        integration_patterns = [
            r"integrat(?:e|ion) with ([^.!?]+)",
            r"connect(?:s|ion) to ([^.!?]+)",
            r"(?:use|uses) ([^.!?]*(?:api|database|service|system)[^.!?]*)",
            r"(?:third[- ]party|external) ([^.!?]+)",
        ]

        for pattern in integration_patterns:
            matches = re.findall(pattern, description, re.IGNORECASE)
            integrations.extend([match.strip() for match in matches])

        return integrations[:8]  # Limit to top 8 integrations

    def _identify_performance_requirements(self, description: str) -> Dict[str, Any]:
        """Identify performance requirements from the description."""
        requirements = {
            "response_time": None,
            "throughput": None,
            "scalability": None,
            "availability": None,
        }

        # Look for specific performance metrics
        if re.search(r"real[- ]time|instant|immediate", description, re.IGNORECASE):
            requirements["response_time"] = "real-time"
        elif re.search(r"fast|quick|responsive", description, re.IGNORECASE):
            requirements["response_time"] = "fast"

        if re.search(r"high[- ]volume|many users|scalable", description, re.IGNORECASE):
            requirements["scalability"] = "high"

        if re.search(
            r"24/7|always available|high availability", description, re.IGNORECASE
        ):
            requirements["availability"] = "high"

        return {k: v for k, v in requirements.items() if v is not None}

    def _extract_requirements(
        self, description: str, analysis: Dict[str, Any]
    ) -> List[ProjectRequirement]:
        """Extract and categorize requirements from the analysis."""
        requirements = []

        # Functional requirements from key features
        for i, feature in enumerate(analysis["key_features"], 1):
            requirements.append(
                ProjectRequirement(
                    id=f"FR{i:03d}",
                    type="functional",
                    description=feature,
                    priority="high" if i <= 3 else "medium",
                    category="core_functionality",
                )
            )

        # Non-functional requirements
        nfr_id = 1

        # Performance requirements
        for perf_type, value in analysis["performance_requirements"].items():
            requirements.append(
                ProjectRequirement(
                    id=f"NFR{nfr_id:03d}",
                    type="non_functional",
                    description=f"System must provide {value} {perf_type.replace('_', ' ')}",
                    priority="high",
                    category="performance",
                )
            )
            nfr_id += 1

        # Integration requirements
        for integration in analysis["integration_requirements"]:
            requirements.append(
                ProjectRequirement(
                    id=f"NFR{nfr_id:03d}",
                    type="non_functional",
                    description=f"System must integrate with {integration}",
                    priority="medium",
                    category="integration",
                )
            )
            nfr_id += 1

        # Technical constraints as requirements
        for constraint in analysis["technical_constraints"]:
            requirements.append(
                ProjectRequirement(
                    id=f"NFR{nfr_id:03d}",
                    type="non_functional",
                    description=constraint,
                    priority="high",
                    category="technical_constraint",
                )
            )
            nfr_id += 1

        return requirements

    def _assess_complexity(
        self, requirements: List[ProjectRequirement], analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess project complexity based on requirements and analysis."""

        # Base complexity factors
        feature_count = len(analysis["key_features"])
        integration_count = len(analysis["integration_requirements"])
        constraint_count = len(analysis["technical_constraints"])

        # Calculate complexity score (1-10)
        complexity_score = min(
            10,
            max(
                1,
                (feature_count * 0.5)
                + (integration_count * 0.8)
                + (constraint_count * 0.3)
                + (2 if analysis["performance_requirements"] else 0),
            ),
        )

        # Determine complexity level
        if complexity_score <= 3:
            complexity_level = "low"
        elif complexity_score <= 6:
            complexity_level = "medium"
        elif complexity_score <= 8:
            complexity_level = "high"
        else:
            complexity_level = "very_high"

        # Estimate effort (in person-days)
        base_effort = {"low": 5, "medium": 15, "high": 30, "very_high": 60}

        effort_estimate = base_effort[complexity_level]

        # Adjust based on project type
        project_type = analysis["project_type"]
        type_multipliers = {
            "cli_tool": 0.7,
            "library": 0.8,
            "web_frontend": 1.0,
            "web_api": 1.2,
            "web_application": 1.5,
            "mobile_application": 1.3,
            "desktop_application": 1.4,
            "microservice": 1.6,
            "data_processing": 1.8,
        }

        effort_estimate *= type_multipliers.get(project_type, 1.0)

        return {
            "score": complexity_score,
            "level": complexity_level,
            "effort_estimate_days": int(effort_estimate),
            "factors": {
                "feature_count": feature_count,
                "integration_count": integration_count,
                "constraint_count": constraint_count,
                "has_performance_requirements": bool(
                    analysis["performance_requirements"]
                ),
            },
        }

    def _recommend_technology_stack(
        self, requirements: List[ProjectRequirement], complexity: Dict[str, Any]
    ) -> TechnologyStack:
        """Recommend appropriate technology stack based on requirements and complexity."""

        # Analyze requirements for technology hints
        tech_hints = []
        for req in requirements:
            if "api" in req.description.lower():
                tech_hints.append("api")
            if "database" in req.description.lower():
                tech_hints.append("database")
            if "web" in req.description.lower():
                tech_hints.append("web")
            if "mobile" in req.description.lower():
                tech_hints.append("mobile")

        # Base recommendations by project type (this would be extracted from analysis)
        project_type = "web_application"  # Default, should come from analysis

        # Language recommendations
        language_recommendations = {
            "web_application": ["Python", "JavaScript", "TypeScript"],
            "web_api": ["Python", "Node.js", "Go"],
            "web_frontend": ["JavaScript", "TypeScript"],
            "mobile_application": ["React Native", "Flutter", "Swift/Kotlin"],
            "cli_tool": ["Python", "Go", "Rust"],
            "library": ["Python", "JavaScript", "Go"],
            "data_processing": ["Python", "Scala", "Java"],
            "microservice": ["Go", "Python", "Java"],
        }

        primary_language = language_recommendations.get(project_type, ["Python"])[0]

        # Framework recommendations
        framework_recommendations = {
            "Python": ["FastAPI", "Django", "Flask"],
            "JavaScript": ["Express.js", "Next.js", "React"],
            "TypeScript": ["Express.js", "Next.js", "NestJS"],
            "Go": ["Gin", "Echo", "Fiber"],
            "Java": ["Spring Boot", "Quarkus"],
        }

        frameworks = framework_recommendations.get(primary_language, [])

        # Database recommendations based on complexity and requirements
        if complexity["level"] in ["low", "medium"]:
            databases = ["SQLite", "PostgreSQL"]
        else:
            databases = ["PostgreSQL", "MongoDB", "Redis"]

        # Tool recommendations
        tools = ["Git", "Docker"]
        if complexity["level"] in ["high", "very_high"]:
            tools.extend(["Kubernetes", "CI/CD Pipeline"])

        return TechnologyStack(
            primary_language=primary_language,
            frameworks=frameworks[:2],  # Top 2 framework recommendations
            databases=databases[:2],  # Top 2 database recommendations
            tools=tools,
            justification=f"Recommended for {project_type} with {complexity['level']} complexity",
        )

    def _define_project_scope(
        self, requirements: List[ProjectRequirement], analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Define project scope based on requirements and analysis."""

        # Categorize requirements by priority
        high_priority = [req for req in requirements if req.priority == "high"]
        medium_priority = [req for req in requirements if req.priority == "medium"]
        low_priority = [req for req in requirements if req.priority == "low"]

        scope = {
            "in_scope": {
                "core_features": [
                    req.description for req in high_priority if req.type == "functional"
                ],
                "essential_integrations": [
                    req.description
                    for req in high_priority
                    if req.category == "integration"
                ],
                "performance_requirements": [
                    req.description
                    for req in high_priority
                    if req.category == "performance"
                ],
            },
            "nice_to_have": {
                "additional_features": [
                    req.description
                    for req in medium_priority
                    if req.type == "functional"
                ],
                "optional_integrations": [
                    req.description
                    for req in medium_priority
                    if req.category == "integration"
                ],
            },
            "out_of_scope": {
                "future_enhancements": [req.description for req in low_priority],
                "excluded_features": [],  # Would be populated based on constraints
            },
            "assumptions": [
                "Development will follow agile methodology",
                "Code will include comprehensive testing",
                "Documentation will be provided for all public APIs",
                "Security best practices will be implemented",
            ],
            "constraints": analysis["technical_constraints"],
        }

        return scope

    def _create_project_plan(
        self,
        description: str,
        analysis: Dict[str, Any],
        requirements: List[ProjectRequirement],
        complexity: Dict[str, Any],
        tech_stack: TechnologyStack,
        scope: Dict[str, Any],
    ) -> ProjectPlan:
        """Create the final structured project plan."""

        return ProjectPlan(
            project_name=self._extract_project_name(description),
            description=description,
            project_type=analysis["project_type"],
            target_users=analysis["target_users"],
            requirements=requirements,
            technology_stack=tech_stack,
            complexity_assessment=complexity,
            scope_definition=scope,
            estimated_timeline_days=complexity["effort_estimate_days"],
            key_assumptions=scope["assumptions"],
            success_criteria=self._define_success_criteria(requirements),
            risks_and_mitigation=self._identify_risks(complexity, analysis),
        )

    def _extract_project_name(self, description: str) -> str:
        """Extract or generate a project name from the description."""
        # Look for explicit project name mentions
        name_patterns = [
            r"project (?:called|named) ([^.!?]+)",
            r"(?:build|create|develop) (?:a|an) ([^.!?]+)",
            r"([^.!?]+) (?:application|app|system|tool|service)",
        ]

        for pattern in name_patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                if len(name) < 50:  # Reasonable name length
                    return name.title()

        # Generate name based on project type and key features
        project_type = self._identify_project_type(description)
        type_names = {
            "web_application": "Web Application",
            "web_api": "API Service",
            "web_frontend": "Frontend Application",
            "mobile_application": "Mobile App",
            "cli_tool": "CLI Tool",
            "library": "Library",
            "data_processing": "Data Processing System",
            "microservice": "Microservice",
        }

        return type_names.get(project_type, "Software Project")

    def _define_success_criteria(
        self, requirements: List[ProjectRequirement]
    ) -> List[str]:
        """Define success criteria based on requirements."""
        criteria = []

        # Functional success criteria
        functional_reqs = [
            req
            for req in requirements
            if req.type == "functional" and req.priority == "high"
        ]
        if functional_reqs:
            criteria.append(
                f"All {len(functional_reqs)} core functional requirements are implemented and tested"
            )

        # Performance success criteria
        perf_reqs = [req for req in requirements if req.category == "performance"]
        if perf_reqs:
            criteria.append("All performance requirements are met and validated")

        # Quality criteria
        criteria.extend(
            [
                "Code coverage is at least 80%",
                "All tests pass successfully",
                "Code follows established style guidelines",
                "Documentation is complete and accurate",
            ]
        )

        return criteria

    def _identify_risks(
        self, complexity: Dict[str, Any], analysis: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Identify project risks and mitigation strategies."""
        risks = []

        # Complexity-based risks
        if complexity["level"] in ["high", "very_high"]:
            risks.append(
                {
                    "risk": "High complexity may lead to scope creep and timeline overruns",
                    "mitigation": "Break down into smaller, manageable phases with regular reviews",
                }
            )

        # Integration risks
        if len(analysis["integration_requirements"]) > 3:
            risks.append(
                {
                    "risk": "Multiple integrations may cause dependency and compatibility issues",
                    "mitigation": "Implement integration points early and test thoroughly",
                }
            )

        # Performance risks
        if analysis["performance_requirements"]:
            risks.append(
                {
                    "risk": "Performance requirements may be challenging to meet",
                    "mitigation": "Implement performance testing early and optimize iteratively",
                }
            )

        # General risks
        risks.extend(
            [
                {
                    "risk": "Requirements may change during development",
                    "mitigation": "Use agile methodology with regular stakeholder feedback",
                },
                {
                    "risk": "Technical challenges may arise during implementation",
                    "mitigation": "Conduct proof-of-concept for complex features early",
                },
            ]
        )

        return risks
