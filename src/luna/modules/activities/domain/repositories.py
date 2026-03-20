from typing import Protocol

from luna.modules.common.domain.entities import Activity
from luna.modules.common.domain.entities import ActivityTreeNode


class ActivityRepository(Protocol):
    async def get_by_id(self, activity_id: int) -> Activity | None: ...

    async def get_branch_ids(
        self, activity_id: int, max_depth: int = 3
    ) -> list[int]: ...

    async def get_branch_ids_by_name(
        self, name: str, max_depth: int = 3
    ) -> list[int]: ...

    async def list_tree(self, max_depth: int = 3) -> list[ActivityTreeNode]: ...
