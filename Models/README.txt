# KavachG Models Directory

This directory holds all YOLO and AI models for detection tasks in the KavachG project.

## Organization
- Each subfolder is a model category (e.g., PPE, Fire, Pose, Fall).
- Place model weights (.pt files) in the appropriate subfolder.

## Example
- PPE-Detection/ppe.pt
- YOLOv8-Fire-and-Smoke-Detection/yolov8n.pt
- YOLOv8-pose/weights/best.pt
- fall_detection_yolov8s/yolov8s-pose.pt

## Usage
- The backend auto-discovers all .pt files for inference.
- Use `/detect/model/{model_name}` endpoint with the model name as shown in the backend `/models` endpoint.

## Best Practices
- Use clear subfolder and file names.
- Delete obsolete models to avoid clutter.
- Keep this README up to date when adding or removing models.
