"""Memory manager using Mem0 for persistent health history.

This module provides persistent memory for Dr. Aunty using Mem0 AI:
- Stores all health reports and conversations
- Enables context-aware responses
- Tracks health trends over time
- Remembers user-specific health information

Why Mem0:
    Unlike simple vector databases, Mem0 understands semantic relationships
    between health records, enabling intelligent trend detection and 
    context-aware conversations.

Example:
    "Your cholesterol went from 5.8 to 6.2 - that's 7% higher!"
    (Mem0 automatically retrieves and compares past reports)
"""
from typing import List, Dict, Any
from mem0 import MemoryClient
import config


class HealthMemoryManager:
    """Manages persistent health history using Mem0 AI.
    
    This class provides intelligent memory for Dr. Aunty:
    - Stores health reports with semantic understanding
    - Retrieves relevant context for conversations
    - Tracks trends across multiple reports
    - Enables personalized health advice
    
    Unlike traditional databases, Mem0 understands the meaning
    of health data and can find relevant context automatically.
    """
    
    def __init__(self):
        """Initialize Mem0 client."""
        try:
            self.client = MemoryClient(api_key=config.MEM0_API_KEY)
        except Exception as e:
            print(f"Error initializing Mem0: {e}")
            self.client = None
    
    def add_health_record(
        self, 
        user_id: str, 
        lab_data: Dict[str, Any],
        analysis: str
    ) -> bool:
        """Add a new health record to memory.
        
        Args:
            user_id: Telegram user ID
            lab_data: Extracted lab report data
            analysis: Dr. Aunty's analysis
            
        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            return False
        
        try:
            # Create memory message
            memory_text = f"""
            Health Report Date: {lab_data.get('test_date', 'Unknown')}
            
            Test Results:
            """
            
            # Add test results
            for test in lab_data.get('tests', []):
                memory_text += f"\n- {test['name']}: {test['value']} {test['unit']} ({test['status']})"
            
            memory_text += f"\n\nDr. Aunty's Analysis: {analysis}"
            
            # Store in Mem0
            self.client.add(
                messages=[{"role": "user", "content": memory_text}],
                user_id=user_id
            )
            
            return True
            
        except Exception as e:
            print(f"Error adding to memory: {e}")
            return False
    
    def get_health_history(self, user_id: str, limit: int = 5) -> str:
        """Retrieve user's health history.
        
        Args:
            user_id: Telegram user ID
            limit: Number of recent records to retrieve
            
        Returns:
            Formatted health history string
        """
        if not self.client:
            return "No previous health records available."
        
        try:
            # Search for user's health memories with required filters
            memories = self.client.search(
                query="health reports and lab test results",
                user_id=user_id,
                limit=limit,
                filters={"user_id": user_id}  # Required filters parameter for v2 API
            )
            
            if not memories:
                return "No previous health records found."
            
            # Format memories - handle both v1 and v2 response formats
            history = "Previous Health Records:\n\n"
            if isinstance(memories, dict):
                # v2 API returns dict with 'results' key
                results = memories.get('results', [])
                for i, memory in enumerate(results, 1):
                    memory_text = memory.get('memory', memory.get('text', ''))
                    history += f"{i}. {memory_text}\n\n"
            elif isinstance(memories, list):
                # v1 API returns list
                for i, memory in enumerate(memories, 1):
                    memory_text = memory.get('memory', memory.get('text', ''))
                    history += f"{i}. {memory_text}\n\n"
            
            return history
            
        except Exception as e:
            print(f"Error retrieving memory: {e}")
            return "No previous health records available."
    
    def get_all_memories(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all memories for a user.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            List of memory dictionaries
        """
        if not self.client:
            return []
        
        try:
            memories = self.client.get_all(user_id=user_id)
            return memories if memories else []
        except Exception as e:
            print(f"Error getting all memories: {e}")
            return []
    
    def add_conversation(
        self, 
        user_id: str, 
        user_message: str, 
        bot_response: str
    ) -> bool:
        """Add a conversation to memory.
        
        Args:
            user_id: Telegram user ID
            user_message: User's message
            bot_response: Bot's response
            
        Returns:
            True if successful
        """
        if not self.client:
            return False
        
        try:
            self.client.add(
                messages=[
                    {"role": "user", "content": user_message},
                    {"role": "assistant", "content": bot_response}
                ],
                user_id=user_id
            )
            return True
        except Exception as e:
            print(f"Error adding conversation: {e}")
            return False

