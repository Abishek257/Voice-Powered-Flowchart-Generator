import os
import subprocess
from pathlib import Path
import google.generativeai as genai
import re
import fitz  # PyMuPDF library for PDF manipulation
from dotenv import load_dotenv # Import the library

# --- Configuration ---

# Load environment variables from .env file
load_dotenv() # <-- Add this line to load the .env file

# 1. Configure Google AI (Gemini) API Key
try:
    api_key = os.environ["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
except KeyError:
    print("❌ Error: GOOGLE_API_KEY not found. Make sure it is set in your .env file.")
    exit()

# 2. Select the Gemini model
MODEL = genai.GenerativeModel('gemini-1.5-flash')

# 3. Create directories for files
TEMP_DIR = Path("./temp_files")
SESSION_DIR = Path("./session_files")
OUTPUT_DIR = Path("./outputs")
TEMPLATE_DIR = Path("./flowchart_templates") # <-- Add this line
TEMP_DIR.mkdir(exist_ok=True)
SESSION_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
TEMPLATE_DIR.mkdir(exist_ok=True) # <-- Add this line

# 4. Full path to the Graphviz 'dot.exe' executable
DOT_PATH = "C:/Program Files/Graphviz/bin/dot.exe" 

# 5. Define the PDF template file
PDF_TEMPLATE_PATH = "Template.pdf"


# --- Helper Functions ---

def sanitize_email_for_folder(email: str) -> str:
    """Sanitizes an email address to be used as a valid folder name."""
    return re.sub(r'[^a-zA-Z0-9_-]', '_', email)

def generate_initial_dot_code(prompt_text: str) -> str | None:
    """Uses Gemini to create the very first version of the DOT code."""
    print(f"🧠 Generating INITIAL DOT code for prompt: '{prompt_text[:50]}...'")
    system_prompt = f"""
    You are an expert in the Graphviz DOT language. A user will provide their first instruction to start a flowchart.
    Your task is to create the initial DOT graph for this first step.

    Rules:
    1.  Start the graph with `digraph flowchart {{` and `rankdir="TB";`.
    2.  Create nodes for the first step described by the user.
    3.  If the user's text includes spaces, the node label MUST be in double quotes. Example: `FirstStep [label="First Step"];`.
    4.  Return ONLY the complete DOT code, ending with `}}`.

    User's first instruction: "{prompt_text}"
    """
    try:
        response = MODEL.generate_content(system_prompt)
        dot_code = response.text.strip().replace("```dot", "").replace("```", "").strip()
        print("✅ Initial DOT code generated.")
        return dot_code
    except Exception as e:
        print(f"❌ An error occurred during AI generation: {e}")
        return None

def modify_dot_code(current_dot_code: str, prompt_text: str) -> str | None:
    """Uses Gemini to modify an existing DOT code based on a new user instruction."""
    print(f"🧠 MODIFTYING DOT code with instruction: '{prompt_text[:50]}...'")
    system_prompt = f"""
    You are an expert in the Graphviz DOT language who is helping a user build a flowchart step-by-step.
    You will be given the CURRENT DOT code and the user's NEXT instruction.
    Your task is to modify the current DOT code to incorporate the new instruction.

    Rules:
    1.  Analyze the current DOT code and the user's instruction.
    2.  Add or modify nodes and edges as requested.
    3.  Remember to use double quotes for any labels with spaces. Example: `NewStep [label="New Step"];`.
    4.  IMPORTANT: When connecting nodes, use a simple arrow `->`. Do NOT use the user's instruction as a label on the arrow. Only add a label if the user explicitly asks for one, such as for a decision path (e.g., 'label it Pass').
    5.  Return ONLY the complete, new, updated DOT code. Do not include explanations.

    Current DOT Code:
    ```dot
    {current_dot_code}
    ```

    User's Next Instruction: "{prompt_text}"
    """
    try:
        response = MODEL.generate_content(system_prompt)
        dot_code = response.text.strip().replace("```dot", "").replace("```", "").strip()
        print("✅ DOT code modified successfully.")
        return dot_code
    except Exception as e:
        print(f"❌ An error occurred during AI generation: {e}")
        return None

def convert_dot_to_png(dot_code: str, output_path: Path) -> bool:
    """Uses Graphviz to convert DOT code into a PNG image."""
    dot_file = TEMP_DIR / f"{output_path.stem}.dot"
    dot_file.write_text(dot_code)
    
    print(f"🔄 Converting DOT file '{dot_file}' to PNG using Graphviz...")
    command = [DOT_PATH, "-Tpng", "-o", str(output_path), str(dot_file)]

    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"✅ PNG image saved successfully to '{output_path}'")
        return True
    except FileNotFoundError:
        print(f"❌ Error: 'dot' command not found at {DOT_PATH}")
        return False
    except subprocess.CalledProcessError as e:
        print(f"❌ Error during Graphviz execution: {e.stderr}")
        return False
    finally:
        if dot_file.exists():
            dot_file.unlink()

def embed_image_in_pdf(template_path: str, image_path: Path, output_pdf_path: Path) -> bool:
    """Opens a PDF template, embeds the generated flowchart image, and saves a new PDF."""
    print(f"📄 Embedding image '{image_path}' into PDF template '{template_path}'...")
    try:
        if not Path(template_path).exists():
            print(f"❌ PDF Template not found at {template_path}")
            return False
        doc = fitz.open(template_path)
        page = doc[0]
        rect = fitz.Rect(50, 120, page.rect.width - 50, page.rect.height - 50)
        page.insert_image(rect, filename=str(image_path))
        doc.save(str(output_pdf_path))
        doc.close()
        print(f"✅ PDF with embedded flowchart saved as '{output_pdf_path}'")
        return True
    except Exception as e:
        print(f"❌ An error occurred during PDF creation: {e}")
        return False

def process_dot_code(dot_code: str, session_file: Path):
    """Saves DOT code, converts to PNG, embeds in PDF, and cleans up."""
    session_file.write_text(dot_code)

    temp_png_path = TEMP_DIR / f"{session_file.stem}.png"
    output_pdf_filename = f"flowchart_{session_file.stem}.pdf"
    output_pdf_path = OUTPUT_DIR / output_pdf_filename

    if not convert_dot_to_png(dot_code, temp_png_path):
        return None, "Failed to convert flowchart to an image."

    if not embed_image_in_pdf(PDF_TEMPLATE_PATH, temp_png_path, output_pdf_path):
        return None, "Failed to embed image in PDF."

    if temp_png_path.exists():
        temp_png_path.unlink()

    return output_pdf_filename, None

def process_flowchart_request(user_prompt: str, session_file: Path, is_new: bool):
    """Generates or modifies DOT code via AI and then processes it."""
    
    if is_new:
        dot_code = generate_initial_dot_code(user_prompt)
    else:
        current_dot_code = session_file.read_text()
        dot_code = modify_dot_code(current_dot_code, user_prompt)

    if not dot_code:
        return None, "Failed to generate flowchart logic."

    return process_dot_code(dot_code, session_file)