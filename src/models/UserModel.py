import logging
from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


class UserModel:
    """MongoDB model for anonymous user profiles with persistent identity."""

    def __init__(self, db_client: AsyncIOMotorDatabase):
        self.collection = db_client["users"]

    async def get_or_create_user(self, session_id: str) -> dict:
        """Find user by session_id, or create a new one with defaults."""
        user = await self.collection.find_one({"session_id": session_id})
        if not user:
            user = {
                "session_id": session_id,
                "display_name": "",
                "avatar_color": self._generate_color(session_id),
                "created_at": datetime.now(timezone.utc),
                "last_seen": datetime.now(timezone.utc),
            }
            await self.collection.insert_one(user)
            logger.info(f"Created new user profile for session {session_id[:8]}...")
        else:
            await self.collection.update_one(
                {"session_id": session_id},
                {"$set": {"last_seen": datetime.now(timezone.utc)}},
            )
        user["_id"] = str(user["_id"])
        # Convert datetime fields to ISO strings for JSON serialization
        for key in ("created_at", "last_seen"):
            if isinstance(user.get(key), datetime):
                user[key] = user[key].isoformat()
        return user

    async def update_display_name(self, session_id: str, display_name: str) -> bool:
        """Update the display name for a user profile."""
        result = await self.collection.update_one(
            {"session_id": session_id},
            {"$set": {"display_name": display_name.strip()[:50]}},
        )
        return result.modified_count > 0

    async def update_avatar(self, session_id: str, avatar_base64: str) -> bool:
        """Update the avatar image explicitly for a given session mapping."""
        # Optional validation can be done in the route to ensure it's < 100kb
        result = await self.collection.update_one(
            {"session_id": session_id},
            {"$set": {"avatar_base64": avatar_base64}},
        )
        return result.modified_count > 0

    async def delete_user(self, session_id: str) -> bool:
        """Purge a user entirely from the collection (Nuclear Reset usage)."""
        result = await self.collection.delete_one({"session_id": session_id})
        return result.deleted_count > 0

    @staticmethod
    def _generate_color(session_id: str) -> str:
        """Deterministic HSL color from session_id hash."""
        hue = hash(session_id) % 360
        return f"hsl({hue}, 70%, 50%)"
