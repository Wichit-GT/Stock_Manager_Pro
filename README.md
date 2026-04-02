📦 Stock Manager Pro

ระบบจัดการสต็อกสินค้า (Inventory & POS System) แบบครบวงจร พัฒนาด้วย Python + Tkinter รองรับการขาย, คลังสินค้า, ลูกค้า และรายงานในโปรแกรมเดียว

✨ Features
🧾 Point of Sale (POS)
สร้างใบเสร็จแบบเรียลไทม์
รองรับส่วนลด และการชำระเงินสด
บันทึกยอดขายและรายการสินค้า

📦 Inventory Management
เพิ่ม / แก้ไข / ลบสินค้า
รองรับหลายหน่วยและหลายราคา
ตัดสต็อกอัตโนมัติ

📊 Dashboard
ยอดขายวันนี้ / เดือนนี้
กำไร และจำนวนบิล
สินค้าขายดี
แจ้งเตือนสินค้าใกล้หมด

📥📤 Stock Control
รับสินค้าเข้า (Stock In)
จ่ายสินค้าออก (Stock Out)
บันทึกประวัติทุกการเคลื่อนไหว

🏭 Supplier & Purchase Orders
จัดการซัพพลายเออร์
สร้างใบสั่งซื้อ (PO)
ติดตามสถานะคำสั่งซื้อ

👥 Customer System
เก็บข้อมูลลูกค้า
ระบบแต้มสะสม
รองรับเครดิตลูกค้า

🔄 Multi-Branch
รองรับหลายสาขา
โอนสินค้า (Stock Transfer)

🔐 Authentication System
ระบบ Login
เข้ารหัสรหัสผ่าน (SHA-256)
Role-based access (Admin / Staff)

🧾 Reports & Export
Export CSV
Export PDF (optional)
กราฟสถิติ (matplotlib)

🏷️ Barcode System
สร้าง Barcode (Code128)
Export เป็น PNG / PDF

🖥️ Screenshots (แนะนำให้เพิ่มเอง)
/docs/screenshots/dashboard.png
/docs/screenshots/pos.png
/docs/screenshots/products.png

🏗️ Tech Stack
Layer	Technology
Language	Python 3
GUI	Tkinter
Database	SQLite3
Charts	matplotlib
PDF Export	reportlab
Image	Pillow

📁 Project Structure
.
├── stock_manager.py   # Main application
├── stock.db           # SQLite database (auto-generated)
└── README.md

⚙️ Installation
1. Clone Repository
git clone https://github.com/your-username/stock-manager-pro.git
cd stock-manager-pro
2. Install Dependencies (Optional)
pip install matplotlib reportlab pillow

▶️ Usage
python stock_manager.py

🔐 Default Credentials
Username	Password
admin	admin123

⚠️ แนะนำให้เปลี่ยนรหัสผ่านทันทีหลังใช้งาน

🗄️ Database Schema (Overview)

ตารางหลักในระบบ:

users
products
categories
suppliers
sales
sale_items
purchase_orders
transactions
customers
promotions
refunds
branches
stock_transfers
shifts
🌐 Internationalization

รองรับหลายภาษา:

🇹🇭 Thai (default)
🇺🇸 English

ตัวอย่างการใช้งาน:

T("product_name")
🎨 Theme Support
Light Mode
Dark Mode
set_theme("dark")

🔒 Security
ใช้ SHA-256 สำหรับ hash password
ไม่มีการเก็บรหัสผ่านแบบ plaintext

🚀 Roadmap
 รองรับ MySQL / PostgreSQL
 REST API Backend
 Web Version (React / Vue)
 Cloud Sync
 AI วิเคราะห์สต็อก
 
🤝 Contributing

Pull requests ยินดีต้อนรับ!
สำหรับการเปลี่ยนแปลงใหญ่ กรุณาเปิด issue ก่อน

📄 License

MIT License

👨‍💻 Author

Developed by Wichit-GT

⭐ Support

ถ้าคุณชอบโปรเจกต์นี้:

⭐ Star บน GitHub
🍴 Fork ไปใช้งาน
🐛 แจ้ง Bug / เสนอ Feature
