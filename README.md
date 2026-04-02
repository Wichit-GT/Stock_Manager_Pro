# 📦 Stock Manager Pro

> **A desktop inventory management system for small businesses**

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey?style=flat-square)](https://github.com/Wichit-GT/Stock_Manager_Pro)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![Release](https://img.shields.io/badge/Release-v1.0.0-blue?style=flat-square)](https://github.com/Wichit-GT/Stock_Manager_Pro/releases/tag/v1.0.0)
[![Status](https://img.shields.io/badge/Status-Stable-brightgreen?style=flat-square)]()

---

## 📚 Table of Contents

- [🚀 Production v1.0.0](#-production-v100)
  - [Description](#description)
  - [📦 Download](#-download)
  - [✅ Production Features](#-production-features)
- [🧩 Versioned Structure](#-versioned-structure)
- [✨ Features](#-features)
- [🛠 Tech Stack](#-tech-stack)
- [📁 Project Structure](#-project-structure)
- [⚙️ Installation](#️-installation)
- [🚀 Usage](#-usage)
- [📌 Versioning Strategy](#-versioning-strategy)
- [🤝 Contributing](#-contributing)
- [📄 License](#-license)

---

## 🚀 Production v1.0.0

### Description

**Stock Manager Pro v1.0.0** is the first stable, production-ready release of a cross-platform desktop inventory management application built with Python and Tkinter. Designed specifically for small businesses, it provides a clean and intuitive Thai-language interface for managing product stock, recording transactions, generating reports, and exporting data — all powered by a lightweight local SQLite database requiring no server setup.

This release is fully tested and intended for day-to-day business operations.

---

### 📦 Download

#### 🔹 Application (Executable)

> Standalone desktop application — no Python installation required.

```text
Download: <link-to-exe>
Platform: Windows
Version:  v1.0.0
```

#### 🔹 Source Code

> Full source code archive for developers and advanced users.


Download (.zip):    [zip](https://github.com/Wichit-GT/Stock_Manager_Pro/blob/main/Version%201.zip)
Download (.tar.xz): [tar](https://github.com/WichitGT/Stock_Manager_Pro/blob/main/Version%201.tar.xz)
Repository:         https://github.com/Wichit-GT/Stock_Manager_Pro
Tag:                v1.0.0

 

---

### ✅ Production Features

- **📥 Stock In** — Record incoming inventory with product selection, quantity, and optional notes
- **📤 Stock Out** — Deduct stock with real-time balance validation to prevent negative inventory
- **📊 Transaction History** — View all IN/OUT movements with filtering by type (All / IN / OUT)
- **📁 CSV Export** — Export transaction history to a UTF-8 CSV file with timestamped filenames
- **📈 Charts & Analytics** — Visual stock movement reports powered by Matplotlib
- **🏷️ QR Code Support** — Generate QR codes for products via the `qrcode` library
- **🖨️ PDF Reports** — Print-ready reports generated with ReportLab
- **💾 Local SQLite Database** — Zero-configuration persistent storage, no server required
- **🌐 Cross-Platform** — Runs on Windows, macOS, and Linux
- **🇹🇭 Thai Language UI** — Full Thai-language interface optimized for local businesses

---

## 🧩 Versioned Structure

Stock Manager Pro follows an **additive versioning model** — each new version gets its own section. Previous versions are never removed or overwritten, ensuring backward compatibility in documentation and release history.

```
🚀 Production v1.0.0  ← Current Stable Release
🚀 Production v2.0.0  ← (Future)
🚀 Production v3.0.0  ← (Future)
```

> **Rule:** New versions are always appended below the previous. No section is ever modified after release.

---

## ✨ Features

### ✅ Production Features (v1.0.0)

| Feature | Status |
|---|---|
| Stock In / Stock Out Management | ✅ Stable |
| Transaction History with Filter | ✅ Stable |
| CSV Export (UTF-8 with BOM) | ✅ Stable |
| Charts & Visual Analytics | ✅ Stable |
| QR Code Generation | ✅ Stable |
| PDF Report Generation | ✅ Stable |
| SQLite Local Database | ✅ Stable |
| Thai Language Interface | ✅ Stable |
| Cross-Platform Support | ✅ Stable |

### 🔮 Upcoming Features (Future Versions)

| Feature | Target Version |
|---|---|
| Multi-user / Role-based Access | v2.0.0 |
| Cloud Sync / Remote Database | v2.0.0 |
| Low-Stock Alerts & Notifications | v2.0.0 |
| Barcode Scanner Integration | v2.0.0 |
| Sales & Invoice Module | v3.0.0 |
| English Language Support | v3.0.0 |

---

## 🛠 Tech Stack

| Layer | Technology | Version |
|---|---|---|
| Language | Python | 3.12 |
| GUI Framework | Tkinter (ttk) | Built-in |
| Database | SQLite3 | Built-in |
| Charts | Matplotlib | 3.10.8 |
| Image Processing | Pillow | 12.1.1 |
| Numerical Computing | NumPy | 2.4.2 |
| QR Code | qrcode | 8.2 |
| PDF Generation | ReportLab | 4.4.10 |
| Packaging | PyInstaller | (dev dependency) |

---

## 📁 Project Structure

### Full Project

```bash
Stock_Manager_Pro/
│
├── stock_manager.py        # ✅ Main entry point — app initialization & navigation
├── mod_stock.py            # ✅ Stock IN / OUT / Transaction modules
├── shared.py               # ✅ Shared constants, helpers, DB connection, UI components
│
├── requirements.txt        # ✅ Production dependencies
│
├── assets/                 # Icons, fonts, images
│   └── ...
│
├── dist/                   # PyInstaller build output
│   └── StockManagerPro.exe
│
├── builds/                 # Archived build artifacts
│   └── v1.0.0/
│       ├── StockManagerPro.exe
│       └── StockManagerPro_v1.0.0_source.zip
│
└── README.md
```

### Deployment Package

```bash
release/
│
├── StockManagerPro.exe     # Standalone executable (no Python required)
├── config/                 # Default configuration files (if any)
└── stock_data.db           # Auto-created on first launch (SQLite database)
```

---

## ⚙️ Installation

### Option A — Run the Executable (Recommended)

No Python installation required. Download the `.exe` from the [Releases page](https://github.com/Wichit-GT/Stock_Manager_Pro/releases) and run it directly.

```text
1. Download: StockManagerPro.exe
2. Double-click to launch
3. A local database (stock_data.db) is created automatically on first run
```

### Option B — Run from Source

**Prerequisites:** Python 3.12+

**1. Clone the repository**

```bash
git clone https://github.com/Wichit-GT/Stock_Manager_Pro.git
cd Stock_Manager_Pro
```

**2. Create and activate a virtual environment**

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Launch the application**

```bash
python stock_manager.py
```

---

## 🚀 Usage

After launching the application, you will see the main navigation sidebar with the following modules:

| Module | Description |
|---|---|
| 📥 รับสินค้า (Stock In) | Select a product and enter quantity to add incoming stock |
| 📤 จ่ายสินค้า (Stock Out) | Select a product and quantity to deduct from inventory |
| 📊 ประวัติการเคลื่อนไหว (Transactions) | View all movements, filter by IN/OUT, and export to CSV |
| 📈 Charts | Visualize stock movement trends over time |
| 🖨️ Reports | Generate and print PDF inventory reports |

### Stock In Example

1. Open the **📥 รับสินค้า** tab
2. Select a product from the dropdown (shows current balance)
3. Enter the quantity received
4. Add an optional note (e.g., supplier name, PO number)
5. Click **📥 บันทึกการรับสินค้า** to confirm

### CSV Export

1. Open the **📊 ประวัติการเคลื่อนไหว** tab
2. Optionally filter by transaction type
3. Click **📊 Export CSV**
4. Choose a save location — the file is exported with a timestamped filename

---

## 📌 Versioning Strategy

Stock Manager Pro follows [Semantic Versioning](https://semver.org/):

```
MAJOR.MINOR.PATCH
  │     │     └── Bug fixes, patches
  │     └──────── New features (backward compatible)
  └────────────── Breaking changes or major rewrites
```

| Channel | Version Format | Description |
|---|---|---|
| **Production** | `v1.0.0`, `v2.0.0` | Stable, fully tested, ready for business use |
| **Beta** | `v1.1.0-beta` | Feature-complete but under final testing |
| **Development** | `v1.1.0-dev` | Active development, may be unstable |

> All production releases are tagged on GitHub and include both a compiled executable and a source archive.

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository: [https://github.com/Wichit-GT/Stock_Manager_Pro](https://github.com/Wichit-GT/Stock_Manager_Pro)
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Commit your changes: `git commit -m "feat: add your feature description"`
4. Push to your branch: `git push origin feature/your-feature-name`
5. Open a Pull Request against the `main` branch

Please ensure your code follows the existing style and that all new features are tested before submitting.

---

## 📄 License

This project is licensed under the **MIT License**.

```
MIT License

Copyright (c) 2024 Wichit-GT

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
```

---

<div align="center">

**Stock Manager Pro** — Built with ❤️ for small businesses

[⬆ Back to Top](#-stock-manager-pro)

</div>
