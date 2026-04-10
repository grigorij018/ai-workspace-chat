from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class RouterDecision(BaseModel):
    task_type: str
    selected_model: str
    selected_tool: str
    manual_override: bool = False
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    short_reason: str


class ToolResult(BaseModel):
    tool_name: str
    status: str
    content: Optional[str] = None
    files: list[dict] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


class MemoryRecord(BaseModel):
    id: str
    user_id: str
    kind: str
    content: str
    source: Optional[str] = None
    enabled: bool = True
    created_at: int
    updated_at: int

    model_config = ConfigDict(from_attributes=True)


class MemoryPreference(BaseModel):
    enabled: bool = True
    auto_store: bool = True


class ChatRequest(BaseModel):
    model: str
    messages: list[dict]
    files: list[dict] = Field(default_factory=list)
    features: dict = Field(default_factory=dict)
    metadata: dict = Field(default_factory=dict)


class ChatResponse(BaseModel):
    id: Optional[str] = None
    object: Optional[str] = None
    model: Optional[str] = None
    choices: list[dict] = Field(default_factory=list)
    router_decision: Optional[RouterDecision] = None
