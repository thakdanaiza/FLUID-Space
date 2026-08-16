# FLUID-Space

โปรเจกต์ใหม่สำหรับทำ phase map แบบ **CAD-authoritative** โดยหน้าจอรับจากผู้ใช้เพียง:

- Interest Zone สำหรับ CH1 และ CH2
- ROI ของ CH1-1, CH1-2, CH2-1 และ CH2-2
- Bubble ของแต่ละ channel (วาดกี่วงก็ได้)

CAD placement, เส้น CAD, เกาะกลาง และ calibration ถูกล็อกเป็น baseline ใน `assets/` แล้ว พื้นที่ผลคำนวณเป็น:

`ภายใน CAD ∩ ROI ∩ Interest Zone − Bubble`

เส้น CAD ถูกวาดทับผลด้วย vector และไม่มีการใช้ manual island/wet polygon อีก

## เริ่มใช้งาน

ดับเบิลคลิก `start_ui.bat` จากนั้นเลือกโปรไฟล์ วาดหรือแก้ geometry แล้วกด **Save** หรือ **Run result**

โปรไฟล์ `current_baseline` มี Interest Zone, ROI และ Bubble ชุดล่าสุดจากโปรเจกต์เดิมเตรียมไว้ครบแล้ว ใช้ **Duplicate as…** เพื่อแตกเป็นงานใหม่โดยไม่กระทบ baseline

การวาดใน UI:

- คลิกซ้ายเพิ่มจุด
- คลิกขวาหรือ Enter เพื่อปิด polygon
- ลูกกลิ้งเมาส์ zoom
- กดลูกกลิ้งค้างแล้วลากเพื่อ pan
- Esc ยกเลิกเส้นที่กำลังวาด
- Ctrl+S บันทึก

ผลของแต่ละโปรไฟล์อยู่ที่ `profiles/<profile>/runs/run_xxx/` และภาพหลักอยู่ใน `graphs/phase_publication_aligned_left.png`

## Conda

Launcher ใช้ `C:\ProgramData\anaconda3\python.exe` ซึ่งเป็น Conda base ที่เครื่องนี้มีอยู่แล้ว หากย้ายเครื่อง ให้รัน `setup_env.bat` เพื่อสร้าง environment จาก `environment.yml` แล้วปรับ `PYTHON_EXE` ใน launcher ให้ตรงตำแหน่ง

## ตรวจระบบ

```powershell
C:\ProgramData\anaconda3\python.exe app.py --check
C:\ProgramData\anaconda3\python.exe run_profile.py --profile current_baseline --check
C:\ProgramData\anaconda3\python.exe -m unittest discover -s tests -v
```
