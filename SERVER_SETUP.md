# راهنمای نصب روی سرور

## مشکل متن‌های برعکس فارسی

اگر متن‌های فارسی روی سرور برعکس نمایش داده می‌شوند، این راهنما را دنبال کنید.

## 🔧 راه‌حل‌ها

### 1. نصب کتابخانه‌های ضروری

```bash
pip install -r requirements.txt
```

یا به صورت جداگانه:

```bash
pip install arabic-reshaper python-bidi
```

### 2. بررسی نصب کتابخانه‌ها

```python
import arabic_reshaper
from bidi.algorithm import get_display

# تست
test_text = "سلام دنیا"
reshaped = arabic_reshaper.reshape(test_text)
bidi_text = get_display(reshaped)
print(bidi_text)
```

### 3. برای سرورهای مختلف

#### Streamlit Cloud
1. فایل `requirements.txt` را به ریپو اضافه کنید
2. در deployment مجدداً deploy کنید

#### Heroku
```bash
heroku buildpacks:add heroku/python
```

#### DigitalOcean/VPS
```bash
sudo apt-get update
sudo apt-get install python3-pip
pip3 install -r requirements.txt
```

### 4. تنظیمات محیط

برای سرورهای Linux، ممکن است نیاز به تنظیم locale باشد:

```bash
export LC_ALL=C.UTF-8
export LANG=C.UTF-8
```

## 🐛 عیب‌یابی

### اگر همچنان مشکل دارید:

1. **بررسی نسخه Python**: حداقل 3.8+
2. **بررسی نسخه پکیج‌ها**: 
   ```bash
   pip list | grep -E "(arabic|bidi)"
   ```
3. **تست در محیط مجازی**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # یا
   venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```

### نمایش وضعیت کتابخانه‌ها

برنامه به صورت خودکار وضعیت کتابخانه‌ها را بررسی می‌کند:
- ✅ سبز: همه چیز کار می‌کند
- ⚠️ زرد: مشکل در کتابخانه‌ها وجود دارد

## 📞 پشتیبانی

اگر مشکل برطرف نشد:
1. خطای دقیق را یادداشت کنید
2. نسخه Python و OS را مشخص کنید
3. نتیجه `pip list` را بفرستید 