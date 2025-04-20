import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display
import os
import traceback
from auth import init_auth, logout
import base64

# تنظیمات اولیه صفحه
st.set_page_config(
    page_title="تصویرساز فارسی",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# تنظیم مسیر فونت
FONT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts", "Vazirmatn-Regular.ttf")

# تبدیل مسیر فایل به URL
FONT_URL = f"data:font/ttf;base64,{base64.b64encode(open(FONT_PATH, 'rb').read()).decode()}"

# تنظیمات استایل
st.markdown(f"""
    <style>
    @font-face {{
        font-family: 'Vazir';
        src: url('{FONT_URL}') format('truetype');
        font-weight: normal;
        font-style: normal;
    }}
    
    html, body, [class*="st-"] {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    input, button, textarea, select {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stTextInput > div > div > input {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stButton > button {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stMarkdown {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stAlert {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stTabs [data-baseweb="tab-list"] {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stSelectbox > div > div {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stSlider > div > div {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stColorPicker > div > div {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stFileUploader > div > div {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stSidebar [data-testid="stSidebar"] {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stTextInput > div > div > input::placeholder {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stTextArea > div > div > textarea {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stTextArea > div > div > textarea::placeholder {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stSelectbox > div > div > div {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stMultiSelect > div > div > div {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stRadio > div {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stCheckbox > div {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stDateInput > div > div > input {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stTimeInput > div > div > input {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stNumberInput > div > div > input {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stDownloadButton > button {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stProgress > div > div {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stSpinner > div {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stSuccess, .stError, .stWarning, .stInfo {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stTooltip {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stHelp {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stCaption {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stCode {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stJson {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stDataFrame {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stTable {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stMetric {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stGraphvizChart {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stPlotlyChart {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stVegaLiteChart {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stPydeckChart {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stMap {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stImage {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stVideo {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stAudio {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stBalloons {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stSnow {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stConfetti {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stProgress > div > div > div {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stSpinner > div > div {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stSuccess > div, .stError > div, .stWarning > div, .stInfo > div {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stTooltip > div {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stHelp > div {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stCaption > div {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stCode > div {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stJson > div {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stDataFrame > div {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stTable > div {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stMetric > div {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stGraphvizChart > div {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stPlotlyChart > div {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stVegaLiteChart > div {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stPydeckChart > div {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stMap > div {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stImage > div {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stVideo > div {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stAudio > div {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stBalloons > div {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stSnow > div {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stConfetti > div {{
        font-family: 'Vazir', sans-serif !important;
    }}
    </style>
""", unsafe_allow_html=True)

# بررسی احراز هویت
if not init_auth():
    st.stop()

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
    
    # نمایش اطلاعات کاربر و دکمه خروج
    st.markdown("---")
    st.markdown(f"👤 کاربر: {st.session_state.username}")
    if st.button("🚪 خروج"):
        logout()

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