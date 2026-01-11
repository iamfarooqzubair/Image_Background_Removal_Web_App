#!/usr/bin/env python3
"""
Background Remover Script using YOLOv11 (latest)
Removes the background from an image using YOLOv11 segmentation model for human detection.
"""

import argparse
import sys
import numpy as np
from pathlib import Path
from PIL import Image
import cv2
from ultralytics import YOLO


def remove_background_yolo(img, model, class_id=0, conf_threshold=0.25):
    """
    Remove background using YOLOv11 segmentation model.
    Detects humans (class 0) and creates a mask for them.
    
    Args:
        img: Input image (BGR format from OpenCV)
        model: YOLOv11 model
        class_id: Class ID to detect (0 = person in COCO dataset)
        conf_threshold: Confidence threshold for detection
    
    Returns:
        mask: Binary mask where 255 = foreground (person), 0 = background
    """
    # Run YOLOv11 inference
    results = model(img, conf=conf_threshold, classes=[class_id])
    
    # Create empty mask
    h, w = img.shape[:2]
    mask = np.zeros((h, w), dtype=np.uint8)
    
    # Process results
    if results and len(results) > 0:
        result = results[0]
        
        # Check if we have segmentation masks
        if result.masks is not None and len(result.masks.data) > 0:
            # Get all masks for detected persons
            masks_data = result.masks.data.cpu().numpy()
            
            # Combine all person masks
            for i, seg_mask in enumerate(masks_data):
                # Resize mask to original image size if needed
                if seg_mask.shape != (h, w):
                    seg_mask = cv2.resize(seg_mask, (w, h), interpolation=cv2.INTER_NEAREST)
                
                # Add to combined mask
                mask = np.maximum(mask, (seg_mask > 0.5).astype(np.uint8) * 255)
            
            print(f"    Detected {len(masks_data)} person(s)")
        else:
            # Fallback: use bounding boxes if masks not available
            boxes = result.boxes
            if boxes is not None and len(boxes) > 0:
                print(f"    Detected {len(boxes)} person(s) (using bounding boxes)")
                for box in boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                    # Fill bounding box area as foreground
                    mask[y1:y2, x1:x2] = 255
            else:
                print("    No persons detected in image")
    else:
        print("    No detection results")
    
    return mask


def remove_background(input_path, output_path=None, model_size='n', conf_threshold=0.25):
    """
    Remove background from an image using YOLOv11 (latest version).
    
    Args:
        input_path (str): Path to the input image
        output_path (str, optional): Path to save the output image. 
                                     If not provided, adds '_no_bg' to the filename.
        model_size (str): YOLOv11 model size ('n'=nano, 's'=small, 'm'=medium, 'l'=large, 'x'=xlarge)
        conf_threshold (float): Confidence threshold for detection (0.0-1.0)
    
    Returns:
        str: Path to the output image
    """
    input_path = Path(input_path)
    
    # Check if input file exists
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Generate output path if not provided (always use PNG to preserve transparency)
    if output_path is None:
        output_path = input_path.parent / f"{input_path.stem}_no_bg.png"
    else:
        output_path = Path(output_path)
        # Ensure output is PNG for transparency
        if output_path.suffix.lower() != '.png':
            output_path = output_path.with_suffix('.png')
    
    print(f"Processing: {input_path}")
    
    # Read the image
    img = cv2.imread(str(input_path))
    if img is None:
        raise ValueError(f"Could not read image from {input_path}")
    
    # Convert BGR to RGB for final output
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    # Load YOLOv11 segmentation model (latest version)
    print(f"Loading YOLOv11{model_size}-seg model...")
    try:
        # Try YOLOv11 first (latest)
        model = YOLO(f'yolov11{model_size}-seg.pt')
        print("Model loaded successfully!")
    except Exception as e:
        print(f"YOLOv11 model not found, trying YOLOv10...")
        try:
            # Fallback to YOLOv10 if v11 not available
            model = YOLO(f'yolov10{model_size}-seg.pt')
            print("YOLOv10 model loaded successfully!")
        except Exception as e2:
            print(f"YOLOv10 not found, using YOLOv8 as fallback...")
            # Final fallback to YOLOv8
            model = YOLO(f'yolov8{model_size}-seg.pt')
            print("YOLOv8 model loaded successfully!")
    
    # Remove background using YOLOv8
    print(f"Detecting humans and removing background (confidence threshold: {conf_threshold})...")
    mask = remove_background_yolo(img, model, class_id=0, conf_threshold=conf_threshold)
    
    # Check mask statistics
    mask_sum = np.sum(mask > 0)
    total_pixels = mask.shape[0] * mask.shape[1]
    print(f"  Mask: {mask_sum}/{total_pixels} pixels are foreground ({100*mask_sum/total_pixels:.1f}%)")
    
    if mask_sum == 0:
        print("  WARNING: No foreground detected! The image might not contain a person, or confidence threshold is too high.")
        print("  Try lowering the confidence threshold with --conf option.")
    
    # Refine mask
    print("  Refining mask...")
    
    # Remove small noise
    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    
    # Smooth edges
    mask = cv2.GaussianBlur(mask, (3, 3), 0)
    mask = (mask > 127).astype(np.uint8) * 255
    
    # Create RGBA image with transparency
    result = img_rgb.copy()
    alpha = mask
    
    # Combine into RGBA
    result_rgba = np.dstack((result, alpha))
    
    # Save the result
    result_pil = Image.fromarray(result_rgba, 'RGBA')
    result_pil.save(str(output_path), 'PNG')
    
    print(f"Background removed! Saved to: {output_path}")
    return str(output_path)


def main():
    parser = argparse.ArgumentParser(
        description='Remove background from an image using YOLOv11 (latest) human detection',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python remove_background.py image.jpg
  python remove_background.py image.jpg -o output.png
  python remove_background.py image.jpg --model-size s --conf 0.3
  python remove_background.py input.jpg output.png

Model Sizes:
  n (nano)   - Fastest, smallest model (default)
  s (small)  - Balanced speed and accuracy
  m (medium) - Better accuracy
  l (large)  - High accuracy
  x (xlarge) - Best accuracy, slowest

Note: Uses YOLOv11 (latest) by default, falls back to YOLOv10 or YOLOv8 if not available.
        """
    )
    
    parser.add_argument(
        'input',
        type=str,
        help='Path to the input image'
    )
    
    parser.add_argument(
        'output',
        type=str,
        nargs='?',
        default=None,
        help='Path to save the output image (optional, defaults to PNG)'
    )
    
    parser.add_argument(
        '-o', '--output',
        dest='output_alt',
        type=str,
        default=None,
        help='Path to save the output image (alternative flag)'
    )
    
    parser.add_argument(
        '--model-size',
        type=str,
        default='n',
        choices=['n', 's', 'm', 'l', 'x'],
        help='YOLOv8 model size: n=nano, s=small, m=medium, l=large, x=xlarge (default: n)'
    )
    
    parser.add_argument(
        '--conf',
        type=float,
        default=0.25,
        help='Confidence threshold for detection (0.0-1.0, default: 0.25)'
    )
    
    args = parser.parse_args()
    
    # Use -o/--output flag if provided, otherwise use positional argument
    output_path = args.output_alt if args.output_alt else args.output
    
    # Validate confidence threshold
    if not 0.0 <= args.conf <= 1.0:
        print("Error: Confidence threshold must be between 0.0 and 1.0", file=sys.stderr)
        sys.exit(1)
    
    try:
        remove_background(args.input, output_path, model_size=args.model_size, conf_threshold=args.conf)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error processing image: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
