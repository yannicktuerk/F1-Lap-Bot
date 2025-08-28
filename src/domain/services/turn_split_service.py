"""Per-turn split calculation and reference model (Issue 11)."""
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

from src.domain.entities.telemetry_sample import TelemetrySample
from src.domain.value_objects.position import Position

logger = logging.getLogger(__name__)


class Track(Enum):
    """F1 Track identifiers."""
    SILVERSTONE = 0
    MONZA = 1
    BAHRAIN = 3
    CHINA = 4
    SPA = 7
    MONACO = 8
    MONTREAL = 9
    BRITAIN = 10
    GERMANY = 11
    HUNGARY = 12
    VALENCIA = 13
    SINGAPORE = 15
    SUZUKA = 16
    ABU_DHABI = 17
    BRAZIL = 18
    AUSTRIA = 19
    RUSSIA = 20
    MEXICO = 21
    BAKU = 22
    SAKHIR_SHORT = 23
    SILVERSTONE_SHORT = 24
    HANOI = 25
    ZANDVOORT = 26
    IMOLA = 27
    PORTIMAO = 28
    JEDDAH = 29
    MIAMI = 30
    LAS_VEGAS = 31
    LOSAIL = 32


@dataclass
class TurnDefinition:
    """Definition of a turn on a track."""
    turn_id: int
    track: Track
    entry_distance: float  # meters from start/finish line
    exit_distance: float   # meters from start/finish line
    name: str
    sector: int


@dataclass 
class TurnSplit:
    """Split time for a specific turn."""
    turn_id: int
    split_time: float  # seconds
    reference_time: float  # reference median time
    delta: float  # split_time - reference_time
    lap_number: int
    timestamp: float


class TurnCatalog:
    """Catalog of turns for each track."""
    
    def __init__(self):
        """Initialize turn catalog with predefined turn definitions."""
        self._turns: Dict[Track, List[TurnDefinition]] = {}
        self._initialize_turns()
    
    def _initialize_turns(self) -> None:
        """Initialize predefined turn definitions for tracks."""
        # Silverstone (example track with major corners)
        self._turns[Track.SILVERSTONE] = [
            TurnDefinition(1, Track.SILVERSTONE, 750, 950, "Copse", 1),
            TurnDefinition(2, Track.SILVERSTONE, 1200, 1400, "Maggotts", 1),
            TurnDefinition(3, Track.SILVERSTONE, 1400, 1600, "Becketts", 1),
            TurnDefinition(4, Track.SILVERSTONE, 2800, 3000, "Stowe", 2),
            TurnDefinition(5, Track.SILVERSTONE, 3200, 3400, "Vale", 2),
            TurnDefinition(6, Track.SILVERSTONE, 3400, 3600, "Club", 2),
            TurnDefinition(7, Track.SILVERSTONE, 4200, 4400, "Abbey", 3),
            TurnDefinition(8, Track.SILVERSTONE, 4800, 5000, "Farm", 3),
            TurnDefinition(9, Track.SILVERSTONE, 5200, 5400, "Village", 3),
        ]
        
        # Monza (example)
        self._turns[Track.MONZA] = [
            TurnDefinition(1, Track.MONZA, 700, 900, "Variante del Rettifilo", 1),
            TurnDefinition(2, Track.MONZA, 1800, 2000, "Curva Biassono", 1),
            TurnDefinition(3, Track.MONZA, 2800, 3000, "Lesmo 1", 2),
            TurnDefinition(4, Track.MONZA, 3000, 3200, "Lesmo 2", 2),
            TurnDefinition(5, Track.MONZA, 4200, 4400, "Ascari", 2),
            TurnDefinition(6, Track.MONZA, 5000, 5200, "Parabolica", 3),
        ]
        
        # Add more tracks as needed
        # For now, provide basic generic turn detection
    
    def get_turns(self, track: Track) -> List[TurnDefinition]:
        """Get all turns for a track."""
        return self._turns.get(track, [])
    
    def get_turn_by_distance(self, track: Track, distance: float) -> Optional[TurnDefinition]:
        """Get turn at a specific distance on track."""
        turns = self.get_turns(track)
        for turn in turns:
            if turn.entry_distance <= distance <= turn.exit_distance:
                return turn
        return None
    
    def detect_turns_from_telemetry(self, track: Track, samples: List[TelemetrySample], 
                                   turn_threshold: float = 50.0) -> List[TurnDefinition]:
        """Detect turns dynamically from telemetry if not predefined."""
        if track in self._turns:
            return self._turns[track]
        
        # Dynamic turn detection based on steering angle and speed changes
        detected_turns = []
        turn_id = 1
        
        for i in range(1, len(samples) - 1):
            current = samples[i]
            prev = samples[i-1]
            next_sample = samples[i+1] if i+1 < len(samples) else samples[i]
            
            # Detect significant steering input + speed reduction
            steering_delta = abs(current.motion_data.steer - prev.motion_data.steer)
            speed_reduction = prev.motion_data.speed - current.motion_data.speed
            
            if steering_delta > 0.2 and speed_reduction > 10:  # Significant turn
                # Find entry and exit points
                entry_distance = max(0, current.lap_data.lap_distance - turn_threshold)
                exit_distance = current.lap_data.lap_distance + turn_threshold
                
                turn = TurnDefinition(
                    turn_id=turn_id,
                    track=track,
                    entry_distance=entry_distance,
                    exit_distance=exit_distance,
                    name=f"Turn {turn_id}",
                    sector=current.lap_data.sector
                )
                detected_turns.append(turn)
                turn_id += 1
        
        self._turns[track] = detected_turns
        return detected_turns


class PerTurnSplitCalculator:
    """Calculates per-turn splits from telemetry data."""
    
    def __init__(self, turn_catalog: TurnCatalog):
        """Initialize with turn catalog."""
        self.turn_catalog = turn_catalog
        self._reference_times: Dict[Tuple[Track, int], float] = {}  # (track, turn_id) -> median time
    
    def calculate_turn_splits(self, samples: List[TelemetrySample], 
                            track: Track) -> List[TurnSplit]:
        """Calculate split times for all turns in a lap."""
        if not samples:
            return []
        
        turns = self.turn_catalog.get_turns(track)
        if not turns:
            # Try dynamic detection
            turns = self.turn_catalog.detect_turns_from_telemetry(track, samples)
        
        splits = []
        lap_number = samples[0].lap_data.current_lap_num if samples else 0
        
        for turn in turns:
            split = self._calculate_turn_split(samples, turn, lap_number)
            if split:
                splits.append(split)
        
        return splits
    
    def _calculate_turn_split(self, samples: List[TelemetrySample], 
                            turn: TurnDefinition, lap_number: int) -> Optional[TurnSplit]:
        """Calculate split time for a specific turn."""
        entry_sample = None
        exit_sample = None
        
        # Find entry and exit samples
        for sample in samples:
            distance = sample.lap_data.lap_distance
            
            if turn.entry_distance <= distance <= turn.entry_distance + 20 and not entry_sample:
                entry_sample = sample
            
            if turn.exit_distance - 20 <= distance <= turn.exit_distance:
                exit_sample = sample
        
        if not entry_sample or not exit_sample:
            return None
        
        # Calculate turn time
        turn_time = exit_sample.lap_data.current_lap_time - entry_sample.lap_data.current_lap_time
        if turn_time <= 0:
            return None
        
        # Get reference time (median)
        reference_key = (turn.track, turn.turn_id)
        reference_time = self._reference_times.get(reference_key, turn_time)
        
        delta = turn_time - reference_time
        
        return TurnSplit(
            turn_id=turn.turn_id,
            split_time=turn_time,
            reference_time=reference_time,
            delta=delta,
            lap_number=lap_number,
            timestamp=entry_sample.session_time
        )
    
    def update_reference_times(self, splits: List[TurnSplit], track: Track) -> None:
        """Update reference times with new split data."""
        # Group splits by turn
        turn_splits: Dict[int, List[float]] = {}
        
        for split in splits:
            if split.turn_id not in turn_splits:
                turn_splits[split.turn_id] = []
            turn_splits[split.turn_id].append(split.split_time)
        
        # Calculate median for each turn
        for turn_id, times in turn_splits.items():
            if len(times) >= 3:  # Need minimum data points
                times.sort()
                median_time = times[len(times) // 2]
                reference_key = (track, turn_id)
                self._reference_times[reference_key] = median_time
                
                logger.debug(f"Updated reference time for {track.name} Turn {turn_id}: {median_time:.3f}s")
    
    def get_reference_time(self, track: Track, turn_id: int) -> Optional[float]:
        """Get reference time for a specific turn."""
        return self._reference_times.get((track, turn_id))
    
    def aggregate_to_sector(self, splits: List[TurnSplit], track: Track) -> Dict[int, float]:
        """Aggregate turn splits to sector deltas."""
        turns = self.turn_catalog.get_turns(track)
        sector_deltas = {1: 0.0, 2: 0.0, 3: 0.0}
        
        for split in splits:
            # Find turn definition to get sector
            turn_def = next((t for t in turns if t.turn_id == split.turn_id), None)
            if turn_def:
                sector_deltas[turn_def.sector] += split.delta
        
        return sector_deltas
    
    def aggregate_to_lap(self, splits: List[TurnSplit]) -> float:
        """Aggregate turn splits to total lap delta."""
        return sum(split.delta for split in splits)


class RewardService:
    """Service for computing bandit rewards from per-turn splits."""
    
    def __init__(self, split_calculator: PerTurnSplitCalculator):
        """Initialize reward service."""
        self.split_calculator = split_calculator
    
    def compute_turn_reward(self, current_splits: List[TurnSplit], 
                          previous_splits: List[TurnSplit],
                          coached_turn_id: int) -> float:
        """Compute reward for a specific turn based on improvement."""
        current_split = next((s for s in current_splits if s.turn_id == coached_turn_id), None)
        previous_split = next((s for s in previous_splits if s.turn_id == coached_turn_id), None)
        
        if not current_split or not previous_split:
            return 0.0  # No reward if data missing
        
        # Positive reward for improvement (negative delta is better)
        improvement = previous_split.delta - current_split.delta
        
        # Normalize reward: +1 for 100ms improvement, -1 for 100ms degradation
        reward = improvement / 0.1  # 100ms = 0.1 seconds
        
        # Clamp reward to reasonable range
        return max(-2.0, min(2.0, reward))
    
    def compute_sector_reward(self, current_splits: List[TurnSplit],
                            previous_splits: List[TurnSplit],
                            track: Track, sector: int) -> float:
        """Compute reward for a sector based on improvement."""
        current_sector = self.split_calculator.aggregate_to_sector(current_splits, track)
        previous_sector = self.split_calculator.aggregate_to_sector(previous_splits, track)
        
        improvement = previous_sector.get(sector, 0.0) - current_sector.get(sector, 0.0)
        
        # Normalize: +1 for 200ms sector improvement
        reward = improvement / 0.2
        
        return max(-2.0, min(2.0, reward))
    
    def compute_lap_reward(self, current_splits: List[TurnSplit],
                         previous_splits: List[TurnSplit]) -> float:
        """Compute reward for overall lap improvement."""
        current_total = self.split_calculator.aggregate_to_lap(current_splits)
        previous_total = self.split_calculator.aggregate_to_lap(previous_splits)
        
        improvement = previous_total - current_total
        
        # Normalize: +1 for 500ms lap improvement  
        reward = improvement / 0.5
        
        return max(-2.0, min(2.0, reward))