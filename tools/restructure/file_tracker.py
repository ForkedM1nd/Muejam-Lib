#!/usr/bin/env python3
"""
File Movement Tracker for Monorepo Restructure

This module provides tracking and logging of all file movements during the
monorepo restructuring process. It maintains a complete record for documentation
and rollback purposes.

Requirements: 11.2
"""

import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict


@dataclass
class FileMovement:
    """Represents a single file movement operation."""
    old_path: str
    new_path: str
    file_type: str  # 'code', 'doc', 'test', 'config', 'artifact'
    phase: int
    timestamp: datetime
    reason: str
    
    def to_dict(self) -> dict:
        """Convert FileMovement to dictionary for JSON serialization."""
        return {
            'old_path': self.old_path,
            'new_path': self.new_path,
            'file_type': self.file_type,
            'phase': self.phase,
            'timestamp': self.timestamp.isoformat(),
            'reason': self.reason
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'FileMovement':
        """Create FileMovement from dictionary."""
        return cls(
            old_path=data['old_path'],
            new_path=data['new_path'],
            file_type=data['file_type'],
            phase=data['phase'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            reason=data['reason']
        )


class FileTracker:
    """Tracks and logs file movements during migration."""
    
    def __init__(self, repo_root: Path, log_file: Optional[Path] = None):
        """
        Initialize FileTracker.
        
        Args:
            repo_root: Root directory of the repository
            log_file: Optional custom path for the movement log file
        """
        self.repo_root = repo_root
        self.log_file = log_file or (repo_root / "tools" / "restructure" / "file_movements.json")
        self.movements: List[FileMovement] = []
        self._load_movements()
    
    def _load_movements(self) -> None:
        """Load existing movements from log file."""
        if self.log_file.exists():
            try:
                data = json.loads(self.log_file.read_text(encoding='utf-8'))
                self.movements = [FileMovement.from_dict(m) for m in data]
            except Exception:
                self.movements = []
    
    def _save_movements(self) -> None:
        """Save movements to log file."""
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        data = [m.to_dict() for m in self.movements]
        self.log_file.write_text(
            json.dumps(data, indent=2),
            encoding='utf-8'
        )
    
    def log_movement(
        self,
        old_path: str,
        new_path: str,
        file_type: str,
        phase: int,
        reason: str = ""
    ) -> FileMovement:
        """
        Log a file movement operation.
        
        Args:
            old_path: Original file path relative to repo root
            new_path: New file path relative to repo root
            file_type: Type of file ('code', 'doc', 'test', 'config', 'artifact')
            phase: Migration phase number
            reason: Optional reason for the movement
            
        Returns:
            Created FileMovement record
        """
        movement = FileMovement(
            old_path=old_path,
            new_path=new_path,
            file_type=file_type,
            phase=phase,
            timestamp=datetime.now(),
            reason=reason
        )
        
        self.movements.append(movement)
        self._save_movements()
        
        return movement
    
    def log_movements_batch(self, movements: List[Dict]) -> List[FileMovement]:
        """
        Log multiple file movements at once.
        
        Args:
            movements: List of dictionaries with movement details
                      Each dict should have: old_path, new_path, file_type, phase, reason
            
        Returns:
            List of created FileMovement records
        """
        created_movements = []
        
        for movement_data in movements:
            movement = FileMovement(
                old_path=movement_data['old_path'],
                new_path=movement_data['new_path'],
                file_type=movement_data['file_type'],
                phase=movement_data['phase'],
                timestamp=datetime.now(),
                reason=movement_data.get('reason', '')
            )
            self.movements.append(movement)
            created_movements.append(movement)
        
        self._save_movements()
        return created_movements
    
    def get_movements_by_phase(self, phase: int) -> List[FileMovement]:
        """
        Get all movements for a specific phase.
        
        Args:
            phase: Migration phase number
            
        Returns:
            List of FileMovement records for the phase
        """
        return [m for m in self.movements if m.phase == phase]
    
    def get_movements_by_type(self, file_type: str) -> List[FileMovement]:
        """
        Get all movements for a specific file type.
        
        Args:
            file_type: Type of file ('code', 'doc', 'test', 'config', 'artifact')
            
        Returns:
            List of FileMovement records for the file type
        """
        return [m for m in self.movements if m.file_type == file_type]
    
    def get_movement_for_file(self, old_path: str) -> Optional[FileMovement]:
        """
        Get the movement record for a specific file.
        
        Args:
            old_path: Original file path
            
        Returns:
            FileMovement record if found, None otherwise
        """
        for movement in self.movements:
            if movement.old_path == old_path:
                return movement
        return None
    
    def get_new_path(self, old_path: str) -> Optional[str]:
        """
        Get the new path for a file given its old path.
        
        Args:
            old_path: Original file path
            
        Returns:
            New file path if found, None otherwise
        """
        movement = self.get_movement_for_file(old_path)
        return movement.new_path if movement else None
    
    def get_all_movements(self) -> List[FileMovement]:
        """
        Get all recorded movements.
        
        Returns:
            List of all FileMovement records
        """
        return self.movements.copy()
    
    def get_movements_count(self) -> int:
        """
        Get total count of recorded movements.
        
        Returns:
            Number of movements
        """
        return len(self.movements)
    
    def get_movements_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[FileMovement]:
        """
        Get movements within a date range.
        
        Args:
            start_date: Start of date range
            end_date: End of date range
            
        Returns:
            List of FileMovement records within the date range
        """
        return [
            m for m in self.movements
            if start_date <= m.timestamp <= end_date
        ]
    
    def generate_movement_report(self) -> Dict:
        """
        Generate a summary report of all movements.
        
        Returns:
            Dictionary with movement statistics
        """
        report = {
            'total_movements': len(self.movements),
            'by_phase': {},
            'by_type': {},
            'first_movement': None,
            'last_movement': None
        }
        
        # Count by phase
        for movement in self.movements:
            phase = movement.phase
            if phase not in report['by_phase']:
                report['by_phase'][phase] = 0
            report['by_phase'][phase] += 1
        
        # Count by type
        for movement in self.movements:
            file_type = movement.file_type
            if file_type not in report['by_type']:
                report['by_type'][file_type] = 0
            report['by_type'][file_type] += 1
        
        # Get first and last movements
        if self.movements:
            sorted_movements = sorted(self.movements, key=lambda m: m.timestamp)
            report['first_movement'] = sorted_movements[0].timestamp.isoformat()
            report['last_movement'] = sorted_movements[-1].timestamp.isoformat()
        
        return report
    
    def export_to_markdown(self, output_path: Path) -> None:
        """
        Export movement history to a Markdown file.
        
        Args:
            output_path: Path to output Markdown file
        """
        lines = [
            "# File Movement History",
            "",
            f"Total movements: {len(self.movements)}",
            "",
            "## Movements by Phase",
            ""
        ]
        
        # Group by phase
        phases = {}
        for movement in self.movements:
            if movement.phase not in phases:
                phases[movement.phase] = []
            phases[movement.phase].append(movement)
        
        # Write each phase
        for phase in sorted(phases.keys()):
            lines.append(f"### Phase {phase}")
            lines.append("")
            lines.append("| Old Path | New Path | Type | Reason |")
            lines.append("|----------|----------|------|--------|")
            
            for movement in phases[phase]:
                lines.append(
                    f"| {movement.old_path} | {movement.new_path} | "
                    f"{movement.file_type} | {movement.reason} |"
                )
            
            lines.append("")
        
        output_path.write_text("\n".join(lines), encoding='utf-8')
    
    def clear_movements(self) -> None:
        """Clear all recorded movements (use with caution)."""
        self.movements = []
        self._save_movements()
