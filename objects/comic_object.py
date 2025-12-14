from pydantic import BaseModel, Field
from dataclasses import dataclass


@dataclass
class ComicData:
    title: str
    description: str
    image_url: str
    source_url: str
    source_name: str


class ComicAnalysis(BaseModel):
    Core_concept: str = Field(
        description="Briefly identify the technical, scientific, or programming principle"
    )
    Explanation: str = Field(
        description="Explain the joke, puns, and alt-text clearly for a general audience under 950 chars"
    )
