from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class QlooLocation(BaseModel):
    model_config = ConfigDict(extra="allow")
    lat: float | None = None
    lon: float | None = None
    geohash: str | None = None


class QlooTag(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)
    id: str | None = None
    tag_id: str | None = None
    name: str = ""
    type: str | None = None
    value: str | None = None

    @model_validator(mode="after")
    def _normalise_id(self) -> QlooTag:
        if not self.id:
            self.id = self.tag_id
        return self

    @property
    def tag_key(self) -> str:
        return self.id or self.value or self.name


class QlooEntityQuery(BaseModel):
    model_config = ConfigDict(extra="allow")
    affinity: float | None = None
    distance: float | None = None
    explainability: dict[str, Any] | None = None


class QlooEntity(BaseModel):
    model_config = ConfigDict(extra="allow")
    name: str
    entity_id: str
    type: str | None = None
    subtype: str | None = None
    types: list[str] = Field(default_factory=list)
    properties: dict[str, Any] = Field(default_factory=dict)
    popularity: float | None = None
    location: QlooLocation | None = None
    tags: list[QlooTag] = Field(default_factory=list)
    query: QlooEntityQuery = Field(default_factory=QlooEntityQuery)
    disambiguation: str | None = None

    @property
    def entity_types(self) -> list[str]:
        values = list(self.types)
        if self.subtype:
            values.append(self.subtype)
        return values

    @property
    def tag_ids(self) -> list[str]:
        return [tag.tag_key for tag in self.tags if tag.tag_key]


class QlooWarning(BaseModel):
    model_config = ConfigDict(extra="allow")
    type: str = "warning"
    message: str | None = None


class QlooSearchResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    results: list[QlooEntity] = Field(default_factory=list)


class QlooInsightsResults(BaseModel):
    model_config = ConfigDict(extra="allow")
    entities: list[QlooEntity] = Field(default_factory=list)


class QlooInsightsResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    success: bool = True
    results: QlooInsightsResults = Field(default_factory=QlooInsightsResults)
    warnings: list[Any] = Field(default_factory=list)


class QlooDemographicBlock(BaseModel):
    model_config = ConfigDict(extra="allow")
    entity_id: str
    query: dict[str, dict[str, float]] = Field(default_factory=dict)


class QlooDemographicsResults(BaseModel):
    model_config = ConfigDict(extra="allow")
    demographics: list[QlooDemographicBlock] = Field(default_factory=list)


class QlooDemographicsResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    success: bool = True
    results: QlooDemographicsResults = Field(default_factory=QlooDemographicsResults)
    warnings: list[Any] = Field(default_factory=list)
