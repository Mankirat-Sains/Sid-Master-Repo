#!/usr/bin/env python3
"""
Progress Streaming System
=========================

Provides real-time progress updates during Agent Mode execution so users can
follow along with the engineering design process step-by-step.

This module enables:
- Live status updates to frontend
- Step-by-step engineering narrative
- Progress tracking with timestamps
- User engagement during long-running operations
"""

import asyncio
import json
import logging
import time
from typing import Dict, Any, List, Callable, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


logger = logging.getLogger("ProgressStreaming")


# ============================================================================
# PROGRESS EVENT TYPES
# ============================================================================

class EventType(Enum):
    """Types of progress events"""
    STATUS = "status"              # General status update
    STAGE_START = "stage_start"    # Starting a new stage
    STAGE_COMPLETE = "stage_complete"  # Stage completed
    TOOL_START = "tool_start"      # Starting a tool operation
    TOOL_COMPLETE = "tool_complete"  # Tool operation completed
    CHECK = "check"                # Engineering check result
    DECISION = "decision"          # Engineering decision made
    WARNING = "warning"            # Warning or concern
    SUCCESS = "success"            # Success message
    ERROR = "error"                # Error message
    PROGRESS = "progress"          # Progress percentage


# ============================================================================
# PROGRESS EVENT
# ============================================================================

@dataclass
class ProgressEvent:
    """Represents a single progress event"""
    event_type: EventType
    message: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    data: Dict[str, Any] = field(default_factory=dict)
    progress_percent: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "type": self.event_type.value,
            "message": self.message,
            "timestamp": self.timestamp,
            "data": self.data,
            "progress": self.progress_percent
        }
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict())


# ============================================================================
# PROGRESS STREAMER
# ============================================================================

class ProgressStreamer:
    """
    Manages progress event streaming during agent execution
    
    This class collects progress events and streams them to registered callbacks
    (e.g., SSE endpoints, websockets, or local logging)
    """
    
    def __init__(self):
        self.events: List[ProgressEvent] = []
        self.callbacks: List[Callable] = []
        self.start_time = time.time()
        self.is_streaming = False
        
    def register_callback(self, callback: Callable):
        """
        Register a callback function to receive progress events
        
        Callback signature: callback(event: ProgressEvent)
        """
        self.callbacks.append(callback)
        logger.info(f"📡 Registered streaming callback: {callback.__name__}")
    
    def emit(self, event: ProgressEvent):
        """Emit a progress event to all registered callbacks"""
        self.events.append(event)
        
        # Call all registered callbacks
        for callback in self.callbacks:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"❌ Callback {callback.__name__} failed: {e}")
    
    def status(self, message: str, **kwargs):
        """Emit a status update"""
        event = ProgressEvent(
            event_type=EventType.STATUS,
            message=message,
            data=kwargs
        )
        self.emit(event)
        logger.info(f"📊 {message}")
    
    def stage_start(self, stage_name: str, description: str = ""):
        """Emit stage start event"""
        event = ProgressEvent(
            event_type=EventType.STAGE_START,
            message=f"▶️ {stage_name}",
            data={"stage": stage_name, "description": description}
        )
        self.emit(event)
        logger.info(f"▶️ STAGE START: {stage_name}")
    
    def stage_complete(self, stage_name: str, result: str = ""):
        """Emit stage complete event"""
        event = ProgressEvent(
            event_type=EventType.STAGE_COMPLETE,
            message=f"✅ {stage_name} complete",
            data={"stage": stage_name, "result": result}
        )
        self.emit(event)
        logger.info(f"✅ STAGE COMPLETE: {stage_name}")
    
    def tool_start(self, tool_name: str, params: Dict[str, Any]):
        """Emit tool start event"""
        event = ProgressEvent(
            event_type=EventType.TOOL_START,
            message=f"🔧 Executing {tool_name}...",
            data={"tool": tool_name, "params": params}
        )
        self.emit(event)
        logger.info(f"🔧 TOOL START: {tool_name}")
    
    def tool_complete(self, tool_name: str, success: bool, result: Any = None):
        """Emit tool complete event"""
        status = "✅" if success else "❌"
        event = ProgressEvent(
            event_type=EventType.TOOL_COMPLETE,
            message=f"{status} {tool_name} {'completed' if success else 'failed'}",
            data={"tool": tool_name, "success": success, "result": result}
        )
        self.emit(event)
        logger.info(f"{status} TOOL COMPLETE: {tool_name}")
    
    def engineering_check(
        self,
        check_type: str,
        ratio: float,
        status: str,
        code_clause: str = ""
    ):
        """Emit engineering check result"""
        status_symbol = "✅" if status == "pass" else "⚠️"
        message = (
            f"{status_symbol} {check_type.capitalize()}: "
            f"{ratio:.2f} ({ratio*100:.0f}% utilization)"
        )
        if code_clause:
            message += f" [{code_clause}]"
        
        event = ProgressEvent(
            event_type=EventType.CHECK,
            message=message,
            data={
                "check_type": check_type,
                "ratio": ratio,
                "status": status,
                "code_clause": code_clause
            }
        )
        self.emit(event)
        logger.info(f"📊 CHECK: {message}")
    
    def engineering_decision(self, decision: str, reasoning: str):
        """Emit engineering decision"""
        event = ProgressEvent(
            event_type=EventType.DECISION,
            message=f"🎯 Decision: {decision}",
            data={"decision": decision, "reasoning": reasoning}
        )
        self.emit(event)
        logger.info(f"🎯 DECISION: {decision}")
        logger.info(f"   Reasoning: {reasoning}")
    
    def warning(self, message: str):
        """Emit warning"""
        event = ProgressEvent(
            event_type=EventType.WARNING,
            message=f"⚠️ {message}",
            data={}
        )
        self.emit(event)
        logger.warning(f"⚠️ WARNING: {message}")
    
    def success(self, message: str):
        """Emit success message"""
        event = ProgressEvent(
            event_type=EventType.SUCCESS,
            message=f"✅ {message}",
            data={}
        )
        self.emit(event)
        logger.info(f"✅ SUCCESS: {message}")
    
    def error(self, message: str, error_details: str = ""):
        """Emit error message"""
        event = ProgressEvent(
            event_type=EventType.ERROR,
            message=f"❌ {message}",
            data={"error": error_details}
        )
        self.emit(event)
        logger.error(f"❌ ERROR: {message}")
    
    def progress(self, percent: float, message: str = ""):
        """Emit progress percentage"""
        event = ProgressEvent(
            event_type=EventType.PROGRESS,
            message=message or f"Progress: {percent:.0f}%",
            progress_percent=percent
        )
        self.emit(event)
    
    def get_elapsed_time(self) -> float:
        """Get elapsed time since streamer started"""
        return time.time() - self.start_time
    
    def get_all_events(self) -> List[Dict[str, Any]]:
        """Get all events as dictionaries"""
        return [event.to_dict() for event in self.events]
    
    def clear(self):
        """Clear all events"""
        self.events = []
        self.start_time = time.time()


# ============================================================================
# GLOBAL STREAMER INSTANCE
# ============================================================================

# Global streamer for easy access
_global_streamer: Optional[ProgressStreamer] = None


def get_progress_streamer() -> ProgressStreamer:
    """Get or create the global progress streamer"""
    global _global_streamer
    if _global_streamer is None:
        _global_streamer = ProgressStreamer()
    return _global_streamer


def reset_progress_streamer():
    """Reset the global progress streamer"""
    global _global_streamer
    _global_streamer = None


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def stream_status(message: str, **kwargs):
    """Convenience function to emit status"""
    get_progress_streamer().status(message, **kwargs)


def stream_stage_start(stage_name: str, description: str = ""):
    """Convenience function to emit stage start"""
    get_progress_streamer().stage_start(stage_name, description)


def stream_stage_complete(stage_name: str, result: str = ""):
    """Convenience function to emit stage complete"""
    get_progress_streamer().stage_complete(stage_name, result)


def stream_tool(tool_name: str, params: Dict[str, Any]):
    """Convenience function to emit tool start"""
    get_progress_streamer().tool_start(tool_name, params)


def stream_check(check_type: str, ratio: float, status: str, code_clause: str = ""):
    """Convenience function to emit engineering check"""
    get_progress_streamer().engineering_check(check_type, ratio, status, code_clause)


def stream_decision(decision: str, reasoning: str):
    """Convenience function to emit engineering decision"""
    get_progress_streamer().engineering_decision(decision, reasoning)


def stream_warning(message: str):
    """Convenience function to emit warning"""
    get_progress_streamer().warning(message)


def stream_success(message: str):
    """Convenience function to emit success"""
    get_progress_streamer().success(message)


def stream_error(message: str, error_details: str = ""):
    """Convenience function to emit error"""
    get_progress_streamer().error(message, error_details)


# ============================================================================
# EXAMPLE ENGINEERING DESIGN STREAM
# ============================================================================

def example_design_stream():
    """
    Example of how the engineering workflow would use the streaming system
    """
    streamer = get_progress_streamer()
    
    # Stage 1: Load Takeoff
    streamer.stage_start("Load Takeoff", "Gathering design loads")
    streamer.status("Analyzing load cases...")
    time.sleep(0.5)
    streamer.status("Dead load: 1.5 kN/m²")
    time.sleep(0.3)
    streamer.status("Live load: 2.4 kN/m²")
    time.sleep(0.3)
    streamer.stage_complete("Load Takeoff", "Loads determined")
    
    # Stage 2: Preliminary Sizing
    streamer.stage_start("Preliminary Sizing", "Selecting initial member")
    streamer.status("Initial size: W250x33")
    time.sleep(0.5)
    streamer.tool_start("WRITE_CELL", {"cell": "E5", "value": 8})
    time.sleep(0.3)
    streamer.tool_complete("WRITE_CELL", True)
    streamer.tool_start("RECALC", {})
    time.sleep(0.5)
    streamer.tool_complete("RECALC", True)
    streamer.stage_complete("Preliminary Sizing")
    
    # Stage 3: Strength Check
    streamer.stage_start("Strength Check", "Evaluating capacity ratios")
    streamer.tool_start("READ_CELL", {"cell": "G25"})
    time.sleep(0.3)
    streamer.tool_complete("READ_CELL", True, "0.92")
    streamer.engineering_check("moment", 0.92, "warning", "CSA S16-19 Clause 13.5")
    time.sleep(0.3)
    streamer.tool_start("READ_CELL", {"cell": "H25"})
    time.sleep(0.3)
    streamer.tool_complete("READ_CELL", True, "0.65")
    streamer.engineering_check("shear", 0.65, "pass", "CSA S16-19 Clause 13.4")
    time.sleep(0.3)
    streamer.stage_complete("Strength Check", "Moment ratio high")
    
    # Stage 4: Optimization
    streamer.stage_start("Optimization", "Adjusting member size")
    streamer.engineering_decision(
        "Upsize to W310x39",
        "Moment ratio 0.92 exceeds optimal range (75-85%). Increasing section for improved safety margin per CSA S16-19."
    )
    time.sleep(0.5)
    streamer.tool_start("WRITE_CELL", {"cell": "F15", "value": "W310x39"})
    time.sleep(0.3)
    streamer.tool_complete("WRITE_CELL", True)
    streamer.tool_start("RECALC", {})
    time.sleep(0.5)
    streamer.tool_complete("RECALC", True)
    
    # Re-check
    streamer.tool_start("READ_CELL", {"cell": "G25"})
    time.sleep(0.3)
    streamer.tool_complete("READ_CELL", True, "0.78")
    streamer.engineering_check("moment", 0.78, "pass", "CSA S16-19 Clause 13.5")
    time.sleep(0.3)
    streamer.stage_complete("Optimization", "Design converged")
    
    # Final Stage
    streamer.stage_start("Final Verification", "Confirming design")
    streamer.status("Final member: W310x39")
    time.sleep(0.3)
    streamer.status("Maximum utilization: 78%")
    time.sleep(0.3)
    streamer.success("Design is optimal and code-compliant!")
    time.sleep(0.3)
    streamer.stage_complete("Final Verification")
    
    return streamer.get_all_events()


if __name__ == "__main__":
    # Test the streaming system
    print("🧪 Testing Progress Streaming System\n")
    
    events = example_design_stream()
    
    print("\n" + "="*80)
    print("CAPTURED EVENTS")
    print("="*80 + "\n")
    
    for event in events:
        print(f"{event['timestamp'][:19]} | {event['type']:15} | {event['message']}")
    
    print(f"\nTotal events: {len(events)}")

