from luna.modules.activities.domain.repositories import ActivityRepository
from luna.modules.common.domain.entities import ActivityTreeNode


class ListActivityTreeService:
    def __init__(self, activity_repository: ActivityRepository) -> None:
        self._activity_repository = activity_repository

    async def execute(self) -> list[ActivityTreeNode]:
        return await self._activity_repository.list_tree(max_depth=3)
