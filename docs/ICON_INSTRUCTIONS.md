# Application Icon Instructions

## Overview
This document provides instructions for creating and adding an application icon to the Bulk Email Sender.

## Icon Requirements

### File Formats
- **Windows**: `.ico` file (multiple sizes: 16x16, 32x32, 48x48, 256x256)
- **macOS**: `.icns` file (multiple sizes)
- **Linux**: `.png` file (typically 256x256 or 512x512)
- **Cross-platform**: `.png` file (256x256 recommended)

### Design Guidelines
- **Theme**: Email/mail related (envelope, @ symbol, send arrow)
- **Colors**: Professional (blue, green, or brand colors)
- **Style**: Modern, flat design
- **Simplicity**: Clear and recognizable at small sizes

## Creating the Icon

### Option 1: Online Icon Generators
Use free online tools to create icons:
- [Favicon.io](https://favicon.io/) - Generate from text, image, or emoji
- [RealFaviconGenerator](https://realfavicongenerator.net/) - Multi-platform icon generator
- [IconArchive](https://iconarchive.com/) - Free icon library

### Option 2: Design Tools
Create custom icons using:
- **GIMP** (free) - Export as PNG, convert to ICO
- **Inkscape** (free) - Vector graphics, export to PNG
- **Adobe Illustrator** (paid) - Professional vector design
- **Figma** (free/paid) - Modern design tool

### Option 3: Icon Libraries
Download free icons from:
- [Flaticon](https://www.flaticon.com/) - Search "email" or "mail"
- [Icons8](https://icons8.com/) - Free icons with attribution
- [Font Awesome](https://fontawesome.com/) - Icon fonts

## Recommended Icon Concept

### Design Elements
- **Primary**: Envelope icon (📧)
- **Secondary**: Multiple envelopes or send arrow
- **Accent**: @ symbol or email lines
- **Color Scheme**: 
  - Primary: #2196F3 (blue)
  - Secondary: #4CAF50 (green)
  - Accent: #FFC107 (amber)

### Example Concepts
1. **Envelope with Arrow**: Envelope with right-pointing arrow (sending)
2. **Multiple Envelopes**: Stack of envelopes (bulk sending)
3. **@ Symbol**: Stylized @ symbol with envelope
4. **Mail Stack**: Organized stack of mail items

## Adding Icon to Application

### Step 1: Create Icon Files
Create icon files in the following sizes:
```
resources/icons/
├── icon.png          # 256x256 PNG (cross-platform)
├── icon.ico          # Windows ICO (16, 32, 48, 256)
├── icon.icns         # macOS ICNS (optional)
└── icon_16.png       # 16x16 PNG (taskbar)
```

### Step 2: Add Resources Directory
Create a resources directory structure:
```bash
mkdir -p resources/icons
```

### Step 3: Update Main Window
Add icon to the main window in `ui/main_window.py`:

```python
from PyQt6.QtGui import QIcon
from pathlib import Path

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Set window icon
        icon_path = Path(__file__).parent.parent / "resources" / "icons" / "icon.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        
        # Rest of initialization...
```

### Step 4: Update Application Icon (PyQt6)
Set application-wide icon in `main.py`:

```python
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from pathlib import Path
import sys

def main():
    app = QApplication(sys.argv)
    
    # Set application icon
    icon_path = Path(__file__).parent / "resources" / "icons" / "icon.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    
    # Rest of application...
```

### Step 5: Package with Executable (Optional)
When creating standalone executables with PyInstaller:

```python
# In your .spec file
a = Analysis(
    ['main.py'],
    datas=[('resources/icons', 'resources/icons')],
    ...
)

exe = EXE(
    pyz,
    a.scripts,
    icon='resources/icons/icon.ico',  # Windows
    ...
)
```

## Testing the Icon

### Windows
1. Run the application
2. Check taskbar icon
3. Check window title bar icon
4. Check Alt+Tab icon

### macOS
1. Run the application
2. Check Dock icon
3. Check window title bar icon
4. Check Cmd+Tab icon

### Linux
1. Run the application
2. Check window manager icon
3. Check taskbar/panel icon

## Placeholder Icon

Until a custom icon is created, the application uses the default PyQt6 icon. To add a simple placeholder:

### Quick Placeholder (Emoji)
Use an emoji as a temporary icon:
```python
# In main_window.py
self.setWindowTitle("📧 Bulk Email Sender")
```

### Text-Based Icon
Create a simple text-based icon using online generators:
1. Go to [Favicon.io](https://favicon.io/favicon-generator/)
2. Enter text: "BES" or "📧"
3. Choose colors and font
4. Download and extract to `resources/icons/`

## Current Status

✅ About dialog created with version info
⚠️ Application icon placeholder (using default PyQt6 icon)
📝 Icon creation instructions provided

## Next Steps

1. Create or download an icon following the guidelines above
2. Add icon files to `resources/icons/` directory
3. Update `main.py` and `ui/main_window.py` to load the icon
4. Test icon display on target platforms
5. Update packaging configuration if creating executables

## Resources

- [PyQt6 QIcon Documentation](https://doc.qt.io/qt-6/qicon.html)
- [Icon Design Best Practices](https://developer.apple.com/design/human-interface-guidelines/app-icons)
- [Windows Icon Guidelines](https://docs.microsoft.com/en-us/windows/apps/design/style/iconography/app-icon-design)
- [Material Design Icons](https://material.io/design/iconography)

