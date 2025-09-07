🎤 Voice-Powered Flowchart Generator
------
Build and edit flowcharts using voice or text instructions, powered by Google Gemini AI and Graphviz.
----------------------------
**✨ Features**

🎙️ Voice input (Web Speech API) — build flowcharts hands-free.

⌨️ Text input — type instructions if preferred.

📂 Load predefined templates (warehouse, top_side, bottom_side).

🔄 Add steps iteratively to expand flowcharts.

📑 Export to PDF — flowcharts are embedded into a professional PDF template.

🗂️ Session management — each user’s flowcharts are stored separately.

**🛠️ Tech Stack**

**Frontend:** HTML, TailwindCSS, JavaScript (Web Speech API).

**Backend:** Flask (Python).

**AI:** Google Gemini (google-generativeai).

**Flowchart Rendering:** Graphviz (dot).

**PDF Handling:** PyMuPDF (fitz).

**📂 Project Structure**

project-root/

│── app.py                # Flask app (routes, API endpoints)

│── backend.py            # Core flowchart + AI logic

│── requirements.txt      # Python dependencies

│── .env                  # API key (Google Gemini)

│── Template.pdf          # Base PDF template

│

├── templates/

│   └── index.html        # Frontend UI

│

├── flowchart_templates/  # Predefined flowcharts

│   ├── warehouse.dot

│   ├── top_side.dot

│   └── bottom_side.dot

│

├── outputs/              # Generated PDFs

├── session_files/        # Per-user DOT sessions

└── temp_files/           # Temporary files

**⚙️ Installation**

1️⃣ Clone the Repository
git clone https://github.com/your-username/voice-flowchart-generator.git
cd voice-flowchart-generator

2️⃣ Install Dependencies
pip install -r requirements.txt

3️⃣ Set Up Environment Variables

Create a .env file in the project root:

GOOGLE_API_KEY="your_google_gemini_api_key"

4️⃣ Install Graphviz

Windows: 

Download from Graphviz
and update DOT_PATH in backend.py.

Linux/macOS:

sudo apt-get install graphviz       # Ubuntu/Debian

brew install graphviz               # macOS

5️⃣ Run the Flask App
python app.py

**🌐 Usage**

**[1]** Open https://localhost:5000

**[2]** Enter your email.

**[3]** Provide instructions either by:

🎤 Clicking the microphone button and speaking,

✍️ Typing into the textbox.

**[4]** Click “New from Instruction” to create a flowchart.

**[5]** Use “Add to Flowchart” to expand it.

**[6]** Or load predefined templates from the dropdown.

**[7]** View the generated PDF flowchart in the right-side panel.
