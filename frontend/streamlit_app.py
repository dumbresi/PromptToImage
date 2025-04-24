import streamlit as st
import requests
from PIL import Image
from io import BytesIO
import time

# Set page config
st.set_page_config(
    page_title="AI Image Generator", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS to improve the UI
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        margin-bottom: 1rem;
    }
    .subheader {
        font-size: 1.5rem;
        margin-bottom: 1rem;
    }
    .stImage {
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }
    .download-btn {
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# API endpoint (replace with your actual API URL)
API_URL = "https://fc54-34-19-84-17.ngrok-free.app"  # Update this with your actual API endpoint
BASE_API_URL = "https://b0ef-34-57-96-211.ngrok-free.app"
# Initialize session state for chat history and other persistent data
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'settings_expanded' not in st.session_state:
    st.session_state.settings_expanded = False
if 'last_settings' not in st.session_state:
    st.session_state.last_settings = {}
if 'generation_count' not in st.session_state:
    st.session_state.generation_count = 0
if 'selected_model' not in st.session_state:
    st.session_state.selected_model = "stable-diffusion-v1-5"  # Default model

# Main UI
st.markdown("<h1 class='main-header'>AI Image Generator Chat</h1>", unsafe_allow_html=True)

# Sidebar for advanced settings
with st.sidebar:
    st.markdown("<h2 class='subheader'>Image Generation Settings</h2>", unsafe_allow_html=True)
    
    # Model selection dropdown
    model = st.selectbox(
        "AI Model",
        ["Base", "Fine-tuned"],
        index=0 if st.session_state.selected_model == "Base" else 1,
        help="Choose which AI model to use for generation"
    )
    # Update the session state with the selected model
    st.session_state.selected_model = model
    
    # Model info expander
    with st.expander("About These Models", expanded=False):
        if model == "stable-diffusion-v1-5":
            st.markdown("""
            **Stable Diffusion v1.5**
            - Balanced quality and speed
            - Good general-purpose image generation
            - Works well with detailed prompts
            - Better for artistic styles
            """)
        else:  # sdxl-turbo
            st.markdown("""
            **SDXL Turbo**
            - Faster generation (fewer steps needed)
            - Better for photorealistic images
            - Improved composition and framing
            - May require different prompting style
            """)
    
    # Presets dropdown
    preset = st.selectbox(
        "Preset Styles",
        ["Custom", "Photorealistic", "Anime Style", "Oil Painting", "Pencil Sketch"],
        help="Choose a preset style or customize your own settings"
    )
    
    # Apply preset settings if selected
    if preset == "Photorealistic":
        num_steps_default = 70
        guidance_scale_default = 8.5
        negative_prompt_default = "blurry, low quality, distorted, deformed"
    elif preset == "Anime Style":
        num_steps_default = 40
        guidance_scale_default = 9.0
        negative_prompt_default = "realistic, photograph, 3d render"
    elif preset == "Oil Painting":
        num_steps_default = 60
        guidance_scale_default = 7.0
        negative_prompt_default = "digital art, photograph, sketch"
    elif preset == "Pencil Sketch":
        num_steps_default = 30
        guidance_scale_default = 6.0
        negative_prompt_default = "color, painting, realistic, photograph"
    else:  # Custom
        num_steps_default = 50
        guidance_scale_default = 7.5
        negative_prompt_default = ""
    
    # Sliders and settings
    with st.expander("Advanced Settings", expanded=st.session_state.settings_expanded):
        st.session_state.settings_expanded = True
        num_steps = st.slider("Number of inference steps", 10, 150, num_steps_default, 
                             help="Higher values = more detail but slower generation")
        guidance_scale = st.slider("Guidance scale", 1.0, 20.0, guidance_scale_default, 0.5,
                                  help="How closely to follow the prompt (higher = more faithful)")
        
        col1, col2 = st.columns(2)
        with col1:
            width = st.select_slider("Width", 
                                    options=[512, 576, 640, 704, 768, 832, 896, 960, 1024], 
                                    value=512)
        with col2:
            height = st.select_slider("Height", 
                                     options=[512, 576, 640, 704, 768, 832, 896, 960, 1024], 
                                     value=512)
        
        negative_prompt = st.text_area("Negative prompt", negative_prompt_default, 
                                      help="What to avoid in the generated image")

    # Stats display
    st.markdown("---")
    st.markdown(f"**Images generated:** {st.session_state.generation_count}")

# Function to check API status
def check_api_status():
    try:
        start_time = time.time()
        health_check = requests.get(f"{API_URL}/", timeout=3)
        latency = (time.time() - start_time) * 1000  # Convert to ms
        
        if health_check.status_code == 200:
            return True, f"✅ API Connected (Latency: {latency:.0f}ms)"
        else:
            return False, f"❌ API Not Responding Correctly ({health_check.status_code})"
    except requests.exceptions.RequestException:
        return False, "❌ API Not Connected"

# Function to call the API
def generate_image_from_api(prompt, negative_prompt, steps, guidance, width, height, model):
    try:
        # Save last used settings
        st.session_state.last_settings = {
            "negative_prompt": negative_prompt,
            "steps": steps,
            "guidance": guidance,
            "width": width,
            "height": height,
            "model": model
        }
        
        # Prepare the request payload
        payload = {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "num_inference_steps": steps,
            "guidance_scale": guidance,
            "width": width,
            "height": height,
            "model": model  # Add the model parameter to the API request
        }
        
        # Make the API call
        if model == "Base":
            response = requests.post(f"{BASE_API_URL}/generate-image/", json=payload, timeout=60)
        else:
            response = requests.post(f"{API_URL}/generate-image/", json=payload, timeout=60)
        
        # Check if successful
        if response.status_code == 200:
            # Convert the response content to a PIL Image
            image = Image.open(BytesIO(response.content))
            # Increment generation counter
            st.session_state.generation_count += 1
            return image, None
        else:
            return None, f"API Error: {response.status_code} - {response.text}"
    
    except requests.exceptions.Timeout:
        return None, "Error: API request timed out. The server may be busy or the image generation is taking too long."
    except requests.exceptions.ConnectionError:
        return None, "Error: Could not connect to the API server. Please check if the server is running."
    except Exception as e:
        return None, f"Error: {str(e)}"

# Function to display generation settings
def display_generation_info(prompt, settings):
    with st.expander("Generation Details", expanded=False):
        st.markdown(f"**Model:** {settings.get('model', 'Not specified')}")
        st.markdown(f"**Prompt:** {prompt}")
        st.markdown(f"**Negative Prompt:** {settings['negative_prompt']}")
        st.markdown(f"**Steps:** {settings['steps']}")
        st.markdown(f"**Guidance Scale:** {settings['guidance']}")
        st.markdown(f"**Size:** {settings['width']}×{settings['height']}")

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "user":
            st.write(message["content"])
        else:  # assistant
            if "image" in message:
                st.image(message["image"], caption=message.get("caption", ""), use_container_width=True)
                
                # Add download button inline with each image
                if "image_bytes" in message:
                    st.download_button(
                        label="Download Image",
                        data=message["image_bytes"],
                        file_name=f"generated_image_{message.get('timestamp', 'img')}.png",
                        mime="image/png",
                        key=f"download_{message.get('timestamp', id(message))}",
                    )
                
                # Display generation info
                if "settings" in message:
                    display_generation_info(message["caption"], message["settings"])
                    
            if "content" in message:
                st.write(message["content"])

# Chat input with placeholder text
placeholder_text = "Describe the image you want to generate..."
if prompt := st.chat_input(placeholder_text):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.write(prompt)
    
    # Display assistant response
    with st.chat_message("assistant"):
        status_placeholder = st.empty()
        progress_bar = st.progress(0)
        
        # Update status message
        status_placeholder.text("Checking API connection...")
        api_status, status_message = check_api_status()
        
        if not api_status:
            status_placeholder.error(status_message)
            st.session_state.messages.append({
                "role": "assistant", 
                "content": status_message
            })
        else:
            # Update status message
            status_placeholder.text("Generating your image...")
            
            # Simulate progress while waiting for the API
            for percent_complete in range(0, 90, 10):
                time.sleep(0.1)  # Adjust based on typical generation time
                progress_bar.progress(percent_complete)
            
            # Call the APIxqxxq
            image, error = generate_image_from_api(
                prompt=prompt,
                negative_prompt=negative_prompt,
                steps=num_steps,
                guidance=guidance_scale,
                width=width,
                height=height,
                model=st.session_state.selected_model
            )
            
            # Complete the progress bar
            progress_bar.progress(100)
            
            if image:
                # Generate a timestamp for unique identifiers
                timestamp = int(time.time())
                
                # Convert image to bytes for download
                buf = BytesIO()
                image.save(buf, format="PNG")
                byte_im = buf.getvalue()
                
                # Remove progress indicators
                status_placeholder.empty()
                progress_bar.empty()
                
                # Display image and response
                st.image(image, caption=prompt, use_container_width=True)
                st.write(f"Here's your image based on: \"{prompt}\"")
                
                # Add download button
                st.download_button(
                    label="Download Image",
                    data=byte_im,
                    file_name=f"generated_image_{timestamp}.png",
                    mime="image/png",
                    key=f"main_download_{timestamp}",
                )
                
                # Display generation details
                settings_used = {
                    "model": st.session_state.selected_model,
                    "negative_prompt": negative_prompt,
                    "steps": num_steps,
                    "guidance": guidance_scale,
                    "width": width,
                    "height": height
                }
                display_generation_info(prompt, settings_used)
                
                # Add to chat history
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": f"Here's your image based on: \"{prompt}\"",
                    "image": image,
                    "image_bytes": byte_im,
                    "caption": prompt,
                    "timestamp": timestamp,
                    "settings": settings_used
                })
                
                # Option to regenerate with same settings
                if st.button("Regenerate with same prompt"):
                    st.experimental_rerun()
                
            else:
                # Remove progress indicators
                status_placeholder.empty()
                progress_bar.empty()
                
                # Display error
                st.error(error)
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": error
                })

# API Status indicator in the sidebar
st.sidebar.markdown("---")
api_status, status_message = check_api_status()
if api_status:
    st.sidebar.success(status_message)
else:
    st.sidebar.error(status_message)