import os
import logging
import google.generativeai as genai
from io import BytesIO
import asyncio # For potential async operations if needed later

from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

# Optional: Load .env file for local development
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("Loaded environment variables from .env")
except ImportError:
    print(".env file not found or python-dotenv not installed, relying on system environment variables.")

# --- Configuration ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
# Specify the Gemini model potentially capable of image generation
# IMPORTANT: This is hypothetical. As of early 2025, 'gemini-pro' does NOT generate images.
# You might need a specific model name (e.g., from Vertex AI Imagen) or this might change in the future.
# Replace 'models/gemini-1.5-flash-latest' or similar with the CORRECT model if one becomes available
# For now, we structure the code assuming such a model exists via this library.
IMAGE_GEN_MODEL_NAME = 'models/gemini-1.5-flash-latest' # Placeholder - CHANGE IF NEEDED

# --- Logging Setup ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING) # Reduce httpx noise
logger = logging.getLogger(__name__)

# --- Google AI Setup ---
if not GOOGLE_API_KEY:
    logger.error("GOOGLE_API_KEY environment variable not set!")
    exit(1) # Or handle more gracefully

try:
    genai.configure(api_key=GOOGLE_API_KEY)
    # Initialize the specific model - Adapt this if using Vertex AI / Imagen
    # This instantiation is ALSO HYPOTHETICAL for direct image generation via this library.
    image_model = genai.GenerativeModel(IMAGE_GEN_MODEL_NAME)
    logger.info(f"Google AI configured with model: {IMAGE_GEN_MODEL_NAME}")
except Exception as e:
    logger.error(f"Failed to configure Google AI: {e}", exc_info=True)
    exit(1)

# --- Telegram Bot Functions ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a welcome message when the /start command is issued."""
    user_name = update.effective_user.first_name
    welcome_message = (
        f"Hi {user_name}! 👋\n\n"
        "I can generate images based on your descriptions using Google's AI.\n\n"
        "Use the command `/generate <your detailed description>` to create an image.\n\n"
        "Example:\n`/generate A futuristic cityscape at sunset, cyberpunk style`"
    )
    await update.message.reply_text(welcome_message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends help message when the /help command is issued."""
    help_text = (
        "**How to use me:**\n"
        "1. Use the `/generate` command followed by a description of the image you want.\n"
        "   Example: `/generate A fluffy white cat sleeping on a bookshelf`\n\n"
        "2. Be descriptive! The more detail you provide, the better the AI can understand your request.\n\n"
        "**Important Note:** Image generation can take a few moments. Please be patient."
    )
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)


async def generate_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Generates an image based on the user's prompt."""
    if not context.args:
        await update.message.reply_text(
            "Please provide a description after the /generate command.\n"
            "Example: `/generate A serene beach with palm trees`"
        )
        return

    prompt = " ".join(context.args)
    chat_id = update.effective_chat.id
    user_name = update.effective_user.first_name

    logger.info(f"Received image generation request from {user_name} (Chat ID: {chat_id}): '{prompt}'")

    # Send a "processing" message
    processing_message = await update.message.reply_text("✨ Generating your image... Please wait.")

    try:
        # --- Call the Google AI Image Generation API ---
        # IMPORTANT: This is the HYPOTHETICAL part.
        # The actual method to generate images might differ significantly.
        # You might need to use `image_model.generate_content` with specific parameters,
        # or switch to the Vertex AI SDK for Imagen models.
        # This assumes the API returns an object with accessible image bytes.

        # Example using generate_content (Adapt based on actual API capabilities):
        # Note: Gemini Pro models typically require multimodal input (text + image) for vision tasks,
        # or just text for text generation. Text-to-image is usually Imagen.
        # Let's *assume* generate_content could be adapted or a future model supports it.
        # THIS WILL LIKELY FAIL with current standard Gemini Pro models.
        response = await asyncio.to_thread(
             image_model.generate_content,
             f"Generate an image depicting: {prompt}", # Adjust prompt structure as needed
             # generation_config=genai.types.GenerationConfig(...) # Add specific configs if required
             # safety_settings=... # Add safety settings
        )

        # --- Process the Response ---
        # This part heavily depends on the *actual* structure of the response object
        # from the image generation call. You'll need to inspect the 'response' object
        # when you have a working generation call.
        # Assumption: Response contains image data directly or indirectly.

        # --- Hypothetical Response Handling ---
        # Check if the response has image data. Adjust attribute names as needed.
        # This could be response.parts[0].blob, response.image_bytes, response.data, etc.
        # You MUST adapt this based on the real API response.
        if hasattr(response, 'parts') and response.parts and hasattr(response.parts[0], 'blob') and response.parts[0].blob.mime_type.startswith('image/'):
             image_bytes = response.parts[0].blob.data
             logger.info(f"Image generated successfully for: '{prompt}'")
        # --- Add other potential response structures here ---
        # elif hasattr(response, 'image_bytes'):
        #     image_bytes = response.image_bytes
        #     logger.info(f"Image generated successfully for: '{prompt}'")
        else:
             # Log the actual response to understand its structure if generation succeeded but data wasn't found
             logger.warning(f"Image generation call succeeded for '{prompt}', but couldn't find image data in the expected format. Response: {response}")
             error_text_user = "Sorry, I received a response from the AI, but couldn't extract the image data."
             image_bytes = None # Ensure image_bytes is None

        # --- Alternative: Placeholder if API call structure is unknown ---
        # logger.warning("Simulating image generation - Replace with actual API call and response handling.")
        # # Placeholder: Create a dummy image for testing structure
        # from PIL import Image, ImageDraw, ImageFont
        # img = Image.new('RGB', (300, 100), color = (73, 109, 137))
        # d = ImageDraw.Draw(img)
        # try:
        #     font = ImageFont.truetype("arial.ttf", 15) # Requires font file or adjust path
        # except IOError:
        #     font = ImageFont.load_default()
        # d.text((10,10), f"Generated: {prompt[:30]}...", fill=(255,255,0), font=font)
        # buffer = BytesIO()
        # img.save(buffer, format='PNG')
        # image_bytes = buffer.getvalue()
        # --- End Placeholder ---


        # --- Send Image or Error Message ---
        if image_bytes:
            image_file = InputFile(BytesIO(image_bytes), filename=f"generated_image_{chat_id}.png")
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=image_file,
                caption=f"Here's the image for: \"{prompt}\"\n\nGenerated by Google AI."
            )
            # Delete the "processing..." message
            await context.bot.delete_message(chat_id=chat_id, message_id=processing_message.message_id)
        else:
             # If image_bytes is None after trying to generate
             await processing_message.edit_text(
                 f"Sorry {user_name}, I couldn't generate an image for that prompt. The AI might not have understood, or there was an internal error."
             )

    except genai.types.BlockedPromptException as e:
        logger.warning(f"Image generation blocked for prompt: '{prompt}'. Reason: {e}")
        await processing_message.edit_text(f"Sorry {user_name}, your request was blocked due to safety reasons. Please try a different prompt.")
    except genai.types.StopCandidateException as e:
         logger.warning(f"Image generation stopped for prompt: '{prompt}'. Reason: {e}")
         await processing_message.edit_text(f"Sorry {user_name}, the generation was stopped. This might be due to safety filters or content policy. Please refine your prompt.")
    except Exception as e:
        logger.error(f"Error during image generation for prompt '{prompt}': {e}", exc_info=True)
        await processing_message.edit_text(f"Sorry {user_name}, an unexpected error occurred while trying to generate the image. Please try again later.")


# --- Main Bot Execution ---
def main() -> None:
    """Start the bot."""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN environment variable not set!")
        return

    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("generate", generate_image))

    # Add a fallback handler for unknown commands (optional)
    # application.add_handler(MessageHandler(filters.COMMAND, unknown_command))

    logger.info("Starting bot polling...")
    # Run the bot until the user presses Ctrl-C
    # For Render.com (Background Worker), polling is fine.
    # If you were using a Web Service on Render, you'd set up a webhook.
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
