import streamlit as st
from PIL import Image
import io
import base64
import requests

# Import Clipboard Paste Button
try:
    from streamlit_paste_button import paste_image_button as pbutton
    PASTE_BUTTON_AVAILABLE = True
except ImportError:
    PASTE_BUTTON_AVAILABLE = False

# 1. Page Configuration
st.set_page_config(
    page_title="Vizard Custom Image Processor",
    page_icon="✂️",
    layout="wide"
)

# Custom Styling
st.markdown("""
    <style>
    .stApp {
        background-color: #0F172A;
        color: #F8FAFC;
    }
    .main-title {
        text-align: center;
        font-size: 2.2rem;
        font-weight: 800;
        color: #38BDF8;
        margin-bottom: 20px;
    }
    div[data-testid="stBlock"] {
        background-color: rgba(30, 41, 59, 0.7);
        padding: 20px;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-title">✂️ Custom 960px Image Processor & Batch Namer</h1>', unsafe_allow_html=True)

# Helper function to resize without warping (Proportional Scaling + Padding)
def fit_image_without_distortion(img, target_width=960, min_height=300, max_height=500, bg_color=(255, 255, 255)):
    orig_w, orig_h = img.size
    aspect_ratio = orig_w / float(orig_h)

    # Calculate proportional height when width is fixed to 960px
    scaled_h = int(round(target_width / aspect_ratio))

    # Clamp height between min_height and max_height bounds
    canvas_h = max(min_height, min(max_height, scaled_h))

    # Calculate scaled dimensions that preserve aspect ratio without exceeding target bounds
    scale = min(target_width / orig_w, canvas_h / orig_h)
    new_w = int(round(orig_w * scale))
    new_h = int(round(orig_h * scale))

    # Resize image preserving ratio with LANCZOS
    resized_img = img.resize((new_w, new_h), resample=Image.Resampling.LANCZOS)

    # Create solid background canvas
    canvas = Image.new("RGB", (target_width, canvas_h), bg_color)

    # Center the resized image on the canvas
    offset_x = (target_width - new_w) // 2
    offset_y = (canvas_h - new_h) // 2

    if resized_img.mode == "RGBA":
        canvas.paste(resized_img, (offset_x, offset_y), mask=resized_img.split()[3])
    else:
        canvas.paste(resized_img, (offset_x, offset_y))

    return canvas, canvas_h

# Helper function to load image from URL or Base64 String
def load_image_from_input(pasted_str):
    pasted_str = pasted_str.strip()
    if not pasted_str:
        return None
        
    if pasted_str.startswith("data:image"):
        try:
            base64_str = pasted_str.split(",")[1]
            image_bytes = base64.b64decode(base64_str)
            return Image.open(io.BytesIO(image_bytes))
        except Exception:
            return None
            
    elif pasted_str.startswith("http://") or pasted_str.startswith("https://"):
        try:
            from urllib.parse import urlparse
            parsed_url = urlparse(pasted_str)
            domain_referer = f"{parsed_url.scheme}://{parsed_url.netloc}/"

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
                'Referer': domain_referer,
            }
            
            session = requests.Session()
            response = session.get(pasted_str, headers=headers, timeout=12, allow_redirects=True)
            response.raise_for_status()
            
            return Image.open(io.BytesIO(response.content))
            
        except Exception:
            return None
            
    else:
        return None

# Background Padding Color
bg_choice = st.radio(
    "🎨 Background Padding Color (to prevent warping):", 
    ["White", "Black"], 
    horizontal=True
)
padding_color = (255, 255, 255) if bg_choice == "White" else (0, 0, 0)

st.markdown("---")

# Input Source Selection
tab1, tab2, tab3 = st.tabs(["📁 Multi-File Upload (7 Rows)", "🔗 Multi-URL / Base64 (7 Rows)", "📋 Clipboard Paste (Single)"])

# -------------------------------------------------------------
# TAB 1: MULTI-FILE UPLOAD (7 ROWS WITH FILENAMES)
# -------------------------------------------------------------
with tab1:
    st.subheader("📁 Upload up to 7 Images with Custom File Names")
    
    file_items = []
    
    for i in range(1, 8):
        col_img, col_name = st.columns([1.5, 1])
        
        with col_img:
            uploaded_file = st.file_uploader(f"Row {i}: Upload Image", type=["jpg", "jpeg", "png", "webp"], key=f"file_upload_{i}")
        
        with col_name:
            custom_name = st.text_input(f"Row {i}: Custom Image Name", value=f"image_{i}", key=f"file_name_{i}")
            
        if uploaded_file is not None:
            try:
                img_obj = Image.open(uploaded_file)
                file_items.append((img_obj, custom_name))
            except Exception as e:
                st.error(f"Row {i} Error: {e}")

    if file_items:
        st.markdown("---")
        st.subheader("⚡ Processed Results")
        
        for idx, (img, name) in enumerate(file_items, 1):
            proc_img, final_h = fit_image_without_distortion(
                img, target_width=960, min_height=300, max_height=500, bg_color=padding_color
            )
            
            clean_name = name.strip() if name.strip() else f"image_{idx}"
            if not clean_name.lower().endswith(('.jpg', '.jpeg')):
                clean_name += ".jpg"

            col_p1, col_p2 = st.columns([1, 1.2])
            with col_p1:
                st.write(f"**Image {idx}:** `{clean_name}` ({proc_img.width}x{final_h}px)")
                buf = io.BytesIO()
                proc_img.save(buf, format="JPEG", quality=95, subsampling=0)
                st.download_button(
                    label=f"📥 Download {clean_name}",
                    data=buf.getvalue(),
                    file_name=clean_name,
                    mime="image/jpeg",
                    type="primary",
                    key=f"dl_file_{idx}"
                )
            with col_p2:
                st.image(proc_img, use_container_width=True)

# -------------------------------------------------------------
# TAB 2: MULTI-URL / BASE64 (7 ROWS WITH FILENAMES)
# -------------------------------------------------------------
with tab2:
    st.subheader("🔗 Paste up to 7 Image URLs or Base64 Strings with Custom File Names")
    
    url_items = []
    
    for i in range(1, 8):
        col_url, col_name = st.columns([1.5, 1])
        
        with col_url:
            pasted_url = st.text_input(f"Row {i}: Image URL / Base64", placeholder="https://example.com/image.jpg", key=f"url_input_{i}")
            
        with col_name:
            custom_name = st.text_input(f"Row {i}: Custom Image Name", value=f"image_{i}", key=f"url_name_{i}")
            
        if pasted_url:
            img_obj = load_image_from_input(pasted_url)
            if img_obj:
                url_items.append((img_obj, custom_name))
            else:
                st.warning(f"Row {i}: Could not load image from URL/Base64. Check the link.")

    if url_items:
        st.markdown("---")
        st.subheader("⚡ Processed Results")
        
        for idx, (img, name) in enumerate(url_items, 1):
            proc_img, final_h = fit_image_without_distortion(
                img, target_width=960, min_height=300, max_height=500, bg_color=padding_color
            )
            
            clean_name = name.strip() if name.strip() else f"image_{idx}"
            if not clean_name.lower().endswith(('.jpg', '.jpeg')):
                clean_name += ".jpg"

            col_p1, col_p2 = st.columns([1, 1.2])
            with col_p1:
                st.write(f"**Image {idx}:** `{clean_name}` ({proc_img.width}x{final_h}px)")
                buf = io.BytesIO()
                proc_img.save(buf, format="JPEG", quality=95, subsampling=0)
                st.download_button(
                    label=f"📥 Download {clean_name}",
                    data=buf.getvalue(),
                    file_name=clean_name,
                    mime="image/jpeg",
                    type="primary",
                    key=f"dl_url_{idx}"
                )
            with col_p2:
                st.image(proc_img, use_container_width=True)

# -------------------------------------------------------------
# TAB 3: CLIPBOARD PASTE
# -------------------------------------------------------------
with tab3:
    st.subheader("📋 Clipboard Single Image Paste")
    if PASTE_BUTTON_AVAILABLE:
        paste_result = pbutton(
            label="📋 Paste Image from Clipboard",
            text_color="#0F172A",
            background_color="#38BDF8",
            hover_background_color="#0284C7",
            errors="raise"
        )
        if paste_result.image_data is not None:
            col_c1, col_c2 = st.columns([1, 1.2])
            proc_img, final_h = fit_image_without_distortion(
                paste_result.image_data, target_width=960, min_height=300, max_height=500, bg_color=padding_color
            )
            with col_c1:
                clip_name = st.text_input("Download Image Name:", value="clipboard_image.jpg")
                if not clip_name.lower().endswith(('.jpg', '.jpeg')):
                    clip_name += ".jpg"
                buf = io.BytesIO()
                proc_img.save(buf, format="JPEG", quality=95, subsampling=0)
                st.download_button(
                    label=f"📥 Download {clip_name}",
                    data=buf.getvalue(),
                    file_name=clip_name,
                    mime="image/jpeg",
                    type="primary"
                )
            with col_c2:
                st.image(proc_img, use_container_width=True)
    else:
        st.warning("Clipboard paste plugin initializing...")
