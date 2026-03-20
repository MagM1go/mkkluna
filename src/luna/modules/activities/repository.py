from collections import defaultdict
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from luna.db.models import ActivityModel
from luna.modules.common.domain.entities import Activity
from luna.modules.common.domain.entities import ActivityTreeNode


class SqlAlchemyActivityRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, activity_id: int) -> Activity | None:
        model = await self._session.get(ActivityModel, activity_id)
        if model is None:
            return None
        return self._to_entity(model)

    async def get_branch_ids(self, activity_id: int, max_depth: int = 3) -> list[int]:
        models = await self._all_models()
        by_parent = self._group_by_parent(models)
        return self._collect_branch_ids([activity_id], by_parent, max_depth)

    async def get_branch_ids_by_name(
        self, name: str, max_depth: int = 3
    ) -> list[int]:
        models = await self._all_models()
        normalized_name = name.casefold()
        matched_ids = [
            model.id
            for model in models
            if normalized_name in model.name.casefold()
        ]
        if not matched_ids:
            return []

        by_parent = self._group_by_parent(models)
        return self._collect_branch_ids(list(matched_ids), by_parent, max_depth)

    async def list_tree(self, max_depth: int = 3) -> list[ActivityTreeNode]:
        models = await self._all_models()
        by_parent = self._group_by_parent(models)
        roots = sorted(by_parent[None], key=lambda item: item.name.lower())
        return [self._build_tree(root, by_parent, 1, max_depth) for root in roots]

    async def _all_models(self) -> Sequence[ActivityModel]:
        result = await self._session.scalars(
            select(ActivityModel).order_by(ActivityModel.name.asc())
        )
        return result.all()

    @staticmethod
    def _group_by_parent(
        models: Sequence[ActivityModel],
    ) -> dict[int | None, list[ActivityModel]]:
        grouped: dict[int | None, list[ActivityModel]] = defaultdict(list)
        for model in models:
            grouped[model.parent_id].append(model)
        return grouped

    def _collect_branch_ids(
        self,
        root_ids: list[int],
        by_parent: dict[int | None, list[ActivityModel]],
        max_depth: int,
    ) -> list[int]:
        collected: list[int] = []
        visited: set[int] = set()
        stack: list[tuple[int, int]] = [(root_id, 1) for root_id in root_ids]

        while stack:
            current_id, depth = stack.pop()
            if current_id in visited or depth > max_depth:
                continue
            visited.add(current_id)
            collected.append(current_id)
            for child in by_parent.get(current_id, []):
                stack.append((child.id, depth + 1))

        return collected

    def _build_tree(
        self,
        model: ActivityModel,
        by_parent: dict[int | None, list[ActivityModel]],
        depth: int,
        max_depth: int,
    ) -> ActivityTreeNode:
        children: list[ActivityTreeNode] = []
        if depth < max_depth:
            children = [
                self._build_tree(child, by_parent, depth + 1, max_depth)
                for child in sorted(
                    by_parent.get(model.id, []),
                    key=lambda item: item.name.lower(),
                )
            ]
        return ActivityTreeNode(
            id=model.id,
            name=model.name,
            parent_id=model.parent_id,
            children=children,
        )

    @staticmethod
    def _to_entity(model: ActivityModel) -> Activity:
        return Activity(id=model.id, name=model.name, parent_id=model.parent_id)
