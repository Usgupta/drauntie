"""Database manager using Supabase PostgreSQL.

This module handles all database operations for Dr. Aunty:
- User management and profiles
- Health report storage (with JSONB for complex data)
- Caregiver relationships (Family Connect feature)
- Video/audio summary tracking

Database Schema:
    - users: User profiles and Telegram IDs
    - health_reports: Lab reports with structured JSONB data
    - caregivers: Family caregiver connections
    - video_summaries: Generated media content

All tables use Row Level Security (RLS) for data protection.
"""
from datetime import datetime
from typing import Dict, Any, List, Optional
from supabase import create_client, Client
import config


class HealthDatabase:
    """Manages health data storage in Supabase PostgreSQL.
    
    Provides methods for:
    - User registration and lookup
    - Health report storage and retrieval
    - Family caregiver connections
    - Video/audio summary tracking
    
    Uses Supabase's real-time PostgreSQL database with:
    - Automatic REST API generation
    - Row Level Security (RLS)
    - JSONB support for complex lab data
    """
    
    def __init__(self):
        """Initialize Supabase client."""
        try:
            self.client: Client = create_client(
                config.SUPABASE_URL, 
                config.SUPABASE_KEY
            )
        except Exception as e:
            print(f"Error initializing Supabase: {e}")
            self.client = None
    
    def create_tables(self):
        """Create necessary database tables if they don't exist.
        
        Note: Run setup_database.sql in your Supabase SQL Editor.
        This creates all tables, indexes, and RLS policies.
        """
        print("⚠️  Please run setup_database.sql in your Supabase SQL Editor")
    
    def add_user(
        self, 
        telegram_id: int, 
        username: str = None, 
        first_name: str = None
    ) -> bool:
        """Add or update user in database.
        
        Args:
            telegram_id: Telegram user ID
            username: Telegram username
            first_name: User's first name
            
        Returns:
            True if successful
        """
        if not self.client:
            return False
        
        try:
            data = {
                "telegram_id": telegram_id,
                "username": username,
                "first_name": first_name
            }
            
            # Upsert user (insert or update)
            self.client.table("users").upsert(data).execute()
            return True
            
        except Exception as e:
            error_msg = str(e)
            if "PGRST205" in error_msg or "Could not find the table" in error_msg:
                print("\n" + "="*60)
                print("⚠️  SUPABASE TABLE NOT FOUND ERROR")
                print("="*60)
                print("The 'users' table doesn't exist in your Supabase database.")
                print("\n📝 TO FIX THIS:")
                print("1. Open your Supabase dashboard: https://supabase.com/dashboard")
                print("2. Go to SQL Editor")
                print("3. Run the SQL script from: setup_database.sql")
                print("4. Restart this bot")
                print("="*60 + "\n")
            elif "42501" in error_msg or "row-level security policy" in error_msg:
                print("\n⚠️  SUPABASE RLS POLICY ERROR: Row Level Security is blocking access.")
                print("📝 Run: setup_database.sql in your Supabase SQL Editor\n")
            else:
                print(f"Error adding user: {e}")
            return False
    
    def save_health_report(
        self,
        telegram_id: int,
        lab_data: Dict[str, Any],
        analysis: str,
        response_time: float
    ) -> Optional[int]:
        """Save health report to database.
        
        Args:
            telegram_id: Telegram user ID
            lab_data: Extracted lab data
            analysis: Dr. Aunty's analysis
            response_time: Analysis response time
            
        Returns:
            Report ID if successful, None otherwise
        """
        if not self.client:
            return None
        
        try:
            data = {
                "telegram_id": telegram_id,
                "test_date": lab_data.get("test_date"),
                "lab_data": lab_data,
                "analysis": analysis,
                "response_time": response_time
            }
            
            result = self.client.table("health_reports").insert(data).execute()
            
            if result.data:
                return result.data[0].get("id")
            return None
            
        except Exception as e:
            error_msg = str(e)
            if "PGRST205" in error_msg or "Could not find the table" in error_msg:
                print("\n" + "="*60)
                print("⚠️  SUPABASE TABLE NOT FOUND ERROR")
                print("="*60)
                print("The 'health_reports' table doesn't exist in your Supabase database.")
                print("\n📝 TO FIX THIS:")
                print("1. Open your Supabase dashboard")
                print("2. Go to SQL Editor")
                print("3. Run the SQL script from: setup_database.sql")
                print("4. Restart this bot")
                print("="*60 + "\n")
            elif "42501" in error_msg or "row-level security policy" in error_msg:
                print("\n" + "="*60)
                print("⚠️  SUPABASE RLS POLICY ERROR")
                print("="*60)
                print("Row Level Security is blocking data access.")
                print("\n📝 TO FIX THIS:")
                print("1. Open your Supabase dashboard: https://supabase.com/dashboard")
                print("2. Go to SQL Editor")
                print("3. Run: setup_database.sql")
                print("4. Restart this bot")
                print("\nThis adds policies that allow your anon key to access tables.")
                print("="*60 + "\n")
            else:
                print(f"Error saving health report: {e}")
            return None
    
    def get_user_reports(
        self, 
        telegram_id: int, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get user's health reports.
        
        Args:
            telegram_id: Telegram user ID
            limit: Maximum number of reports to retrieve
            
        Returns:
            List of health reports
        """
        if not self.client:
            return []
        
        try:
            result = self.client.table("health_reports")\
                .select("*")\
                .eq("telegram_id", telegram_id)\
                .order("created_at", desc=True)\
                .limit(limit)\
                .execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            print(f"Error getting user reports: {e}")
            return []
    
    def save_video_summary(
        self,
        telegram_id: int,
        script: str,
        video_url: str
    ) -> Optional[int]:
        """Save video summary to database.
        
        Args:
            telegram_id: Telegram user ID
            script: Video script
            video_url: URL to generated video
            
        Returns:
            Video summary ID if successful
        """
        if not self.client:
            return None
        
        try:
            data = {
                "telegram_id": telegram_id,
                "script": script,
                "video_url": video_url
            }
            
            result = self.client.table("video_summaries").insert(data).execute()
            
            if result.data:
                return result.data[0].get("id")
            return None
            
        except Exception as e:
            error_msg = str(e)
            if "PGRST205" in error_msg or "Could not find the table" in error_msg:
                print("\n⚠️  Supabase table 'video_summaries' not found. Run setup_database.sql in your dashboard.\n")
            elif "42501" in error_msg or "row-level security policy" in error_msg:
                print("\n⚠️  SUPABASE RLS POLICY ERROR: Row Level Security is blocking access.")
                print("📝 Run: setup_database.sql in your Supabase SQL Editor\n")
            else:
                print(f"Error saving video summary: {e}")
            return None
    
    def get_health_summary(self, telegram_id: int) -> str:
        """Generate a summary of user's health data.
        
        Args:
            telegram_id: Telegram user ID
            
        Returns:
            Formatted health summary
        """
        reports = self.get_user_reports(telegram_id, limit=5)
        
        if not reports:
            return "No health reports available yet."
        
        summary = f"Health Summary (Last {len(reports)} reports):\n\n"
        
        for report in reports:
            lab_data = report.get("lab_data", {})
            test_date = lab_data.get("test_date", "Unknown date")
            summary += f"📋 Report from {test_date}:\n"
            
            tests = lab_data.get("tests", [])
            for test in tests[:5]:  # Show first 5 tests
                summary += f"  • {test.get('name')}: {test.get('value')} {test.get('unit')} ({test.get('status')})\n"
            
            summary += "\n"
        
        return summary
    
    # ========== FAMILY CONNECT METHODS ==========
    
    def add_caregiver(
        self,
        patient_telegram_id: int,
        caregiver_telegram_id: int,
        caregiver_name: str = None,
        relationship: str = "family"
    ) -> bool:
        """Link a caregiver to a patient.
        
        Args:
            patient_telegram_id: Patient's Telegram ID
            caregiver_telegram_id: Caregiver's Telegram ID
            caregiver_name: Caregiver's name
            relationship: Relationship type (family, son, daughter, etc.)
            
        Returns:
            True if successful
        """
        if not self.client:
            return False
        
        try:
            data = {
                "patient_telegram_id": patient_telegram_id,
                "caregiver_telegram_id": caregiver_telegram_id,
                "caregiver_name": caregiver_name,
                "relationship": relationship
            }
            
            # Upsert (insert or update if exists)
            self.client.table("caregivers").upsert(data).execute()
            return True
            
        except Exception as e:
            error_msg = str(e)
            if "PGRST205" in error_msg or "Could not find the table" in error_msg:
                print("\n⚠️  Supabase table 'caregivers' not found. Run setup_database.sql in your dashboard.\n")
            else:
                print(f"Error adding caregiver: {e}")
            return False
    
    def get_caregiver(self, patient_telegram_id: int) -> Optional[Dict[str, Any]]:
        """Get caregiver for a patient.
        
        Args:
            patient_telegram_id: Patient's Telegram ID
            
        Returns:
            Caregiver info or None
        """
        if not self.client:
            return None
        
        try:
            result = self.client.table("caregivers")\
                .select("*")\
                .eq("patient_telegram_id", patient_telegram_id)\
                .execute()
            
            if result.data and len(result.data) > 0:
                return result.data[0]
            return None
            
        except Exception as e:
            print(f"Error getting caregiver: {e}")
            return None
    
    def remove_caregiver(self, patient_telegram_id: int) -> bool:
        """Remove caregiver connection for a patient.
        
        Args:
            patient_telegram_id: Patient's Telegram ID
            
        Returns:
            True if successful
        """
        if not self.client:
            return False
        
        try:
            self.client.table("caregivers")\
                .delete()\
                .eq("patient_telegram_id", patient_telegram_id)\
                .execute()
            return True
            
        except Exception as e:
            print(f"Error removing caregiver: {e}")
            return False

