"""
State persistence utilities for the Tool Builder System.

Handles saving and loading state to/from JSON files.
"""

import json
import os
from pathlib import Path
from typing import Optional
from .state import ToolBuilderState


class StatePersistence:
    """Manages state persistence to disk."""

    def __init__(self, base_path: str = ".agent_state"):
        """
        Initialize state persistence manager.

        Args:
            base_path: Directory path for storing state files
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True, parents=True)

    def save_state(self, state: ToolBuilderState, session_id: Optional[str] = None) -> str:
        """
        Save state to a JSON file.

        Args:
            state: Current state to save
            session_id: Optional session identifier. If not provided, uses function_name

        Returns:
            Path to saved state file

        Raises:
            ValueError: If neither session_id nor function_name is available
        """
        # Determine filename
        if session_id:
            filename = f"{session_id}.json"
        elif state.get("function_name"):
            filename = f"{state['function_name']}.json"
        else:
            raise ValueError("Cannot save state: no session_id or function_name available")

        filepath = self.base_path / filename

        # Save state
        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2)

        return str(filepath)

    def load_state(self, session_id: str) -> Optional[ToolBuilderState]:
        """
        Load state from a JSON file.

        Args:
            session_id: Session identifier or function name

        Returns:
            Loaded state, or None if file doesn't exist
        """
        filepath = self.base_path / f"{session_id}.json"

        if not filepath.exists():
            return None

        with open(filepath, 'r') as f:
            return json.load(f)

    def delete_state(self, session_id: str) -> bool:
        """
        Delete a saved state file.

        Args:
            session_id: Session identifier

        Returns:
            True if file was deleted, False if it didn't exist
        """
        filepath = self.base_path / f"{session_id}.json"

        if filepath.exists():
            filepath.unlink()
            return True
        return False

    def list_sessions(self) -> list[str]:
        """
        List all saved sessions.

        Returns:
            List of session identifiers (filenames without .json extension)
        """
        return [
            f.stem
            for f in self.base_path.glob("*.json")
        ]
