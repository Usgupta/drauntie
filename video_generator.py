"""Video and audio generation using fal.ai and ElevenLabs."""
import os
import logging
from typing import Optional, Tuple
import config

logger = logging.getLogger(__name__)

class VideoGenerator:
    """Generates talking avatar videos and audio summaries."""
    
    def __init__(self):
        """Initialize video generation clients."""
        self.fal_available = bool(config.FAL_KEY or config.FAL_API_KEY)
        self.elevenlabs_available = bool(config.ELEVENLABS_API_KEY)
        
        # Log available services
        if self.fal_available:
            logger.info("✅ fal.ai video generation available")
        else:
            logger.warning("⚠️ fal.ai not configured (FAL_KEY missing)")
            
        if self.elevenlabs_available:
            logger.info("✅ ElevenLabs audio generation available")
        else:
            logger.warning("⚠️ ElevenLabs not configured (ELEVENLABS_API_KEY missing)")
    
    async def generate_single_chunk_async(
        self, 
        chunk: str, 
        index: int, 
        total_chunks: int
    ) -> Tuple[int, str, Optional[str]]:
        """Generate a single video chunk asynchronously.
        
        Args:
            chunk: Script text for this chunk
            index: Chunk index (0-based)
            total_chunks: Total number of chunks
            
        Returns:
            Tuple of (index, chunk_text, video_url or None)
        """
        logger.info(f"🎬 Generating video {index + 1}/{total_chunks}: {chunk[:50]}...")
        
        try:
            # Check if fal.ai is available
            if not self.fal_available:
                logger.warning(f"❌ fal.ai not available for chunk {index + 1}")
                return (index, chunk, None)
            
            # Import fal_client only if available
            try:
                import fal_client  # noqa: F401
            except ImportError:
                logger.error("fal_client not installed. Install with: pip install fal-client")
                return (index, chunk, None)
            
            # Generate video using fal.ai
            # Note: This is a placeholder - actual implementation depends on fal.ai's current API
            logger.info(f"⏳ Submitting video generation request for chunk {index + 1}")
            
            # Simulate video generation (replace with actual fal.ai call)
            # In production, this would be something like:
            # result = await fal_client.run_async(
            #     "fal-ai/your-model",
            #     arguments={"text": chunk, ...}
            # )
            
            # For now, return None to trigger audio fallback
            logger.warning(f"⚠️ Video generation not fully implemented for chunk {index + 1}")
            return (index, chunk, None)
            
        except Exception as e:
            logger.error(f"❌ Error generating video for chunk {index + 1}: {e}")
            return (index, chunk, None)
    
    def generate_audio_summary(self, script: str) -> Optional[str]:
        """Generate audio file from script using ElevenLabs.
        
        Args:
            script: Full script text
            
        Returns:
            Path to generated audio file, or None if failed
        """
        logger.info(f"🎤 Generating audio summary ({len(script)} chars)")
        
        try:
            # Check if ElevenLabs is available
            if not self.elevenlabs_available:
                logger.error("❌ ElevenLabs not configured (ELEVENLABS_API_KEY missing)")
                return None
            
            # Import ElevenLabs only if available
            try:
                from elevenlabs import generate, save, Voice, VoiceSettings  # noqa: F401
            except ImportError:
                logger.error("elevenlabs not installed. Install with: pip install elevenlabs")
                return None
            
            # Generate audio with ElevenLabs
            logger.info("⏳ Generating audio with ElevenLabs...")
            
            # Use a voice that sounds like a Singaporean aunty
            # You can customize this with different voice IDs from ElevenLabs
            audio = generate(
                text=script,
                voice=Voice(
                    voice_id="EXAVITQu4vr4xnSDxMaL",  # Sarah voice (customize as needed)
                    settings=VoiceSettings(
                        stability=0.5,
                        similarity_boost=0.75,
                        style=0.5,
                        use_speaker_boost=True
                    )
                ),
                model="eleven_multilingual_v2"  # Supports various accents
            )
            
            # Save audio file
            import tempfile
            temp_audio = tempfile.NamedTemporaryFile(
                delete=False, 
                suffix='.mp3',
                prefix='dr_aunty_'
            )
            temp_path = temp_audio.name
            temp_audio.close()
            
            save(audio, temp_path)
            logger.info(f"✅ Audio saved to {temp_path}")
            return temp_path
            
        except Exception as e:
            logger.error(f"❌ Error generating audio: {e}")
            logger.error("   Make sure ELEVENLABS_API_KEY is set correctly")
            return None
    
    def generate_health_summary_video(
        self,
        script: str,
        duration: int = 8
    ) -> Optional[str]:
        """Generate a health summary video (synchronous wrapper).
        
        Args:
            script: Video script
            duration: Video duration in seconds
            
        Returns:
            Video URL or None if failed
        """
        logger.info(f"🎥 Generating health summary video ({duration}s)")
        
        try:
            if not self.fal_available:
                logger.error("❌ fal.ai not configured")
                return None
            
            # This would be the actual fal.ai video generation
            # For now, log that it's not implemented
            logger.warning("⚠️ Video generation not fully implemented - use audio fallback")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error generating video: {e}")
            return None


# Standalone function for quick testing
def test_audio_generation():
    """Test audio generation."""
    generator = VideoGenerator()
    
    if not generator.elevenlabs_available:
        print("❌ ElevenLabs not configured. Set ELEVENLABS_API_KEY in .env")
        return
    
    test_script = "Aiyo! Your cholesterol 6.2 lah! Should be 5.2! Stop eating so much fried food! Switch to steamed lah!"
    
    print(f"Testing audio generation with script: {test_script}")
    audio_path = generator.generate_audio_summary(test_script)
    
    if audio_path:
        print(f"✅ Audio generated: {audio_path}")
        print(f"   File size: {os.path.getsize(audio_path)} bytes")
        print(f"   To play: open {audio_path}")
    else:
        print("❌ Audio generation failed")


if __name__ == "__main__":
    # Test the generator
    test_audio_generation()

