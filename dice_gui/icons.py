import sys
from pathlib import Path
from PyQt6.QtGui import QIcon

def resolve_asset_path(filename: str) -> Path:
    """Resolve asset paths relative to dice_gui/assets/icons/."""
    if hasattr(sys, '_MEIPASS'):
        base_path = Path(sys._MEIPASS)
    else:
        # Returns the 'dice_gui' directory containing icons.py
        base_path = Path(__file__).resolve().parent 
        
    return base_path / "assets" / "icons" / filename

class Icons:
    _cache: dict[str, QIcon] = {}

    @classmethod
    def get(cls, name: str) -> QIcon:
        """Fetch a cached QIcon by name (e.g., Icons.get('settings'))."""
        if name not in cls._cache:
            # Prefer vector SVGs for crisp high-DPI scaling
            icon_path = resolve_asset_path(f"{name}.svg")
            if not icon_path.exists():
                icon_path = resolve_asset_path(f"{name}.png")
                
            cls._cache[name] = QIcon(str(icon_path))
        return cls._cache[name]
    
