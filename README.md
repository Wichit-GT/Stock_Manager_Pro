Stock Manager Pro (SMP) — V1
สรุป

แอปจัดการสต็อกสินค้าแบบเดสก์ท็อปเขียนด้วย Python + Tkinter
ฟีเจอร์หลัก: สินค้า/หมวดหมู่, รับ/จ่ายสินค้า, ประวัติการเคลื่อนไหว, รายงาน PDF/CSV, นับสต็อก, ผู้ใช้งาน, หลักฐาน audit
ฐานข้อมูล: SQLite (stock.db) เก็บไว้ในโฟลเดอร์โปรเจค
ความต้องการระบบ

Python 3.12+
Virtualenv (แนะนำ)
ไลบรารีที่ติดตั้ง (ดูตัวอย่างใน requirements.txt): Pillow, numpy, matplotlib, reportlab, qrcode, python-dateutil, ฯลฯ
ติดตั้ง (ตัวอย่างคำสั่ง)

bash

# อยู่ในโฟลเดอร์โปรเจค
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
รันแอป

bash

# ในโฟลเดอร์ V1
source venv/bin/activate
python stock_manager.py   # หรือ python main.py ขึ้นกับไฟล์เริ่มต้นของเวอร์ชัน
โครงสร้างไฟล์สำคัญ

stock_manager.py / main.py — จุดเริ่มต้นของแอป
shared.py — ฟังก์ชันช่วยเหลือ, DB init, theme, settings
modules/ (หรือโฟลเดอร์ตามชื่อ) — โมดูลหน้าต่างต่างๆ (สินค้า, สต็อก, ขาย, ระบบ ฯลฯ)
stock.db — ฐานข้อมูล SQLite (จะถูกสร้าง/อัพเดตโดย init_db())
venv/ — virtual environment (ถาสร้างแล้ว)
requirements.txt — รายการไลบรารี (มีอยู่แล้วในโปรเจค)
การตั้งค่าเริ่มต้น

ผู้ใช้เริ่มต้น: username admin / password admin123 (ถูกสร้างโดย init_db())
การตั้งค่าระบบเก็บในตาราง shop_settings (สามารถแก้ผ่าน UI หรือโดยตรงใน DB)
ฐานข้อมูลและมิเกรชัน

init_db() จะสร้างตารางพื้นฐานและพยายามเพิ่มคอลัมน์เสริม (แบบ idempotent)
หากเพิ่มฟีเจอร์ใหม่ อย่าลืมเพิ่มโค้ดมิเกรชันใน shared.init_db()
การสร้างรายงาน PDF/CSV

ต้องติดตั้ง reportlab สำหรับ PDF (pip install reportlab)
ฟังก์ชัน export อยู่ในโมดูล TransactionsFrame / ProductsFrame
การดีบักและปัญหาที่พบบ่อย

NameError สำหรับฟังก์ชันที่มี underscore นำหน้า: ให้ตรวจสอบว่า import ถูกต้อง (บางกรณี from shared import * อาจไม่ดึงชื่อที่ขึ้นต้นด้วย _)
ตรวจสอบว่า virtualenv ถูก activate ก่อนรัน เพื่อใช้ไลบรารีที่ติดตั้งในโปรเจค
ถ้ารันแล้วไม่มีฐานข้อมูล ให้ตรวจสอบสิทธิ์การเขียนไฟล์ในโฟลเดอร์โปรเจค
คำสั่งช่วยเหลือที่มีประโยชน์

bash

# ตรวจสอบแพ็กเกจที่ติดตั้งใน venv
source venv/bin/activate
pip freeze

# เปิด SQLite DB
sqlite3 stock.db
# ตัวอย่าง: list tables
.tables
การพัฒนาเพิ่มเติม

แยก UI/โลจิกให้เป็นโมดูลมากขึ้น
เพิ่ม unit tests สำหรับ logic สำคัญ (เช่น next_number, audit, สต็อกอัพเดต)
เพิ่มระบบ backup/restore ของ stock.db
พิจารณาใช้ packaging (PyInstaller) สำหรับแจกจ่ายเป็นไฟล์ .exe/.AppImage
