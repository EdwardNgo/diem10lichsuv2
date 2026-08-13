from diem10_api.controllers.admin_access_controller import router as admin_access_router
from diem10_api.controllers.admin_controller import router as admin_router
from diem10_api.controllers.admin_extractions_controller import (
    router as admin_extractions_router,
)
from diem10_api.controllers.admin_publishing_controller import (
    router as admin_publishing_router,
)
from diem10_api.controllers.admin_source_documents_controller import (
    router as admin_source_documents_router,
)

__all__ = [
    "admin_access_router",
    "admin_extractions_router",
    "admin_publishing_router",
    "admin_router",
    "admin_source_documents_router",
]
