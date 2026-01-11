"""
API Views for Background Remover and Image Resizer
"""
import os
import sys
import uuid
import numpy as np
from pathlib import Path
from PIL import Image
import cv2

from django.conf import settings
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status

# Add parent directory to path to import the background remover
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from ultralytics import YOLO

# Global model instance (lazy loaded)
_model = None


def get_model(model_size='n'):
    """Load and cache the YOLO model."""
    global _model
    if _model is None:
        print(f"Loading YOLOv8{model_size}-seg model...")
        try:
            _model = YOLO(f'yolov11{model_size}-seg.pt')
        except Exception:
            try:
                _model = YOLO(f'yolov10{model_size}-seg.pt')
            except Exception:
                _model = YOLO(f'yolov8{model_size}-seg.pt')
        print("Model loaded successfully!")
    return _model


def remove_background_yolo(img, model, class_id=0, conf_threshold=0.25):
    """
    Remove background using YOLO segmentation model.
    """
    results = model(img, conf=conf_threshold, classes=[class_id])
    
    h, w = img.shape[:2]
    mask = np.zeros((h, w), dtype=np.uint8)
    
    if results and len(results) > 0:
        result = results[0]
        
        if result.masks is not None and len(result.masks.data) > 0:
            masks_data = result.masks.data.cpu().numpy()
            
            for seg_mask in masks_data:
                if seg_mask.shape != (h, w):
                    seg_mask = cv2.resize(seg_mask, (w, h), interpolation=cv2.INTER_NEAREST)
                mask = np.maximum(mask, (seg_mask > 0.5).astype(np.uint8) * 255)
        else:
            boxes = result.boxes
            if boxes is not None and len(boxes) > 0:
                for box in boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                    mask[y1:y2, x1:x2] = 255
    
    return mask


def process_image(input_path, output_path, conf_threshold=0.25):
    """Process an image and remove its background."""
    img = cv2.imread(str(input_path))
    if img is None:
        raise ValueError(f"Could not read image from {input_path}")
    
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    model = get_model()
    mask = remove_background_yolo(img, model, class_id=0, conf_threshold=conf_threshold)
    
    # Refine mask
    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    mask = cv2.GaussianBlur(mask, (3, 3), 0)
    mask = (mask > 127).astype(np.uint8) * 255
    
    # Create RGBA image
    result_rgba = np.dstack((img_rgb, mask))
    result_pil = Image.fromarray(result_rgba, 'RGBA')
    result_pil.save(str(output_path), 'PNG')
    
    return output_path


def resize_image_file(input_path, output_path, width=None, height=None, scale=None):
    """Resize an image."""
    img = Image.open(input_path)
    
    if scale is not None:
        # Resize by percentage
        width = int(img.width * (scale / 100))
        height = int(img.height * (scale / 100))
    elif width is not None and height is not None:
        # Resize by exact dimensions
        width = int(width)
        height = int(height)
    else:
        # Fallback if nothing provided
        shutil.copy(input_path, output_path)
        return
        
    # High-quality resize
    resized_img = img.resize((width, height), Image.Resampling.LANCZOS)
    resized_img.save(str(output_path), quality=95)


def health_check(request):
    """Simple health check endpoint."""
    return JsonResponse({'status': 'ok', 'message': 'Background Remover API is running'})


class RemoveBackgroundView(APIView):
    """API endpoint for removing background from images."""
    parser_classes = (MultiPartParser, FormParser)
    
    def post(self, request, *args, **kwargs):
        if 'image' not in request.FILES:
            return Response({'error': 'No image file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        image_file = request.FILES['image']
        
        # Save uploaded file
        uploads_dir = settings.MEDIA_ROOT / 'uploads'
        processed_dir = settings.MEDIA_ROOT / 'processed'
        uploads_dir.mkdir(parents=True, exist_ok=True)
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        unique_id = str(uuid.uuid4())[:8]
        input_filename = f"{unique_id}_{image_file.name}"
        input_path = uploads_dir / input_filename
        
        with open(input_path, 'wb+') as destination:
            for chunk in image_file.chunks():
                destination.write(chunk)
        
        try:
            conf_threshold = float(request.data.get('confidence', 0.25))
            conf_threshold = max(0.0, min(1.0, conf_threshold))
            
            output_filename = f"{unique_id}_no_bg.png"
            output_path = processed_dir / output_filename
            
            process_image(input_path, output_path, conf_threshold)
            
            processed_url = request.build_absolute_uri(f"{settings.MEDIA_URL}processed/{output_filename}")
            
            return Response({
                'success': True,
                'message': 'Background removed successfully',
                'processed_image_url': processed_url,
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            if input_path.exists():
                input_path.unlink()
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ResizeImageView(APIView):
    """API endpoint for resizing images."""
    parser_classes = (MultiPartParser, FormParser)
    
    def post(self, request, *args, **kwargs):
        if 'image' not in request.FILES:
            return Response({'error': 'No image file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        image_file = request.FILES['image']
        
        # Save uploaded file
        uploads_dir = settings.MEDIA_ROOT / 'uploads'
        processed_dir = settings.MEDIA_ROOT / 'resized'
        uploads_dir.mkdir(parents=True, exist_ok=True)
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        unique_id = str(uuid.uuid4())[:8]
        input_filename = f"{unique_id}_{image_file.name}"
        input_path = uploads_dir / input_filename
        
        with open(input_path, 'wb+') as destination:
            for chunk in image_file.chunks():
                destination.write(chunk)
        
        try:
            # Get Parameters
            width = request.data.get('width')
            height = request.data.get('height')
            scale = request.data.get('scale') 
            
            if scale:
                scale = float(scale)
            
            output_filename = f"{unique_id}_resized_{image_file.name}"
            output_path = processed_dir / output_filename
            
            resize_image_file(input_path, output_path, width, height, scale)
            
            processed_url = request.build_absolute_uri(f"{settings.MEDIA_URL}resized/{output_filename}")
            
            return Response({
                'success': True,
                'message': 'Image resized successfully',
                'processed_image_url': processed_url,
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            if input_path.exists():
                input_path.unlink()
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
