"""Version information for F1 Lap Bot.

Version is determined by:
1. BOT_VERSION environment variable (set during build/deployment)
2. VERSION file in project root (generated during CI/CD)
3. Fallback to 'development' if neither is available
"""
import os
from pathlib import Path

# Cache the version to avoid repeated file reads
_cached_version: str | None = None


def get_version() -> str:
    """Get the current bot version.
    
    Returns:
        Version string in semantic versioning format (MAJOR.MINOR.PATCH)
        or 'development' if version cannot be determined.
    """
    global _cached_version
    
    if _cached_version is not None:
        return _cached_version
    
    # Try environment variable first (highest priority)
    env_version = os.getenv("BOT_VERSION")
    if env_version:
        _cached_version = env_version.strip()
        return _cached_version
    
    # Try VERSION file in project root
    try:
        version_file = Path(__file__).parent.parent / "VERSION"
        if version_file.exists():
            _cached_version = version_file.read_text().strip()
            return _cached_version
    except Exception:
        pass  # Ignore file read errors
    
    # Fallback to development
    _cached_version = "development"
    return _cached_version


def get_version_info() -> dict[str, str]:
    """Get detailed version information.
    
    Returns:
        Dictionary containing version details.
    """
    version = get_version()
    
    info = {
        "version": version,
        "is_development": version == "development",
    }
    
    # Parse semantic version if possible
    if version != "development" and version.count(".") == 2:
        parts = version.replace("v", "").split(".")
        try:
            info["major"] = parts[0]
            info["minor"] = parts[1]
            info["patch"] = parts[2]
        except (ValueError, IndexError):
            pass
    
    return info
