# Melody Morph

Melody Morph is a web application that transforms any song into an instrumental masterpiece. Upload your audio tracks and convert them into various instrument renditions like Flute, Piano, Guitar, Violin, and Trumpet.

## Features

-   **Audio Upload**: Support for uploading audio files (MP3, WAV, etc.).
-   **Instrument Conversion**: Convert the melody of your song into:
    -   Flute
    -   Piano
    -   Guitar
    -   Violin
    -   Trumpet
-   **Advanced Processing**: Uses pitch tracking and MIDI synthesis to recreate melodies.
-   **Fallback Synthesis**: Includes a custom wave generator if high-quality synthesis tools are unavailable.
-   **Web Interface**: Simple and intuitive interface for easy interaction.

## Prerequisites

Before running the application, ensure you have the following installed on your system:

1.  **Python 3.8+**
2.  **FFmpeg**: Required for audio processing (used by `pydub` and `librosa`).
    -   [Download FFmpeg](https://ffmpeg.org/download.html) and add it to your system PATH.
3.  **FluidSynth**: Required for high-quality MIDI-to-Audio conversion.
    -   [Download FluidSynth](https://github.com/FluidSynth/fluidsynth/releases) and add it to your system PATH.
4.  **SoundFont**: A `.sf2` soundfont file is required for realistic instrument sounds.
    -   Place a file named `soundfont.sf2` in the `backend/` directory.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd "Melody Morph"
    ```

2.  **Set up the backend**:
    Navigate to the backend directory:
    ```bash
    cd backend
    ```

3.  **Create a Virtual Environment**:
    ```bash
    python -m venv venv
    ```

4.  **Activate the Virtual Environment**:
    -   **Windows**:
        ```bash
        venv\Scripts\activate
        ```
    -   **macOS/Linux**:
        ```bash
        source venv/bin/activate
        ```

5.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

### Running with Batch Script (Windows)

Simply double-click the `run.bat` file in the root directory. This will:
1.  Activate the virtual environment.
2.  Start the backend server.
3.  Open the application in your default web browser.

### Manual Start

1.  Activate the virtual environment (if not already active).
2.  Run the server using Uvicorn:
    ```bash
    uvicorn main:app --reload --port 8000
    ```
3.  Open your browser and navigate to:
    ```
    http://localhost:8000
    ```

## Project Structure

```
Melody Morph/
├── backend/
│   ├── main.py           # FastAPI application entry point
│   ├── processor.py      # Audio processing logic
│   ├── requirements.txt  # Python dependencies
│   ├── static/           # Frontend assets (HTML, CSS, JS)
│   ├── uploads/          # Temporary storage for uploaded files
│   ├── outputs/          # Storage for processed audio files
│   └── soundfont.sf2     # (Required) SoundFont file for synthesis
├── run.bat               # Windows startup script
└── README.md             # Project documentation
```

## Troubleshooting

-   **"Couldn't find ffmpeg or avconv"**: Ensure FFmpeg is installed and added to your system's PATH environment variable.
-   **"FluidSynth failed"**: Ensure FluidSynth is installed and the `soundfont.sf2` file is present in the `backend` directory. The application will fall back to a basic sine wave synthesizer if FluidSynth fails.

## License

[MIT License](LICENSE)
