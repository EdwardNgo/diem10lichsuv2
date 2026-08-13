from fastapi import APIRouter, Depends

from diem10_api.controllers.deps import require_admin
from diem10_api.models import User
from diem10_api.schemas.admin import AdminProbe

router = APIRouter(prefix="/v1/admin", tags=["admin"])


@router.get("/probe", response_model=AdminProbe)
def admin_probe(_: User = Depends(require_admin)) -> AdminProbe:
    return AdminProbe(ok=True)
