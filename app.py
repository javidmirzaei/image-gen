import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display
import os
import traceback
import base64
from auth import init_auth, logout

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
    
    .layer-card {{
        background-color: white;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }}
    
    .layer-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
    }}
    
    .layer-title {{
        font-size: 1.2rem;
        font-weight: bold;
        color: #1a237e;
    }}
    
    .layer-controls {{
        display: flex;
        gap: 0.5rem;
    }}
    
    .layer-content {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 1rem;
    }}
    
    .layer-preview {{
        width: 100%;
        height: 150px;
        object-fit: contain;
        border: 1px solid #e0e0e0;
        border-radius: 5px;
    }}
    
    .layer-settings {{
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    }}
    
    .add-layer-button {{
        width: 100%;
        padding: 1rem;
        background-color: #e3f2fd;
        border: 2px dashed #2196F3;
        border-radius: 10px;
        color: #1976D2;
        font-weight: bold;
        cursor: pointer;
        transition: all 0.3s ease;
    }}
    
    .add-layer-button:hover {{
        background-color: #bbdefb;
    }}
    </style>
""", unsafe_allow_html=True)

# بررسی احراز هویت
if not init_auth():
    st.stop()

# کلاس برای مدیریت لایه‌ها
class Layer:
    def __init__(self, name, image=None):
        self.name = name
        self.image = image
        self.x_percent = 50
        self.y_percent = 50
        self.size_percent = 30
        self.opacity = 100
        self.visible = True

# مدیریت لایه‌ها در session state
if 'layers' not in st.session_state:
    st.session_state.layers = []

# عنوان اصلی
st.title("🎨 تصویرساز فارسی")
st.markdown("---")

# آپلود تمپلیت
st.markdown('<p class="upload-header">1️⃣ آپلود تمپلیت</p>', unsafe_allow_html=True)
template_file = st.file_uploader("تمپلیت را انتخاب کنید", type=["png", "jpg", "jpeg"], help="یک تصویر تمپلیت با فرمت PNG یا JPEG آپلود کنید")
if template_file:
    try:
        template_preview = Image.open(template_file)
        st.image(template_preview, caption="پیش‌نمایش تمپلیت", width=300)
    except Exception as e:
        st.error(f"خطا در بارگذاری تمپلیت: {str(e)}")

# ورود متن
st.markdown('<p class="upload-header">3️⃣ وارد کردن متن</p>', unsafe_allow_html=True)
text = st.text_input("متن مورد نظر را وارد کنید", help="متن فارسی که می‌خواهید روی تصویر قرار دهید را وارد کنید")

# تنظیمات متن
st.markdown('<p class="settings-header">⚙️ تنظیمات متن</p>', unsafe_allow_html=True)
text_col1, text_col2 = st.columns(2)
with text_col1:
    font_size_percent = st.slider("سایز فونت (% ارتفاع تصویر)", 1, 20, 5, help="سایز فونت به صورت درصدی از ارتفاع تصویر")
    text_color = st.color_picker("رنگ متن", "#000000", help="رنگ متن را انتخاب کنید")
with text_col2:
    text_x_percent = st.slider("موقعیت افقی متن (%)", 0, 100, 50, help="0: چپ، 50: وسط، 100: راست")
    text_y_percent = st.slider("موقعیت عمودی متن (%)", 0, 100, 50, help="0: بالا، 50: وسط، 100: پایین")

# سایدبار
with st.sidebar:
    # تب‌های سایدبار
    tab1, tab2 = st.tabs(["📝 راهنما", "👁️ پیش‌نمایش"])
    
    with tab1:
        st.header("راهنمای استفاده")
        st.markdown("""
        ### نحوه استفاده:
        1. یک تمپلیت آپلود کنید
        2. لایه‌های مورد نظر را اضافه کنید
        3. برای هر لایه:
           - تصویر را آپلود کنید
           - موقعیت و اندازه را تنظیم کنید
           - شفافیت را تنظیم کنید
        4. متن فارسی را وارد کنید
        5. دکمه ساخت تصویر را بزنید
        
        ### نکات مهم:
        - از فونت وزیر برای نمایش متن فارسی استفاده می‌شود
        - می‌توانید ترتیب لایه‌ها را تغییر دهید
        - هر لایه را می‌توانید فعال یا غیرفعال کنید
        - تصویر نهایی در فایل output.png ذخیره می‌شود
        """)
    
    with tab2:
        st.header("پیش‌نمایش")
        if template_file and (st.session_state.layers or text):
            try:
                # باز کردن تمپلیت
                template = Image.open(template_file)
                preview_image = template.copy()
                draw = ImageDraw.Draw(preview_image)
                
                # محاسبه ابعاد تصویر
                template_width, template_height = template.size
                min_dimension = min(template_width, template_height)
                
                # اضافه کردن لایه‌ها
                for layer in st.session_state.layers:
                    if layer.visible and layer.image:
                        # محاسبه سایز تصویر بر اساس درصد کوچکترین بعد
                        img_size = int(min_dimension * (layer.size_percent / 100))
                        
                        # تغییر سایز تصویر لایه
                        layer_image = layer.image.resize((img_size, img_size))
                        
                        # تبدیل به RGBA اگر PNG است
                        if layer_image.mode != 'RGBA':
                            layer_image = layer_image.convert('RGBA')
                        
                        # اعمال شفافیت
                        if layer.opacity < 100:
                            layer_image.putalpha(int(255 * layer.opacity / 100))
                        
                        # محاسبه موقعیت مرکز تصویر
                        img_x = int((template_width - img_size) * (layer.x_percent / 100))
                        img_y = int((template_height - img_size) * (layer.y_percent / 100))
                        
                        # اضافه کردن تصویر به پیش‌نمایش
                        preview_image.paste(layer_image, (img_x, img_y), layer_image)
                
                # اضافه کردن متن به پیش‌نمایش
                if text:
                    # آماده‌سازی متن فارسی
                    reshaped_text = arabic_reshaper.reshape(text)
                    bidi_text = get_display(reshaped_text)
                    
                    # محاسبه سایز فونت بر اساس درصد ارتفاع
                    font_size = int(template_height * (font_size_percent / 100))
                    
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
                st.image(preview_image, caption=f"پیش‌نمایش ({template_width}x{template_height})", use_column_width=True)
                
            except Exception as e:
                st.error(f"خطا در پیش‌نمایش: {str(e)}")
                st.error("جزئیات خطا:")
                st.code(traceback.format_exc())
        else:
            st.info("👆 برای مشاهده پیش‌نمایش، ابتدا یک تمپلیت آپلود کنید و حداقل یک لایه یا متن اضافه کنید.")
    
    # نمایش اطلاعات کاربر و دکمه خروج
    st.markdown("---")
    st.markdown(f"👤 کاربر: {st.session_state.username}")
    if st.button("🚪 خروج"):
        logout()

# مدیریت لایه‌ها
st.markdown('<p class="upload-header">2️⃣ مدیریت لایه‌ها</p>', unsafe_allow_html=True)

# دکمه افزودن لایه جدید
if st.button("➕ افزودن لایه جدید"):
    new_layer = Layer(f"لایه {len(st.session_state.layers) + 1}")
    st.session_state.layers.append(new_layer)

# نمایش لایه‌ها
for i, layer in enumerate(st.session_state.layers):
    with st.container():
        st.markdown(f"### 🖼️ {layer.name}")
        
        # آپلود تصویر برای لایه
        uploaded_file = st.file_uploader(
            "تصویر را انتخاب کنید",
            type=["png", "jpg", "jpeg"],
            key=f"layer_{i}_upload",
            help="تصویری که می‌خواهید در این لایه قرار دهید را آپلود کنید"
        )
        
        if uploaded_file:
            try:
                layer.image = Image.open(uploaded_file)
                st.image(layer.image, caption="پیش‌نمایش تصویر", width=200)
            except Exception as e:
                st.error(f"خطا در بارگذاری تصویر: {str(e)}")
        
        # تنظیمات لایه
        col1, col2 = st.columns(2)
        with col1:
            layer.x_percent = st.slider(
                "موقعیت افقی (%)",
                0, 100, layer.x_percent,
                key=f"layer_{i}_x",
                help="0: چپ، 50: وسط، 100: راست"
            )
            layer.size_percent = st.slider(
                "اندازه (%)",
                10, 100, layer.size_percent,
                key=f"layer_{i}_size",
                help="سایز تصویر به صورت درصدی از کوچکترین بعد تمپلیت"
            )
        
        with col2:
            layer.y_percent = st.slider(
                "موقعیت عمودی (%)",
                0, 100, layer.y_percent,
                key=f"layer_{i}_y",
                help="0: بالا، 50: وسط، 100: پایین"
            )
            layer.opacity = st.slider(
                "شفافیت (%)",
                0, 100, layer.opacity,
                key=f"layer_{i}_opacity",
                help="شفافیت تصویر (0: کاملاً شفاف، 100: کاملاً مات)"
            )
        
        # کنترل‌های لایه
        col1, col2 = st.columns(2)
        with col1:
            layer.visible = st.checkbox(
                "نمایش لایه",
                value=layer.visible,
                key=f"layer_{i}_visible"
            )
        with col2:
            if st.button("🗑️ حذف لایه", key=f"layer_{i}_delete"):
                st.session_state.layers.pop(i)
                st.rerun()
        
        st.markdown("---")

# دکمه ساخت تصویر
st.markdown("---")
if st.button("🎨 ساخت تصویر"):
    if template_file and (st.session_state.layers or text):
        try:
            # باز کردن تمپلیت
            template = Image.open(template_file)
            
            # ایجاد یک کپی از تمپلیت برای ویرایش
            final_image = template.copy()
            draw = ImageDraw.Draw(final_image)
            
            # محاسبه ابعاد تصویر
            template_width, template_height = template.size
            min_dimension = min(template_width, template_height)
            
            # اضافه کردن لایه‌ها
            for layer in st.session_state.layers:
                if layer.visible and layer.image:
                    # محاسبه سایز تصویر بر اساس درصد کوچکترین بعد
                    img_size = int(min_dimension * (layer.size_percent / 100))
                    
                    # تغییر سایز تصویر لایه
                    layer_image = layer.image.resize((img_size, img_size))
                    
                    # تبدیل به RGBA اگر PNG است
                    if layer_image.mode != 'RGBA':
                        layer_image = layer_image.convert('RGBA')
                    
                    # اعمال شفافیت
                    if layer.opacity < 100:
                        layer_image.putalpha(int(255 * layer.opacity / 100))
                    
                    # محاسبه موقعیت مرکز تصویر
                    img_x = int((template_width - img_size) * (layer.x_percent / 100))
                    img_y = int((template_height - img_size) * (layer.y_percent / 100))
                    
                    # اضافه کردن تصویر به تصویر نهایی
                    final_image.paste(layer_image, (img_x, img_y), layer_image)
            
            # اضافه کردن متن به تصویر
            if text:
                # آماده‌سازی متن فارسی
                reshaped_text = arabic_reshaper.reshape(text)
                bidi_text = get_display(reshaped_text)
                
                # محاسبه سایز فونت بر اساس درصد ارتفاع
                font_size = int(template_height * (font_size_percent / 100))
                
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
        st.error("❌ لطفاً حداقل یک لایه یا متن وارد کنید!") 