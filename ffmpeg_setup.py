# C:\_myDrive\repos\dump_video_frames\ffmpeg_setup.py

import os
import sys
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

def _find_ffmpeg_bin_directory(current_file: Path) -> Optional[Path]:
    """Finds the 'bin' directory containing FFmpeg executables."""
    script_dir = current_file.parent.resolve()
    bin_dir = script_dir / "bin"
    
    if bin_dir.is_dir() and (bin_dir / "ffmpeg.exe").is_file():
        return bin_dir
    return None

def setup_ffmpeg_path():
    """Adds the directory containing FFmpeg executables to the system's PATH."""
    bin_path = _find_ffmpeg_bin_directory(Path(__file__))
    
    if bin_path:
        if str(bin_path) not in os.environ["PATH"].split(os.pathsep):
            os.environ["PATH"] += os.pathsep + str(bin_path)
            logger.info(f"Added FFmpeg directory to PATH: {bin_path}")
        else:
            logger.info(f"FFmpeg directory already in PATH: {bin_path}")
    else:
        logger.error("Could not find FFmpeg binaries. Ensure the 'bin' directory is correctly located.")
        # Consider raising an exception here if FFmpeg is mandatory for the application to function
        # raise RuntimeError("FFmpeg binaries not found.")