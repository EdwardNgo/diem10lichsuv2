from fastapi import FastAPI

from diem10_api.admin import router as admin_router
from diem10_api.auth import router as auth_router
from diem10_api.public_exams import router as public_exams_router
from diem10_api.student_attempts import router as student_attempts_router
from diem10_api.student_exams import router as student_exams_router

app = FastAPI(title="Điểm 10 Lịch sử API", version="0.1.0")
app.include_router(admin_router)
app.include_router(auth_router)
app.include_router(public_exams_router)
app.include_router(student_attempts_router)
app.include_router(student_exams_router)


@app.get("/healthz")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
