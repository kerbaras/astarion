"""Base agent class for all Astarion agents."""

from abc import ABC
from typing import Any, Dict, Optional

from loguru import logger
from pydantic import BaseModel, Field


class AgentMetadata(BaseModel):
    """Metadata for an agent."""
    name: str = Field(description="Agent name")
    description: str = Field(description="Agent description")
    version: str = Field(default="1.0.0", description="Agent version")
    capabilities: list[str] = Field(default_factory=list, description="Agent capabilities")


class BaseAgent(ABC):
    """Base class for all agents in the Astarion system."""
    
    def __init__(self, name: str, description: str):
        """Initialize the base agent.
        
        Args:
            name: Agent name
            description: Agent description
        """
        self.metadata = AgentMetadata(
            name=name,
            description=description
        )
        logger.info(f"Initialized {name} agent")
        
    def get_metadata(self) -> AgentMetadata:
        """Get agent metadata."""
        return self.metadata
        
    def add_capability(self, capability: str):
        """Add a capability to the agent."""
        if capability not in self.metadata.capabilities:
            self.metadata.capabilities.append(capability)
            
    async def process(self, **kwargs) -> Any:
        """Process a request. To be implemented by subclasses."""
        raise NotImplementedError(
            f"{self.metadata.name} must implement process method"
        ) 