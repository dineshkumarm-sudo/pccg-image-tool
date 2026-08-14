import streamlit as st
from PIL import Image, ImageOps
from streamlit_cropper import st_cropper
from streamlit_drawable_canvas import st_canvas
import io
import base64

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

st.markdown('<h1 class="main-title">✂️ Custom 960px Image Cropper, Eraser & Auto-Fit Tool</h1>', unsafe_allow_html=True)

# 2. Input Source Selection
st.subheader("1. Select Image Input Method")
tab1, tab2 = st.tabs(["📁 File Upload", "📋 Paste from Clipboard"])

img_input = None

with tab1:
    uploaded_file = st.file_uploader("Upload Image", type=["jpg", "jpeg", "png", "webp"])
    if uploaded_file:
        img_input = Image.open(uploaded_file)

with tab2:
    pasted_data = st.text_input(
        "Paste Image Base64 string / Data URL here:", 
        key="clipboard_text_input", 
        help="Copy an image to clipboard, then right-click and paste here."
    )
    
    if pasted_data and pasted_data.startswith("data:image"):
        try:
            base64_str = pasted_data.split(",")[1]
            image_bytes = base64.b64decode(base64_str)
            img_input = Image.open(io.BytesIO(image_bytes))
        except Exception as e:
            st.error("Could not parse image from clipboard string.")

if img_input is not None:
    st.markdown("---")
    
    # Tool Selection Mode
    mode = st.radio(
        "🛠️ Choose Processing Tool:", 
        [
            "⚡ 1-Click Auto-Fit (960px x 300-500px)", 
            "🎯 Manual Interactive Crop", 
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

        # Calculate optimal target height (300px - 500px) based on original image ratio
        orig_w, orig_h = img_input.size
        orig_aspect_ratio = orig_w / float(orig_h)

        # Theoretical ideal height at 960px width
        ideal_height = 960 / orig_aspect_ratio
        
        # Clamp height within [300, 500]
        optimal_height = int(max(300, min(500, round(ideal_height))))

        with col_controls:
            st.info(f"📏 **Original Size:** {orig_w} x {orig_h} px")
            st.success(f"🎯 **Auto-Calculated Output:** 960 x {optimal_height} px")

            # Option to manually tweak alignment (Default is 0.5 center)
            centering_y = st.slider("Vertical Alignment Shift (Top ↔ Bottom):", 0.0, 1.0, 0.5, 0.05)

            # Auto-Fit execution using PIL ImageOps
            auto_fit_img = ImageOps.fit(
                img_input,
                (960, optimal_height),
                method=Image.Resampling.LANCZOS,
                centering=(0.5, centering_y)
            )

        with col_preview:
            st.image(auto_fit_img, caption=f"Auto-Fit Result: 960 x {optimal_height} px", use_column_width=True)

            # Download Setup
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
    # MODE 2: MANUAL INTERACTIVE CROP
    # -------------------------------------------------------------
    elif "Manual Interactive Crop" in mode:
        col_crop, col_preview = st.columns([1.2, 1])
        
        with col_crop:
            st.subheader("🎯 Drag & Crop Area")
            target_height = st.slider("Target Output Height (px):", min_value=300, max_value=500, value=400, step=10)
            
            calc_aspect_ratio = (960, target_height)
            box_color = st.color_picker("Crop Box Color", "#38BDF8")

            cropped_img = st_cropper(
                img_input,
                realtime_update=True,
                box_color=box_color,
                aspect_ratio=calc_aspect_ratio,
                return_type='image'
            )

        with col_preview:
            st.subheader("🖼️ Final Output Preview")
            final_img = cropped_img.resize((960, target_height), Image.Resampling.LANCZOS)
            st.image(final_img, caption=f"Final Output: 960 x {target_height} px", use_column_width=True)

            buf = io.BytesIO()
            save_img = final_img.convert("RGB") if final_img.mode in ("RGBA", "P") else final_img
            save_img.save(buf, format="JPEG", quality=95)
            
            st.download_button(
                label="📥 Download Cropped Image (960px)",
                data=buf.getvalue(),
                file_name=f"vizard_cropped_960x{target_height}.jpg",
                mime="image/jpeg",
                type="primary",
                use_container_width=True
            )

    # -------------------------------------------------------------
    # MODE 3: WHITE ERASER BRUSH
    # -------------------------------------------------------------
    else:
        st.subheader("🧹 White Eraser Tool")
        st.caption("Paint over unwanted regions using the white brush. Adjust brush size using the slider.")

        e_col1, e_col2 = st.columns([1.2, 1])

        with e_col1:
            eraser_size = st.slider("White Eraser Brush Size (px):", min_value=5, max_value=100, value=25, step=5)

            canvas_width = 700
            w_percent = (canvas_width / float(img_input.size[0]))
            h_size = int((float(img_input.size[1]) * float(w_percent)))
            resized_for_canvas = img_input.resize((canvas_width, h_size), Image.Resampling.LANCZOS)

            canvas_result = st_canvas(
                fill_color="rgba(255, 255, 255, 1.0)",
                stroke_width=eraser_size,
                stroke_color="#FFFFFF",
                background_image=resized_for_canvas,
                update_streamlit=True,
                height=h_size,
                width=canvas_width,
                drawing_mode="freedraw",
                key="white_eraser_canvas",
            )

        with e_col2:
            st.subheader("🖼️ Output Image")
            if canvas_result.image_data is not None:
                canvas_img = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
                base_img = resized_for_canvas.convert("RGBA")
                erased_final = Image.alpha_composite(base_img, canvas_img)

                st.image(erased_final, caption="Erased Output Preview", use_column_width=True)

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