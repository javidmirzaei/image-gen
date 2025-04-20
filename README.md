# Persian Image Generator

A web-based application for creating images with Persian text and custom images. Built with Streamlit, this tool allows you to overlay Persian text and images on templates with precise positioning and sizing controls.

## Features

- 🎨 Persian text support with Vazir font
- 📸 Template and custom image upload
- 📏 Percentage-based positioning for both text and images
- 👁️ Live preview of changes
- ⚡ Real-time updates
- 💾 Direct image download
- 🌙 Modern dark theme UI
- 📱 Responsive design

## Prerequisites

- Python 3.7 or higher
- pip (Python package installer)
- Git (optional, for version control)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/javidmirzaei/image-gen.git
cd image-gen
```

2. Create and activate a virtual environment:

For macOS/Linux:
```bash
python -m venv venv
source venv/bin/activate
```

For Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

## Usage

1. Start the application:
```bash
streamlit run app.py
```

2. Open your web browser and navigate to the URL shown in the terminal (usually http://localhost:8501)

3. Using the application:
   - Upload a template image (PNG or JPEG)
   - Upload your custom image (PNG or JPEG)
   - Enter Persian text
   - Adjust text and image positions using percentage-based sliders
   - Modify font size (as percentage of image height)
   - Adjust image size (as percentage of template's smallest dimension)
   - Click "Create Image" to generate
   - Download the final image using the download button

## Position Controls

- Text and image positions are controlled using percentage values (0-100):
  - Horizontal: 0 = left, 50 = center, 100 = right
  - Vertical: 0 = top, 50 = center, 100 = bottom

## Size Controls

- Font size: 1-20% of image height
- Image size: 10-100% of template's smallest dimension

## Project Structure

```
image-gen/
├── app.py              # Main application file
├── requirements.txt    # Python dependencies
├── fonts/             # Font files directory
│   └── Vazir-Regular.ttf
└── README.md          # This file
```

## Dependencies

- streamlit: Web application framework
- Pillow: Image processing
- arabic-reshaper: Persian text reshaping
- python-bidi: Bidirectional text support

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Vazir font by [Parham](https://github.com/rastikerdar/vazir-font)
- Streamlit team for the amazing framework
- All contributors and users of this project
