from pydantic import BaseModel

from luna.modules.common.domain.entities import ActivityTreeNode


class ActivityTreeNodeResponse(BaseModel):
    id: int
    name: str
    parent_id: int | None
    children: list["ActivityTreeNodeResponse"]

    @classmethod
    def from_entity(cls, node: ActivityTreeNode) -> "ActivityTreeNodeResponse":
        return cls(
            id=node.id,
            name=node.name,
            parent_id=node.parent_id,
            children=[cls.from_entity(child) for child in node.children],
        )


ActivityTreeNodeResponse.model_rebuild()
