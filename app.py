import streamlit as st
from PIL import Image, ImageOps
import io
import base64
import requests
import streamlit.components.v1 as components

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

st.markdown('<h1 class="main-title">✂️ Custom 960px Image Eraser & Auto-Fit Tool</h1>', unsafe_allow_html=True)

# Helper function to convert PIL Image to Base64 Data URL
def image_to_base64_url(img):
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"

# Helper function to load image from URL or Base64
def load_image_from_input(pasted_str):
    pasted_str = pasted_str.strip()
    if pasted_str.startswith("data:image"):
        try:
            base64_str = pasted_str.split(",")[1]
            image_bytes = base64.b64decode(base64_str)
            return Image.open(io.BytesIO(image_bytes))
        except Exception as e:
            st.error(f"Error decoding Base64 image: {e}")
            return None
    elif pasted_str.startswith("http://") or pasted_str.startswith("https://"):
        try:
            response = requests.get(pasted_str, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
            response.raise_for_status()
            return Image.open(io.BytesIO(response.content))
        except Exception as e:
            st.error(f"Failed to fetch image from URL: {e}")
            return None
    else:
        st.warning("Please paste a valid Image Web URL (http/https) or Base64 image data.")
        return None

# 2. Input Source Selection
st.subheader("1. Select Image Input Method")
tab1, tab2 = st.tabs(["📁 File Upload", "📋 Paste URL / Clipboard"])

img_input = None

with tab1:
    uploaded_file = st.file_uploader("Upload Image", type=["jpg", "jpeg", "png", "webp"])
    if uploaded_file:
        img_input = Image.open(uploaded_file)

with tab2:
    pasted_data = st.text_input(
        "Paste Image URL or Base64 Data here:", 
        key="clipboard_text_input", 
        placeholder="https://example.com/image.jpg or data:image/png;base64,...",
        help="Paste a direct image link or copied base64 string."
    )
    
    if pasted_data:
        img_input = load_image_from_input(pasted_data)

if img_input is not None:
    st.markdown("---")
    
    mode = st.radio(
        "🛠️ Choose Processing Tool:", 
        [
            "⚡ 1-Click Auto-Fit (960px x 300-500px)", 
            "🧹 White Eraser Brush"
        ], 
        horizontal=True
    )

    # -------------------------------------------------------------
    # MODE 1: 1-CLICK AUTO-FIT MODE
    # -------------------------------------------------------------
    if "1-Click Auto-Fit" in mode:
        st.subheader("⚡ 1-Click Auto-Fit Center Crop")
        st.caption("Automatically calculates the closest aspect ratio to fit height between 300px and 500px at 960px width with minimal cropping.")
        
        col_controls, col_preview = st.columns([1, 1.2])

        orig_w, orig_h = img_input.size
        orig_aspect_ratio = orig_w / float(orig_h)
        ideal_height = 960 / orig_aspect_ratio
        optimal_height = int(max(300, min(500, round(ideal_height))))

        with col_controls:
            st.info(f"📏 **Original Size:** {orig_w} x {orig_h} px")
            st.success(f"🎯 **Auto-Calculated Output:** 960 x {optimal_height} px")

            centering_y = st.slider("Vertical Alignment Shift (Top ↔ Bottom):", 0.0, 1.0, 0.5, 0.05)

            auto_fit_img = ImageOps.fit(
                img_input,
                (960, optimal_height),
                method=Image.Resampling.LANCZOS,
                centering=(0.5, centering_y)
            )

        with col_preview:
            st.image(auto_fit_img, caption=f"Auto-Fit Result: 960 x {optimal_height} px", use_container_width=True)

            buf = io.BytesIO()
            save_img = auto_fit_img.convert("RGB") if auto_fit_img.mode in ("RGBA", "P") else auto_fit_img
            save_img.save(buf, format="JPEG", quality=95)
            
            st.download_button(
                label=f"📥 Download Auto-Fit Image (960 x {optimal_height} px)",
                data=buf.getvalue(),
                file_name=f"autofit_960x{optimal_height}.jpg",
                mime="image/jpeg",
                type="primary",
                use_container_width=True
            )

    # -------------------------------------------------------------
    # MODE 2: WHITE ERASER BRUSH (HTML5 CANVAS - NO CRASHES)
    # -------------------------------------------------------------
    else:
        st.subheader("🧹 White Eraser Tool")
        st.caption("Paint directly over the image using the white brush. Adjust brush size using the slider.")

        e_col1, e_col2 = st.columns([1.2, 1])

        with e_col1:
            eraser_size = st.slider("White Eraser Brush Size (px):", min_value=5, max_value=100, value=25, step=5)

            canvas_width = 700
            w_percent = (canvas_width / float(img_input.size[0]))
            h_size = int((float(img_input.size[1]) * float(w_percent)))
            resized_for_canvas = img_input.resize((canvas_width, h_size), Image.Resampling.LANCZOS)
            bg_data_url = image_to_base64_url(resized_for_canvas)

            # Native HTML5 Canvas component that renders image natively and enables white brush
            html_code = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ margin: 0; padding: 0; background-color: transparent; font-family: sans-serif; color: white; }}
                    #canvas-container {{ position: relative; width: {canvas_width}px; height: {h_size}px; cursor: crosshair; }}
                    canvas {{ border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.3); }}
                    .btn-container {{ margin-top: 10px; display: flex; gap: 10px; }}
                    button {{
                        background-color: #38BDF8; color: #0F172A; border: none; padding: 8px 16px;
                        font-weight: bold; border-radius: 6px; cursor: pointer; transition: 0.2s;
                    }}
                    button:hover {{ background-color: #0284C7; color: white; }}
                    button.clear {{ background-color: #EF4444; color: white; }}
                    button.clear:hover {{ background-color: #DC2626; }}
                </style>
            </head>
            <body>
                <div id="canvas-container">
                    <canvas id="eraserCanvas" width="{canvas_width}" height="{h_size}"></canvas>
                </div>
                <div class="btn-container">
                    <button id="saveBtn">💾 Apply Changes</button>
                    <button id="clearBtn" class="clear">🔄 Reset Canvas</button>
                </div>

                <script>
                    const canvas = document.getElementById('eraserCanvas');
                    const ctx = canvas.getContext('2d');
                    const img = new Image();
                    img.src = "{bg_data_url}";

                    let isDrawing = false;
                    let brushSize = {eraser_size};

                    img.onload = () => {{
                        ctx.drawImage(img, 0, 0, {canvas_width}, {h_size});
                    }};

                    function getPos(e) {{
                        const rect = canvas.getBoundingClientRect();
                        return {{
                            x: e.clientX - rect.left,
                            y: e.clientY - rect.top
                        }};
                    }}

                    function startDrawing(e) {{
                        isDrawing = true;
                        draw(e);
                    }}

                    function stopDrawing() {{
                        isDrawing = false;
                        ctx.beginPath();
                    }}

                    function draw(e) {{
                        if (!isDrawing) return;
                        const pos = getPos(e);
                        ctx.lineWidth = brushSize;
                        ctx.lineCap = 'round';
                        ctx.strokeStyle = '#FFFFFF';

                        ctx.lineTo(pos.x, pos.y);
                        ctx.stroke();
                        ctx.beginPath();
                        ctx.moveTo(pos.x, pos.y);
                    }}

                    canvas.addEventListener('mousedown', startDrawing);
                    canvas.addEventListener('mousemove', draw);
                    canvas.addEventListener('mouseup', stopDrawing);
                    canvas.addEventListener('mouseleave', stopDrawing);

                    document.getElementById('clearBtn').onclick = () => {{
                        ctx.clearRect(0, 0, canvas.width, canvas.height);
                        ctx.drawImage(img, 0, 0, {canvas_width}, {h_size});
                    }};

                    document.getElementById('saveBtn').onclick = () => {{
                        const dataUrl = canvas.toDataURL('image/png');
                        window.parent.postMessage({{
                            type: 'streamlit:setComponentValue',
                            value: dataUrl
                        }}, '*');
                    }};
                </script>
            </body>
            </html>
            """

            # Render HTML Canvas (Height accommodates canvas + controls)
            canvas_result_data = components.html(html_code, height=h_size + 60)

        with e_col2:
            st.subheader("🖼️ Output Image")
            
            # Allow image processing from canvas output or original fallback
            if canvas_result_data:
                try:
                    base64_result = canvas_result_data.split(",")[1]
                    erased_final = Image.open(io.BytesIO(base64.b64decode(base64_result)))
                    st.image(erased_final, caption="Erased Output Preview", use_container_width=True)

                    buf_e = io.BytesIO()
                    erased_final.convert("RGB").save(buf_e, format="JPEG", quality=95)

                    st.download_button(
                        label="📥 Download Erased Image",
                        data=buf_e.getvalue(),
                        file_name="erased_image.jpg",
                        mime="image/jpeg",
                        type="primary",
                        use_container_width=True
                    )
                except Exception as e:
                    st.image(resized_for_canvas, caption="Paint over the image and click 'Apply Changes'", use_container_width=True)
            else:
                st.info("👈 Paint over the image using the white brush on the left, then click **💾 Apply Changes** to see the preview & download.")
                st.image(resized_for_canvas, caption="Original Image Preview", use_container_width=True)
