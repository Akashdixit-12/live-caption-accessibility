# Live Caption Generator for Deaf People

## Problem Statement
Deaf and hard-of-hearing people face difficulty understanding speech during meetings, video calls, and real-time conversations. 
This project aims to convert live speech into text captions and display them in real time to assist deaf users.

## Solution
This system captures live speech through a microphone, converts speech into text using Speech Recognition, 
detects important sentences using a Machine Learning model, and displays captions in a floating window. 
The captions can also be transmitted to another device over a network for deaf users to read in real time.

## Features
- Real-time Speech-to-Text conversion
- Important sentence detection using Machine Learning
- Floating caption window (always on top)
- Sender–Receiver system for deaf users
- Caption logging in CSV file
- Report generation with graphs
- Keyword extraction from captions

## Technologies Used
- Python
- SpeechRecognition
- Socket Programming (TCP)(Basic understanding)
- Pandas
- Matplotlib
- Numpy

## System Architecture
Speech → Speech Recognition → Caption Display → Save CSV → Send via Socket → Receiver Display → Report Generation

## How to Run

### 1. Install Required Libraries
pip install -r requirements.txt

### 2. Run Main Caption Window
python main_app/deaf_caption_app.py

### 3. Run Receiver (Deaf User Device)
python receiver/reciver.py

### 4. Run Sender (Speaker Device)
python sender/sender.py

Make sure both devices are connected to the same WiFi network.

## Project Structure
live-caption-deaf-accessibility/
│
├── README.md
├── requirements.txt
├── main_app/
├── sender/
├── receiver/
├── screenshots/
├── reports/
└── data/

## Output Screenshots


## Future Improvements
- Use Whisper AI for better speech recognition accuracy
- Multi-language caption support
- Mobile application version
- Cloud database storage
- Speaker identification

## Author
Akash Dixit
B.Tech Computer Science
