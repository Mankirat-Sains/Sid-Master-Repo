"""
Custom logging handler that captures logs into thinking_log format
Intercepts existing log messages and converts them to human-readable thinking logs
"""
import logging
import re
from typing import List
from .trace import ExecutionTrace

class ThinkingLogHandler(logging.Handler):
    """Logging handler that captures logs and converts to thinking_log"""
    
    def __init__(self, trace: ExecutionTrace):
        super().__init__()
        self.trace = trace
        self.setLevel(logging.INFO)  # Capture INFO and above
    
    def emit(self, record):
        """Convert log record to thinking log entry"""
        message = record.getMessage()
        
        # Skip certain log messages (too verbose)
        skip_patterns = [
            r'^>>>',
            r'^<<<',
            r'^\d+\.\d+s',
            r'^\[',
        ]
        
        if any(re.match(pattern, message) for pattern in skip_patterns):
            return
        
        # Convert log messages to thinking log format
        thinking_entry = self._format_thinking_log(record.name, message)
        if thinking_entry:
            self.trace.add_thinking(thinking_entry)
    
    def _format_thinking_log(self, logger_name: str, message: str) -> str:
        """Format log message as thinking log entry"""
        # Map logger names to categories
        category_map = {
            "QUERY_FLOW": "Query Processing",
            "ROUTING": "Routing Decision",
            "DATABASE": "Database Query",
            "SYNTHESIS": "Answer Synthesis",
            "VLM": "Image Processing"
        }
        
        category = category_map.get(logger_name, "System")
        
        # Extract key information from common log patterns
        if "PLAN" in message.upper():
            if "START" in message.upper():
                return f"## 📋 Planning Query\n\nAnalyzing your query to create an execution plan..."
            elif "DONE" in message.upper() or "COMPLETE" in message.upper():
                return f"## ✅ Planning Complete\n\nQuery plan generated successfully"
            elif "REASONING" in message.upper():
                reasoning = message.split("Reasoning:")[-1].strip()
                return f"**Planning Reasoning:** {reasoning}"
            elif "STEP" in message.upper():
                return f"**Plan Step:** {message}"
        
        if "RETRIEVE" in message.upper():
            if "START" in message.upper():
                return f"## 📚 Retrieving Documents\n\nSearching vector database for relevant documents..."
            elif "DONE" in message.upper() or "COMPLETE" in message.upper():
                return f"## ✅ Retrieval Complete\n\nDocuments retrieved successfully"
            elif "CHUNKS" in message.upper() or "DOCS" in message.upper():
                # Extract numbers
                numbers = re.findall(r'\d+', message)
                if numbers:
                    return f"**Retrieved:** {numbers[0]} document chunks"
        
        if "GRADE" in message.upper() or "RELEVANCE" in message.upper():
            return f"## 🎯 Grading Relevance\n\nEvaluating document relevance to your query..."
        
        if "ANSWER" in message.upper() or "SYNTHESIS" in message.upper():
            if "START" in message.upper():
                return f"## ✨ Generating Answer\n\nSynthesizing answer from retrieved documents..."
            elif "DONE" in message.upper() or "COMPLETE" in message.upper():
                return f"## ✅ Answer Generated\n\nAnswer synthesized successfully"
        
        if "ROUTER" in message.upper() or "ROUTE" in message.upper():
            if "DECISION" in message.upper():
                route = message.split("→")[-1].strip() if "→" in message else "smart"
                return f"**Routing Decision:** Using {route} chunk database"
        
        # Default: return formatted message
        if len(message) > 200:
            return f"**{category}:** {message[:200]}..."
        return f"**{category}:** {message}"