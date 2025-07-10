# Dump Video Frames

A simple command-line tool to extract frames from videos at regular intervals or in batches, designed for preparing data for multimodal models like Gemini.

It uses a self-contained `ffmpeg` executable from the `bin` directory, so no system-wide FFmpeg installation is required.

## Features
- Extract a specific number of frames from a video (`--num_frames`).
- Extract frames based on a time interval (`--interval_sec`).
- Process a single video file or a batch of videos from a JSON file.
- Clean up by deleting all `.png` frames from a target directory.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd dump-video-frames
    ```

2.  **Create and activate a virtual environment (recommended):**
    ```bash
    # Create the venv
    python -m venv venv

    # Activate it
    # On Windows:
    .\venv\Scripts\activate
    # On macOS/Linux:
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Usage

The script has two main actions: `extract` and `delete`.

```bash
# General structure
python app.py [action] --[options]
```

### Arguments

| Action    | Argument         | Required | Description                                                                                               |
| :-------- | :--------------- | :------- | :-------------------------------------------------------------------------------------------------------- |
| `extract` | `--path`         | Yes      | Path to a single video file or a `.json` file containing a list of video paths.                             |
|           | `--num_frames`   | Yes*     | Total number of frames to extract. *Required if `--interval_sec` is not used.*                             |
|           | `--interval_sec` | Yes*     | Interval in seconds between frames. *Required if `--num_frames` is not used.*                              |
|           | `--output_dir`   | No       | Custom output directory. Defaults to a `frames` subfolder in the video's parent directory. Not used for batch processing. |
| `delete`  | `--target_path`  | Yes      | Path to the video's parent directory or the specific `frames` directory from which to delete `.png` files.  |


### Example `batch.json` File

To process multiple videos, create a JSON file like this:
```json
{
  "videos": [
    "C:/my_videos/project_a/video1.mp4",
    "C:/my_videos/project_a/video2.mov",
    "D:/archive/footage/clip_03.mkv"
  ]
}
```

### Examples

**1. Extract 15 frames from a single video:**
Frames will be saved to `C:/my_videos/video0/frames/`.
```bash
python app.py extract --path "C:/my_videos/video0/input.mp4" --num_frames 15
```

**2. Extract frames every 2.5 seconds from a single video:**
```bash
python app.py extract --path "C:/my_videos/video0/input.mp4" --interval_sec 2.5
```

**3. Extract 20 frames from a batch of videos defined in a JSON file:**
For each video in the JSON, frames are saved to a `frames` subdirectory (e.g., `C:/my_videos/project_a/frames/`).
```bash
python app.py extract --path "./batch.json" --num_frames 20
```

**4. Delete frames from a video's directory:**
This will find and delete `.png` files in `C:/my_videos/video0/frames/`.
```bash
python app.py delete --target_path "C:/my_videos/video0/"
```

## License
MIT