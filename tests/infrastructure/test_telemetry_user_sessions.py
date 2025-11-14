"""Tests for user-based session lookup in SQLiteTelemetryRepository.

This test module verifies the new user_id tracking functionality
added to the telemetry repository for Mathe-Coach UX improvement.
"""

import pytest
import pytest_asyncio
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.infrastructure.persistence.sqlite_telemetry_repository import SQLiteTelemetryRepository


@pytest_asyncio.fixture
async def repository(tmp_path):
    """Create temporary telemetry repository with schema."""
    db_path = tmp_path / "test_telemetry.db"
    repo = SQLiteTelemetryRepository(str(db_path))
    
    # Apply migrations
    import aiosqlite
    async with aiosqlite.connect(str(db_path)) as db:
        # Load migration 001
        with open("src/infrastructure/migrations/001_telemetry_schema.sql") as f:
            await db.executescript(f.read())
        
        # Load migration 002
        with open("src/infrastructure/migrations/002_add_user_to_sessions.sql") as f:
            await db.executescript(f.read())
        
        await db.commit()
    
    return repo


@pytest.mark.asyncio
async def test_save_session_with_user_id(repository):
    """Test saving session with user_id."""
    await repository.save_session(
        session_uid=1000,
        track_id="monaco",
        session_type=18,
        user_id="123456789"
    )
    
    session = await repository.get_session(1000)
    assert session is not None
    assert session["session_uid"] == 1000
    assert session["track_id"] == "monaco"


@pytest.mark.asyncio
async def test_save_session_without_user_id(repository):
    """Test saving session without user_id (legacy compatibility)."""
    await repository.save_session(
        session_uid=2000,
        track_id="silverstone",
        session_type=18,
        user_id=None
    )
    
    session = await repository.get_session(2000)
    assert session is not None
    assert session["session_uid"] == 2000


@pytest.mark.asyncio
async def test_get_latest_session_for_user(repository):
    """Test retrieving latest session for a specific user."""
    # Create sessions for two users
    await repository.save_session(1001, "monaco", 18, user_id="user_1")
    await repository.save_session(1002, "silverstone", 18, user_id="user_1")
    await repository.save_session(1003, "spa", 18, user_id="user_2")
    
    # Get latest for user_1 (should be session 1002)
    latest = await repository.get_latest_session_for_user("user_1")
    assert latest == 1002
    
    # Get latest for user_2
    latest = await repository.get_latest_session_for_user("user_2")
    assert latest == 1003


@pytest.mark.asyncio
async def test_get_latest_session_for_user_no_sessions(repository):
    """Test retrieving latest session when user has no sessions."""
    latest = await repository.get_latest_session_for_user("nonexistent_user")
    assert latest is None


@pytest.mark.asyncio
async def test_get_latest_session_for_user_and_track(repository):
    """Test retrieving latest session for user on specific track."""
    # Create multiple sessions for user on different tracks
    await repository.save_session(2001, "monaco", 18, user_id="user_1")
    await repository.save_session(2002, "silverstone", 18, user_id="user_1")
    await repository.save_session(2003, "monaco", 18, user_id="user_1")
    await repository.save_session(2004, "silverstone", 18, user_id="user_2")
    
    # Get latest Monaco session for user_1 (should be 2003)
    latest = await repository.get_latest_session_for_user_and_track("user_1", "monaco")
    assert latest == 2003
    
    # Get latest Silverstone session for user_1 (should be 2002)
    latest = await repository.get_latest_session_for_user_and_track("user_1", "silverstone")
    assert latest == 2002
    
    # Get for user_2
    latest = await repository.get_latest_session_for_user_and_track("user_2", "silverstone")
    assert latest == 2004


@pytest.mark.asyncio
async def test_get_latest_session_for_user_and_track_no_match(repository):
    """Test retrieving session when no match exists."""
    await repository.save_session(3001, "monaco", 18, user_id="user_1")
    
    # User has no sessions on Silverstone
    latest = await repository.get_latest_session_for_user_and_track("user_1", "silverstone")
    assert latest is None
    
    # User doesn't exist
    latest = await repository.get_latest_session_for_user_and_track("user_999", "monaco")
    assert latest is None


@pytest.mark.asyncio
async def test_session_ordering_by_timestamp(repository):
    """Test that latest session is determined by created_at timestamp."""
    # Create sessions with explicit timestamps
    from datetime import timedelta
    
    base_time = datetime(2024, 1, 1, 12, 0, 0)
    
    await repository.save_session(
        4001, "monaco", 18, 
        user_id="user_1", 
        started_at=base_time
    )
    
    await repository.save_session(
        4002, "monaco", 18,
        user_id="user_1",
        started_at=base_time + timedelta(hours=1)
    )
    
    await repository.save_session(
        4003, "monaco", 18,
        user_id="user_1",
        started_at=base_time + timedelta(hours=2)
    )
    
    # Latest should be 4003 (most recent timestamp)
    latest = await repository.get_latest_session_for_user("user_1")
    assert latest == 4003


@pytest.mark.asyncio
async def test_user_session_isolation(repository):
    """Test that user sessions are properly isolated."""
    # User 1 has Monaco and Silverstone
    await repository.save_session(5001, "monaco", 18, user_id="user_1")
    await repository.save_session(5002, "silverstone", 18, user_id="user_1")
    
    # User 2 has Monaco only
    await repository.save_session(5003, "monaco", 18, user_id="user_2")
    
    # User 1's latest should not include user_2's sessions
    latest_user1 = await repository.get_latest_session_for_user("user_1")
    assert latest_user1 in [5001, 5002]
    
    latest_user2 = await repository.get_latest_session_for_user("user_2")
    assert latest_user2 == 5003
