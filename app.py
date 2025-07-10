import argparse
import logging
import os
import shutil
import subprocess
import json
import sys
from pathlib import Path

import ffmpeg # Requires 'ffmpeg-python' library

from ffmpeg_setup import setup_ffmpeg_path
from logging_setup import configure_logging


configure_logging(level=logging.INFO)
logger = logging.getLogger(__name__)


def _get_video_metadata(video_path: Path) -> dict:
    """Extracts video metadata (duration, width, height, FPS) using ffprobe."""
    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    try:
        probe = ffmpeg.probe(str(video_path))
        video_stream = next((s for s in probe['streams'] if s['codec_type'] == 'video'), None)
        if not video_stream:
            raise ValueError(f"No video stream found in {video_path}")

        duration_s = float(video_stream.get('duration', probe.get('format', {}).get('duration', 0.0)))
        width = video_stream['width']
        height = video_stream['height']
        
        avg_frame_rate = video_stream.get('avg_frame_rate')
        if avg_frame_rate and '/' in avg_frame_rate:
            num, den = map(int, avg_frame_rate.split('/'))
            fps = num / den if den != 0 else 0.0
        elif avg_frame_rate:
            fps = float(avg_frame_rate)
        else: # Fallback to r_frame_rate
            r_frame_rate = video_stream.get('r_frame_rate')
            if r_frame_rate and '/' in r_frame_rate:
                num, den = map(int, r_frame_rate.split('/'))
                fps = num / den if den != 0 else 0.0
            else:
                fps = 0.0

        if duration_s <= 0 or fps <= 0:
             logger.warning(f"Invalid video metadata for {video_path}: Duration={duration_s}s, FPS={fps}.")

        return {'duration_s': duration_s, 'width': width, 'height': height, 'fps': fps}
    except ffmpeg.Error as e:
        error_msg = e.stderr.decode('utf-8', errors='ignore')
        logger.error(f"FFprobe error for {video_path}: {error_msg}")
        raise RuntimeError(f"Could not get video metadata for {video_path}.")
    except Exception as e:
        logger.error(f"Error processing video metadata for {video_path}: {e}")
        raise RuntimeError(f"Could not get video metadata for {video_path}.")


def extract_frames(video_path: Path, output_dir: Path, num_frames: int = None, interval_sec: float = None):
    """
    Extracts frames from a single video.
    Either `num_frames` or `interval_sec` must be provided.
    """
    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found at: {video_path}")
    if not video_path.is_file():
        raise ValueError(f"Provided path is not a file: {video_path}")

    try:
        metadata = _get_video_metadata(video_path)
        duration_s = metadata['duration_s']
        
        target_fps = None
        if num_frames is not None:
            if duration_s <= 0:
                logger.warning(f"Video duration is 0 or less. Defaulting to 1 frame/sec for {video_path}.")
                target_fps = 1.0
            else:
                target_fps = num_frames / duration_s
        elif interval_sec is not None:
            if interval_sec <= 0:
                raise ValueError("Interval seconds must be greater than 0.")
            target_fps = 1.0 / interval_sec
        else:
            raise ValueError("Either 'num_frames' or 'interval_sec' must be specified.")

        if target_fps is None or target_fps <= 0:
            logger.error(f"Invalid target FPS for {video_path}. Frame extraction aborted.")
            return

        output_dir.mkdir(parents=True, exist_ok=True)
        output_pattern = output_dir / "frame_%04d.png"
        
        stream = ffmpeg.input(str(video_path))
        stream = ffmpeg.filter(stream, 'fps', fps=target_fps)
        stream = ffmpeg.output(stream, str(output_pattern), vsync='0') 

        ffmpeg_cmd = ffmpeg.compile(stream)
        logger.info(f"FFmpeg command for {video_path.name}: {' '.join(ffmpeg_cmd)}")

        try:
            process = subprocess.run(ffmpeg_cmd, capture_output=True, text=True, check=True)
            logger.info(f"Frames extracted to: '{output_dir}'")
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg process failed for {video_path.name}: STDOUT:\n{e.stdout}\nSTDERR:\n{e.stderr}")
            raise RuntimeError("FFmpeg failed during extraction.")

    except Exception as e:
        logger.critical(f"Critical error during frame extraction for {video_path.name}: {e}")
        raise


def delete_frames(target_path: Path):
    """
    Deletes .png files from a specified directory.
    If `target_path` is a video's parent directory, it looks for a 'frames' subdirectory.
    """
    if not target_path.exists():
        logger.warning(f"Path does not exist: '{target_path}'. Nothing to delete.")
        return

    frames_dir_to_clean = target_path
    
    if target_path.is_dir() and not target_path.name.lower() == 'frames':
        potential_frames_dir = target_path / "frames"
        if potential_frames_dir.is_dir():
            frames_dir_to_clean = potential_frames_dir
        else:
            logger.warning(f"No 'frames' subdirectory in '{target_path}'. Deleting PNGs from '{target_path}' directly.")

    if not frames_dir_to_clean.is_dir():
        raise ValueError(f"Resolved path is not a directory: '{frames_dir_to_clean}'.")

    png_files = list(frames_dir_to_clean.glob("*.png"))
    
    if not png_files:
        logger.info(f"No .png files found in '{frames_dir_to_clean}'.")
        return

    logger.info(f"Deleting {len(png_files)} .png files from: '{frames_dir_to_clean}'.")
    for p_file in png_files:
        try:
            os.remove(p_file)
        except OSError as e:
            logger.error(f"Error deleting file '{p_file}': {e}. Skipping.")

    try:
        if frames_dir_to_clean.name.lower() == 'frames' and not list(frames_dir_to_clean.iterdir()):
            shutil.rmtree(frames_dir_to_clean)
            logger.info(f"Removed empty frames directory: '{frames_dir_to_clean}'")
    except OSError as e:
        logger.warning(f"Could not remove empty directory '{frames_dir_to_clean}': {e}.")


def main():
    parser = argparse.ArgumentParser(
        description="Utility to extract frames from video files, singly or in batches.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="action", required=True)

    extract_parser = subparsers.add_parser("extract", help="Extract frames from video(s).")
    extract_parser.add_argument("--path", type=str, required=True, help="Path to a single video or a batch .json file.")
    extract_parser.add_argument(
        "--output_dir", type=str, default=None,
        help="Optional: Custom output directory. Ignored for batch processing."
    )
    group = extract_parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--num_frames", type=int, help="Total number of frames to extract per video.")
    group.add_argument("--interval_sec", type=float, help="Interval in seconds between frames.")

    delete_parser = subparsers.add_parser("delete", help="Delete extracted .png frames from a directory.")
    delete_parser.add_argument(
        "--target_path", type=str, required=True,
        help="Path to the video's parent directory or the specific frames directory."
    )
    args = parser.parse_args()

    setup_ffmpeg_path()
    logger.info("FFmpeg path setup completed.")

    if args.action == "extract":
        videos_to_process = []
        input_path = Path(args.path)

        if not input_path.exists():
            logger.error(f"Input path does not exist: {input_path}")
            sys.exit(1)
        
        if input_path.suffix.lower() == '.json':
            logger.info(f"Detected JSON file for batch processing: {input_path}")
            try:
                with open(input_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if 'videos' not in data or not isinstance(data['videos'], list):
                    raise ValueError("JSON must have a 'videos' key with a list of file paths.")
                videos_to_process = [Path(p) for p in data['videos']]
            except (json.JSONDecodeError, ValueError, KeyError) as e:
                logger.error(f"Failed to read or parse batch file: {e}")
                sys.exit(1)
        else:
            videos_to_process.append(input_path)

        logger.info(f"Found {len(videos_to_process)} video(s) to process.")
        for video_path in videos_to_process:
            try:
                # For batch, output_dir is always relative to the video path
                output_dir = video_path.parent / "frames"
                if len(videos_to_process) == 1 and args.output_dir:
                    # Only use custom output_dir for single video processing
                    output_dir = Path(args.output_dir)

                extract_frames(video_path, output_dir, args.num_frames, args.interval_sec)
            except Exception as e:
                logger.error(f"Could not process '{video_path.name}': {e}. Continuing to next video.")

    elif args.action == "delete":
        try:
            target_path = Path(args.target_path)
            delete_frames(target_path)
        except Exception as e:
            logger.error(f"Delete operation failed: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main()