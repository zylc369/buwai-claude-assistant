"""AI resource service for business logic."""

import asyncio
import json
import os
import re
import tempfile
from pathlib import Path
from typing import List, Optional, Set

from sqlalchemy.ext.asyncio import AsyncSession

from config import get_config
from database.models import AiResource, Workspace
from repositories.ai_resource_repository import AiResourceRepository
from utils.id_generator import generate_uuidv7
from utils.timestamp import get_timestamp_ms
from logger import get_logger

logger = get_logger(__name__)

SYNC_LOCK: dict[str, asyncio.Lock] = {}
DEFAULT_REFRESH_INTERVAL_MS = 24 * 60 * 60 * 1000

TYPE_DIR_MAP: dict[str, str] = {
    "skill": "skills",
    "command": "commands",
    "system_prompt": "prompts",
}

TYPE_EXT_MAP: dict[str, str] = {
    "skill": "md",
    "command": "md",
    "system_prompt": "md",
}


def sanitize_filename(name: str) -> str:
    name = re.sub(r'[^\w\-_.]', '_', name)
    name = re.sub(r'\.{2,}', '_', name)
    name = name.strip('._')[:255]
    return name or 'unnamed'


class AiResourceService:
    """Service layer for AI resource management.

    Provides business logic for AI resource operations, wrapping the
    AiResourceRepository with additional functionality like timestamp
    management and JSON handling for content field.

    Attributes:
        session: SQLAlchemy async session.
        ai_resource_repo: AiResourceRepository instance.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.ai_resource_repo = AiResourceRepository(session)

    async def create_ai_resource(
        self,
        name: str,
        type: str,
        sub_type: str,
        owner: Optional[str],
        disabled: bool,
        content: dict,
        test: bool = False,
        resource_unique_id: Optional[str] = None,
    ) -> AiResource:
        logger.debug(f"create_ai_resource called with name={name}, type={type}")

        if resource_unique_id is None:
            resource_unique_id = generate_uuidv7()

        # Serialize content to JSON string
        content_json = json.dumps(content)

        current_time = get_timestamp_ms()

        try:
            logger.info(f"Business decision: creating AI resource {resource_unique_id}")
            resource = await self.ai_resource_repo.create(
                resource_unique_id=resource_unique_id,
                name=name,
                type=type,
                sub_type=sub_type,
                owner=owner,
                disabled=disabled,
                content=content_json,
                gmt_create=current_time,
                gmt_modified=current_time,
                test=test,
            )

            await self.session.commit()
            await self.session.refresh(resource)

            logger.debug(f"create_ai_resource completed")
            return resource
        except Exception as e:
            logger.error(f"create_ai_resource failed: {str(e)}")
            raise

    async def get_ai_resource_by_unique_id(
        self, resource_unique_id: str, test: bool = False
    ) -> Optional[AiResource]:
        logger.debug(f"get_ai_resource_by_unique_id called with resource_unique_id={resource_unique_id}")
        result = await self.ai_resource_repo.get_by_unique_id(resource_unique_id, test=test)
        logger.debug(f"get_ai_resource_by_unique_id completed, found={result is not None}")
        return result

    async def list_ai_resources(
        self,
        offset: int = 0,
        limit: int = 100,
        test: bool = False,
    ) -> List[AiResource]:
        logger.debug(f"list_ai_resources called with offset={offset}, limit={limit}")
        result = await self.ai_resource_repo.get_all(
            offset=offset,
            limit=limit,
            test=test,
        )
        logger.debug(f"list_ai_resources completed, returned {len(result)} resources")
        return result

    async def update_ai_resource(
        self,
        resource_unique_id: str,
        test: bool = False,
        **kwargs
    ) -> Optional[AiResource]:
        logger.debug(f"update_ai_resource called with resource_unique_id={resource_unique_id}")
        resource = await self.ai_resource_repo.get_by_unique_id(resource_unique_id, test=test)
        if not resource:
            logger.debug(f"update_ai_resource completed, resource not found")
            return None

        # Serialize content to JSON if provided as dict
        if "content" in kwargs and isinstance(kwargs["content"], dict):
            kwargs["content"] = json.dumps(kwargs["content"])

        kwargs["gmt_modified"] = get_timestamp_ms()

        logger.info(f"Business decision: updating AI resource {resource_unique_id}")
        updated = await self.ai_resource_repo.update(resource, **kwargs)
        await self.session.commit()
        await self.session.refresh(updated)

        logger.debug(f"update_ai_resource completed")
        return updated

    async def delete_ai_resource(self, resource_unique_id: str, test: bool = False) -> bool:
        logger.debug(f"delete_ai_resource called with resource_unique_id={resource_unique_id}")
        resource = await self.ai_resource_repo.get_by_unique_id(resource_unique_id, test=test)
        if not resource:
            logger.debug(f"delete_ai_resource completed, resource not found")
            return False

        logger.info(f"Business decision: deleting AI resource {resource_unique_id}")
        await self.ai_resource_repo.delete(resource)
        await self.session.commit()

        logger.debug(f"delete_ai_resource completed")
        return True

    async def get_ai_resource_by_id(self, resource_id: int, test: bool = False) -> Optional[AiResource]:
        logger.debug(f"get_ai_resource_by_id called with resource_id={resource_id}")
        result = await self.ai_resource_repo.get_by_id(resource_id, test=test)
        logger.debug(f"get_ai_resource_by_id completed, found={result is not None}")
        return result

    def _should_sync(
        self,
        workspace: Workspace,
        refresh_interval_ms: int = DEFAULT_REFRESH_INTERVAL_MS,
    ) -> bool:
        if workspace.latest_active_time is None:
            logger.debug(f"_should_sync: workspace {workspace.directory} never synced")
            return True

        current_time = get_timestamp_ms()
        elapsed = current_time - workspace.latest_active_time
        needs_refresh = elapsed >= refresh_interval_ms
        logger.debug(f"_should_sync: workspace {workspace.directory}, elapsed={elapsed}ms, needs_refresh={needs_refresh}")
        return needs_refresh

    async def _get_sync_lock(self, workspace_directory: str) -> asyncio.Lock:
        if workspace_directory not in SYNC_LOCK:
            SYNC_LOCK[workspace_directory] = asyncio.Lock()
        return SYNC_LOCK[workspace_directory]

    async def _write_atomically(self, filepath: Path, content: str) -> None:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_path = tempfile.mkstemp(
            dir=filepath.parent,
            prefix='.tmp_',
            suffix=filepath.suffix
        )
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                f.write(content)
            os.rename(temp_path, str(filepath))
            logger.debug(f"_write_atomically: wrote {filepath}")
        except Exception:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise

    async def _write_resource_files(
        self,
        resources: List[AiResource],
        root_path: Path,
        owner: Optional[str],
    ) -> Set[Path]:
        written_paths: Set[Path] = set()

        for resource in resources:
            type_dir = TYPE_DIR_MAP.get(resource.type, resource.type)
            ext = TYPE_EXT_MAP.get(resource.type, 'md')
            owner_dir = owner if owner else "global"
            sub_type = sanitize_filename(resource.sub_type)
            name = sanitize_filename(resource.name)

            relative_path = Path(owner_dir) / type_dir / sub_type / f"{name}.{ext}"
            filepath = root_path / relative_path

            await self._write_atomically(filepath, resource.content)
            written_paths.add(filepath)

        logger.debug(f"_write_resource_files: wrote {len(written_paths)} files")
        return written_paths

    def _create_symlink_safe(self, target: Path, link: Path) -> bool:
        if link.is_symlink():
            logger.debug(f"_create_symlink_safe: symlink already exists: {link}")
            return True
        if link.exists():
            logger.warning(f"_create_symlink_safe: target exists as non-symlink: {link}")
            return False

        target = target.resolve()
        if not target.exists():
            logger.warning(f"_create_symlink_safe: symlink target directory missing: {target}")
            return False

        link.parent.mkdir(parents=True, exist_ok=True)
        os.symlink(str(target), str(link))
        logger.debug(f"_create_symlink_safe: created symlink {link} -> {target}")
        return True

    async def _create_symlinks(
        self,
        root_path: Path,
        owner: Optional[str],
        workspace_path: Path,
    ) -> None:
        owner_dir = owner if owner else "global"
        claude_dir = workspace_path / ".claude"

        for resource_type, type_dir in TYPE_DIR_MAP.items():
            if resource_type == "system_prompt":
                continue

            target_dir = root_path / owner_dir / type_dir
            link_dir = claude_dir / type_dir

            if target_dir.exists():
                self._create_symlink_safe(target_dir, link_dir)

    async def _read_system_prompts(
        self,
        resources: List[AiResource],
    ) -> str:
        prompts: List[str] = []
        for resource in resources:
            if resource.type == "system_prompt" and not resource.disabled:
                prompts.append(resource.content)

        merged = "\n\n---\n\n".join(prompts) if prompts else ""
        logger.debug(f"_read_system_prompts: merged {len(prompts)} prompts")
        return merged

    async def _delete_orphan_files(
        self,
        root_path: Path,
        owner: Optional[str],
        valid_paths: Set[Path],
    ) -> int:
        owner_dir = owner if owner else "global"
        deleted_count = 0

        for type_dir in TYPE_DIR_MAP.values():
            resource_dir = root_path / owner_dir / type_dir
            if not resource_dir.exists():
                continue

            for filepath in resource_dir.rglob("*"):
                if filepath.is_file() and filepath not in valid_paths:
                    try:
                        filepath.unlink()
                        deleted_count += 1
                        logger.debug(f"_delete_orphan_files: deleted {filepath}")
                    except Exception as e:
                        logger.warning(f"_delete_orphan_files: failed to delete {filepath}: {e}")

        logger.info(f"_delete_orphan_files: deleted {deleted_count} orphan files")
        return deleted_count

    async def sync_ai_resources(
        self,
        workspace: Workspace,
        refresh_interval_ms: int = DEFAULT_REFRESH_INTERVAL_MS,
    ) -> str:
        if not self._should_sync(workspace, refresh_interval_ms):
            logger.debug(f"sync_ai_resources: skipping sync for workspace {workspace.directory}")
            resources = await self.ai_resource_repo.get_resources_for_sync(
                owner=workspace.directory,
                test=workspace.test
            )
            return await self._read_system_prompts(resources)

        lock = await self._get_sync_lock(workspace.directory)
        async with lock:
            logger.info(f"sync_ai_resources: starting sync for workspace {workspace.directory}")

            config = get_config()
            root_path = Path(config.projects.root)
            workspace_path = root_path / workspace.directory

            resources = await self.ai_resource_repo.get_resources_for_sync(
                owner=workspace.directory,
                test=workspace.test
            )

            written_paths = await self._write_resource_files(
                resources=resources,
                root_path=root_path,
                owner=workspace.directory,
            )

            await self._delete_orphan_files(
                root_path=root_path,
                owner=workspace.directory,
                valid_paths=written_paths,
            )

            await self._create_symlinks(
                root_path=root_path,
                owner=workspace.directory,
                workspace_path=workspace_path,
            )

            merged_prompt = await self._read_system_prompts(resources)

            logger.info(f"sync_ai_resources: completed sync for workspace {workspace.directory}")
            return merged_prompt
