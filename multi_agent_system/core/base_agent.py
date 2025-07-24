"""Base agent class for all multi-agent system agents."""

from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
import logging
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters
from dotenv import load_dotenv
import os

load_dotenv()

GEMINI_MODEL = "gemini-2.5-flash"

logger = logging.getLogger(__name__)


class BaseMultiAgent(LlmAgent, ABC):
    """
    Base class for all agents in the multi-agent system.
    
    Provides standardized interface for agent communication, validation,
    and execution within the coordinated workflow.
    """
    
    def __init__(self, name: str, description: str, instruction: str, tools: Optional[list] = None):
        """
        Initialize the base multi-agent.
        
        Args:
            name: Agent name for identification
            description: Brief description of agent's purpose
            instruction: Detailed instruction for agent behavior
            tools: Optional list of tools, defaults to filesystem MCP toolset
        """
        if tools is None:
            tools = [
                MCPToolset(
                    connection_params=StdioServerParameters(
                        command='npx',
                        args=[
                            "-y",
                            "@modelcontextprotocol/server-filesystem",
                            "/",  # Root access for file operations
                        ],
                    ),
                )
            ]
        
        super().__init__(
            model=GEMINI_MODEL,
            name=name,
            description=description,
            instruction=instruction,
            tools=tools
        )
        
        # Store agent name and logger separately since LlmAgent is a Pydantic model
        self._agent_name = name
        self._logger = logging.getLogger(f"{__name__}.{name}")
    
    @abstractmethod
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the agent's main functionality.
        
        Args:
            input_data: Input data from previous agent or user
            
        Returns:
            Dict containing the agent's output data
            
        Raises:
            ValidationError: If input data is invalid
            AgentExecutionError: If execution fails
        """
        pass
    
    @abstractmethod
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate input data structure and content.
        
        Args:
            input_data: Data to validate
            
        Returns:
            True if input is valid, False otherwise
        """
        pass
    
    @abstractmethod
    def format_output(self, result: Any) -> Dict[str, Any]:
        """
        Format execution result for next agent in pipeline.
        
        Args:
            result: Raw execution result
            
        Returns:
            Formatted output dictionary
        """
        pass
    
    @property
    def agent_name(self) -> str:
        """Get the agent name."""
        return self._agent_name
    
    @property
    def logger(self):
        """Get the logger instance."""
        return self._logger
    
    def get_agent_info(self) -> Dict[str, str]:
        """
        Get basic information about this agent.
        
        Returns:
            Dictionary with agent name, description, and type
        """
        return {
            "name": self.agent_name,
            "description": self.description,
            "type": self.__class__.__name__
        }
    
    def log_execution_start(self, input_data: Dict[str, Any]) -> None:
        """Log the start of agent execution."""
        self.logger.info(f"Starting execution for agent {self.agent_name}")
        self.logger.debug(f"Input data keys: {list(input_data.keys())}")
    
    def log_execution_end(self, output_data: Dict[str, Any]) -> None:
        """Log the end of agent execution."""
        self.logger.info(f"Completed execution for agent {self.agent_name}")
        self.logger.debug(f"Output data keys: {list(output_data.keys())}")
    
    def log_error(self, error: Exception, context: str = "") -> None:
        """Log an error during agent execution."""
        self.logger.error(f"Error in agent {self.agent_name}: {error}")
        if context:
            self.logger.error(f"Context: {context}")


class AgentExecutionError(Exception):
    """Exception raised when agent execution fails."""
    
    def __init__(self, agent_name: str, message: str, original_error: Optional[Exception] = None):
        self.agent_name = agent_name
        self.original_error = original_error
        super().__init__(f"Agent {agent_name} execution failed: {message}")


class ValidationError(Exception):
    """Exception raised when input validation fails."""
    
    def __init__(self, agent_name: str, field: str, message: str):
        self.agent_name = agent_name
        self.field = field
        super().__init__(f"Validation error in agent {agent_name} for field {field}: {message}")