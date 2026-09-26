"""Dependency container (single instances shared by the API)."""
from app.config.settings import settings
from app.engines.registry import ModelRegistry
from app.services.cache_service import make_cache
from app.services.auth_service import AuthService
from app.services.change_detection_service import ChangeDetectionService
from app.services.demo_service import DemoService
from app.services.detection_service import DetectionService
from app.services.image_service import ImageService
from app.services.orchestrator import Orchestrator
from app.services.query_router import RuleBasedRouter
from app.services.repository import Repository
from app.services.segmentation_service import SegmentationService
from app.services.storage_service import LocalStorageService, S3StorageService

storage = LocalStorageService(settings.data_dir) if settings.storage_backend == "local" else S3StorageService()
repo = Repository(storage)
auth = AuthService(repo)
cache = make_cache(settings.redis_url)
registry = ModelRegistry()
images = ImageService(storage, repo)
orchestrator = Orchestrator(images, repo, cache, registry, RuleBasedRouter(), DetectionService(registry, images, cache),
                            SegmentationService(registry, images, cache), ChangeDetectionService(registry, images, cache))
demo = DemoService(images)
