from pydantic import BaseModel, Field

class ComicAnalysis(BaseModel):
    Core_concept: str = Field(description="Briefly identify the technical, scientific, or programming principle")
    Explanation: str = Field(description="Explain the joke, puns, and alt-text clearly for a general audience under 800 chars")