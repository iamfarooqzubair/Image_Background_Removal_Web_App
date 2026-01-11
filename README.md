# 🖼️ Image Studio Pro (AL-Studio)

A premium, full-stack AI-powered web application and CLI tool for advanced image processing. Built with **React**, **Django**, and **YOLOv11**.

---

## ✨ Features

- **✨ AI Background Remover**: Instantly remove backgrounds with high precision using YOLOv11 segmentation.
- **📏 Smart Image Resizer**: Resize images by specific dimensions (Pixels) or scale them using an intuitive percentage slider.
- **🎨 Premium UI**: Modern dark-mode design with glassmorphism, smooth animations, and a sticky navigation bar.
- **📱 Fully Responsive**: Optimized for desktop, tablets, and mobile devices.
- **🚀 Dual Interface**:
  - **Web App**: Drag-and-drop web portal for easy editing.
  - **CLI Tool**: Standalone Python script for automation and batch processing.

---

## 🛠️ Project Structure

```
bg_remover/
├── 📂 backend/         # Django REST API (Python)
│   ├── api/           # Processing logic for BG removal & Resizing
│   └── requirements.txt
├── 📂 frontend/        # React + Vite (JS/CSS)
│   ├── src/           # Components & Premium Styling
│   └── package.json
└── 📄 remove_background.py  # Standalone CLI Script
```

---

## 🚀 Installation & Setup

### Prerequisites
- **Python 3.8+**
- **Node.js 16+**

### 1. Backend Setup
```bash
# Activate virtual environment
venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt

# Start Server
cd backend
python manage.py migrate
python manage.py runserver
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

---

## ⌨️ CLI Usage

For command-line enthusiasts:
```bash
# Basic background removal
python remove_background.py input.jpg

# Professional options
python remove_background.py input.jpg --model-size m --conf 0.3
```

---

## ⚙️ Technical Details

- **Backend**: Django REST Framework handles file management and model inference.
- **Inference**: Uses YOLOv11 (fallback to v10/v8) for state-of-the-art segmentation.
- **Frontend**: React (Vite) with Vanilla CSS (Glassmorphism & Flexbox centering).
- **Processing**: PIL (Pillow) and OpenCV for high-quality image manipulation.

---

## 📄 License

MIT License. See `LICENSE` for details.
