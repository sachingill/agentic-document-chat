from fastapi import APIRouter

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/{user_id}")
async def get_user(user_id: int):
    return {"user_id": user_id, "name": "Test User"}