import tkinter as tk
from tkinter import messagebox, ttk
import speech_recognition as sr
import pyttsx3
import threading
from queue import Queue
from datetime import datetime
import webbrowser
import pyjokes
import wikipedia
import os
from wikipedia.exceptions import DisambiguationError, PageError, WikipediaException

# ---------------- Setup ----------------
recognizer = sr.Recognizer()
engine = pyttsx3.init()
engine.setProperty('rate', 150)
wake_word = "hey jaya"

# Safe speaking queue
speech_queue = Queue()

# Background speaker thread
def speech_loop():
    while True:
        text = speech_queue.get()
        if text == "exit":
            break
        if text:
            try:
                engine.say(text)
                engine.runAndWait()
            except RuntimeError as e:
                print("TTS Error:", e)

speech_thread = threading.Thread(target=speech_loop, daemon=True)
speech_thread.start()

wikipedia.set_lang("en")
wikipedia.set_rate_limiting(True)

def speak(text):
    speech_queue.put(text)

def wikipedia_search(query):
    try:
        try:
            return wikipedia.summary(query, sentences=2, auto_suggest=False)
        except (PageError, DisambiguationError):
            return wikipedia.summary(query, sentences=2, auto_suggest=True)
    except DisambiguationError as e:
        return f"Did you mean: {', '.join(e.options[:3])}?"
    except PageError:
        results = wikipedia.search(query)
        return f"Similar topics: {', '.join(results[:3])}" if results else f"No info on {query}."
    except WikipediaException:
        return "Wikipedia isn't available right now."
    except Exception as e:
        return f"Error: {str(e)}"

def get_response(command):
    command = command.lower()
    if "hello" in command or "hi" in command:
        return "Hello! I am Jaya. How can I help you today?"
    elif "your name" in command:
        return "My name is Jaya, your voice assistant."
    elif "time" in command:
        return "The current time is " + datetime.now().strftime("%I:%M %p")
    elif "date" in command:
        return "Today's date is " + datetime.now().strftime("%B %d, %Y")
    elif "open youtube" in command:
        webbrowser.open("https://www.youtube.com")
        return "Opening YouTube for you!"
    elif "play" in command and ("on youtube" in command or "song" in command):
        song = command.replace("play", "").replace("on youtube", "").replace("song", "").strip()
        webbrowser.open(f"https://www.youtube.com/results?search_query={song}")
        return f"Playing {song} on YouTube"
    elif "joke" in command:
        return pyjokes.get_joke()
    elif "bye" in command or "exit" in command or "goodbye" in command:
        return "Goodbye! Have a great day!"
    elif "open google" in command:
        webbrowser.open("https://www.google.com")
        return "Opening Google for you!"
    elif "search for" in command or "search" in command:
        query = command.replace("search for", "").replace("search", "").strip()
        webbrowser.open(f"https://www.google.com/search?q={query}")
        return f"Searching Google for {query}"
    elif "open ai" in command or "chatgpt" in command:
        webbrowser.open("https://chat.openai.com")
        return "Opening ChatGPT for you!"
    elif "who is" in command or "what is" in command:
        query = command.replace("who is", "").replace("what is", "").strip()
        return wikipedia_search(query)
    elif "news" in command:
        webbrowser.open("https://news.google.com")
        return "Opening Google News for you!"
    elif "calculate" in command:
        try:
            expression = command.replace("calculate", "").strip()
            # Safe calculation - only allow basic math operations
            allowed_chars = set('0123456789+-*/.() ')
            if all(c in allowed_chars for c in expression):
                result = eval(expression)
                return f"The result is {result}"
            else:
                return "Sorry, I can only do basic math calculations."
        except:
            return "Sorry, I couldn't calculate that."
    elif "open calculator" in command:
        try:
            if os.name == 'nt':  # Windows
                os.system('calc.exe')
            else:  # Mac/Linux
                os.system('gnome-calculator' if os.uname().sysname == 'Linux' else 'open -a Calculator')
            return "Opening calculator"
        except:
            return "Couldn't open calculator"
    else:
        return "Sorry, I don't understand that command. Try something like 'what is the time?' or 'tell me a joke'."

def listen_for_command():
    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)
            update_status("Listening for your command...", "green")
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=7)
            try:
                command = recognizer.recognize_google(audio)
                update_status("You said: " + command, "blue")
                response = get_response(command)
                update_response("Jaya: " + response)
                speak(response)
                if "bye" in command.lower() or "exit" in command.lower() or "goodbye" in command.lower():
                    root.after(2000, on_close)
            except sr.UnknownValueError:
                update_status("Didn't catch that.", "red")
                update_response("Jaya: Please try again.")
                speak("Sorry, I didn't catch that.")
    except sr.WaitTimeoutError:
        update_status("Timed out. Try again.", "red")
    except Exception as e:
        show_error(str(e))

def wake_word_loop():
    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)
            update_status("Say 'Hey Jaya' to activate...", "purple")

            while True:
                try:
                    audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
                    trigger = recognizer.recognize_google(audio).lower()
                    print("Heard:", trigger)
                    if wake_word in trigger:
                        update_status(f"Wake word heard: {trigger}", "green")
                        speak("Yes?")
                        listen_for_command()
                        update_status("Say 'Hey Jaya' to activate again...", "purple")
                except sr.WaitTimeoutError:
                    update_status("Still waiting for 'Hey Jaya'...", "purple")
                except sr.UnknownValueError:
                    update_status("Didn't catch that.", "red")
    except Exception as e:
        show_error(str(e))

def update_status(text, color="black"):
    if root.winfo_exists():
        root.after(0, lambda: status_label.config(text=text, fg=color))

def update_response(text):
    if root.winfo_exists():
        root.after(0, lambda: response_text.config(state='normal'))
        root.after(0, lambda: response_text.delete(1.0, tk.END))
        root.after(0, lambda: response_text.insert(tk.END, text))
        root.after(0, lambda: response_text.config(state='disabled'))
        root.after(0, lambda: response_text.see(tk.END))

def show_error(text):
    if root.winfo_exists():
        root.after(0, lambda: messagebox.showerror("Error", text))

def start_assistant():
    threading.Thread(target=wake_word_loop, daemon=True).start()

def on_close():
    speak("Goodbye!")
    speech_queue.put("exit")  # Signal the speech thread to exit
    root.destroy()

# ---------------- Enhanced GUI ----------------
root = tk.Tk()
root.title("🎙️ Jaya - Voice Assistant")
root.geometry("500x500")
root.configure(bg="#f5f5f5")
root.protocol("WM_DELETE_WINDOW", on_close)

# Custom style
style = ttk.Style()
style.theme_use('clam')

# Configure styles
style.configure('TFrame', background='#f5f5f5')
style.configure('TButton', font=('Helvetica', 12), padding=10)
style.configure('TLabel', background='#f5f5f5')

# Header Frame
header_frame = ttk.Frame(root, style='TFrame')
header_frame.pack(pady=(10, 5), fill='x')

title = tk.Label(header_frame,
                text="Jaya Voice Assistant",
                font=("Helvetica", 20, "bold"),
                bg="#f5f5f5",
                fg="#3F51B5")
title.pack()

subtitle = tk.Label(header_frame,
                   text="Say 'Hey Jaya' to activate",
                   font=("Helvetica", 12),
                   bg="#f5f5f5",
                   fg="#607D8B")
subtitle.pack()

# Status Frame
status_frame = ttk.Frame(root, style='TFrame')
status_frame.pack(pady=10, fill='x')

status_label = tk.Label(status_frame,
                       text="Waiting for wake word...",
                       font=("Helvetica", 12),
                       bg="#f5f5f5",
                       fg="#9C27B0")
status_label.pack()

# Response Frame
response_frame = ttk.Frame(root, style='TFrame')
response_frame.pack(pady=10, fill='both', expand=True)

response_label = tk.Label(response_frame,
                         text="Response:",
                         font=("Helvetica", 11, "bold"),
                         bg="#f5f5f5",
                         fg="#3F51B5")
response_label.pack(anchor='w')

response_text = tk.Text(response_frame,
                       height=10,
                       width=50,
                       wrap=tk.WORD,
                       font=("Helvetica", 11),
                       bg="#ECEFF1",
                       fg="#263238",
                       padx=10,
                       pady=10,
                       relief=tk.FLAT,
                       state='disabled')
response_text.pack(fill='both', expand=True)

# Add scrollbar
scrollbar = ttk.Scrollbar(response_text)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
response_text.config(yscrollcommand=scrollbar.set)
scrollbar.config(command=response_text.yview)

# Button Frame
button_frame = ttk.Frame(root, style='TFrame')
button_frame.pack(pady=15, fill='x')

listen_button = ttk.Button(button_frame,
                          text="🎤 Start Listening",
                          command=start_assistant)
listen_button.pack(pady=5, ipadx=20)

# Footer Frame
footer_frame = ttk.Frame(root, style='TFrame')
footer_frame.pack(side="bottom", fill='x', pady=10)

footer = tk.Label(footer_frame,
                 text="Jaya - Python Voice Assistant © 2023",
                 font=("Helvetica", 9),
                 bg="#f5f5f5",
                 fg="#757575")
footer.pack()

# Auto start
root.after(1000, start_assistant)

try:
    root.mainloop()
except KeyboardInterrupt:
    print("Assistant manually stopped.")