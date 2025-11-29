from flask import Flask, render_template, request, send_file, session, redirect, url_for, flash, jsonify
from db import get_db_connection 
from flask_bcrypt import Bcrypt
from flask_session import Session
from gtts import gTTS
import os
from datetime import datetime
from flask import send_file
import speech_recognition as sr


app = Flask(__name__)
bcrypt = Bcrypt(app)

# Configure session
app.secret_key = "super_secret_key"
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Ensure TTS audio folder exists
AUDIO_FOLDER = "static/tts_audio"
os.makedirs(AUDIO_FOLDER, exist_ok=True)

# Ensure STT audio storage folder exists
STT_FOLDER = "static/stt_texts"
os.makedirs(STT_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = STT_FOLDER

# ✅ Ensure Braille folder exists
BRAILLE_FOLDER = "static/braille_texts"
os.makedirs(BRAILLE_FOLDER, exist_ok=True)

# Folder to store converted Braille files
STB_FOLDER = "static/stb_files"
os.makedirs(STB_FOLDER, exist_ok=True)


# ✅ Custom Braille Dictionary
BRAILLE_DICT = {
    "a": "⠁", "b": "⠃", "c": "⠉", "d": "⠙", "e": "⠑", "f": "⠋", "g": "⠛", "h": "⠓",
    "i": "⠊", "j": "⠚", "k": "⠅", "l": "⠇", "m": "⠍", "n": "⠝", "o": "⠕", "p": "⠏",
    "q": "⠟", "r": "⠗", "s": "⠎", "t": "⠞", "u": "⠥", "v": "⠧", "w": "⠺", "x": "⠭",
    "y": "⠽", "z": "⠵",
    "A": "⠠⠁", "B": "⠠⠃", "C": "⠠⠉", "D": "⠠⠙", "E": "⠠⠑", "F": "⠠⠋", "G": "⠠⠛", "H": "⠠⠓",
    "I": "⠠⠊", "J": "⠠⠚", "K": "⠠⠅", "L": "⠠⠇", "M": "⠠⠍", "N": "⠠⠝", "O": "⠠⠕", "P": "⠠⠏",
    "Q": "⠠⠟", "R": "⠠⠗", "S": "⠠⠎", "T": "⠠⠞", "U": "⠠⠥", "V": "⠠⠧", "W": "⠠⠺", "X": "⠠⠭",
    "Y": "⠠⠽", "Z": "⠠⠵",
    "0": "⠴", "1": "⠂", "2": "⠆", "3": "⠒", "4": "⠲", "5": "⠢", "6": "⠖", "7": "⠶", "8": "⠦", "9": "⠔",
    ".": "⠲", ",": "⠂", "?": "⠦", "!": "⠖", "-": "⠤", "(": "⠶", ")": "⠶", "\"": "⠶⠶", "'": "⠄",
    ":": "⠒", ";": "⠆", "/": "⠌", "+": "⠖", "=": "⠶", "*": "⠔", "@": "⠈⠁", "&": "⠯", "%": "⠴⠴"
}

# Home Route (Redirects to Login)
@app.route("/")
def home():
     return render_template("index.html")

# ✅ Signup Route
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("signup-name")
        email = request.form.get("signup-email")
        password = request.form.get("signup-password")

        if not username or not email or not password:
            flash("All fields are required!", "error")
            return redirect(url_for("signup"))

        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

        db = get_db_connection()
        cursor = db.cursor()

        try:
            # Check if email already exists
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            if cursor.fetchone():
                flash("User ID already exists! Please log in.", "error")
                return redirect(url_for("login"))

            # Insert new user
            cursor.execute("INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)", 
                           (username, email, hashed_password))
            db.commit()
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for("login"))
        except Exception as e:
            db.rollback()
            flash(f"Error: {e}", "error")
        finally:
            cursor.close()
            db.close()

    return render_template("signup.html")

#LOGIN ROUTE
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")  # ✅ Matches input name in login.html
        password = request.form.get("password")  # ✅ Matches input name in login.html

        db = get_db_connection()
        cursor = db.cursor()

        # Fetch user from DB
        cursor.execute("SELECT id, username, password_hash FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        db.close()

        if user and bcrypt.check_password_hash(user[2], password):
            session["user_id"] = user[0]
            session["username"] = user[1]
            flash("Login successful!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid email or password!", "error")
            return redirect(url_for("login"))

    return render_template("login.html")

# Dashboard Route (Accessible only if logged in)
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        flash("You must log in first.", "error")
        return redirect(url_for("login"))
    return render_template("dashboard.html")

# Logout Route
@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


# Contact Page
@app.route("/contact")
def contact():
    return render_template("contact.html")

# Feedback Page
@app.route("/feedback")
def feedback():
    return render_template("feedback.html")

# Conversion Feature Routes (Only accessible if logged in)
#TTS
# ✅ TTS Conversion Route
@app.route("/text-to-speech", methods=["GET", "POST"])
def text_to_speech():
    if "user_id" not in session:
        flash("You must log in first.", "error")
        return redirect(url_for("login"))

    if request.method == "POST":
        text = request.form.get("tts-input")
        if not text:
            flash("Please enter text for conversion.", "error")
            return redirect(url_for("text_to_speech"))

        # Generate MP3 File
        tts = gTTS(text=text, lang="en")
        filename = f"tts_{session['user_id']}_{int(datetime.now().timestamp())}.mp3"
        file_path = os.path.join(AUDIO_FOLDER, filename)
        tts.save(file_path)

        # Save Conversion to Database
        db = get_db_connection()
        cursor = db.cursor()
        try:
            cursor.execute(
                "INSERT INTO tts_history (user_id, text, file_path) VALUES (%s, %s, %s)",
                (session["user_id"], text, file_path)
            )
            db.commit()
            flash("Conversion successful!Your file is downloaded!!!.", "success")
        except Exception as e:
            db.rollback()
            flash(f"Error: {e}", "error")
        finally:
            cursor.close()
            db.close()

        return redirect(url_for("text_to_speech"))

    return render_template("text_to_speech.html")

@app.route("/download_tts/<filename>")
def download_tts(filename):
    file_path = os.path.join(AUDIO_FOLDER, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        flash("File not found!", "error")
        return redirect(url_for("text_to_speech"))






@app.route("/speech-to-text", methods=["GET", "POST"])
def speech_to_text():
    if "user_id" not in session:
        flash("You must log in first.", "error")
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == "POST":
        if "audio_file" not in request.files or request.files["audio_file"].filename == "":
            flash("No file uploaded.", "error")
            return redirect(url_for("speech_to_text"))

        file = request.files["audio_file"]
        filename = f"{session['user_id']}_{file.filename}"  # Store filename with user_id
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)

        # Convert speech to text
        recognizer = sr.Recognizer()
        with sr.AudioFile(filepath) as source:
            audio_data = recognizer.record(source)

        try:
            converted_text = recognizer.recognize_google(audio_data)
            session["stt_text"] = converted_text

            # Save text file
            text_filename = f"{filename}.txt"
            text_filepath = os.path.join(app.config["UPLOAD_FOLDER"], text_filename)
            with open(text_filepath, "w", encoding="utf-8") as text_file:
                text_file.write(converted_text)
            session["stt_text_file"] = text_filename

            # ✅ Store in database
            user_id = session["user_id"]
            cursor.execute("INSERT INTO speech_text (user_id, audio_filename, converted_text) VALUES (%s, %s, %s)", 
                           (user_id, filename, converted_text))
            conn.commit()

            flash("Speech converted successfully!", "success")
        except sr.UnknownValueError:
            flash("Could not understand the audio.", "error")
        except sr.RequestError:
            flash("Speech recognition service error.", "error")

    # ✅ Fetch previous conversions
    cursor.execute("SELECT audio_filename, converted_text, timestamp FROM speech_text WHERE user_id = %s ORDER BY timestamp DESC", (session["user_id"],))
    conversions = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("speech_to_text.html", conversions=conversions)


@app.route("/download_stt")
def download_stt():
    if "stt_text_file" in session:
        return send_file(os.path.join(STT_FOLDER, session["stt_text_file"]), as_attachment=True)
    else:
        flash("No text file available for download.", "error")
        return redirect(url_for("speech_to_text"))






# ✅ Convert Text to Braille
def convert_to_braille(text):
    return "".join(BRAILLE_DICT.get(char, char) for char in text)

# ✅ Text-to-Braille Route
@app.route("/text-to-braille", methods=["GET", "POST"])
def text_to_braille():
    if "user_id" not in session:
        flash("You must log in first.", "error")
        return redirect(url_for("login"))

    if request.method == "POST":
        input_text = request.form.get("braille-input", "").strip()

        if not input_text:
            flash("Please enter text to convert!", "error")
            return redirect(url_for("text_to_braille"))

        # Convert to Braille
        braille_text = convert_to_braille(input_text)

        # Save as TXT file
        filename = f"braille_{session['user_id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}.txt"
        file_path = os.path.join(BRAILLE_FOLDER, filename)

        with open(file_path, "w", encoding="utf-8") as file:
            file.write(braille_text)

        # Store in Database
        db = get_db_connection()
        cursor = db.cursor()
        try:
            cursor.execute(
                "INSERT INTO braille_conversions (user_id, input_text, braille_text, file_path) VALUES (%s, %s, %s, %s)",
                (session["user_id"], input_text, braille_text, file_path)
            )
            db.commit()
            flash("Conversion successful! You can download your file.", "success")
        except Exception as e:
            db.rollback()
            flash(f"Database error: {e}", "error")
        finally:
            cursor.close()
            db.close()

        session["braille_file"] = filename
        return redirect(url_for("text_to_braille"))

    return render_template("text_to_braille.html")

# ✅ Download Converted Braille File
@app.route("/download_braille")
def download_braille():
    if "braille_file" in session:
        return send_file(os.path.join(BRAILLE_FOLDER, session["braille_file"]), as_attachment=True)
    else:
        flash("No Braille file available for download.", "error")
        return redirect(url_for("text_to_braille"))








# ✅ Convert Text to Braille
def convert_to_braille(text):
    return "".join(BRAILLE_DICT.get(char, char) for char in text)

# ✅ API for JavaScript-based Braille conversion
@app.route("/convert_braille_js", methods=["POST"])
def convert_braille_js():
    data = request.get_json()
    text = data.get("text", "")
    braille_text = convert_to_braille(text)
    return jsonify({"braille": braille_text})

# ✅ Speech to Braille Route
@app.route("/speech-to-braille", methods=["GET", "POST"])
def speech_to_braille():
    if "user_id" not in session:
        flash("You must log in first.", "error")
        return redirect(url_for("login"))

    braille_text = ""

    if request.method == "POST":
        if "audio_file" in request.files:
            file = request.files["audio_file"]
            if file.filename == "":
                flash("No audio file selected.", "error")
                return redirect(url_for("speech_to_braille"))

            # ✅ Save Audio File
            audio_path = os.path.join(STB_FOLDER, file.filename)
            file.save(audio_path)

            # ✅ Convert Speech to Text
            recognizer = sr.Recognizer()
            with sr.AudioFile(audio_path) as source:
                audio_data = recognizer.record(source)
            try:
                text_output = recognizer.recognize_google(audio_data)
                braille_text = convert_to_braille(text_output)

                # ✅ Save Braille text as a file
                braille_filename = f"braille_{datetime.now().strftime('%Y%m%d%H%M%S')}.txt"
                braille_filepath = os.path.join(STB_FOLDER, braille_filename)

                with open(braille_filepath, "w", encoding="utf-8") as braille_file:
                    braille_file.write(braille_text)

                session["braille_file"] = braille_filename
                flash("Speech converted to Braille successfully!", "success")

            except sr.UnknownValueError:
                flash("Could not understand the audio.", "error")
            except sr.RequestError:
                flash("Speech recognition service error.", "error")

    return render_template("speech_to_braille.html", braille_text=braille_text)

# ✅ Download Braille File
@app.route("/download_stb")
def download_stb():
    if "braille_file" in session:
        return send_file(os.path.join(STB_FOLDER, session["braille_file"]), as_attachment=True)
    else:
        flash("No Braille file available for download.", "error")
        return redirect(url_for("speech_to_braille"))
# # ✅ Function: Convert Text to Braille
# def text_to_braille(text):
#     return "".join(BRAILLE_DICT.get(char, char) for char in text)


# # ✅ Speech to Braille Route
# @app.route("/speech-to-braille", methods=["GET", "POST"])
# def speech_to_braille():
#     if "user_id" not in session:
#         flash("You must log in first.", "error")
#         return redirect(url_for("login"))

#     if request.method == "POST":
#         file = request.files.get("audio_file")
#         if not file or file.filename == "":
#             flash("No audio file provided.", "error")
#             return redirect(url_for("speech_to_braille"))

#         # Save audio file
#         audio_path = os.path.join(STB_FOLDER, file.filename)
#         file.save(audio_path)

#         # Convert Speech to Text
#         recognizer = sr.Recognizer()
#         with sr.AudioFile(audio_path) as source:
#             audio_data = recognizer.record(source)

#         try:
#             text_output = recognizer.recognize_google(audio_data)
#             braille_output = text_to_braille(text_output)

#             # Save Braille as File
#             # ✅ Save Braille as a file (UTF-8 encoding to avoid errors)
#             braille_filename = f"{file.filename}.txt"
#             braille_filepath = os.path.join(STB_FOLDER, braille_filename)

#             # ✅ Open file explicitly in UTF-8 mode
#             with open(braille_filepath, "w", encoding="utf-8") as braille_file:
#                 braille_file.write(braille_output)


#             # ✅ Save to Database
#             db = get_db_connection()
#             cursor = db.cursor()
#             cursor.execute(
#                 "INSERT INTO speech_to_braille (user_id, audio_path, text_output, braille_output, braille_file_path) VALUES (%s, %s, %s, %s, %s)",
#                 (session["user_id"], audio_path, text_output, braille_output, braille_filepath)
#             )
#             db.commit()
#             cursor.close()
#             db.close()

#             session["stb_file"] = braille_filename
#             flash("Speech converted to Braille successfully!", "success")
#         except sr.UnknownValueError:
#             flash("Could not understand the audio.", "error")
#         except sr.RequestError:
#             flash("Speech recognition service error.", "error")

#         return redirect(url_for("speech_to_braille"))

#     return render_template("speech_to_braille.html")

# # ✅ Download Braille File
# @app.route("/download_stb")
# def download_stb():
#     if "stb_file" in session:
#         return send_file(os.path.join(STB_FOLDER, session["stb_file"]), as_attachment=True)
#     else:
#         flash("No Braille file available for download.", "error")
#         return redirect(url_for("speech_to_braille"))
    

# Feedback Submission
@app.route("/submit_feedback", methods=["POST"])
def submit_feedback():
    name = request.form.get("name")
    email = request.form.get("email")
    rating = request.form.get("rating")
    category = request.form.get("category")
    feedback_text = request.form.get("feedback")

    if not name or not email or not rating or not category or not feedback_text:
        flash("All fields are required!", "error")
        return redirect(url_for("feedback"))

    db = get_db_connection()
    cursor = db.cursor()

    try:
        cursor.execute(
            "INSERT INTO feedback (name, email, rating, category, feedback_text) VALUES (%s, %s, %s, %s, %s)",
            (name, email, rating, category, feedback_text)
        )
        db.commit()
        flash("Feedback submitted successfully!", "success")
    except Exception as e:
        db.rollback()
        flash(f"Error: {e}", "error")
    finally:
        cursor.close()
        db.close()

    return redirect(url_for("feedback"))

# Run Application
if __name__ == "__main__":
    app.run(debug=True)
