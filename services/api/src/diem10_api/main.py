from fastapi import FastAPI

from diem10_api.public_exams import router as public_exams_router

app = FastAPI(title="Điểm 10 Lịch sử API", version="0.1.0")
app.include_router(public_exams_router)


@app.get("/healthz")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
