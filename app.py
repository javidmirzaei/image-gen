import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display
import os
import traceback

# تنظیمات اولیه صفحه
st.set_page_config(
    page_title="تصویرساز فارسی",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# تنظیم مسیر فونت
FONT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts", "Vazirmatn-Regular.ttf")

# تنظیمات استایل
st.markdown(f"""
    <style>
    @font-face {{
        font-family: 'Vazir';
        src: url('{FONT_PATH}') format('truetype');
    }}
    
    * {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .main {{
        padding: 2rem;
        background-color: #f8f9fa;
    }}
    
    .stButton>button {{
        width: 100%;
        height: 3rem;
        font-size: 1.2rem;
        background-color: #2196F3;
        color: white;
        border-radius: 10px;
        border: none;
        margin-top: 1rem;
        transition: all 0.3s ease;
    }}
    
    .stButton>button:hover {{
        background-color: #1976D2;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }}
    
    .upload-header {{
        font-size: 1.5rem;
        color: #1a237e;
        margin-bottom: 1rem;
        font-weight: bold;
    }}
    
    .settings-header {{
        font-size: 1.3rem;
        color: #283593;
        margin-top: 2rem;
        margin-bottom: 1rem;
        font-weight: bold;
    }}
    
    .preview-container {{
        background-color: white;
        padding: 2rem;
        border-radius: 15px;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }}
    
    .stSlider {{
        margin: 1rem 0;
    }}
    
    .stColorPicker {{
        margin: 1rem 0;
    }}
    
    .sidebar .sidebar-content {{
        background-color: #1a237e;
        color: white;
    }}
    
    .stAlert {{
        border-radius: 10px;
        padding: 1rem;
    }}
    
    .stFileUploader {{
        border: 2px dashed #2196F3;
        border-radius: 10px;
        padding: 1rem;
    }}
    </style>
""", unsafe_allow_html=True)

# عنوان اصلی
st.title("🎨 تصویرساز فارسی")
st.markdown("---")

# سایدبار
with st.sidebar:
    st.header("📝 راهنما")
    st.markdown("""
    ### نحوه استفاده:
    1. یک تمپلیت آپلود کنید
    2. تصویر مورد نظر را آپلود کنید
    3. متن فارسی را وارد کنید
    4. تنظیمات را تغییر دهید
    5. دکمه ساخت تصویر را بزنید
    
    ### نکات مهم:
    - از فونت وزیر برای نمایش متن فارسی استفاده می‌شود
    - می‌توانید موقعیت و سایز تصویر و متن را تنظیم کنید
    - تصویر نهایی در فایل output.png ذخیره می‌شود
    """)

# آپلود تمپلیت
st.markdown('<p class="upload-header">1️⃣ آپلود تمپلیت</p>', unsafe_allow_html=True)
template_file = st.file_uploader("تمپلیت را انتخاب کنید", type=["png", "jpg", "jpeg"], help="یک تصویر تمپلیت با فرمت PNG یا JPEG آپلود کنید")
if template_file:
    try:
        template_preview = Image.open(template_file)
        st.image(template_preview, caption="پیش‌نمایش تمپلیت", width=300)
    except Exception as e:
        st.error(f"خطا در بارگذاری تمپلیت: {str(e)}")

# آپلود تصویر
st.markdown('<p class="upload-header">2️⃣ آپلود تصویر</p>', unsafe_allow_html=True)
image_file = st.file_uploader("تصویر را انتخاب کنید", type=["png", "jpg", "jpeg"], help="تصویری که می‌خواهید در تمپلیت قرار دهید را آپلود کنید")
if image_file:
    try:
        image_preview = Image.open(image_file)
        st.image(image_preview, caption="پیش‌نمایش تصویر", width=300)
    except Exception as e:
        st.error(f"خطا در بارگذاری تصویر: {str(e)}")

# ورود متن
st.markdown('<p class="upload-header">3️⃣ وارد کردن متن</p>', unsafe_allow_html=True)
text = st.text_input("متن مورد نظر را وارد کنید", help="متن فارسی که می‌خواهید روی تصویر قرار دهید را وارد کنید")

# تنظیمات متن و تصویر
st.markdown('<p class="settings-header">⚙️ تنظیمات متن</p>', unsafe_allow_html=True)
text_col1, text_col2 = st.columns(2)
with text_col1:
    font_size_percent = st.slider("سایز فونت (% ارتفاع تصویر)", 1, 20, 5, help="سایز فونت به صورت درصدی از ارتفاع تصویر")
    text_color = st.color_picker("رنگ متن", "#000000", help="رنگ متن را انتخاب کنید")
with text_col2:
    text_x_percent = st.slider("موقعیت افقی متن (%)", 0, 100, 50, help="0: چپ، 50: وسط، 100: راست")
    text_y_percent = st.slider("موقعیت عمودی متن (%)", 0, 100, 50, help="0: بالا، 50: وسط، 100: پایین")

st.markdown('<p class="settings-header">⚙️ تنظیمات تصویر</p>', unsafe_allow_html=True)
img_col1, img_col2, img_col3 = st.columns(3)
with img_col1:
    img_x_percent = st.slider("موقعیت افقی تصویر (%)", 0, 100, 50, help="0: چپ، 50: وسط، 100: راست")
with img_col2:
    img_y_percent = st.slider("موقعیت عمودی تصویر (%)", 0, 100, 50, help="0: بالا، 50: وسط، 100: پایین")
with img_col3:
    img_size_percent = st.slider("سایز تصویر (% کوچکترین بعد)", 10, 100, 30, help="سایز تصویر به صورت درصدی از کوچکترین بعد تمپلیت")

# پیش‌نمایش زنده
if template_file and (image_file or text):
    st.markdown('<p class="settings-header">👁️ پیش‌نمایش</p>', unsafe_allow_html=True)
    st.markdown('<div class="preview-container">', unsafe_allow_html=True)
    try:
        # باز کردن تمپلیت
        template = Image.open(template_file)
        preview_image = template.copy()
        draw = ImageDraw.Draw(preview_image)
        
        # محاسبه موقعیت‌های واقعی بر اساس درصد
        template_width, template_height = template.size
        min_dimension = min(template_width, template_height)
        
        # محاسبه سایز فونت بر اساس درصد ارتفاع
        font_size = int(template_height * (font_size_percent / 100))
        
        # محاسبه سایز تصویر بر اساس درصد کوچکترین بعد
        img_size = int(min_dimension * (img_size_percent / 100))
        
        # محاسبه موقعیت تصویر
        if image_file:
            uploaded_image = Image.open(image_file)
            # تبدیل به RGBA اگر PNG است
            if uploaded_image.mode != 'RGBA':
                uploaded_image = uploaded_image.convert('RGBA')
            uploaded_image = uploaded_image.resize((img_size, img_size))
            
            # محاسبه موقعیت مرکز تصویر
            img_x = int((template_width - img_size) * (img_x_percent / 100))
            img_y = int((template_height - img_size) * (img_y_percent / 100))
            
            # استفاده از alpha channel برای paste
            preview_image.paste(uploaded_image, (img_x, img_y), uploaded_image)
        
        # اضافه کردن متن به پیش‌نمایش
        if text:
            # آماده‌سازی متن فارسی
            reshaped_text = arabic_reshaper.reshape(text)
            bidi_text = get_display(reshaped_text)
            
            # اضافه کردن متن
            try:
                font = ImageFont.truetype(FONT_PATH, font_size)
                # محاسبه اندازه متن
                text_bbox = draw.textbbox((0, 0), bidi_text, font=font)
                text_width = text_bbox[2] - text_bbox[0]
                text_height = text_bbox[3] - text_bbox[1]
                
                # محاسبه موقعیت مرکز متن
                text_x = int((template_width - text_width) * (text_x_percent / 100))
                text_y = int((template_height - text_height) * (text_y_percent / 100))
                
                draw.text((text_x, text_y), bidi_text, font=font, fill=text_color)
            except Exception as e:
                st.error(f"خطا در بارگذاری فونت: {str(e)}")
                font = ImageFont.load_default()
                draw.text((text_x, text_y), bidi_text, font=font, fill=text_color)
        
        # نمایش پیش‌نمایش با سایز محدود شده
        st.image(preview_image, caption="پیش‌نمایش نهایی", width=300)
        
    except Exception as e:
        st.error(f"خطا در پیش‌نمایش: {str(e)}")
        st.error("جزئیات خطا:")
        st.code(traceback.format_exc())
    st.markdown('</div>', unsafe_allow_html=True)

# دکمه ساخت تصویر
st.markdown("---")
if st.button("🎨 ساخت تصویر"):
    if template_file and (image_file or text):
        try:
            # باز کردن تمپلیت
            template = Image.open(template_file)
            
            # ایجاد یک کپی از تمپلیت برای ویرایش
            final_image = template.copy()
            draw = ImageDraw.Draw(final_image)
            
            # محاسبه ابعاد تصویر
            template_width, template_height = template.size
            min_dimension = min(template_width, template_height)
            
            # محاسبه سایز فونت بر اساس درصد ارتفاع
            font_size = int(template_height * (font_size_percent / 100))
            
            # محاسبه سایز تصویر بر اساس درصد کوچکترین بعد
            img_size = int(min_dimension * (img_size_percent / 100))
            
            # اضافه کردن تصویر به تمپلیت
            if image_file:
                uploaded_image = Image.open(image_file)
                # تبدیل به RGBA اگر PNG است
                if uploaded_image.mode != 'RGBA':
                    uploaded_image = uploaded_image.convert('RGBA')
                uploaded_image = uploaded_image.resize((img_size, img_size))
                
                # محاسبه موقعیت مرکز تصویر
                img_x = int((template_width - img_size) * (img_x_percent / 100))
                img_y = int((template_height - img_size) * (img_y_percent / 100))
                
                # استفاده از alpha channel برای paste
                final_image.paste(uploaded_image, (img_x, img_y), uploaded_image)
            
            # اضافه کردن متن به تصویر
            if text:
                # آماده‌سازی متن فارسی
                reshaped_text = arabic_reshaper.reshape(text)
                bidi_text = get_display(reshaped_text)
                
                try:
                    # استفاده از فونت وزیر
                    font = ImageFont.truetype(FONT_PATH, font_size)
                    # محاسبه اندازه متن
                    text_bbox = draw.textbbox((0, 0), bidi_text, font=font)
                    text_width = text_bbox[2] - text_bbox[0]
                    text_height = text_bbox[3] - text_bbox[1]
                    
                    # محاسبه موقعیت مرکز متن
                    text_x = int((template_width - text_width) * (text_x_percent / 100))
                    text_y = int((template_height - text_height) * (text_y_percent / 100))
                    
                    draw.text((text_x, text_y), bidi_text, font=font, fill=text_color)
                except Exception as e:
                    st.error(f"خطا در بارگذاری فونت: {str(e)}")
                    # استفاده از فونت پیش‌فرض در صورت خطا
                    font = ImageFont.load_default()
                    draw.text((text_x, text_y), bidi_text, font=font, fill=text_color)
            
            # نمایش تصویر نهایی با سایز محدود شده برای پیش‌نمایش
            st.image(final_image, caption=f"تصویر نهایی ({template_width}x{template_height})", width=300)
            
            # ذخیره تصویر با سایز اصلی
            final_image.save("output.png", quality=100)
            
            # ایجاد دکمه دانلود
            with open("output.png", "rb") as file:
                btn = st.download_button(
                    label="⬇️ دانلود تصویر",
                    data=file,
                    file_name="output.png",
                    mime="image/png"
                )
            
            st.success(f"✅ تصویر با موفقیت ساخته شد! (سایز: {template_width}x{template_height})")
            
        except Exception as e:
            st.error(f"❌ خطا در ساخت تصویر: {str(e)}")
            st.error("جزئیات خطا:")
            st.code(traceback.format_exc())
    else:
        st.error("❌ لطفاً حداقل یک تصویر یا متن وارد کنید!")

# اضافه کردن JavaScript برای دریافت مختصات کلیک
st.markdown("""
<script>
const img = document.querySelector('img[alt="روی تمپلیت کلیک کنید"]');
if (img) {
    img.addEventListener('click', function(e) {
        const rect = img.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        window.parent.postMessage({
            type: 'streamlit:setComponentValue',
            value: {x: x, y: y}
        }, '*');
    });
}
</script>
""", unsafe_allow_html=True) 