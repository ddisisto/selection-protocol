"""
Mod API client. Single interface to BepInEx mod HTTP API.

This is the ONLY Python module that imports requests.
Provides Pythonic game-semantic methods, hiding REST/JSON details.

Architecture:
- Two primitives: Target (focused Bibite) and World (sim state)
- Fail-fast: ModUnavailableError on init if mod not responding
- Clean exceptions: ModError base class for all mod failures
- Game semantics: kill/lay/extend, not keypresses/clicks/clipboard
"""

import requests
from dataclasses import dataclass
from typing import Optional


class ModError(Exception):
    """Base exception for mod communication failures."""
    pass


class ModUnavailableError(ModError):
    """Mod not responding (game not running or mod not loaded)."""
    pass


class ActionValidationError(ModError):
    """Action cannot be executed (e.g., target can't lay)."""
    pass


@dataclass
class TargetInfo:
    """Info about currently focused Bibite."""
    bibite_id: int
    lineage_tag: str
    species: str
    age: float
    energy: float
    can_kill: bool
    can_lay: bool


@dataclass
class ActionResult:
    """Result of an action execution."""
    success: bool
    action: str
    message: Optional[str] = None


class ModClient:
    """
    Client for BepInEx mod HTTP API.

    Provides high-level game-semantic operations that map to Unity game internals.
    All complexity (pause/unpause, field access, validation) handled C# side.

    Usage:
        mod = ModClient()  # Fails fast if mod unavailable
        result = mod.kill_target()
        result = mod.lay_target(lineage_tag='TwitchUser123')
    """

    def __init__(self, base_url='http://localhost:5001', timeout=5.0):
        """
        Initialize mod client and verify connection.

        Args:
            base_url: Mod HTTP API base URL
            timeout: Request timeout in seconds

        Raises:
            ModUnavailableError: If mod not responding
        """
        self.base_url = base_url
        self.timeout = timeout
        self._verify_connection()

    def _verify_connection(self):
        """
        Verify mod is available (fail-fast on init).

        Raises:
            ModUnavailableError: If health check fails
        """
        try:
            resp = requests.get(f'{self.base_url}/health', timeout=self.timeout)
            resp.raise_for_status()
        except requests.RequestException as e:
            raise ModUnavailableError(
                f"Mod API not available at {self.base_url}: {e}\n"
                "Ensure The Bibites is running with BepInEx mod loaded."
            )

    # ============================================================
    # TARGET ACTIONS (focused Bibite)
    # ============================================================

    def get_target_info(self) -> Optional[TargetInfo]:
        """
        Get info about currently focused Bibite.

        Returns:
            TargetInfo if target exists, None if no target selected

        Raises:
            ModError: If request fails
        """
        resp = self._post('/target/info')
        if resp is None:
            return None
        return TargetInfo(**resp)

    def kill_target(self) -> ActionResult:
        """
        Execute kill on current target.

        Mod handles validation (target exists).

        Returns:
            ActionResult with success status and optional error message

        Raises:
            ModError: If request fails
        """
        resp = self._post('/target/kill')
        return ActionResult(**resp)

    def lay_target(self, lineage_tag: str) -> ActionResult:
        """
        Execute lay on current target with lineage tag.

        Mod handles:
        - Pause game
        - Validate target can reproduce (age, energy)
        - Set lineage tag field
        - Execute reproduction
        - Unpause game

        Args:
            lineage_tag: Username to tag organism with

        Returns:
            ActionResult with success status and optional error message

        Raises:
            ModError: If request fails
        """
        resp = self._post('/target/lay', {'lineage_tag': lineage_tag})
        return ActionResult(**resp)

    def extend_target(self) -> ActionResult:
        """
        Extend observation (no-op, just for API consistency).

        Returns:
            ActionResult with success=True
        """
        return ActionResult(success=True, action='extend')

    # ============================================================
    # WORLD CONTROLS (simulation state)
    # ============================================================

    def get_pause_state(self) -> bool:
        """
        Get current pause state.

        Returns:
            True if paused, False if running

        Raises:
            ModError: If request fails
        """
        resp = self._get('/world/pause')
        return resp['paused']

    def set_pause_state(self, paused: bool) -> None:
        """
        Set pause state.

        Args:
            paused: True to pause, False to unpause

        Raises:
            ModError: If request fails
        """
        self._post('/world/pause', {'paused': paused})

    def zoom(self, direction: str) -> None:
        """
        Zoom in/out.

        Args:
            direction: 'in' or 'out'

        Raises:
            ModError: If request fails
        """
        if direction not in ['in', 'out']:
            raise ValueError(f"Invalid zoom direction: {direction}")
        self._post('/world/zoom', {'direction': direction})

    def set_info_panel(self, panel: int) -> None:
        """
        Set info panel visibility.

        Args:
            panel: 0 (hide all) or 1-4 (show panel number)

        Raises:
            ModError: If request fails
        """
        if panel not in [0, 1, 2, 3, 4]:
            raise ValueError(f"Invalid panel number: {panel}")
        self._post('/world/info_panel', {'panel': panel})

    # ============================================================
    # HTTP HELPERS (private)
    # ============================================================

    def _get(self, path: str) -> dict:
        """
        GET request, return JSON.

        Args:
            path: API endpoint path

        Returns:
            Parsed JSON response

        Raises:
            ModError: If request fails
        """
        try:
            resp = requests.get(f'{self.base_url}{path}', timeout=self.timeout)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            raise ModError(f"GET {path} failed: {e}")

    def _post(self, path: str, data: dict = None) -> dict:
        """
        POST request, return JSON.

        Args:
            path: API endpoint path
            data: Optional JSON payload

        Returns:
            Parsed JSON response

        Raises:
            ModError: If request fails
        """
        try:
            resp = requests.post(
                f'{self.base_url}{path}',
                json=data,
                timeout=self.timeout
            )
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            raise ModError(f"POST {path} failed: {e}")


# ============================================================
# GLOBAL SINGLETON
# ============================================================

_mod_client = None


def get_mod_client() -> ModClient:
    """
    Get global mod client instance (created on first call).

    Returns:
        Singleton ModClient instance

    Raises:
        ModUnavailableError: If mod not available on first call
    """
    global _mod_client
    if _mod_client is None:
        _mod_client = ModClient()
    return _mod_client
