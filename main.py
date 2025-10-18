"""
Dr. Aunty - Telegram Health Bot with Singaporean Personality
A hackathon project featuring AI health analysis and talking avatar videos.
"""
import os
import logging
import warnings
import asyncio
from datetime import datetime
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# Suppress SSL warnings for development
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

import config
from health_analyzer import HealthAnalyzer
from memory_manager import HealthMemoryManager
from database import HealthDatabase
from video_generator import VideoGenerator

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize components
health_analyzer = HealthAnalyzer()
memory_manager = HealthMemoryManager()
database = HealthDatabase()
video_generator = VideoGenerator()


def format_health_report_for_caregiver(lab_data: dict, patient_name: str) -> str:
    """Format health report data into a clean, visually appealing format for caregivers.
    
    Args:
        lab_data: Dictionary containing lab test results
        patient_name: Name of the patient
        
    Returns:
        Formatted markdown text with health data
    """
    report = "╭━━━━━━━━━━━━━━━━━━━━━╮\n"
    report += "┃ 📊 *Health Report* ┃\n"
    report += "╰━━━━━━━━━━━━━━━━━━━━━╯\n\n"
    report += f"👤 *Patient:* {patient_name}\n"
    report += f"📅 *Date:* {lab_data.get('test_date', 'N/A')}\n"
    
    tests = lab_data.get('tests', [])
    
    if not tests:
        return report + "\n_No test data available._"
    
    # Count abnormal values
    abnormal = [t for t in tests if t.get('status') != 'normal']
    normal = [t for t in tests if t.get('status') == 'normal']
    
    # Summary with visual indicator
    report += f"\n📈 *Summary:* {len(tests)} tests total\n"
    if abnormal:
        report += f"⚠️ {len(abnormal)} need attention\n"
    if normal:
        report += f"✅ {len(normal)} normal\n"
    
    # Abnormal values first (if any)
    if abnormal:
        report += "\n━━━━━━━━━━━━━━━━━━━━━\n"
        report += "*⚠️ NEEDS ATTENTION*\n"
        report += "━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        for test in abnormal:
            name = test.get('name', 'Unknown')
            value = test.get('value', 'N/A')
            unit = test.get('unit', '')
            ref_range = test.get('reference_range', 'N/A')
            status = test.get('status', '').upper()
            
            # Format status indicator
            if status == "HIGH":
                indicator = "🔴 HIGH"
            elif status == "LOW":
                indicator = "🔵 LOW"
            else:
                indicator = "⚠️ ABNORMAL"
            
            report += f"*{name}*\n"
            report += f"  {indicator}\n"
            report += f"  • Result: *{value} {unit}*\n"
            report += f"  • Normal: {ref_range}\n\n"
    
    # Normal values (collapsed)
    if normal:
        report += "━━━━━━━━━━━━━━━━━━━━━\n"
        report += f"*✅ NORMAL VALUES* ({len(normal)} tests)\n"
        report += "━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        for test in normal[:5]:  # Show first 5
            name = test.get('name', 'Unknown')
            value = test.get('value', 'N/A')
            unit = test.get('unit', '')
            report += f"• {name}: {value} {unit}\n"
        
        if len(normal) > 5:
            report += f"• _...and {len(normal) - 5} more tests_\n"
    
    report += "\n━━━━━━━━━━━━━━━━━━━━━\n"
    report += "🎤 *Detailed audio explanation coming next*\n"
    report += "Listen for specific guidance and action steps."
    
    return report


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    telegram_id = user.id
    
    # Save user to database
    database.add_user(telegram_id, user.username, user.first_name)
    
    welcome_message = f"""
Aiyo {user.first_name}! Welcome welcome!

I'm Dr. Aunty lah - your health companion who tells it like it is! 

What I can do:
- Analyze your lab reports (just send me photo!)
- Answer health questions
- Track your health over time
- Share updates with your son/daughter if you want

*Send me your lab report photo to get started!*

Want to share with family?
Use `/setcaregiver <their_telegram_id> <their_name>` to connect them.

Commands:
/help - See what I can do
/setcaregiver - Connect a family member
/video - Generate another video
/history - View past reports

Don't shy lah, aunty won't bite! (But I will scold if your cholesterol too high!)
    """
    
    await update.message.reply_text(
        welcome_message,
        parse_mode="Markdown"
    )


async def setcaregiver(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Connect a family caregiver."""
    user = update.effective_user
    telegram_id = user.id
    
    # Check if arguments provided
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "❌ Aiyo! You need to tell me who lah!\n\n"
            "*Usage:* `/setcaregiver <telegram_id> <name>`\n\n"
            "*Example:* `/setcaregiver 123456789 John`\n\n"
            "💡 *How to get their Telegram ID:*\n"
            "1. Ask them to message @userinfobot\n"
            "2. The bot will show their Telegram ID\n"
            "3. Send it to me here!",
            parse_mode="Markdown"
        )
        return
    
    try:
        caregiver_id = int(context.args[0])
        caregiver_name = " ".join(context.args[1:])
        
        # Save to database
        success = database.add_caregiver(
            patient_telegram_id=telegram_id,
            caregiver_telegram_id=caregiver_id,
            caregiver_name=caregiver_name,
            relationship="family"
        )
        
        if success:
            await update.message.reply_text(
                f"✅ *Family Connected!* 👨‍👩‍👧\n\n"
                f"Your family member *{caregiver_name}* is now connected!\n\n"
                f"⚠️ *IMPORTANT*: Tell {caregiver_name} to:\n"
                f"1️⃣ Open Telegram\n"
                f"2️⃣ Search for this bot\n"
                f"3️⃣ Send `/start` to activate\n\n"
                f"Without this, they won't receive messages!\n\n"
                f"📹 Once set up, when you send lab reports:\n"
                f"• *You* get gentle, reassuring videos 💚\n"
                f"• *{caregiver_name}* gets detailed clinical videos 📊\n\n"
                f"Both happen automatically! 🚀",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                "❌ Aiyo! Got problem saving to database lah!\n"
                "Try again or contact support."
            )
            
    except ValueError:
        await update.message.reply_text(
            "❌ Aiyo! The Telegram ID must be a number lah!\n\n"
            "*Usage:* `/setcaregiver <telegram_id> <name>`\n"
            "*Example:* `/setcaregiver 123456789 John`",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Error setting caregiver: {e}")
        await update.message.reply_text(
            f"❌ Aiyo! Something went wrong: {str(e)}"
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    help_text = """
*Dr. Aunty Commands*

What I can do:
- Analyze your lab reports
- Answer health questions
- Create videos with advice
- Share updates with family

Commands:
/start - Welcome message
/help - Show this help
/setcaregiver <id> <name> - Connect family member
/video - Generate another video
/history - View past reports
/stats - Your health statistics

How to use:
1. Take photo of your lab report
2. Send it to me
3. Get my analysis
4. Videos come after
5. (Optional) Connect family with /setcaregiver

Family Connect:
• You get gentle, reassuring videos
• Your family gets detailed audio reports
• Both sent automatically

I got memory one! I track your health and compare trends. Cannot hide from aunty!

Any questions? Just ask! (But prepare for sass!)
    """
    
    await update.message.reply_text(help_text, parse_mode="Markdown")


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle photo uploads (lab reports) with PARALLEL processing."""
    user = update.effective_user
    telegram_id = user.id
    
    # Send immediate acknowledgment
    processing_msg = await update.message.reply_text(
        "Wah! Got your lab report lah! Let me check check..."
    )
    
    try:
        # Download the photo
        photo_file = await update.message.photo[-1].get_file()
        photo_path = f"temp_{telegram_id}.jpg"
        await photo_file.download_to_drive(photo_path)
        
        # Extract lab data with Gemini Vision
        await processing_msg.edit_text(
            "Reading your lab report..."
        )
        lab_data = health_analyzer.extract_lab_data(photo_path)
        
        # Check for extraction errors
        if "error" in lab_data:
            await processing_msg.edit_text(
                f"❌ Aiyo! {lab_data['error']}\n\nCan you send a clearer photo? Make sure all text is visible!"
            )
            # Clean up
            if os.path.exists(photo_path):
                os.remove(photo_path)
            return
        
        # Save lab data to database FIRST (so video generation can access it)
        # We'll update with full analysis later
        await asyncio.to_thread(
            database.save_health_report, telegram_id, lab_data, "Processing...", 0.0
        )
        
        await processing_msg.edit_text(
            "Analyzing now..."
        )
        
        # Clean up temp file early
        if os.path.exists(photo_path):
            os.remove(photo_path)
        
        # Define parallel tasks
        async def generate_text_analysis():
            """Task 1: Generate and send text analysis."""
            # Run synchronous operations in thread pool to avoid blocking
            health_history = await asyncio.to_thread(
                memory_manager.get_health_history, str(telegram_id)
            )
            
            # Generate analysis with Groq (ultra-fast!)
            analysis, response_time = await asyncio.to_thread(
                health_analyzer.analyze_with_aunty,
                lab_data, 
                health_history
            )
            
            # Update database with full analysis
            await asyncio.to_thread(
                database.save_health_report, telegram_id, lab_data, analysis, response_time
            )
            
            # Save to Mem0
            await asyncio.to_thread(
                memory_manager.add_health_record, str(telegram_id), lab_data, analysis
            )
            
            # Send analysis with timing info
            response_message = f"""
{analysis}
            """
            
            await update.message.reply_text(response_message, parse_mode="Markdown")
            logger.info(f"✅ Text analysis sent in {response_time:.2f}s")
            
            return response_time
        
        # ============================================================
        # 🎬 VIDEO GENERATION TOGGLE
        # ============================================================
        # TO ENABLE VIDEOS: Change ENABLE_VIDEOS to True
        # TO DISABLE VIDEOS: Change ENABLE_VIDEOS to False
        ENABLE_VIDEOS = True  # 👈 CHANGE THIS TO True WHEN READY!
        # ============================================================
        
        async def generate_videos_and_caregiver_audio():
            """Generate patient videos + caregiver audio (when videos enabled)."""
            await auto_generate_video(update, telegram_id, user.first_name or "friend")
        
        async def send_caregiver_audio_only():
            """Send audio to caregiver only (when videos disabled)."""
            # Check if caregiver exists
            caregiver_info = await asyncio.to_thread(database.get_caregiver, telegram_id)
            
            if not caregiver_info:
                logger.info("No caregiver configured, skipping audio generation")
                return
            
            logger.info(f"🏥 Generating audio for caregiver: {caregiver_info['caregiver_name']}")
            
            try:
                # Get health summary
                health_summary = await asyncio.to_thread(
                    database.get_health_summary, telegram_id
                )
                
                if "No health reports" in health_summary:
                    logger.warning("No health reports found for caregiver audio")
                    return
                
                # Generate caregiver script
                caregiver_script_chunks = await asyncio.to_thread(
                    health_analyzer.generate_caregiver_video_script, health_summary, user.first_name or "friend"
                )
                
                # Combine script chunks
                full_caregiver_script = " ".join(caregiver_script_chunks)
                
                # Generate audio
                caregiver_audio_path = await asyncio.to_thread(
                    video_generator.generate_audio_summary, full_caregiver_script
                )
                
                if caregiver_audio_path:
                    # Get the latest lab data from database
                    latest_reports = await asyncio.to_thread(
                        database.get_user_reports, telegram_id, limit=1
                    )
                    
                    # Send formatted text report first
                    if latest_reports and len(latest_reports) > 0:
                        lab_data = latest_reports[0].get('lab_data', {})
                        formatted_report = format_health_report_for_caregiver(
                            lab_data,
                            user.first_name or 'Patient'
                        )
                        
                        await update.get_bot().send_message(
                            chat_id=caregiver_info['caregiver_telegram_id'],
                            text=formatted_report,
                            parse_mode="Markdown"
                        )
                        logger.info("✅ Sent formatted text report to caregiver")
                    
                    # Create meaningful filename
                    date_str = datetime.now().strftime("%Y-%m-%d_%H-%M")
                    patient_name = (user.first_name or "Patient").replace(" ", "_")
                    filename = f"Health_Report_{patient_name}_{date_str}.mp3"
                    
                    # Send audio report with details
                    with open(caregiver_audio_path, 'rb') as audio_file:
                        await update.get_bot().send_audio(
                            chat_id=caregiver_info['caregiver_telegram_id'],
                            audio=audio_file,
                            caption="*🎤 Detailed Audio Explanation*\n\n"
                                    "Listen for specific guidance, what to monitor, and action steps.",
                            parse_mode="Markdown",
                            filename=filename
                        )
                    logger.info(f"✅ Sent audio to caregiver {caregiver_info['caregiver_name']} as {filename}")
                    
                    # Clean up audio file
                    if os.path.exists(caregiver_audio_path):
                        os.remove(caregiver_audio_path)
                    
                    # Notify patient
                    await update.message.reply_text(
                        f"📨 Sent report to {caregiver_info['caregiver_name']}!",
                        parse_mode="Markdown"
                    )
                else:
                    logger.error("❌ Failed to generate caregiver audio")
                    
            except Exception as e:
                logger.error(f"❌ Error sending audio to caregiver: {e}")
                logger.error(f"   Error type: {type(e).__name__}")
                
                # Notify patient about the error
                try:
                    await update.message.reply_text(
                        f"⚠️ Couldn't send report to {caregiver_info['caregiver_name']}\n\n"
                        f"They may need to send /start to the bot first.\n"
                        f"Error: {str(e)[:100]}",
                        parse_mode="Markdown"
                    )
                except Exception:
                    # If we can't notify patient, just log it
                    logger.error("Could not notify patient about caregiver error")
        
        # Run both tasks in parallel!
        await processing_msg.edit_text(
            "Getting your results ready..."
        )
        
        # Choose video/audio strategy based on toggle
        if ENABLE_VIDEOS:
            # VIDEOS ENABLED: Generate videos for patient + audio for caregiver
            results = await asyncio.gather(
                generate_text_analysis(),
                generate_videos_and_caregiver_audio(),
                return_exceptions=True
            )
        else:
            # VIDEOS DISABLED: Text analysis + caregiver audio only
            results = await asyncio.gather(
                generate_text_analysis(),
                send_caregiver_audio_only(),
                return_exceptions=True
            )
        
        # Check for errors
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Task {i+1} error: {result}")
        
        # Delete processing message
        await processing_msg.delete()
        
        logger.info("✅ Parallel processing complete!")
            
    except Exception as e:
        logger.error(f"Error processing photo: {e}")
        await processing_msg.edit_text(
            f"❌ Aiyo! Something went wrong lah!\n\nError: {str(e)}\n\nTry again later or contact support."
        )
        
        # Clean up temp file
        if os.path.exists(photo_path):
            os.remove(photo_path)


async def auto_generate_video(update: Update, telegram_id: int, user_name: str) -> None:
    """Automatically generate video after photo analysis - with Family Connect support."""
    # Check if caregiver exists
    caregiver_info = await asyncio.to_thread(database.get_caregiver, telegram_id)
    
    if caregiver_info:
        video_msg = await update.message.reply_text(
            f"Wah! Making videos for you!\n"
            f"Also sending report to {caregiver_info['caregiver_name']}.\n"
            f"Wait ah!"
        )
    else:
        video_msg = await update.message.reply_text(
            "Wah! Now aunty going to scold you in video format! This one take a bit longer hor, wait ah!"
        )
    
    try:
        # Get health summary from database (run in thread to not block)
        health_summary = await asyncio.to_thread(
            database.get_health_summary, telegram_id
        )
        
        if "No health reports" in health_summary:
            await video_msg.edit_text(
                "❌ Aiyo! Something went wrong getting your report!"
            )
            return
        
        # Generate video scripts based on whether caregiver exists
        if caregiver_info:
            await video_msg.edit_text(
                "Writing your scripts now..."
            )
            # Generate BOTH scripts
            patient_chunks, caregiver_chunks = await asyncio.gather(
                asyncio.to_thread(
                    health_analyzer.generate_patient_video_script, health_summary, user_name
                ),
                asyncio.to_thread(
                    health_analyzer.generate_caregiver_video_script, health_summary, user_name
                )
            )
            script_chunks = patient_chunks  # For patient videos
            caregiver_script_chunks = caregiver_chunks  # For caregiver audio (not video)
        else:
            # Generate regular sassy video script chunks with Groq (run in thread)
            await video_msg.edit_text(
                "Writing your scripts now..."
            )
            script_chunks = await asyncio.to_thread(
                health_analyzer.generate_video_script_chunks, health_summary, user_name
            )
            caregiver_script_chunks = None
        
        await video_msg.edit_text(
            f"Creating {len(script_chunks)} videos for you now! They'll come one by one..."
        )
        
        # Generate videos concurrently, send in order as ready
        # Create semaphore for batching (3 concurrent)
        semaphore = asyncio.Semaphore(3)
        
        # Dictionary to store completed videos
        completed_videos = {}
        next_to_send = 0
        sent_videos = []
        lock = asyncio.Lock()
        
        async def generate_video_only(chunk: str, index: int):
            """Generate video (no sending here)."""
            async with semaphore:
                # Generate video
                result = await video_generator.generate_single_chunk_async(
                    chunk, index, len(script_chunks)
                )
                idx, chunk_text, video_url = result
                
                # Store result
                async with lock:
                    completed_videos[idx] = (chunk_text, video_url)
                    
                return (idx, chunk_text, video_url)
        
        async def send_videos_in_order():
            """Send videos in order as they become available."""
            nonlocal next_to_send
            
            while next_to_send < len(script_chunks):
                # Wait for next video to be ready
                while next_to_send not in completed_videos:
                    await asyncio.sleep(0.1)
                
                # Get the video
                chunk_text, video_url = completed_videos[next_to_send]
                
                if video_url:
                    caption = f"""
*Part {next_to_send + 1}/{len(script_chunks)}*

"{chunk_text}"
                    """
                    
                    try:
                        await update.message.reply_video(
                            video=video_url,
                            caption=caption,
                            parse_mode="Markdown"
                        )
                        sent_videos.append(video_url)
                        logger.info(f"✅ Sent video {next_to_send + 1}/{len(script_chunks)}")
                    except Exception as e:
                        logger.error(f"Error sending video {next_to_send + 1}: {e}")
                        await update.message.reply_text(
                            f"Video {next_to_send + 1} couldn't be sent: {str(e)}"
                        )
                else:
                    await update.message.reply_text(
                        f"Video {next_to_send + 1} generation failed lah!"
                    )
                
                next_to_send += 1
        
        # Create generation tasks
        generation_tasks = [
            generate_video_only(chunk, i)
            for i, chunk in enumerate(script_chunks)
        ]
        
        # Create sender task
        sender_task = asyncio.create_task(send_videos_in_order())
        
        # Wait for both generation and sending to complete
        await asyncio.gather(*generation_tasks)
        await sender_task
        
        if len(sent_videos) == 0:
            # All videos failed - fall back to audio
            await video_msg.edit_text(
                "Videos having problem lah! Wait, let me send you audio instead..."
            )
            
            # Generate audio fallback
            logger.info("🎤 All videos failed, falling back to audio generation...")
            
            # Generate full script from chunks (combine them)
            full_script = " ".join(script_chunks)
            
            # Generate audio for patient
            patient_audio_path = await asyncio.to_thread(
                video_generator.generate_audio_summary, full_script
            )
            
            if patient_audio_path:
                # Send audio to patient with meaningful filename
                try:
                    date_str = datetime.now().strftime("%Y-%m-%d_%H-%M")
                    filename = f"Dr_Aunty_Health_Advice_{date_str}.mp3"
                    
                    with open(patient_audio_path, 'rb') as audio_file:
                        await update.message.reply_audio(
                            audio=audio_file,
                            caption="*Your Health Summary*\n\nHere's your health advice!",
                            parse_mode="Markdown",
                            filename=filename
                        )
                    logger.info(f"✅ Sent audio to patient as {filename}")
                    
                    # Clean up patient audio file
                    if os.path.exists(patient_audio_path):
                        os.remove(patient_audio_path)
                    
                    # If caregiver exists, generate and send caregiver audio
                    if caregiver_info and caregiver_script_chunks:
                        logger.info(f"🏥 Generating audio for caregiver: {caregiver_info['caregiver_name']}")
                        logger.info(f"   Caregiver Telegram ID: {caregiver_info['caregiver_telegram_id']}")
                        
                        full_caregiver_script = " ".join(caregiver_script_chunks)
                        caregiver_audio_path = await asyncio.to_thread(
                            video_generator.generate_audio_summary, full_caregiver_script
                        )
                        
                        if caregiver_audio_path:
                            try:
                                # Get the latest lab data from database
                                latest_reports = await asyncio.to_thread(
                                    database.get_user_reports, telegram_id, limit=1
                                )
                                
                                # Send formatted text report first
                                if latest_reports and len(latest_reports) > 0:
                                    lab_data = latest_reports[0].get('lab_data', {})
                                    formatted_report = format_health_report_for_caregiver(
                                        lab_data,
                                        user_name
                                    )
                                    
                                    await update.get_bot().send_message(
                                        chat_id=caregiver_info['caregiver_telegram_id'],
                                        text=formatted_report,
                                        parse_mode="Markdown"
                                    )
                                    logger.info("✅ Sent formatted text report to caregiver")
                                
                                # Create meaningful filename
                                date_str = datetime.now().strftime("%Y-%m-%d_%H-%M")
                                patient_name_clean = user_name.replace(" ", "_")
                                filename = f"Health_Report_{patient_name_clean}_{date_str}.mp3"
                                
                                # Send audio with details
                                logger.info(f"📤 Sending audio to caregiver at chat_id: {caregiver_info['caregiver_telegram_id']}")
                                with open(caregiver_audio_path, 'rb') as audio_file:
                                    await update.get_bot().send_audio(
                                        chat_id=caregiver_info['caregiver_telegram_id'],
                                        audio=audio_file,
                                        caption="*🎤 Detailed Audio Explanation*\n\n"
                                                "Listen for specific guidance, what to monitor, and action steps.",
                                        parse_mode="Markdown",
                                        filename=filename
                                    )
                                logger.info(f"✅ Sent audio to caregiver {caregiver_info['caregiver_name']} as {filename}")
                                
                                # Notify patient
                                await update.message.reply_text(
                                    f"Also sent update to {caregiver_info['caregiver_name']}!",
                                    parse_mode="Markdown"
                                )
                                
                                # Clean up caregiver audio file
                                if os.path.exists(caregiver_audio_path):
                                    os.remove(caregiver_audio_path)
                                    
                            except Exception as e:
                                logger.error(f"❌ Error sending audio to caregiver: {e}")
                                logger.error(f"   Error type: {type(e).__name__}")
                                logger.error(f"   Details: {str(e)}")
                                
                                # Notify patient about the error
                                await update.message.reply_text(
                                    f"⚠️ Couldn't send audio to {caregiver_info['caregiver_name']}\n\n"
                                    f"Possible reasons:\n"
                                    f"• They haven't started the bot yet (tell them to send /start to @{(await update.get_bot().get_me()).username})\n"
                                    f"• Their Telegram ID might be wrong\n\n"
                                    f"Error: {str(e)[:100]}",
                                    parse_mode="Markdown"
                                )
                        else:
                            logger.error("❌ Failed to generate caregiver audio")
                            await update.message.reply_text(
                                f"⚠️ Couldn't generate audio for {caregiver_info['caregiver_name']}"
                            )
                    elif caregiver_info and not caregiver_script_chunks:
                        logger.warning(f"⚠️ Caregiver {caregiver_info['caregiver_name']} exists but no caregiver script chunks!")
                        await update.message.reply_text(
                            f"⚠️ Note: Couldn't generate separate audio for {caregiver_info['caregiver_name']} (no caregiver script available)",
                            parse_mode="Markdown"
                        )
                    
                    await video_msg.delete()
                    return
                    
                except Exception as e:
                    logger.error(f"Error sending audio to patient: {e}")
                    await video_msg.edit_text(
                        f"❌ Audio sending failed: {str(e)}\n\nPlease try again later! 😔"
                    )
                    return
            else:
                await video_msg.edit_text(
                    "❌ Aiyo! Both video AND audio generation failed lah!\n\n"
                    "Maybe try again later? The servers might be busy. 😔"
                )
                return
        
        successful_count = len(sent_videos)
        
        # Send completion message for patient
        completion_msg = f"Done! Sent you {successful_count} videos."
        
        if caregiver_info:
            completion_msg += f"\n\nNow sending report to {caregiver_info['caregiver_name']}..."
        
        await update.message.reply_text(completion_msg, parse_mode="Markdown")
        
        # If caregiver exists, generate and send caregiver AUDIO (not videos)
        if caregiver_info and caregiver_script_chunks:
            logger.info(f"🏥 Generating audio for caregiver: {caregiver_info['caregiver_name']}")
            logger.info(f"   Caregiver Telegram ID: {caregiver_info['caregiver_telegram_id']}")
            
            # Generate audio from caregiver script chunks
            full_caregiver_script = " ".join(caregiver_script_chunks)
            caregiver_audio_path = await asyncio.to_thread(
                video_generator.generate_audio_summary, full_caregiver_script
            )
            
            if caregiver_audio_path:
                try:
                    # Get the latest lab data from database
                    latest_reports = await asyncio.to_thread(
                        database.get_user_reports, telegram_id, limit=1
                    )
                    
                    # Send formatted text report first
                    if latest_reports and len(latest_reports) > 0:
                        lab_data = latest_reports[0].get('lab_data', {})
                        formatted_report = format_health_report_for_caregiver(
                            lab_data,
                            user_name
                        )
                        
                        await update.get_bot().send_message(
                            chat_id=caregiver_info['caregiver_telegram_id'],
                            text=formatted_report,
                            parse_mode="Markdown"
                        )
                        logger.info(f"✅ Sent formatted text report to caregiver {caregiver_info['caregiver_name']}")
                    
                    # Create meaningful filename
                    date_str = datetime.now().strftime("%Y-%m-%d_%H-%M")
                    patient_name_clean = user_name.replace(" ", "_")
                    filename = f"Health_Report_{patient_name_clean}_{date_str}.mp3"
                    
                    # Send audio report with details
                    with open(caregiver_audio_path, 'rb') as audio_file:
                        await update.get_bot().send_audio(
                            chat_id=caregiver_info['caregiver_telegram_id'],
                            audio=audio_file,
                            caption="*🎤 Detailed Audio Explanation*\n\n"
                                    "Listen for specific guidance, what to monitor, and action steps.",
                            parse_mode="Markdown",
                            filename=filename
                        )
                    logger.info(f"✅ Sent audio to caregiver {caregiver_info['caregiver_name']} as {filename}")
                    
                    # Clean up caregiver audio file
                    if os.path.exists(caregiver_audio_path):
                        os.remove(caregiver_audio_path)
                    
                    # Notify patient that caregiver update was sent
                    await update.message.reply_text(
                        "Sent report to your family!",
                        parse_mode="Markdown"
                    )
                        
                except Exception as e:
                    logger.error(f"❌ Error sending to caregiver: {e}")
                    logger.error(f"   Error type: {type(e).__name__}")
                    logger.error(f"   Details: {str(e)}")
                    
                    # Notify patient about the error
                    await update.message.reply_text(
                        f"⚠️ Couldn't send report to {caregiver_info['caregiver_name']}\n\n"
                        f"Possible reasons:\n"
                        f"• They haven't started the bot yet (tell them to send /start to @{(await update.get_bot().get_me()).username})\n"
                        f"• Their Telegram ID might be wrong\n\n"
                        f"Error: {str(e)[:100]}",
                        parse_mode="Markdown"
                    )
            else:
                logger.error("❌ Failed to generate caregiver audio")
                await update.message.reply_text(
                    f"⚠️ Couldn't generate audio for {caregiver_info['caregiver_name']}"
                )
        else:
            # No caregiver - send regular completion message
            await update.message.reply_text(
                "Tip: Use `/setcaregiver` to share reports with family!",
                parse_mode="Markdown"
            )
        
        # Save to database (save all chunks) - run in thread
        full_script = " | ".join(script_chunks)
        video_urls_str = " | ".join(sent_videos)
        await asyncio.to_thread(
            database.save_video_summary, telegram_id, full_script, video_urls_str
        )
        
        # Delete processing message
        await video_msg.delete()
            
    except Exception as e:
        logger.error(f"Error creating video: {e}")
        await video_msg.edit_text(
            f"❌ Aiyo! Video creation got problem!\n\nError: {str(e)}\n\nTry again later lah! 😅"
        )


async def create_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Generate sassy Aunty video summary in chunks."""
    # ============================================================
    # 🎬 VIDEO GENERATION TOGGLE
    # ============================================================
    # TO ENABLE VIDEOS: Change ENABLE_VIDEOS to True (line 271 in handle_photo)
    ENABLE_VIDEOS = False  # 👈 MUST MATCH THE FLAG IN handle_photo!
    # ============================================================
    
    if not ENABLE_VIDEOS:
        await update.message.reply_text(
            "⚠️ *Video generation temporarily disabled*\n\n"
            "Saving credits for final features! You'll still get text analysis and memory tracking. 💚",
            parse_mode="Markdown"
        )
        return
    
    user = update.effective_user
    telegram_id = user.id
    user_name = user.first_name or "friend"
    
    processing_msg = await update.message.reply_text(
        "Wah! Aunty going to scold you in video format now! This one take a bit longer hor, wait ah!"
    )
    
    try:
        # Get health summary from database
        health_summary = database.get_health_summary(telegram_id)
        
        if "No health reports" in health_summary:
            await processing_msg.edit_text(
                "Aiyo! You haven't uploaded any lab reports yet lah!\n\nSend me a lab report photo first, then I can scold you properly!"
            )
            return
        
        # Generate sassy video script chunks with Groq
        await processing_msg.edit_text(
            "Writing your scripts now..."
        )
        script_chunks = health_analyzer.generate_video_script_chunks(health_summary, user_name)
        
        await processing_msg.edit_text(
            f"Creating {len(script_chunks)} videos for you now! They'll come one by one..."
        )
        
        # Generate videos concurrently, send in order as ready
        # Create semaphore for batching (3 concurrent)
        semaphore = asyncio.Semaphore(3)
        
        # Dictionary to store completed videos
        completed_videos = {}
        next_to_send = 0
        sent_videos = []
        lock = asyncio.Lock()
        
        async def generate_video_only(chunk: str, index: int):
            """Generate video (no sending here)."""
            async with semaphore:
                # Generate video
                result = await video_generator.generate_single_chunk_async(
                    chunk, index, len(script_chunks)
                )
                idx, chunk_text, video_url = result
                
                # Store result
                async with lock:
                    completed_videos[idx] = (chunk_text, video_url)
                    
                return (idx, chunk_text, video_url)
        
        async def send_videos_in_order():
            """Send videos in order as they become available."""
            nonlocal next_to_send
            
            while next_to_send < len(script_chunks):
                # Wait for next video to be ready
                while next_to_send not in completed_videos:
                    await asyncio.sleep(0.1)
                
                # Get the video
                chunk_text, video_url = completed_videos[next_to_send]
                
                if video_url:
                    caption = f"""
*Part {next_to_send + 1}/{len(script_chunks)}*

"{chunk_text}"
                    """
                    
                    try:
                        await update.message.reply_video(
                            video=video_url,
                            caption=caption,
                            parse_mode="Markdown"
                        )
                        sent_videos.append(video_url)
                        logger.info(f"✅ Sent video {next_to_send + 1}/{len(script_chunks)}")
                    except Exception as e:
                        logger.error(f"Error sending video {next_to_send + 1}: {e}")
                        await update.message.reply_text(
                            f"Video {next_to_send + 1} couldn't be sent: {str(e)}"
                        )
                else:
                    await update.message.reply_text(
                        f"Video {next_to_send + 1} generation failed lah!"
                    )
                
                next_to_send += 1
        
        # Create generation tasks
        generation_tasks = [
            generate_video_only(chunk, i)
            for i, chunk in enumerate(script_chunks)
        ]
        
        # Create sender task
        sender_task = asyncio.create_task(send_videos_in_order())
        
        # Wait for both generation and sending to complete
        await asyncio.gather(*generation_tasks)
        await sender_task
        
        if len(sent_videos) == 0:
            # All videos failed - fall back to audio
            await processing_msg.edit_text(
                "Videos having problem lah! Wait, let me send you audio instead..."
            )
            
            # Generate audio fallback
            logger.info("🎤 All videos failed, falling back to audio generation...")
            
            # Generate full script from chunks (combine them)
            full_script = " ".join(script_chunks)
            
            # Generate audio
            audio_path = await asyncio.to_thread(
                video_generator.generate_audio_summary, full_script
            )
            
            if audio_path:
                # Send audio to user with meaningful filename
                try:
                    date_str = datetime.now().strftime("%Y-%m-%d_%H-%M")
                    filename = f"Dr_Aunty_Health_Advice_{date_str}.mp3"
                    
                    with open(audio_path, 'rb') as audio_file:
                        await update.message.reply_audio(
                            audio=audio_file,
                            caption="*Your Health Summary*\n\nHere's your health advice!",
                            parse_mode="Markdown",
                            filename=filename
                        )
                    logger.info(f"✅ Sent audio to user as {filename}")
                    
                    # Clean up audio file
                    if os.path.exists(audio_path):
                        os.remove(audio_path)
                    
                    await processing_msg.delete()
                    return
                    
                except Exception as e:
                    logger.error(f"Error sending audio: {e}")
                    await processing_msg.edit_text(
                        f"❌ Audio sending failed: {str(e)}\n\nPlease try again later! 😔"
                    )
                    return
            else:
                await processing_msg.edit_text(
                    "❌ Aiyo! Both video AND audio generation failed lah!\n\n"
                    "Maybe try again later? The servers might be busy. 😔"
                )
                return
        
        successful_count = len(sent_videos)
        
        # Send completion message
        completion_msg = f"Done! Sent you {successful_count} videos.\n\nUpload new lab reports to get fresh advice!"
        
        await update.message.reply_text(completion_msg, parse_mode="Markdown")
        
        # Save to database (save all chunks)
        full_script = " | ".join(script_chunks)
        video_urls_str = " | ".join(sent_videos)
        database.save_video_summary(telegram_id, full_script, video_urls_str)
        
        # Delete processing message
        await processing_msg.delete()
            
    except Exception as e:
        logger.error(f"Error creating video: {e}")
        await processing_msg.edit_text(
            f"❌ Aiyo! Video creation got problem!\n\nError: {str(e)}\n\nTry again later lah! 😅"
        )


async def history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user's health report history."""
    user = update.effective_user
    telegram_id = user.id
    
    reports = database.get_user_reports(telegram_id, limit=5)
    
    if not reports:
        await update.message.reply_text(
            "No health reports yet lah!\n\nSend me a lab report photo to get started!"
        )
        return
    
    history_text = "*Your Health Report History*\n\n"
    
    for i, report in enumerate(reports, 1):
        lab_data = report.get("lab_data", {})
        test_date = lab_data.get("test_date", "Unknown")
        
        history_text += f"*{i}. Report from {test_date}*\n"
        
        # Show key tests
        tests = lab_data.get("tests", [])
        abnormal_count = sum(1 for t in tests if t.get("status") != "normal")
        
        history_text += f"   • {len(tests)} tests analyzed\n"
        if abnormal_count > 0:
            history_text += f"   • {abnormal_count} values outside normal range\n"
        history_text += "\n"
    
    history_text += "\nUse /video to create a summary video!"
    
    await update.message.reply_text(history_text, parse_mode="Markdown")


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user statistics."""
    user = update.effective_user
    telegram_id = user.id
    
    reports = database.get_user_reports(telegram_id)
    memories = memory_manager.get_all_memories(str(telegram_id))
    
    if not reports:
        await update.message.reply_text(
            "No statistics yet lah! Upload some lab reports first!"
        )
        return
    
    total_tests = sum(
        len(r.get("lab_data", {}).get("tests", [])) 
        for r in reports
    )
    
    avg_response_time = sum(
        r.get("response_time", 0) for r in reports
    ) / len(reports) if reports else 0
    
    stats_text = f"""
*Your Health Tracking Stats*

Total reports: {len(reports)}
Total tests analyzed: {total_tests}
Memories stored: {len(memories)}

You're doing great keeping track! Keep it up!
    """
    
    await update.message.reply_text(stats_text, parse_mode="Markdown")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle text messages - chat with Dr. Aunty."""
    user = update.effective_user
    telegram_id = user.id
    user_message = update.message.text
    
    # Get context from memory
    health_history = memory_manager.get_health_history(str(telegram_id), limit=2)
    
    # Chat with Dr. Aunty using Groq
    response, response_time = health_analyzer.chat_with_aunty(
        user_message,
        health_history
    )
    
    # Save conversation to memory
    memory_manager.add_conversation(str(telegram_id), user_message, response)
    
    # Send response
    await update.message.reply_text(
        response,
        parse_mode="Markdown"
    )


def main() -> None:
    """Start the bot."""
    # Create the Application with SSL verification disabled (for local development)
    from telegram.request import HTTPXRequest
    
    # Create custom request with SSL verification disabled
    request = HTTPXRequest(
        connection_pool_size=8,
        connect_timeout=5.0,
        read_timeout=5.0,
        write_timeout=5.0,
        pool_timeout=1.0,
    )
    
    # Disable SSL verification
    import httpx
    custom_client = httpx.AsyncClient(verify=False)
    request._client = custom_client
    
    application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).request(request).build()
    
    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("setcaregiver", setcaregiver))
    application.add_handler(CommandHandler("video", create_video))
    application.add_handler(CommandHandler("history", history))
    application.add_handler(CommandHandler("stats", stats))
    
    # Photo handler for lab reports
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    # Text message handler for chatting
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Start the Bot
    print("🚀 Dr. Aunty is starting...")
    print("✅ Groq: Lightning-fast LLM")
    print("✅ Gemini: Vision AI for lab reports")
    print("✅ Mem0: Health memory system")
    print("✅ fal.ai: Talking avatar videos (primary)")
    print("✅ OpenAI Sora 2: Video fallback (secondary)")
    print("✅ ElevenLabs: Audio fallback (final, always works!)")
    print("✅ Supabase: Database storage")
    print("\n👵 Dr. Aunty is ready lah! Send /start to begin!\n")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
