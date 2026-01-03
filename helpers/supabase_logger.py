"""
Simplified Supabase Logger Module - Single Table Approach
Tracks user queries and feedback in one comprehensive table
"""

import os
import uuid
import base64
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class SupabaseLogger:
    """Manages logging of user queries and feedback to a single Supabase table"""
    
    def __init__(self):
        """Initialize Supabase client"""
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_ANON_KEY")
        
        if not self.supabase_url or not self.supabase_key:
            logger.warning("Supabase credentials not found. Supabase logging disabled.")
            self.client = None
            self.enabled = False
            return
            
        try:
            self.client = create_client(self.supabase_url, self.supabase_key)
            self.enabled = True
            logger.info("✓ Supabase logging enabled")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            self.client = None
            self.enabled = False
    
    def upload_image(self, image_base64: str, message_id: str, mime_type: str = "image/png") -> Optional[str]:
        """
        Upload an image to Supabase Storage and return the public URL.
        
        Args:
            image_base64: Base64-encoded image data
            message_id: The message ID to associate with this image
            mime_type: The MIME type of the image
            
        Returns:
            str: Public URL of the uploaded image, or None if failed
        """
        if not self.enabled:
            return None
            
        try:
            # Decode base64 to bytes
            image_bytes = base64.b64decode(image_base64)
            
            # Determine file extension from MIME type
            ext_map = {
                "image/png": "png",
                "image/jpeg": "jpg", 
                "image/gif": "gif",
                "image/webp": "webp"
            }
            extension = ext_map.get(mime_type, "png")
            
            # Generate unique filename with timestamp path for organization
            date_path = datetime.now().strftime("%Y/%m")
            filename = f"user_images/{date_path}/{message_id}.{extension}"
            
            # Upload to Supabase Storage
            self.client.storage.from_("user-uploads").upload(
                path=filename,
                file=image_bytes,
                file_options={"content-type": mime_type}
            )
            
            # Get public URL
            public_url = self.client.storage.from_("user-uploads").get_public_url(filename)
            
            logger.info(f"✓ Uploaded image to Supabase Storage: {filename}")
            return public_url
            
        except Exception as e:
            logger.error(f"Error uploading image to Supabase: {e}")
            return None

    def log_user_query(self, query_data: Dict) -> bool:
        """
        Log a user query and RAG response to Supabase
        
        Args:
            query_data: Dictionary containing:
                - message_id: str
                - session_id: str
                - user_query: str
                - rag_response: str
                - route: str (optional)
                - citations_count: int (optional)
                - latency_ms: float (optional)
                - user_identifier: str (optional)
                - image_url: str (optional) - URL to uploaded image in Supabase Storage
                
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.enabled:
            return False
            
        try:
            # Prepare interaction record
            interaction_record = {
                "message_id": query_data["message_id"],
                "session_id": query_data["session_id"],
                "user_identifier": query_data.get("user_identifier"),
                "user_query": query_data["user_query"],
                "rag_response": query_data["rag_response"],
                "route": query_data.get("route"),
                "citations_count": query_data.get("citations_count", 0),
                "latency_ms": query_data.get("latency_ms"),
                "image_url": query_data.get("image_url")
            }
            
            # Insert interaction record
            result = self.client.table("user_interactions").insert(interaction_record).execute()
            
            if result.data:
                logger.info(f"✓ Logged query to Supabase: {query_data['message_id']}")
                return True
            else:
                logger.error("Failed to insert interaction record")
                
        except Exception as e:
            logger.error(f"Error logging query to Supabase: {e}")
            
        return False
    
    def log_feedback(self, feedback_data: Dict) -> bool:
        """
        Log user feedback to Supabase by updating the existing record
        
        Args:
            feedback_data: Dictionary containing:
                - message_id: str
                - rating: str ('positive' or 'negative')
                - comment: str (optional)
                - user_identifier: str (optional)
                
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.enabled:
            return False
            
        try:
            # Update the existing record with feedback data
            update_data = {
                "feedback_rating": feedback_data["rating"],
                "feedback_comment": feedback_data.get("comment", ""),
                "feedback_updated_at": datetime.now().isoformat()
            }
            
            # Update the record where message_id matches
            result = self.client.table("user_interactions").update(update_data).eq("message_id", feedback_data["message_id"]).execute()
            
            if result.data:
                logger.info(f"✓ Updated feedback in Supabase: {feedback_data['message_id']} - {feedback_data['rating']}")
                return True
            else:
                logger.error(f"No record found for message_id: {feedback_data['message_id']}")
                
        except Exception as e:
            logger.error(f"Error logging feedback to Supabase: {e}")
            
        return False
    
    def get_interaction_stats(self, user_identifier: str = None, days: int = 30) -> Dict:
        """
        Get comprehensive interaction statistics
        
        Args:
            user_identifier: Optional user identifier to filter by
            days: Number of days to look back
            
        Returns:
            Dictionary with interaction statistics
        """
        if not self.enabled:
            return {}
            
        try:
            # Build query with filters
            query = self.client.table("user_interactions").select("*")
            
            if user_identifier:
                query = query.eq("user_identifier", user_identifier)
            
            # Add date filter
            from datetime import datetime, timedelta
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            query = query.gte("created_at", cutoff_date)
            
            result = query.execute()
            
            if result.data:
                total_interactions = len(result.data)
                
                # Query statistics
                routes = {}
                avg_latency = 0
                total_citations = 0
                
                # Feedback statistics
                feedback_count = 0
                positive_count = 0
                negative_count = 0
                
                for interaction in result.data:
                    # Route analysis
                    route = interaction.get("route", "unknown")
                    routes[route] = routes.get(route, 0) + 1
                    
                    # Latency analysis
                    if interaction.get("latency_ms"):
                        avg_latency += interaction["latency_ms"]
                    
                    # Citations analysis
                    if interaction.get("citations_count"):
                        total_citations += interaction["citations_count"]
                    
                    # Feedback analysis
                    if interaction.get("feedback_rating"):
                        feedback_count += 1
                        if interaction["feedback_rating"] == "positive":
                            positive_count += 1
                        elif interaction["feedback_rating"] == "negative":
                            negative_count += 1
                
                avg_latency = avg_latency / total_interactions if total_interactions > 0 else 0
                satisfaction_rate = (positive_count / feedback_count * 100) if feedback_count > 0 else 0
                
                return {
                    "total_interactions": total_interactions,
                    "total_queries": total_interactions,  # Same as interactions
                    "total_feedback": feedback_count,
                    "routes": routes,
                    "avg_latency_ms": round(avg_latency, 2),
                    "total_citations": total_citations,
                    "avg_citations": round(total_citations / total_interactions, 2) if total_interactions > 0 else 0,
                    "feedback_stats": {
                        "positive": positive_count,
                        "negative": negative_count,
                        "satisfaction_rate": round(satisfaction_rate, 2)
                    },
                    "days": days
                }
                
        except Exception as e:
            logger.error(f"Error getting interaction stats: {e}")
            
        return {}
    
    def get_recent_interactions(self, limit: int = 50, user_identifier: str = None) -> List[Dict]:
        """
        Get recent interactions with optional user filtering
        
        Args:
            limit: Maximum number of interactions to return
            user_identifier: Optional user identifier to filter by
            
        Returns:
            List of interaction records
        """
        if not self.enabled:
            return []
            
        try:
            query = self.client.table("user_interactions").select("*").order("created_at", desc=True).limit(limit)
            
            if user_identifier:
                query = query.eq("user_identifier", user_identifier)
            
            result = query.execute()
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error getting recent interactions: {e}")
            return []
    
    def get_user_summary(self, user_identifier: str, days: int = 30) -> Dict:
        """
        Get a comprehensive summary for a specific user
        
        Args:
            user_identifier: User identifier to get summary for
            days: Number of days to look back
            
        Returns:
            Dictionary with user summary
        """
        if not self.enabled:
            return {}
            
        try:
            # Get stats for this user
            stats = self.get_interaction_stats(user_identifier, days)
            
            # Get recent interactions
            recent = self.get_recent_interactions(10, user_identifier)
            
            return {
                "user_identifier": user_identifier,
                "stats": stats,
                "recent_interactions": recent,
                "summary_date": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting user summary: {e}")
            return {}


# Global instance
_supabase_logger = None

def get_supabase_logger() -> SupabaseLogger:
    """Get the global Supabase logger instance"""
    global _supabase_logger
    if _supabase_logger is None:
        _supabase_logger = SupabaseLogger()
    return _supabase_logger
