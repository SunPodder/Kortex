"""User information provider for Linux/KDE systems."""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QObject, Property, Signal

logger = logging.getLogger(__name__)


class UserInfo(QObject):
    """Provides current Linux user information to QML."""
    
    usernameChanged = Signal()
    avatarPathChanged = Signal()
    
    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._username = self._get_username()
        self._avatar_path = self._find_avatar_path()
    
    @Property(str, notify=usernameChanged)
    def username(self) -> str:
        """Get the current Linux username."""
        return self._username
    
    @Property(str, notify=avatarPathChanged)
    def avatarPath(self) -> str:
        """Get the path to the user's avatar image."""
        return self._avatar_path
    
    def _get_username(self) -> str:
        """Get the current Linux username."""
        # Try multiple methods to get the username
        try:
            # Method 1: Environment variable
            username = os.environ.get("USER", "")
            if username:
                return username
            
            # Method 2: getlogin
            import pwd
            return pwd.getpwuid(os.getuid()).pw_name
        except Exception as e:
            logger.warning(f"Failed to get username: {e}")
            return "User"
    
    def _find_avatar_path(self) -> str:
        """Find the user's avatar image path from various sources."""
        home = Path.home()
        
        # Common avatar locations on Linux/KDE
        avatar_paths = [
            # KDE Plasma 5/6 face icon
            home / ".face",
            home / ".face.icon",
            
            # GNOME/AccountsService avatar
            Path(f"/var/lib/AccountsService/icons/{self._username}"),
            
            # Legacy locations
            home / ".config" / "kdeglobals",  # May contain face path
            
            # Common KDE avatar locations
            home / ".local" / "share" / "konsole" / "profile.png",
        ]
        
        # Check KDE-specific face icon locations
        kde_face_paths = [
            home / ".face",
            home / ".face.icon", 
            home / ".face.png",
            home / ".face.jpg",
            home / ".face.jpeg",
        ]
        
        for path in kde_face_paths:
            if path.exists() and path.is_file():
                logger.info(f"Found user avatar at: {path}")
                return str(path)
        
        # Check AccountsService (works on most modern Linux distros)
        accounts_service_path = Path(f"/var/lib/AccountsService/icons/{self._username}")
        if accounts_service_path.exists():
            logger.info(f"Found user avatar at AccountsService: {accounts_service_path}")
            return str(accounts_service_path)
        
        # Try to read the AccountsService user file for avatar path
        accounts_user_file = Path(f"/var/lib/AccountsService/users/{self._username}")
        if accounts_user_file.exists():
            try:
                content = accounts_user_file.read_text()
                for line in content.split("\n"):
                    if line.startswith("Icon="):
                        icon_path = line.split("=", 1)[1].strip()
                        if Path(icon_path).exists():
                            logger.info(f"Found user avatar from AccountsService config: {icon_path}")
                            return icon_path
            except Exception as e:
                logger.debug(f"Failed to read AccountsService user file: {e}")
        
        logger.debug("No user avatar found")
        return ""
