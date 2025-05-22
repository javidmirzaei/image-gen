import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display
import os
import traceback
import base64
from auth import init_auth, logout
import shutil
import glob
import json

# تابع کمکی برای شکستن متن به چند خط
def wrap_text_to_lines(draw, text, font, max_width):
    """
    متن را فقط بر اساس خطوط جدید (اینتر) جدا می‌کند
    و هیچ شکستن خط خودکاری انجام نمی‌دهد
    """
    # فقط متن را بر اساس خطوط جدید (اینتر) جدا می‌کنیم
    return text.split('\n')

# تنظیمات اولیه صفحه
st.set_page_config(
    page_title="تصویرساز فارسی",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# تنظیم مسیر فونت‌ها و تمپلیت‌ها
FONT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts", "Vazirmatn-Regular.ttf")
FONT_BOLD_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts", "Vazirmatn-Bold.ttf")

# استفاده از مسیر tmp برای پوشه‌های قابل نوشتن
TEMPLATES_DIR = os.path.join("/tmp", "templates")
SETTINGS_DIR = os.path.join("/tmp", "settings")

# اطمینان از وجود پوشه تمپلیت‌ها و تنظیمات
if not os.path.exists(TEMPLATES_DIR):
    os.makedirs(TEMPLATES_DIR)
if not os.path.exists(SETTINGS_DIR):
    os.makedirs(SETTINGS_DIR)

# تبدیل مسیر فایل‌ها به URL
FONT_URL = f"data:font/ttf;base64,{base64.b64encode(open(FONT_PATH, 'rb').read()).decode()}"
FONT_BOLD_URL = f"data:font/ttf;base64,{base64.b64encode(open(FONT_BOLD_PATH, 'rb').read()).decode()}"

# تنظیمات استایل
st.markdown(f"""
    <style>
    @font-face {{
        font-family: 'Vazir';
        src: url('{FONT_URL}') format('truetype');
        font-weight: normal;
        font-style: normal;
    }}
    
    @font-face {{
        font-family: 'Vazir';
        src: url('{FONT_BOLD_URL}') format('truetype');
        font-weight: bold;
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
    
    .header-container {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
    }}
    
    .settings-button {{
        margin-left: 1rem;
    }}

    /* استایل مخصوص دکمه‌های انتخاب رنگ */
    .color-button > button {{
        position: relative;
        min-height: 60px;
        height: auto !important;
        display: flex;
        flex-direction: column;
        justify-content: flex-end;
        align-items: center;
        padding: 5px 2px;
        text-align: center;
        color: transparent !important;
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        overflow: hidden;
    }}

    .color-button > button::after {{
        content: attr(data-color-name);
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        color: #333;
        font-size: 0.7rem;
        padding: 2px;
        background-color: rgba(255, 255, 255, 0.7);
        border-bottom-left-radius: 4px;
        border-bottom-right-radius: 4px;
    }}

    .color-button > button::before {{
        content: "";
        position: absolute;
        top: 0;
        right: 0;
        bottom: 25px;
        left: 0;
        background-color: attr(data-color);
        border-radius: 4px;
        border: 1px solid #ccc;
    }}
    </style>
""", unsafe_allow_html=True)

# بررسی احراز هویت
if not init_auth():
    st.stop()

# مسیر فایل دیتابیس رنگ‌ها
COLORS_DB_PATH = os.path.join("/tmp", "colors.json")

# اطمینان از وجود پوشه data
if not os.path.exists(os.path.dirname(COLORS_DB_PATH)):
    os.makedirs(os.path.dirname(COLORS_DB_PATH))

# تابع بارگذاری رنگ‌ها از فایل
def load_colors():
    if os.path.exists(COLORS_DB_PATH):
        try:
            with open(COLORS_DB_PATH, 'r', encoding='utf-8') as file:
                return json.load(file)
        except Exception as e:
            print(f"خطا در بارگذاری رنگ‌ها: {str(e)}")
    return []

# تابع ذخیره رنگ‌ها در فایل
def save_colors(colors):
    try:
        with open(COLORS_DB_PATH, 'w', encoding='utf-8') as file:
            json.dump(colors, file, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"خطا در ذخیره رنگ‌ها: {str(e)}")
        return False

# تابع ذخیره تنظیمات پیش‌فرض تمپلیت
def save_template_settings(template_name, settings):
    try:
        settings_path = os.path.join(SETTINGS_DIR, f"{template_name}.json")
        with open(settings_path, 'w', encoding='utf-8') as file:
            json.dump(settings, file, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"خطا در ذخیره تنظیمات تمپلیت: {str(e)}")
        return False

# تابع بارگذاری تنظیمات پیش‌فرض تمپلیت
def load_template_settings(template_name):
    settings_path = os.path.join(SETTINGS_DIR, f"{template_name}.json")
    if os.path.exists(settings_path):
        try:
            with open(settings_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except Exception as e:
            print(f"خطا در بارگذاری تنظیمات تمپلیت: {str(e)}")
    return None

# تابع بررسی وجود تنظیمات پیش‌فرض برای تمپلیت
def has_template_settings(template_name):
    settings_path = os.path.join(SETTINGS_DIR, f"{template_name}.json")
    return os.path.exists(settings_path)

# کلاس برای مدیریت لایه‌ها
class Layer:
    def __init__(self, name, image=None):
        self.name = name
        self.image = image
        self.x_percent = 50
        self.y_percent = 0
        self.size_percent = 100
        self.opacity = 100
        self.visible = True
        self.image_key = None  # کلید یکتا برای هر تصویر

# مدیریت لایه‌ها در session state
if 'layers' not in st.session_state:
    st.session_state.layers = []

# برای ذخیره نام تمپلیت انتخاب شده
if 'selected_template_name' not in st.session_state:
    st.session_state.selected_template_name = None

# برای ذخیره مسیر تمپلیت انتخاب شده
if 'selected_template_path' not in st.session_state:
    st.session_state.selected_template_path = None

# برای ذخیره تمپلیت آپلود شده
if 'template_file' not in st.session_state:
    st.session_state.template_file = None

# برای ذخیره متن
if 'text' not in st.session_state:
    st.session_state.text = ""

# برای ذخیره تنظیمات متن
if 'font_size_percent' not in st.session_state:
    st.session_state.font_size_percent = 4
if 'text_color' not in st.session_state:
    st.session_state.text_color = "#000000"
if 'is_bold' not in st.session_state:
    st.session_state.is_bold = False
if 'text_x_percent' not in st.session_state:
    st.session_state.text_x_percent = 50
if 'text_y_percent' not in st.session_state:
    st.session_state.text_y_percent = 98
if 'max_text_width_percent' not in st.session_state:
    st.session_state.max_text_width_percent = 80
if 'line_spacing_percent' not in st.session_state:
    st.session_state.line_spacing_percent = 120

# برای ذخیره وضعیت صفحه‌ای که کاربر در آن قرار دارد
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'main'  # صفحه اصلی به عنوان پیش‌فرض

# برای ذخیره رنگ‌های پیش‌فرض
if 'default_colors' not in st.session_state:
    st.session_state.default_colors = load_colors()

# برای ذخیره نام رنگ جدید
if 'new_color_name' not in st.session_state:
    st.session_state.new_color_name = ""

# برای ذخیره مقدار رنگ جدید
if 'new_color_value' not in st.session_state:
    st.session_state.new_color_value = "#000000"

# نمایش صفحه متناسب با وضعیت
if st.session_state.current_page == 'settings':
    # صفحه تنظیمات
    
    # ایجاد هدر با دکمه بازگشت
    col1, col2 = st.columns([5, 1])
    with col1:
        st.title("⚙️ تنظیمات")
    with col2:
        if st.button("🔙 بازگشت", key="header_back_button"):
            st.session_state.current_page = 'main'
            st.rerun()
    
    st.markdown("---")
    
    # ایجاد تب‌های اصلی تنظیمات
    settings_tab1, settings_tab2 = st.tabs(["📁 مدیریت تمپلیت‌ها", "🎨 مدیریت رنگ‌ها"])
    
    with settings_tab1:
        # نمایش تب‌های مدیریت تمپلیت
        template_tab1, template_tab2 = st.tabs(["📂 تمپلیت‌های موجود", "⬆️ آپلود تمپلیت جدید"])
        
        with template_tab1:
            # دریافت لیست تمپلیت‌های موجود
            template_files = glob.glob(os.path.join(TEMPLATES_DIR, "*.png")) + glob.glob(os.path.join(TEMPLATES_DIR, "*.jpg"))
            template_files.sort(key=os.path.getmtime, reverse=True)  # مرتب‌سازی بر اساس زمان ایجاد
            
            if template_files:
                # ساخت لیست نمایشی از تمپلیت‌ها
                template_names = [os.path.basename(f) for f in template_files]
                
                # نمایش لیست تمپلیت‌ها
                st.markdown("تمپلیت‌های ذخیره شده:")
                for i, template in enumerate(template_names):
                    # بررسی آیا تمپلیت دارای تنظیمات پیش‌فرض است
                    template_basename = os.path.splitext(template)[0]
                    has_settings = has_template_settings(template_basename)
                    
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        # نمایش ستاره برای تمپلیت‌هایی که تنظیمات پیش‌فرض دارند
                        if has_settings:
                            st.write(f"{i+1}. ⭐ {template}")
                        else:
                            st.write(f"{i+1}. {template}")
                    with col2:
                        if st.button("🗑️", key=f"delete_{i}"):
                            try:
                                os.remove(os.path.join(TEMPLATES_DIR, template))
                                # حذف فایل تنظیمات اگر وجود داشته باشد
                                if has_settings:
                                    settings_path = os.path.join(SETTINGS_DIR, f"{template_basename}.json")
                                    if os.path.exists(settings_path):
                                        os.remove(settings_path)
                                
                                # اگر تمپلیت حذف شده با تمپلیت انتخاب شده یکسان است، انتخاب را پاک کن
                                if st.session_state.selected_template_name == template:
                                    st.session_state.selected_template_name = None
                                    st.session_state.selected_template_path = None
                                st.success(f"تمپلیت {template} با موفقیت حذف شد!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"خطا در حذف تمپلیت: {str(e)}")
            else:
                st.info("🔍 هنوز تمپلیتی ذخیره نشده است. لطفاً از تب آپلود، یک تمپلیت جدید اضافه کنید.")
        
        with template_tab2:
            template_file = st.file_uploader("تمپلیت جدید را انتخاب کنید", type=["png", "jpg", "jpeg"], help="یک تصویر تمپلیت با فرمت PNG یا JPEG آپلود کنید")
            template_name = st.text_input("نام تمپلیت (اختیاری)", help="اگر خالی بماند، از نام فایل استفاده می‌شود")
            
            if template_file:
                try:
                    # نمایش پیش‌نمایش
                    template_preview = Image.open(template_file)
                    
                    # ایجاد کلیدهای session_state برای پیش‌نمایش
                    if "preview_template" not in st.session_state:
                        st.session_state.preview_template = template_preview
                    else:
                        st.session_state.preview_template = template_preview
                    
                    if "preview_layers" not in st.session_state:
                        st.session_state.preview_layers = []
                    
                    if "preview_text" not in st.session_state:
                        st.session_state.preview_text = ""
                    
                    # نمایش تمپلیت آپلود شده
                    st.image(template_preview, caption="پیش‌نمایش تمپلیت جدید", width=300)
                    
                    # تب‌های پیش‌نمایش و تنظیمات
                    preview_tab1, preview_tab2, preview_tab3 = st.tabs(["⚙️ تنظیمات پیش‌فرض", "🖼️ پیش‌نمایش با لایه‌ها", "📝 پیش‌نمایش با متن"])
                    
                    with preview_tab1:
                        # تنظیمات پیش‌فرض تمپلیت
                        st.info("تنظیمات پیش‌فرض برای این تمپلیت، هنگام استفاده از آن به‌طور خودکار اعمال خواهند شد.")
                        
                        # تنظیمات مربوط به متن
                        st.subheader("📝 تنظیمات متن")
                        default_font_col1, default_font_col2 = st.columns(2)
                        with default_font_col1:
                            default_font_size = st.slider("سایز فونت (% ارتفاع تصویر)", 1, 20, 4, key="default_font_size", help="سایز فونت به صورت درصدی از ارتفاع تصویر")
                            default_text_x = st.slider("موقعیت افقی متن (%)", 0, 100, 50, key="default_text_x", help="0: کاملاً چپ تمپلیت، 50: وسط تمپلیت، 100: کاملاً راست تمپلیت")
                        
                        with default_font_col2:
                            default_text_y = st.slider("موقعیت عمودی متن (%)", 0, 100, 98, key="default_text_y", help="0: کاملاً بالای تمپلیت، 50: وسط تمپلیت، 100: کاملاً پایین تمپلیت")
                            default_text_color = st.color_picker("رنگ پیش‌فرض متن", "#000000", key="default_text_color")
                        
                        # تنظیمات پیشرفته متن - به جای expander از checkbox استفاده می‌کنیم
                        show_advanced_text_settings = st.checkbox("نمایش تنظیمات پیشرفته متن", value=False, key="show_advanced_text")
                        if show_advanced_text_settings:
                            default_max_text_width = st.slider("عرض متن (%)", 10, 100, 80, key="default_max_text_width", help="حداکثر عرض متن به صورت درصدی از عرض تمپلیت")
                            default_line_spacing = st.slider("فاصله خطوط (%)", 100, 200, 120, key="default_line_spacing", help="فاصله بین خطوط متن به صورت درصدی از ارتفاع خط")
                            default_is_bold = st.checkbox("متن بولد", value=False, key="default_is_bold", help="نمایش متن به صورت بولد")
                        else:
                            # مقادیر پیش‌فرض برای زمانی که تنظیمات پیشرفته نمایش داده نمی‌شود
                            if "default_max_text_width" not in st.session_state:
                                st.session_state.default_max_text_width = 80
                            if "default_line_spacing" not in st.session_state:
                                st.session_state.default_line_spacing = 120
                            if "default_is_bold" not in st.session_state:
                                st.session_state.default_is_bold = False
                        
                        # تنظیمات مربوط به لایه‌ها
                        st.subheader("🖼️ تنظیمات لایه‌ها")
                        default_layer_col1, default_layer_col2 = st.columns(2)
                        with default_layer_col1:
                            default_layer_x = st.slider("موقعیت افقی لایه (%)", 0, 100, 50, key="default_layer_x", help="0: چپ، 50: وسط، 100: راست")
                            default_layer_size = st.slider("اندازه لایه (%)", 10, 300, 100, key="default_layer_size", help="سایز تصویر به صورت درصدی از کوچکترین بعد تمپلیت")
                        
                        with default_layer_col2:
                            default_layer_y = st.slider("موقعیت عمودی لایه (%)", 0, 100, 0, key="default_layer_y", help="0: بالا، 50: وسط، 100: پایین")
                            default_layer_opacity = st.slider("شفافیت لایه (%)", 0, 100, 100, key="default_layer_opacity", help="شفافیت تصویر (0: کاملاً شفاف، 100: کاملاً مات)")
                    
                    with preview_tab2:
                        # پیش‌نمایش با لایه‌ها
                        st.subheader("پیش‌نمایش با لایه‌ها")
                        st.info("در این بخش می‌توانید لایه اضافه کنید و نتیجه تنظیمات پیش‌فرض روی آن را ببینید. این لایه‌ها فقط برای پیش‌نمایش هستند و ذخیره نمی‌شوند.")
                        
                        # دکمه افزودن لایه آزمایشی
                        if st.button("➕ افزودن لایه آزمایشی", key="add_preview_layer"):
                            preview_layer = Layer(f"لایه آزمایشی {len(st.session_state.preview_layers) + 1}")
                            # اعمال تنظیمات پیش‌فرض
                            preview_layer.x_percent = st.session_state.default_layer_x
                            preview_layer.y_percent = st.session_state.default_layer_y
                            preview_layer.size_percent = st.session_state.default_layer_size
                            preview_layer.opacity = st.session_state.default_layer_opacity
                            st.session_state.preview_layers.append(preview_layer)
                            st.rerun()
                        
                        # نمایش لایه‌های موجود
                        has_layer_with_image = False
                        for i, layer in enumerate(st.session_state.preview_layers):
                            with st.container():
                                st.markdown(f"#### 🖼️ {layer.name}")
                                
                                # آپلود تصویر برای لایه
                                uploaded_file = st.file_uploader(
                                    "تصویر را انتخاب کنید",
                                    type=["png", "jpg", "jpeg"],
                                    key=f"preview_layer_{i}_upload",
                                    help="تصویری که می‌خواهید در این لایه قرار دهید را آپلود کنید"
                                )
                                
                                if uploaded_file:
                                    try:
                                        # ایجاد کلید یکتا برای تصویر
                                        if layer.image_key != uploaded_file.name:
                                            layer.image_key = uploaded_file.name
                                            layer.image = Image.open(uploaded_file)
                                            st.rerun()
                                        st.image(layer.image, caption="پیش‌نمایش تصویر", width=200)
                                        has_layer_with_image = True
                                    except Exception as e:
                                        st.error(f"خطا در بارگذاری تصویر: {str(e)}")
                                
                                if layer.image:
                                    # تنظیمات لایه - تغییرات مقادیر و ساخت پیش‌نمایش زنده
                                    layer_settings_col1, layer_settings_col2 = st.columns(2)
                                    with layer_settings_col1:
                                        # ذخیره مقدار قبلی در متغیر موقت
                                        temp_x = layer.x_percent
                                        layer.x_percent = st.slider(
                                            "موقعیت افقی (%)", 
                                            0, 100, temp_x, 
                                            key=f"layer_{i}_x_slider", 
                                            help="0: چپ، 50: وسط، 100: راست"
                                        )
                                        
                                        temp_size = layer.size_percent
                                        layer.size_percent = st.slider(
                                            "اندازه (%)", 
                                            10, 300, temp_size, 
                                            key=f"layer_{i}_size_slider", 
                                            help="سایز تصویر به صورت درصدی از کوچکترین بعد تمپلیت"
                                        )
                                    
                                    with layer_settings_col2:
                                        temp_y = layer.y_percent
                                        layer.y_percent = st.slider(
                                            "موقعیت عمودی (%)", 
                                            0, 100, temp_y, 
                                            key=f"layer_{i}_y_slider", 
                                            help="0: بالا، 50: وسط، 100: پایین"
                                        )
                                        
                                        temp_opacity = layer.opacity
                                        layer.opacity = st.slider(
                                            "شفافیت (%)", 
                                            0, 100, temp_opacity, 
                                            key=f"layer_{i}_opacity_slider", 
                                            help="شفافیت تصویر (0: کاملاً شفاف، 100: کاملاً مات)"
                                        )
                                
                                # دکمه حذف لایه
                                if st.button("🗑️ حذف لایه", key=f"preview_layer_{i}_delete"):
                                    st.session_state.preview_layers.pop(i)
                                    st.rerun()
                                
                                st.markdown("---")
                        
                        # ساخت پیش‌نمایش زنده با همه لایه‌ها
                        if has_layer_with_image and st.session_state.preview_layers:
                            st.subheader("پیش‌نمایش ترکیب تمام لایه‌ها")
                            try:
                                # ایجاد پیش‌نمایش با تمپلیت و همه لایه‌ها
                                template_width, template_height = template_preview.size
                                min_dimension = min(template_width, template_height)
                                
                                # ایجاد یک تصویر پایه خالی
                                preview_image = Image.new('RGBA', (template_width, template_height), (255, 255, 255, 255))
                                
                                # اضافه کردن لایه‌ها به زمینه سفید
                                for layer in st.session_state.preview_layers:
                                    if layer.image:
                                        # محاسبه سایز تصویر بر اساس درصد کوچکترین بعد تمپلیت
                                        max_dimension = int(min_dimension * (layer.size_percent / 100))
                                        
                                        # تغییر سایز تصویر لایه با حفظ نسبت تصویر
                                        original_width, original_height = layer.image.size
                                        aspect_ratio = original_width / original_height
                                        
                                        if aspect_ratio >= 1:  # عرض بزرگتر یا مساوی ارتفاع است
                                            new_width = max_dimension
                                            new_height = int(max_dimension / aspect_ratio)
                                        else:  # ارتفاع بزرگتر از عرض است
                                            new_height = max_dimension
                                            new_width = int(max_dimension * aspect_ratio)
                                        
                                        # تغییر سایز انجام می‌شود (بزرگنمایی)
                                        layer_image = layer.image.resize((new_width, new_height), Image.LANCZOS)
                                        
                                        # تبدیل به RGBA اگر PNG است
                                        if layer_image.mode != 'RGBA':
                                            layer_image = layer_image.convert('RGBA')
                                        
                                        # اعمال شفافیت
                                        if layer.opacity < 100:
                                            layer_image.putalpha(int(255 * layer.opacity / 100))
                                        
                                        # محاسبه موقعیت مرکز تصویر
                                        img_x = int((template_width - new_width) * (layer.x_percent / 100))
                                        img_y = int((template_height - new_height) * (layer.y_percent / 100))
                                        
                                        # اضافه کردن تصویر به پیش‌نمایش
                                        preview_image.paste(layer_image, (img_x, img_y), layer_image)
                                
                                # اضافه کردن تمپلیت به عنوان لایه بالایی
                                if template_preview.mode == 'RGBA':
                                    preview_image = Image.alpha_composite(preview_image, template_preview)
                                else:
                                    template_rgba = template_preview.convert('RGBA')
                                    preview_image = Image.alpha_composite(preview_image, template_rgba)
                                
                                # نمایش نتیجه
                                st.image(preview_image, caption="پیش‌نمایش ترکیب تمام لایه‌ها با تمپلیت", width=300)
                                
                            except Exception as e:
                                st.error(f"خطا در ساخت پیش‌نمایش ترکیبی: {str(e)}")
                                st.error("جزئیات خطا:")
                                st.code(traceback.format_exc())
                        
                        # دکمه پاک کردن همه لایه‌ها
                        if st.session_state.preview_layers:
                            if st.button("🗑️ پاک کردن همه لایه‌ها", key="clear_all_preview_layers"):
                                st.session_state.preview_layers = []
                                st.rerun()
                    
                    with preview_tab3:
                        # پیش‌نمایش با متن
                        st.subheader("پیش‌نمایش با متن")
                        st.info("در این بخش می‌توانید متن اضافه کنید و نتیجه تنظیمات پیش‌فرض روی آن را ببینید. این متن فقط برای پیش‌نمایش است و ذخیره نمی‌شود.")
                        
                        # ایجاد متغیرهای جدید در session_state برای پیش‌نمایش متن
                        if 'preview_font_size' not in st.session_state:
                            st.session_state.preview_font_size = st.session_state.default_font_size
                        if 'preview_text_x' not in st.session_state:
                            st.session_state.preview_text_x = st.session_state.default_text_x
                        if 'preview_text_y' not in st.session_state:
                            st.session_state.preview_text_y = st.session_state.default_text_y
                        if 'preview_text_color' not in st.session_state:
                            st.session_state.preview_text_color = st.session_state.default_text_color
                        if 'preview_max_text_width' not in st.session_state:
                            st.session_state.preview_max_text_width = st.session_state.default_max_text_width
                        if 'preview_line_spacing' not in st.session_state:
                            st.session_state.preview_line_spacing = st.session_state.default_line_spacing
                        if 'preview_is_bold' not in st.session_state:
                            st.session_state.preview_is_bold = st.session_state.default_is_bold
                        
                        # ورود متن آزمایشی
                        preview_text = st.text_area("متن آزمایشی را وارد کنید", value=st.session_state.preview_text, height=150)
                        
                        # ذخیره متن در session state
                        if preview_text != st.session_state.preview_text:
                            st.session_state.preview_text = preview_text
                            st.rerun()  # رفرش صفحه برای بروزرسانی پیش‌نمایش
                        
                        # نمایش پیش‌نمایش متن اگر متن وارد شده باشد
                        if st.session_state.preview_text:
                            st.subheader("تنظیمات و پیش‌نمایش")
                            
                            # تنظیمات متن با پیش‌نمایش زنده
                            text_settings_col1, text_settings_col2 = st.columns(2)
                            with text_settings_col1:
                                st.session_state.preview_font_size = st.slider(
                                    "سایز فونت (% ارتفاع تصویر)", 
                                    1, 20, st.session_state.preview_font_size, 
                                    key="preview_font_size_slider", 
                                    help="سایز فونت به صورت درصدی از ارتفاع تصویر"
                                )
                                st.session_state.preview_text_x = st.slider(
                                    "موقعیت افقی متن (%)", 
                                    0, 100, st.session_state.preview_text_x, 
                                    key="preview_text_x_slider", 
                                    help="0: کاملاً چپ تمپلیت، 50: وسط تمپلیت، 100: کاملاً راست تمپلیت"
                                 )
                            
                            with text_settings_col2:
                                st.session_state.preview_text_y = st.slider(
                                    "موقعیت عمودی متن (%)", 
                                    0, 100, st.session_state.preview_text_y, 
                                    key="preview_text_y_slider", 
                                    help="0: کاملاً بالای تمپلیت، 50: وسط تمپلیت، 100: کاملاً پایین تمپلیت"
                                 )
                                st.session_state.preview_text_color = st.color_picker(
                                    "رنگ متن", 
                                    st.session_state.preview_text_color, 
                                    key="preview_text_color_picker"
                                 )
                            
                            # تنظیمات پیشرفته متن با پیش‌نمایش زنده
                            preview_show_advanced = st.checkbox("نمایش تنظیمات پیشرفته متن", value=False, key="preview_show_advanced")
                            if preview_show_advanced:
                                adv_col1, adv_col2 = st.columns(2)
                                with adv_col1:
                                    st.session_state.preview_max_text_width = st.slider(
                                        "عرض متن (%)", 
                                        10, 100, st.session_state.preview_max_text_width, 
                                        key="preview_max_width_slider", 
                                        help="حداکثر عرض متن به صورت درصدی از عرض تمپلیت"
                                     )
                                
                                with adv_col2:
                                    st.session_state.preview_line_spacing = st.slider(
                                        "فاصله خطوط (%)", 
                                        100, 200, st.session_state.preview_line_spacing, 
                                        key="preview_line_spacing_slider", 
                                        help="فاصله بین خطوط متن به صورت درصدی از ارتفاع خط"
                                     )
                                
                                st.session_state.preview_is_bold = st.checkbox(
                                    "متن بولد", 
                                    value=st.session_state.preview_is_bold, 
                                    key="preview_is_bold_checkbox", 
                                    help="نمایش متن به صورت بولد"
                                 )
                            
                            # دکمه اعمال تنظیمات به عنوان پیش‌فرض
                            if st.button("اعمال این تنظیمات به عنوان پیش‌فرض", key="apply_preview_settings"):
                                st.session_state.default_font_size = st.session_state.preview_font_size
                                st.session_state.default_text_x = st.session_state.preview_text_x
                                st.session_state.default_text_y = st.session_state.preview_text_y
                                st.session_state.default_text_color = st.session_state.preview_text_color
                                st.session_state.default_max_text_width = st.session_state.preview_max_text_width
                                st.session_state.default_line_spacing = st.session_state.preview_line_spacing
                                st.session_state.default_is_bold = st.session_state.preview_is_bold
                                st.success("✅ تنظیمات به عنوان پیش‌فرض اعمال شدند.")
                            
                            # ساخت پیش‌نمایش زنده با متن
                            try:
                                # ایجاد پیش‌نمایش با تمپلیت و متن
                                template_width, template_height = template_preview.size
                                
                                # ایجاد یک تصویر پایه خالی
                                preview_image = Image.new('RGBA', (template_width, template_height), (255, 255, 255, 255))
                                
                                # اضافه کردن تمپلیت
                                if template_preview.mode == 'RGBA':
                                    preview_image = Image.alpha_composite(preview_image, template_preview)
                                else:
                                    template_rgba = template_preview.convert('RGBA')
                                    preview_image = Image.alpha_composite(preview_image, template_rgba)
                                
                                # آماده‌سازی متن فارسی
                                reshaped_text = arabic_reshaper.reshape(st.session_state.preview_text)
                                bidi_text = get_display(reshaped_text)
                                
                                # محاسبه سایز فونت بر اساس درصد ارتفاع
                                font_size = int(template_height * (st.session_state.preview_font_size / 100))
                                
                                # انتخاب فونت مناسب
                                font_path = FONT_BOLD_PATH if st.session_state.preview_is_bold else FONT_PATH
                                font = ImageFont.truetype(font_path, font_size)
                                
                                # ایجاد یک تصویر شفاف برای متن
                                text_image = Image.new('RGBA', (template_width, template_height), (255, 255, 255, 0))
                                text_draw = ImageDraw.Draw(text_image)
                                
                                # محاسبه حداکثر عرض متن
                                max_width = template_width * (st.session_state.preview_max_text_width / 100)
                                
                                # شکستن متن به خطوط
                                lines = wrap_text_to_lines(text_draw, bidi_text, font, max_width)
                                
                                # محاسبه ارتفاع کل متن
                                line_spacing_factor = st.session_state.preview_line_spacing / 100
                                line_height = int(font_size * line_spacing_factor)
                                total_text_height = line_height * len(lines)
                                
                                # محاسبه موقعیت شروع متن
                                start_y = int((template_height - total_text_height) * (st.session_state.preview_text_y / 100))
                                
                                # رسم هر خط متن
                                for i, line in enumerate(lines):
                                    line_width = text_draw.textlength(line, font=font)
                                    line_x = int((template_width - line_width) * (st.session_state.preview_text_x / 100))
                                    line_y = start_y + i * line_height
                                    text_draw.text((line_x, line_y), line, font=font, fill=st.session_state.preview_text_color)
                                
                                # ترکیب تصویر متن با تصویر اصلی
                                preview_image = Image.alpha_composite(preview_image, text_image)
                                
                                # نمایش نتیجه
                                st.image(preview_image, caption="پیش‌نمایش نهایی با متن", width=300)
                                
                            except Exception as e:
                                st.error(f"خطا در ساخت پیش‌نمایش متن: {str(e)}")
                                st.error("جزئیات خطا:")
                                st.code(traceback.format_exc())
                        else:
                            st.warning("لطفاً ابتدا متنی وارد کنید تا پیش‌نمایش را ببینید.")

                    # دکمه ذخیره تمپلیت
                    st.markdown("---")
                    if st.button("💾 ذخیره این تمپلیت"):
                        # تعیین نام فایل برای ذخیره
                        if template_name:
                            # اطمینان از داشتن پسوند مناسب
                            if not (template_name.endswith('.png') or template_name.endswith('.jpg') or template_name.endswith('.jpeg')):
                                template_name += '.' + template_file.name.split('.')[-1]
                        else:
                            template_name = template_file.name
                        
                        # مسیر ذخیره تمپلیت
                        save_path = os.path.join(TEMPLATES_DIR, template_name)
                        
                        # ذخیره فایل
                        with open(save_path, "wb") as f:
                            f.write(template_file.getbuffer())
                        
                        # ذخیره تنظیمات پیش‌فرض
                        template_settings = {
                            "text": {
                                "font_size_percent": st.session_state.default_font_size,
                                "text_color": st.session_state.default_text_color,
                                "text_x_percent": st.session_state.default_text_x,
                                "text_y_percent": st.session_state.default_text_y,
                                "max_text_width_percent": st.session_state.default_max_text_width,
                                "line_spacing_percent": st.session_state.default_line_spacing,
                                "is_bold": st.session_state.default_is_bold
                            },
                            "layer": {
                                "x_percent": st.session_state.default_layer_x,
                                "y_percent": st.session_state.default_layer_y,
                                "size_percent": st.session_state.default_layer_size,
                                "opacity": st.session_state.default_layer_opacity
                            }
                        }
                        
                        template_name_without_ext = os.path.splitext(template_name)[0]
                        save_template_settings(template_name_without_ext, template_settings)
                        
                        # پاک کردن لایه‌های پیش‌نمایش و متن پیش‌نمایش
                        st.session_state.preview_layers = []
                        st.session_state.preview_text = ""
                        
                        st.success(f"✅ تمپلیت با موفقیت ذخیره شد! ({template_name})")
                        if template_settings:
                            st.success("✅ تنظیمات پیش‌فرض برای این تمپلیت ذخیره شد.")
                        st.info("تمپلیت جدید به لیست تمپلیت‌های موجود اضافه شد.")
                except Exception as e:
                    st.error(f"خطا در بارگذاری تمپلیت: {str(e)}")
    
    with settings_tab2:
        # بخش مدیریت رنگ‌های پیش‌فرض
        # کارت رنگ‌های موجود
        with st.container():
            st.subheader("📋 رنگ‌های ذخیره شده")
            
            if st.session_state.default_colors:
                # تعداد ستون‌ها برای نمایش رنگ‌ها
                num_cols = 3
                color_rows = [st.session_state.default_colors[i:i+num_cols] for i in range(0, len(st.session_state.default_colors), num_cols)]
                
                for row_idx, row in enumerate(color_rows):
                    cols = st.columns(num_cols)
                    for col_idx, color_item in enumerate(row):
                        idx = row_idx * num_cols + col_idx
                        with cols[col_idx]:
                            # نمایش نام و مقدار رنگ
                            st.markdown(f"<div style='display: flex; align-items: center; margin-bottom: 10px;'>"
                                        f"<div style='width: 30px; height: 30px; background-color: {color_item['value']}; margin-right: 10px; border: 1px solid #ccc;'></div>"
                                        f"<span>{color_item['name']} ({color_item['value']})</span>"
                                        f"</div>", unsafe_allow_html=True)
                            
                            # دکمه حذف رنگ
                            if st.button("🗑️ حذف", key=f"delete_color_{idx}"):
                                st.session_state.default_colors.pop(idx)
                                
                                # ذخیره تغییرات در فایل دیتابیس
                                if save_colors(st.session_state.default_colors):
                                    st.success(f"رنگ با موفقیت حذف شد!")
                                else:
                                    st.error("خطا در ذخیره‌سازی تغییرات. تغییرات موقت اعمال شد.")
                                
                                st.rerun()
            else:
                st.info("🔍 هنوز رنگی ذخیره نشده است. لطفاً از فرم زیر، رنگ مورد نظر خود را اضافه کنید.")
        
        # کارت افزودن رنگ جدید
        with st.container():
            st.subheader("➕ افزودن رنگ جدید")
            
            # فرم افزودن رنگ جدید
            col1, col2 = st.columns(2)
            
            with col1:
                new_color_name = st.text_input("نام رنگ", value=st.session_state.new_color_name, key="new_color_name_input", 
                                              help="یک نام معنادار برای رنگ خود وارد کنید (مثلا: آبی آسمانی، قرمز لوگو، و...)")
                
                # بروزرسانی مقدار در session state
                if st.session_state.new_color_name != new_color_name:
                    st.session_state.new_color_name = new_color_name
            
            with col2:
                new_color_value = st.color_picker("انتخاب رنگ", value=st.session_state.new_color_value, key="new_color_value_picker")
                
                # بروزرسانی مقدار در session state
                if st.session_state.new_color_value != new_color_value:
                    st.session_state.new_color_value = new_color_value
            
            # نمایش پیش‌نمایش رنگ
            st.markdown(f"<div style='display: flex; align-items: center; margin: 15px 0;'>"
                       f"<div style='width: 50px; height: 30px; background-color: {new_color_value}; margin-right: 10px; border: 1px solid #ccc;'></div>"
                       f"<span>پیش‌نمایش رنگ انتخاب شده: {new_color_value}</span>"
                       f"</div>", unsafe_allow_html=True)
            
            # دکمه ذخیره رنگ
            if st.button("💾 ذخیره این رنگ"):
                if new_color_name.strip() == "":
                    st.error("❌ لطفاً یک نام برای رنگ وارد کنید.")
                else:
                    # بررسی تکراری نبودن نام
                    existing_names = [color["name"] for color in st.session_state.default_colors]
                    if new_color_name in existing_names:
                        st.warning(f"⚠️ رنگی با نام '{new_color_name}' قبلاً ذخیره شده است. لطفاً نام دیگری انتخاب کنید.")
                    else:
                        # افزودن رنگ جدید به لیست
                        st.session_state.default_colors.append({
                            "name": new_color_name,
                            "value": new_color_value
                        })
                        
                        # ذخیره رنگ‌ها در فایل
                        if save_colors(st.session_state.default_colors):
                            # پاک کردن مقادیر فرم برای رنگ بعدی
                            st.session_state.new_color_name = ""
                            st.session_state.new_color_value = "#000000"
                            
                            st.success(f"✅ رنگ '{new_color_name}' با موفقیت ذخیره شد!")
                        else:
                            st.error("❌ خطا در ذخیره‌سازی رنگ. لطفاً دوباره تلاش کنید.")
                        
                        st.rerun()
    
    # فضای خالی برای تنظیمات بیشتر در آینده
    st.markdown("---")
    st.markdown("### تنظیمات بیشتر")
    # در اینجا می‌توانید تنظیمات بیشتری اضافه کنید

else:
    # صفحه اصلی
    # عنوان اصلی
    
    # ایجاد هدر با دکمه تنظیمات
    col1, col2 = st.columns([5, 1])
    with col1:
        st.title("🎨 تصویرساز فارسی")
    with col2:
        if st.button("⚙️ تنظیمات", key="header_settings_button"):
            st.session_state.current_page = 'settings'
            st.rerun()
    
    st.markdown("---")
    
    # سایدبار
    with st.sidebar:
        # تب‌های سایدبار
        tab1, tab2 = st.tabs(["📝 راهنما", "👁️ پیش‌نمایش"])
        
        with tab1:
            st.header("راهنمای استفاده")
            st.markdown("""
            ### نحوه استفاده:
            1. یک تمپلیت آپلود یا انتخاب کنید
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
            # بررسی وجود تمپلیت (از فایل آپلود شده یا انتخاب شده)
            template_path = None
            if st.session_state.selected_template_path:
                template_path = st.session_state.selected_template_path
            
            if template_path and (st.session_state.layers or st.session_state.text):
                try:
                    # باز کردن تمپلیت
                    template = Image.open(template_path)
                    
                    # محاسبه ابعاد تصویر
                    template_width, template_height = template.size
                    min_dimension = min(template_width, template_height)
                    
                    # ایجاد یک تصویر پایه خالی (سفید)
                    preview_image = Image.new('RGBA', (template_width, template_height), (255, 255, 255, 255))
                    draw = ImageDraw.Draw(preview_image)
                    
                    # اضافه کردن لایه‌ها به زمینه سفید
                    for layer in st.session_state.layers:
                        if layer.visible and layer.image:
                            # محاسبه سایز تصویر بر اساس درصد کوچکترین بعد تمپلیت
                            # مقادیر بزرگتر از 100% باعث می‌شود تصویر بزرگتر از حالت اصلی شود
                            max_dimension = int(min_dimension * (layer.size_percent / 100))
                            
                            # تغییر سایز تصویر لایه با حفظ نسبت تصویر
                            original_width, original_height = layer.image.size
                            aspect_ratio = original_width / original_height
                            
                            if aspect_ratio >= 1:  # عرض بزرگتر یا مساوی ارتفاع است
                                new_width = max_dimension
                                new_height = int(max_dimension / aspect_ratio)
                            else:  # ارتفاع بزرگتر از عرض است
                                new_height = max_dimension
                                new_width = int(max_dimension * aspect_ratio)
                            
                            # حتی اگر مقیاس بزرگتر از 100% باشد، تغییر سایز انجام می‌شود (بزرگنمایی)
                            layer_image = layer.image.resize((new_width, new_height), Image.LANCZOS)
                            
                            # تبدیل به RGBA اگر PNG است
                            if layer_image.mode != 'RGBA':
                                layer_image = layer_image.convert('RGBA')
                            
                            # اعمال شفافیت
                            if layer.opacity < 100:
                                layer_image.putalpha(int(255 * layer.opacity / 100))
                            
                            # محاسبه موقعیت مرکز تصویر
                            img_x = int((template_width - new_width) * (layer.x_percent / 100))
                            img_y = int((template_height - new_height) * (layer.y_percent / 100))
                            
                            # اضافه کردن تصویر به پیش‌نمایش
                            preview_image.paste(layer_image, (img_x, img_y), layer_image)
                    
                    # اضافه کردن تمپلیت به عنوان لایه بالایی (بالاتر از لایه‌های تصویر)
                    if template.mode == 'RGBA':
                        # اگر تمپلیت شفافیت داشته باشد، با حفظ شفافیت روی تصویر قرار می‌گیرد
                        preview_image = Image.alpha_composite(preview_image, template)
                    else:
                        # تبدیل تمپلیت به RGBA
                        template_rgba = template.convert('RGBA')
                        preview_image = Image.alpha_composite(preview_image, template_rgba)
                    
                    # اضافه کردن متن به عنوان بالاترین لایه (روی همه چیز، حتی تمپلیت)
                    if st.session_state.text:
                        # آماده‌سازی متن فارسی
                        reshaped_text = arabic_reshaper.reshape(st.session_state.text)
                        bidi_text = get_display(reshaped_text)
                        
                        # محاسبه سایز فونت بر اساس درصد ارتفاع
                        font_size = int(template_height * (st.session_state.font_size_percent / 100))
                        
                        try:
                            # انتخاب فونت مناسب بر اساس وضعیت بولد
                            font_path = FONT_BOLD_PATH if st.session_state.is_bold else FONT_PATH
                            font = ImageFont.truetype(font_path, font_size)
                            
                            # ایجاد یک تصویر شفاف برای متن
                            text_image = Image.new('RGBA', (template_width, template_height), (255, 255, 255, 0))
                            text_draw = ImageDraw.Draw(text_image)
                            
                            # محاسبه حداکثر عرض متن
                            max_width = template_width * (st.session_state.max_text_width_percent / 100)
                            
                            # شکستن متن به خطوط
                            lines = wrap_text_to_lines(text_draw, bidi_text, font, max_width)
                            
                            # محاسبه ارتفاع کل متن
                            # فاصله بین خطوط را به درصدی از ارتفاع فونت تنظیم می‌کنیم
                            line_spacing_factor = st.session_state.line_spacing_percent / 100
                            line_height = int(font_size * line_spacing_factor)
                            total_text_height = line_height * len(lines)
                            
                            # محاسبه موقعیت شروع متن - نسبت به ابعاد تمپلیت
                            # برای موقعیت افقی (x): 0% یعنی چپ، 50% یعنی وسط و 100% یعنی راست تمپلیت
                            # برای موقعیت عمودی (y): 0% یعنی بالا، 50% یعنی وسط و 100% یعنی پایین تمپلیت
                            start_y = int((template_height - total_text_height) * (st.session_state.text_y_percent / 100))
                            
                            # رسم هر خط متن روی تصویر شفاف
                            for i, line in enumerate(lines):
                                line_width = text_draw.textlength(line, font=font)
                                # محاسبه موقعیت افقی متن نسبت به عرض تمپلیت
                                line_x = int((template_width - line_width) * (st.session_state.text_x_percent / 100))
                                line_y = start_y + i * line_height
                                text_draw.text((line_x, line_y), line, font=font, fill=st.session_state.text_color)
                            
                            # ترکیب تصویر متن با تصویر اصلی
                            preview_image = Image.alpha_composite(preview_image, text_image)
                        except Exception as e:
                            st.error(f"خطا در بارگذاری فونت: {str(e)}")
                            # استفاده از فونت پیش‌فرض در صورت خطا
                            font = ImageFont.load_default()
                            st.warning("از فونت پیش‌فرض استفاده شد. متن چندخطی با این فونت پشتیبانی نمی‌شود.")
                            draw.text((10, 10), bidi_text, font=font, fill=st.session_state.text_color)
                    
                    # نمایش تصویر با سایز محدود شده
                    st.image(preview_image, caption=f"پیش‌نمایش ({template_width}x{template_height})", width=300)
                    
                    # ذخیره تصویر با سایز اصلی
                    final_image = preview_image.copy()
                    final_image.save("output.png", quality=100)
                    
                    # ایجاد دکمه دانلود
                    with open("output.png", "rb") as file:
                        btn = st.download_button(
                            label="⬇️ دانلود تصویر",
                            data=file,
                            file_name="output.png",
                            mime="image/png",
                            key="sidebar_download_btn"
                        )
                    
                    st.success(f"✅ تصویر با موفقیت ساخته شد! (سایز: {template_width}x{template_height})")
                    
                except Exception as e:
                    st.error(f"❌ خطا در ساخت تصویر: {str(e)}")
                    st.error("جزئیات خطا:")
                    st.code(traceback.format_exc())
            else:
                st.info("👆 برای مشاهده پیش‌نمایش، ابتدا یک تمپلیت انتخاب کنید و حداقل یک لایه یا متن اضافه کنید.")
        
        # نمایش اطلاعات کاربر و دکمه خروج
        st.markdown("---")
        st.markdown(f"👤 کاربر: {st.session_state.username}")
        if st.button("🚪 خروج"):
            logout()
    
    # آپلود و مدیریت تمپلیت
    st.markdown('<p class="upload-header">1️⃣ انتخاب تمپلیت</p>', unsafe_allow_html=True)
    
    # دریافت لیست تمپلیت‌های موجود
    template_files = glob.glob(os.path.join(TEMPLATES_DIR, "*.png")) + glob.glob(os.path.join(TEMPLATES_DIR, "*.jpg"))
    template_files.sort(key=os.path.getmtime, reverse=True)  # مرتب‌سازی بر اساس زمان ایجاد
    
    if template_files:
        # ساخت لیست نمایشی از تمپلیت‌ها
        template_names = [os.path.basename(f) for f in template_files]
        
        # ایجاد لیست نمایشی با ستاره برای تمپلیت‌هایی که تنظیمات پیش‌فرض دارند
        display_template_names = []
        for template in template_names:
            template_basename = os.path.splitext(template)[0]
            if has_template_settings(template_basename):
                display_template_names.append(f"⭐ {template}")
            else:
                display_template_names.append(template)
        
        template_options = ["انتخاب کنید..."] + display_template_names
        
        # انتخاب تمپلیت
        selected_display_template = st.selectbox(
            "تمپلیت موردنظر را انتخاب کنید",
            template_options,
            index=0,
            help="یک تمپلیت از لیست انتخاب کنید یا از بخش 'تنظیمات' تمپلیت جدید اضافه کنید"
        )
        
        if selected_display_template != "انتخاب کنید...":
            # حذف ستاره از نام تمپلیت برای پیدا کردن فایل
            selected_template = selected_display_template.replace("⭐ ", "")
            selected_template_path = os.path.join(TEMPLATES_DIR, selected_template)
            
            # ذخیره انتخاب کاربر
            st.session_state.selected_template_name = selected_template
            st.session_state.selected_template_path = selected_template_path
            
            # بررسی و بارگذاری تنظیمات پیش‌فرض
            template_basename = os.path.splitext(selected_template)[0]
            template_settings = load_template_settings(template_basename)
            
            if template_settings:
                # اعمال تنظیمات پیش‌فرض برای متن
                text_settings = template_settings.get("text", {})
                st.session_state.font_size_percent = text_settings.get("font_size_percent", 4)
                st.session_state.text_color = text_settings.get("text_color", "#000000")
                st.session_state.is_bold = text_settings.get("is_bold", False)
                st.session_state.text_x_percent = text_settings.get("text_x_percent", 50)
                st.session_state.text_y_percent = text_settings.get("text_y_percent", 98)
                st.session_state.max_text_width_percent = text_settings.get("max_text_width_percent", 80)
                st.session_state.line_spacing_percent = text_settings.get("line_spacing_percent", 120)
                
                # ذخیره تنظیمات پیش‌فرض لایه برای استفاده در هنگام ایجاد لایه جدید
                if "default_layer_settings" not in st.session_state:
                    st.session_state.default_layer_settings = {}
                
                st.session_state.default_layer_settings = template_settings.get("layer", {})
            
            # نمایش پیش‌نمایش تمپلیت
            try:
                template_preview = Image.open(selected_template_path)
                st.image(template_preview, caption=f"پیش‌نمایش تمپلیت: {selected_template}", width=300)
                
                if template_settings:
                    st.success(f"✅ تمپلیت '{selected_template}' با تنظیمات پیش‌فرض انتخاب شد. حالا می‌توانید لایه‌ها و متن را اضافه کنید.")
                else:
                    st.success(f"✅ تمپلیت '{selected_template}' انتخاب شد. حالا می‌توانید لایه‌ها و متن را اضافه کنید.")
            except Exception as e:
                st.error(f"خطا در بارگذاری تمپلیت: {str(e)}")
    else:
        st.info("🔍 هنوز تمپلیتی ذخیره نشده است. لطفاً از بخش 'تنظیمات'، تمپلیت جدید اضافه کنید.")
        # دکمه رفتن به بخش تنظیمات
        if st.button("رفتن به بخش تنظیمات"):
            st.session_state.current_page = 'settings'
            st.rerun()
    
    # بررسی وضعیت انتخاب تمپلیت برای نمایش بخش‌های بعدی
    if st.session_state.selected_template_path:
        # نمایش بخش مدیریت لایه‌ها
        st.markdown('<p class="upload-header">2️⃣ مدیریت لایه‌ها</p>', unsafe_allow_html=True)
        
        # دکمه افزودن لایه جدید
        if st.button("➕ افزودن لایه جدید"):
            new_layer = Layer(f"لایه {len(st.session_state.layers) + 1}")
            
            # اعمال تنظیمات پیش‌فرض لایه اگر موجود باشد
            if "default_layer_settings" in st.session_state and st.session_state.default_layer_settings:
                new_layer.x_percent = st.session_state.default_layer_settings.get("x_percent", 50)
                new_layer.y_percent = st.session_state.default_layer_settings.get("y_percent", 0)
                new_layer.size_percent = st.session_state.default_layer_settings.get("size_percent", 100)
                new_layer.opacity = st.session_state.default_layer_settings.get("opacity", 100)
            
            st.session_state.layers.append(new_layer)
            st.rerun()
        
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
                        # ایجاد کلید یکتا برای تصویر
                        if layer.image_key != uploaded_file.name:
                            layer.image_key = uploaded_file.name
                            layer.image = Image.open(uploaded_file)
                            st.rerun()  # بروزرسانی صفحه برای نمایش تصویر جدید
                        
                        st.image(layer.image, caption="پیش‌نمایش تصویر", width=200)
                    except Exception as e:
                        st.error(f"خطا در بارگذاری تصویر: {str(e)}")
                
                # تنظیمات لایه
                col1, col2 = st.columns(2)
                with col1:
                    new_x = st.slider(
                        "موقعیت افقی (%)",
                        0, 100, layer.x_percent,
                        key=f"layer_{i}_x",
                        help="0: چپ، 50: وسط، 100: راست"
                    )
                    new_size = st.slider(
                        "اندازه (%)",
                        10, 300, layer.size_percent,
                        key=f"layer_{i}_size",
                        help="سایز تصویر به صورت درصدی از کوچکترین بعد تمپلیت (مقادیر بزرگتر از 100% تصویر را بزرگتر از حالت اصلی نمایش می‌دهند)"
                    )
                    
                    # بروزرسانی مقادیر و رفرش صفحه
                    if new_x != layer.x_percent or new_size != layer.size_percent:
                        layer.x_percent = new_x
                        layer.size_percent = new_size
                        st.rerun()
                
                with col2:
                    new_y = st.slider(
                        "موقعیت عمودی (%)",
                        0, 100, layer.y_percent,
                        key=f"layer_{i}_y",
                        help="0: بالا، 50: وسط، 100: پایین"
                    )
                    new_opacity = st.slider(
                        "شفافیت (%)",
                        0, 100, layer.opacity,
                        key=f"layer_{i}_opacity",
                        help="شفافیت تصویر (0: کاملاً شفاف، 100: کاملاً مات)"
                    )
                    
                    # بروزرسانی مقادیر و رفرش صفحه
                    if new_y != layer.y_percent or new_opacity != layer.opacity:
                        layer.y_percent = new_y
                        layer.opacity = new_opacity
                        st.rerun()
                
                # کنترل‌های لایه
                col1, col2 = st.columns(2)
                with col1:
                    new_visible = st.checkbox(
                        "نمایش لایه",
                        value=layer.visible,
                        key=f"layer_{i}_visible"
                    )
                    
                    # بروزرسانی وضعیت نمایش و رفرش صفحه
                    if new_visible != layer.visible:
                        layer.visible = new_visible
                        st.rerun()
                    
                with col2:
                    if st.button("🗑️ حذف لایه", key=f"layer_{i}_delete"):
                        st.session_state.layers.pop(i)
                        st.rerun()
                
                st.markdown("---")

        # ورود متن
        st.markdown('<p class="upload-header">3️⃣ وارد کردن متن</p>', unsafe_allow_html=True)
        text_input = st.text_area("متن مورد نظر را وارد کنید", value=st.session_state.text, height=150, key="text_input", help="متن فارسی که می‌خواهید روی تصویر قرار دهید را وارد کنید. هر خط جدید در تصویر نیز به عنوان خط جدید نمایش داده می‌شود.")

        # ذخیره متن در session state
        if 'text_input' in st.session_state and st.session_state.text_input != st.session_state.text:
            st.session_state.text = st.session_state.text_input
            st.rerun()
        
        # تنظیمات متن
        st.markdown('<p class="settings-header">⚙️ تنظیمات متن</p>', unsafe_allow_html=True)
        text_col1, text_col2 = st.columns(2)

        with text_col1:
            font_size = st.slider("سایز فونت (% ارتفاع تصویر)", 1, 20, st.session_state.font_size_percent, key="font_size_slider", help="سایز فونت به صورت درصدی از ارتفاع تصویر", on_change=lambda: st.session_state.update({"font_size_percent": st.session_state.font_size_slider}))
            
            # بخش انتخاب رنگ متن با قابلیت استفاده از رنگ‌های ذخیره شده
            st.markdown("#### رنگ متن")
            
            # نمایش رنگ فعلی
            st.markdown(f"""
            <div style="display: flex; align-items: center; margin-bottom: 15px;">
                <div style="width: 30px; height: 30px; background-color: {st.session_state.text_color}; border: 1px solid #ccc; margin-right: 10px; border-radius: 4px;"></div>
                <span>رنگ فعلی: {st.session_state.text_color}</span>
            </div>
            """, unsafe_allow_html=True)
            
            # انتخاب رنگ سفارشی
            st.markdown("##### انتخاب رنگ سفارشی:")
            text_color = st.color_picker("", st.session_state.text_color, key="text_color_picker", help="رنگ متن را انتخاب کنید")
            if 'text_color_picker' in st.session_state and st.session_state.text_color_picker != st.session_state.text_color:
                st.session_state.text_color = st.session_state.text_color_picker
            
            # نمایش رنگ‌های ذخیره شده
            if st.session_state.default_colors:
                st.markdown("##### انتخاب از رنگ‌های ذخیره شده:")
                
                # تعریف تعداد ستون‌ها - افزایش تعداد ستون‌ها برای نمایش فشرده‌تر
                colors_per_row = 6
                
                # ساخت HTML برای نمایش رنگ‌ها
                for i in range(0, len(st.session_state.default_colors), colors_per_row):
                    cols = st.columns(colors_per_row)
                    for j in range(colors_per_row):
                        idx = i + j
                        if idx < len(st.session_state.default_colors):
                            color = st.session_state.default_colors[idx]
                            with cols[j]:
                                # ایجاد یک دکمه که ظاهر آن به صورت مربع رنگی است
                                # افزودن کلاس CSS برای استایل دهی مناسب
                                st_key = f"color_btn_{idx}"
                                
                                # استفاده از HTML مستقیم برای نمایش رنگ
                                st.markdown(f"""
                                <div style="width: 100%; position: relative; margin-bottom: 5px;">
                                    <div style="width: 100%; height: 30px; background-color: {color['value']}; 
                                         border: {('2px solid black' if color['value'] == st.session_state.text_color else '1px solid #ccc')}; 
                                         border-radius: 4px;"></div>
                                    <div style="font-size: 0.8em; margin-top: 2px; text-align: center;">{color['name']}</div>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                # دکمه نامرئی که روی رنگ قرار می‌گیرد
                                # تابع تغییر رنگ بدون rerun
                                def change_color(color_value=color['value']):
                                    st.session_state.text_color = color_value
                                
                                if st.button("انتخاب", key=st_key, help=f"انتخاب رنگ {color['name']}", use_container_width=True, on_click=change_color):
                                    pass  # عملیات دیگری مورد نیاز نیست
                                
                                # CSS برای پوشاندن دکمه روی رنگ
                                st.markdown(f"""
                                <style>
                                button[data-testid="button-{st_key}"] {{
                                    position: absolute;
                                    top: 0;
                                    left: 0;
                                    width: 100%;
                                    height: calc(100% - 20px);
                                    opacity: 0;
                                    margin-top: -50px;
                                }}
                                </style>
                                """, unsafe_allow_html=True)
            else:
                st.info("هنوز رنگی ذخیره نشده است. از بخش تنظیمات، رنگ‌های مورد نظر خود را اضافه کنید.")
            
            is_bold = st.checkbox("متن بولد", value=st.session_state.is_bold, key="is_bold_checkbox", help="نمایش متن به صورت بولد")
            if 'is_bold_checkbox' in st.session_state and st.session_state.is_bold_checkbox != st.session_state.is_bold:
                st.session_state.is_bold = st.session_state.is_bold_checkbox

        with text_col2:
            text_x = st.slider("موقعیت افقی متن (%)", 0, 100, st.session_state.text_x_percent, key="text_x_slider", help="0: کاملاً چپ تمپلیت، 50: وسط تمپلیت، 100: کاملاً راست تمپلیت", on_change=lambda: st.session_state.update({"text_x_percent": st.session_state.text_x_slider}))
            text_y = st.slider("موقعیت عمودی متن (%)", 0, 100, st.session_state.text_y_percent, key="text_y_slider", help="0: کاملاً بالای تمپلیت، 50: وسط تمپلیت، 100: کاملاً پایین تمپلیت", on_change=lambda: st.session_state.update({"text_y_percent": st.session_state.text_y_slider}))
            max_text_width = st.slider("عرض متن (%)", 10, 100, st.session_state.max_text_width_percent, key="max_text_width_slider", help="حداکثر عرض متن به صورت درصدی از عرض تمپلیت", on_change=lambda: st.session_state.update({"max_text_width_percent": st.session_state.max_text_width_slider}))
            line_spacing = st.slider("فاصله خطوط (%)", 100, 200, st.session_state.line_spacing_percent, key="line_spacing_slider", help="فاصله بین خطوط متن به صورت درصدی از ارتفاع خط", on_change=lambda: st.session_state.update({"line_spacing_percent": st.session_state.line_spacing_slider}))

        # دکمه ساخت تصویر
        st.markdown("---")
        if st.button("🎨 ساخت تصویر"):
            # بررسی وجود تمپلیت (از فایل آپلود شده یا انتخاب شده)
            template_path = None
            if st.session_state.template_file:
                template_path = st.session_state.template_file
            elif st.session_state.selected_template_path:
                template_path = st.session_state.selected_template_path
            
            if template_path and (st.session_state.layers or st.session_state.text):
                try:
                    # باز کردن تمپلیت
                    template = Image.open(template_path)
                    
                    # محاسبه ابعاد تصویر
                    template_width, template_height = template.size
                    min_dimension = min(template_width, template_height)
                    
                    # ایجاد یک تصویر پایه خالی (سفید)
                    preview_image = Image.new('RGBA', (template_width, template_height), (255, 255, 255, 255))
                    draw = ImageDraw.Draw(preview_image)
                    
                    # اضافه کردن لایه‌ها به زمینه سفید
                    for layer in st.session_state.layers:
                        if layer.visible and layer.image:
                            # محاسبه سایز تصویر بر اساس درصد کوچکترین بعد تمپلیت
                            # مقادیر بزرگتر از 100% باعث می‌شود تصویر بزرگتر از حالت اصلی شود
                            max_dimension = int(min_dimension * (layer.size_percent / 100))
                            
                            # تغییر سایز تصویر لایه با حفظ نسبت تصویر
                            original_width, original_height = layer.image.size
                            aspect_ratio = original_width / original_height
                            
                            if aspect_ratio >= 1:  # عرض بزرگتر یا مساوی ارتفاع است
                                new_width = max_dimension
                                new_height = int(max_dimension / aspect_ratio)
                            else:  # ارتفاع بزرگتر از عرض است
                                new_height = max_dimension
                                new_width = int(max_dimension * aspect_ratio)
                            
                            # حتی اگر مقیاس بزرگتر از 100% باشد، تغییر سایز انجام می‌شود (بزرگنمایی)
                            layer_image = layer.image.resize((new_width, new_height), Image.LANCZOS)
                            
                            # تبدیل به RGBA اگر PNG است
                            if layer_image.mode != 'RGBA':
                                layer_image = layer_image.convert('RGBA')
                            
                            # اعمال شفافیت
                            if layer.opacity < 100:
                                layer_image.putalpha(int(255 * layer.opacity / 100))
                            
                            # محاسبه موقعیت مرکز تصویر
                            img_x = int((template_width - new_width) * (layer.x_percent / 100))
                            img_y = int((template_height - new_height) * (layer.y_percent / 100))
                            
                            # اضافه کردن تصویر به پیش‌نمایش
                            preview_image.paste(layer_image, (img_x, img_y), layer_image)
                    
                    # اضافه کردن تمپلیت به عنوان لایه بالایی (بالاتر از لایه‌های تصویر)
                    if template.mode == 'RGBA':
                        # اگر تمپلیت شفافیت داشته باشد، با حفظ شفافیت روی تصویر قرار می‌گیرد
                        preview_image = Image.alpha_composite(preview_image, template)
                    else:
                        # تبدیل تمپلیت به RGBA
                        template_rgba = template.convert('RGBA')
                        preview_image = Image.alpha_composite(preview_image, template_rgba)
                    
                    # اضافه کردن متن به عنوان بالاترین لایه (روی همه چیز، حتی تمپلیت)
                    if st.session_state.text:
                        # آماده‌سازی متن فارسی
                        reshaped_text = arabic_reshaper.reshape(st.session_state.text)
                        bidi_text = get_display(reshaped_text)
                        
                        # محاسبه سایز فونت بر اساس درصد ارتفاع
                        font_size = int(template_height * (st.session_state.font_size_percent / 100))
                        
                        try:
                            # انتخاب فونت مناسب بر اساس وضعیت بولد
                            font_path = FONT_BOLD_PATH if st.session_state.is_bold else FONT_PATH
                            font = ImageFont.truetype(font_path, font_size)
                            
                            # ایجاد یک تصویر شفاف برای متن
                            text_image = Image.new('RGBA', (template_width, template_height), (255, 255, 255, 0))
                            text_draw = ImageDraw.Draw(text_image)
                            
                            # محاسبه حداکثر عرض متن
                            max_width = template_width * (st.session_state.max_text_width_percent / 100)
                            
                            # شکستن متن به خطوط
                            lines = wrap_text_to_lines(text_draw, bidi_text, font, max_width)
                            
                            # محاسبه ارتفاع کل متن
                            # فاصله بین خطوط را به درصدی از ارتفاع فونت تنظیم می‌کنیم
                            line_spacing_factor = st.session_state.line_spacing_percent / 100
                            line_height = int(font_size * line_spacing_factor)
                            total_text_height = line_height * len(lines)
                            
                            # محاسبه موقعیت شروع متن - نسبت به ابعاد تمپلیت
                            # برای موقعیت افقی (x): 0% یعنی چپ، 50% یعنی وسط و 100% یعنی راست تمپلیت
                            # برای موقعیت عمودی (y): 0% یعنی بالا، 50% یعنی وسط و 100% یعنی پایین تمپلیت
                            start_y = int((template_height - total_text_height) * (st.session_state.text_y_percent / 100))
                            
                            # رسم هر خط متن روی تصویر شفاف
                            for i, line in enumerate(lines):
                                line_width = text_draw.textlength(line, font=font)
                                # محاسبه موقعیت افقی متن نسبت به عرض تمپلیت
                                line_x = int((template_width - line_width) * (st.session_state.text_x_percent / 100))
                                line_y = start_y + i * line_height
                                text_draw.text((line_x, line_y), line, font=font, fill=st.session_state.text_color)
                            
                            # ترکیب تصویر متن با تصویر اصلی
                            preview_image = Image.alpha_composite(preview_image, text_image)
                        except Exception as e:
                            st.error(f"خطا در بارگذاری فونت: {str(e)}")
                            # استفاده از فونت پیش‌فرض در صورت خطا
                            font = ImageFont.load_default()
                            st.warning("از فونت پیش‌فرض استفاده شد. متن چندخطی با این فونت پشتیبانی نمی‌شود.")
                            draw.text((10, 10), bidi_text, font=font, fill=st.session_state.text_color)
                    
                    # نمایش تصویر با سایز محدود شده
                    st.image(preview_image, caption=f"پیش‌نمایش ({template_width}x{template_height})", width=300)
                    
                    # ذخیره تصویر با سایز اصلی
                    final_image = preview_image.copy()
                    final_image.save("output.png", quality=100)
                    
                    # ایجاد دکمه دانلود
                    with open("output.png", "rb") as file:
                        btn = st.download_button(
                            label="⬇️ دانلود تصویر",
                            data=file,
                            file_name="output.png",
                            mime="image/png",
                            key="main_download_btn"
                        )
                    
                    st.success(f"✅ تصویر با موفقیت ساخته شد! (سایز: {template_width}x{template_height})")
                    
                except Exception as e:
                    st.error(f"❌ خطا در ساخت تصویر: {str(e)}")
                    st.error("جزئیات خطا:")
                    st.code(traceback.format_exc())
            else:
                st.error("❌ لطفاً ابتدا یک تمپلیت انتخاب کنید و حداقل یک لایه یا متن وارد کنید!")
        else:
            st.warning("⚠️ لطفاً ابتدا یک تمپلیت انتخاب کنید یا یک تمپلیت جدید آپلود کنید.") 