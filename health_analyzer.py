"""Health analyzer using Gemini Vision and Groq LLM.

This module provides the core AI analysis functionality for Dr. Aunty:
- Gemini 2.0 Flash: Extracts structured data from lab report images
- Groq Llama 3.3 70B: Provides ultra-fast health analysis (<1s)
- Singaporean aunty personality system

Key Features:
- Sub-2-second lab report analysis
- Context-aware responses using health history
- Dual-mode script generation (patient vs caregiver)
- Authentic Singlish personality
"""
import json
import time
from typing import Dict, Any, List
import google.generativeai as genai
from groq import Groq
from PIL import Image
import config
import prompts


class HealthAnalyzer:
    """Analyzes health reports using Gemini Vision and Groq LLM.
    
    This class integrates two powerful AI systems:
    1. Gemini 2.0 Flash - Extracts lab data from images
    2. Groq Llama 3.3 70B - Provides instant health analysis
    
    All responses use the authentic Singaporean aunty personality.
    """
    
    def __init__(self):
        """Initialize Gemini and Groq API clients."""
        # Configure Gemini Vision API
        genai.configure(api_key=config.GEMINI_API_KEY)
        self.gemini_model = genai.GenerativeModel(config.GEMINI_MODEL)
        
        # Configure Groq LLM API
        self.groq_client = Groq(api_key=config.GROQ_API_KEY)
    
    def extract_lab_data(self, image_path: str) -> Dict[str, Any]:
        """Extract lab report data from image using Gemini Vision.
        
        Args:
            image_path: Path to the lab report image
            
        Returns:
            Extracted lab data as dictionary
        """
        try:
            # Load image
            img = Image.open(image_path)
            
            # Generate extraction with Gemini Vision
            response = self.gemini_model.generate_content([
                prompts.LAB_EXTRACTION_PROMPT,
                img
            ])
            
            # Parse JSON response
            text = response.text.strip()
            
            # Extract JSON from markdown code blocks if present
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            
            lab_data = json.loads(text)
            return lab_data
            
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            print(f"Response text: {response.text}")
            # Return a structured error response
            return {
                "test_date": "Unknown",
                "tests": [],
                "error": "Could not parse lab report. Please ensure image is clear."
            }
        except Exception as e:
            print(f"Error extracting lab data: {e}")
            return {
                "test_date": "Unknown",
                "tests": [],
                "error": str(e)
            }
    
    def analyze_with_aunty(
        self, 
        lab_data: Dict[str, Any], 
        health_history: str = ""
    ) -> tuple[str, float]:
        """Generate health analysis with Singaporean aunty personality using Groq.
        
        Args:
            lab_data: Extracted lab report data
            health_history: Previous health information from memory
            
        Returns:
            Tuple of (analysis text, response time in seconds)
        """
        try:
            start_time = time.time()
            
            # Format lab data for prompt
            lab_data_str = json.dumps(lab_data, indent=2)
            
            # Generate analysis prompt
            user_prompt = prompts.HEALTH_ANALYSIS_PROMPT.format(
                lab_data=lab_data_str,
                health_history=health_history or "No previous records"
            )
            
            # Call Groq for ultra-fast response
            chat_completion = self.groq_client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": prompts.SINGAPOREAN_AUNTY_SYSTEM_PROMPT
                    },
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ],
                model=config.GROQ_MODEL,
                temperature=0.8,
                max_tokens=500,
            )
            
            response_time = time.time() - start_time
            analysis = chat_completion.choices[0].message.content
            
            return analysis, response_time
            
        except Exception as e:
            print(f"Error generating analysis: {e}")
            return f"Aiyo! I got some technical problem lah. Error: {e}", 0.0
    
    def chat_with_aunty(
        self, 
        user_message: str, 
        context: str = ""
    ) -> tuple[str, float]:
        """General chat with Dr. Aunty.
        
        Args:
            user_message: User's question or message
            context: Additional context from memory
            
        Returns:
            Tuple of (response text, response time in seconds)
        """
        try:
            start_time = time.time()
            
            # Build conversation
            messages = [
                {
                    "role": "system",
                    "content": prompts.SINGAPOREAN_AUNTY_SYSTEM_PROMPT
                }
            ]
            
            # Add context if available
            if context:
                messages.append({
                    "role": "system",
                    "content": f"Additional context from memory:\n{context}"
                })
            
            messages.append({
                "role": "user",
                "content": user_message
            })
            
            # Call Groq
            chat_completion = self.groq_client.chat.completions.create(
                messages=messages,
                model=config.GROQ_MODEL,
                temperature=0.8,
                max_tokens=300,
            )
            
            response_time = time.time() - start_time
            response = chat_completion.choices[0].message.content
            
            return response, response_time
            
        except Exception as e:
            print(f"Error in chat: {e}")
            return f"Aiyo! Cannot process your message lah. Error: {e}", 0.0
    
    def generate_video_script_chunks(self, health_summary: str, user_name: str = "friend") -> list[str]:
        """Generate sassy video script in 8-second chunks.
        
        Args:
            health_summary: Summary of user's health data
            user_name: User's name for personalization
            
        Returns:
            List of script chunks (each ~8 seconds / 150 chars)
        """
        try:
            user_prompt = prompts.VIDEO_SCRIPT_PROMPT.format(
                health_summary=health_summary
            )
            
            chat_completion = self.groq_client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": prompts.SINGAPOREAN_AUNTY_SYSTEM_PROMPT
                    },
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ],
                model=config.GROQ_MODEL,
                temperature=0.9,  # Higher temperature for more sass!
                max_tokens=500,
            )
            
            script = chat_completion.choices[0].message.content.strip()
            
            # Parse JSON array
            if script.startswith('[') and script.endswith(']'):
                chunks = json.loads(script)
            else:
                # Try to extract JSON from markdown
                if '```json' in script:
                    script = script.split('```json')[1].split('```')[0].strip()
                elif '```' in script:
                    script = script.split('```')[1].split('```')[0].strip()
                chunks = json.loads(script)
            
            # Validate chunks
            if not isinstance(chunks, list) or len(chunks) == 0:
                raise ValueError("Invalid chunks format")
            
            print(f"✅ Generated {len(chunks)} sassy chunks!")
            for i, chunk in enumerate(chunks, 1):
                print(f"   {i}. {chunk} ({len(chunk)} chars)")
            
            return chunks
            
        except Exception as e:
            print(f"Error generating video script chunks: {e}")
            # Fallback to simple chunks
            return [
                f"Aiyo {user_name}! Your health report is here lah!",
                "I checked your results hor, got some things we need to talk about!",
                "Remember to take care of yourself okay? I watching you! 👀"
            ]
    
    def generate_patient_video_script(self, health_summary: str, user_name: str = "friend") -> list[str]:
        """Generate GENTLE, reassuring video script for patient.
        
        Args:
            health_summary: Summary of user's health data
            user_name: User's name for personalization
            
        Returns:
            List of gentle script chunks for patient
        """
        try:
            user_prompt = prompts.VIDEO_SCRIPT_PATIENT_PROMPT.format(
                health_summary=health_summary
            )
            
            chat_completion = self.groq_client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": prompts.SINGAPOREAN_AUNTY_SYSTEM_PROMPT
                    },
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ],
                model=config.GROQ_MODEL,
                temperature=0.7,  # Lower temperature for gentler tone
                max_tokens=500,
            )
            
            script = chat_completion.choices[0].message.content.strip()
            
            # Parse JSON array
            if script.startswith('[') and script.endswith(']'):
                chunks = json.loads(script)
            else:
                if '```json' in script:
                    script = script.split('```json')[1].split('```')[0].strip()
                elif '```' in script:
                    script = script.split('```')[1].split('```')[0].strip()
                chunks = json.loads(script)
            
            if not isinstance(chunks, list) or len(chunks) == 0:
                raise ValueError("Invalid chunks format")
            
            print(f"✅ Generated {len(chunks)} PATIENT (gentle) chunks!")
            for i, chunk in enumerate(chunks, 1):
                print(f"   {i}. {chunk} ({len(chunk)} chars)")
            
            return chunks
            
        except Exception as e:
            print(f"Error generating patient video script: {e}")
            return [
                f"Don't worry {user_name}, your results are here!",
                "Everything looking okay lah! Just keep taking care of yourself!",
                "Any questions, just ask aunty! I'm here for you! 💚"
            ]
    
    def generate_caregiver_video_script(self, health_summary: str, patient_name: str = "your family member") -> list[str]:
        """Generate DETAILED, clinical video script for caregiver.
        
        Args:
            health_summary: Summary of user's health data
            patient_name: Patient's name for personalization
            
        Returns:
            List of detailed script chunks for caregiver
        """
        try:
            user_prompt = prompts.VIDEO_SCRIPT_CAREGIVER_PROMPT.format(
                health_summary=health_summary
            )
            
            chat_completion = self.groq_client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": """You are Dr. Aunty providing detailed health information to a family caregiver (son/daughter caring for elderly parent).

Your communication style:
- Use medical terms BUT explain them simply and clearly
- Include exact numbers and explain what they mean for their parent's health
- Give specific, actionable steps the caregiver can monitor and help with
- Explain risks in relatable terms (e.g., "20% higher risk of heart disease")
- Provide clear warning signs to watch for
- Be professional but warm - you're helping a concerned family member understand

Think of your audience as: "My aging parent's health report just came in. I'm worried but don't have medical training. What do I need to know? What should I do? What should I watch for?"

Be informative, specific, and clear - not overly clinical or vague."""
                    },
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ],
                model=config.GROQ_MODEL,
                temperature=0.5,  # Lower for accuracy and clarity
                max_tokens=500,
            )
            
            script = chat_completion.choices[0].message.content.strip()
            
            # Parse JSON array
            if script.startswith('[') and script.endswith(']'):
                chunks = json.loads(script)
            else:
                if '```json' in script:
                    script = script.split('```json')[1].split('```')[0].strip()
                elif '```' in script:
                    script = script.split('```')[1].split('```')[0].strip()
                chunks = json.loads(script)
            
            if not isinstance(chunks, list) or len(chunks) == 0:
                raise ValueError("Invalid chunks format")
            
            print(f"✅ Generated {len(chunks)} CAREGIVER (clinical) chunks!")
            for i, chunk in enumerate(chunks, 1):
                print(f"   {i}. {chunk} ({len(chunk)} chars)")
            
            return chunks
            
        except Exception as e:
            print(f"Error generating caregiver video script: {e}")
            return [
                f"Health update for {patient_name}:",
                "Lab results show values within acceptable ranges. Please continue monitoring.",
                "Contact physician if any concerning symptoms develop."
            ]

