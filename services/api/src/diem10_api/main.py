from fastapi import FastAPI

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
from diem10_api.controllers.auth_controller import router as auth_router
from diem10_api.controllers.public_exams_controller import router as public_exams_router
from diem10_api.controllers.student_attempts_controller import (
    router as student_attempts_router,
)
from diem10_api.controllers.student_exams_controller import (
    router as student_exams_router,
)
from diem10_api.core.logging import configure_logging
from diem10_api.middleware.request_logging import RequestLoggingMiddleware

configure_logging()

app = FastAPI(title="Điểm 10 Lịch sử API", version="0.1.0")
app.add_middleware(RequestLoggingMiddleware)
app.include_router(admin_router)
app.include_router(admin_access_router)
app.include_router(admin_source_documents_router)
app.include_router(admin_extractions_router)
app.include_router(admin_publishing_router)
app.include_router(auth_router)
app.include_router(public_exams_router)
app.include_router(student_attempts_router)
app.include_router(student_exams_router)


@app.get("/healthz")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
