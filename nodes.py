"""
WebSocket Save with Real Prompt ID for ComfyUI
Final version - Captures the actual prompt_id from the ComfyUI execution request
GitHub: https://github.com/shedyhs/my-custom-nodes2
"""

from PIL import Image
import numpy as np
import json
import time
import os
import inspect
import threading

try:
    import comfy.utils
    import folder_paths
    COMFY_AVAILABLE = True
except ImportError:
    COMFY_AVAILABLE = False
    print("[WebSocketSavePromptID] Warning: ComfyUI modules not available")


class WebSocketSavePromptID:
    """
    Save images via WebSocket with the real prompt_id from the ComfyUI request.
    The prompt_id is captured from the execution context and sent with each image.
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE", ),
            },
            "optional": {
                "filename_prefix": ("STRING", {"default": "ComfyUI", "multiline": False}),
            },
            "hidden": {
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO", 
                "unique_id": "UNIQUE_ID"
            }
        }
    
    RETURN_TYPES = ()
    RETURN_NAMES = ()
    FUNCTION = "save_via_websocket"
    OUTPUT_NODE = True
    CATEGORY = "image/output"
    
    def get_real_prompt_id(self):
        """
        Attempts to capture the real prompt_id from various sources in ComfyUI
        """
        prompt_id = None
        
        # Method 1: Try to get from execution module
        if not prompt_id:
            try:
                import execution
                # Check if there's a currently executing prompt
                if hasattr(execution, 'PromptExecutor'):
                    for attr in ['currently_executing', 'current_prompt', 'executing_prompt']:
                        if hasattr(execution.PromptExecutor, attr):
                            current = getattr(execution.PromptExecutor, attr)
                            if current:
                                if isinstance(current, (list, tuple)) and len(current) > 0:
                                    prompt_id = str(current[0])
                                elif isinstance(current, str):
                                    prompt_id = current
                                elif isinstance(current, dict) and 'prompt_id' in current:
                                    prompt_id = current['prompt_id']
                                if prompt_id:
                                    print(f"[WebSocketSavePromptID] Found prompt_id from execution.{attr}: {prompt_id}")
                                    break
            except Exception as e:
                pass
        
        # Method 2: Try to get from server module
        if not prompt_id:
            try:
                from server import PromptServer
                if hasattr(PromptServer, 'instance') and PromptServer.instance:
                    server = PromptServer.instance
                    # Check various possible attributes
                    for attr in ['last_prompt_id', 'current_prompt_id', 'executing_prompt_id']:
                        if hasattr(server, attr):
                            pid = getattr(server, attr)
                            if pid:
                                prompt_id = str(pid)
                                print(f"[WebSocketSavePromptID] Found prompt_id from server.{attr}: {prompt_id}")
                                break
            except Exception as e:
                pass
        
        # Method 3: Inspect the call stack for prompt_id
        if not prompt_id:
            try:
                frame = inspect.currentframe()
                for _ in range(20):  # Check up to 20 frames up the stack
                    if frame is None:
                        break
                    
                    frame_locals = frame.f_locals
                    frame_globals = frame.f_globals
                    
                    # Check locals
                    if 'prompt_id' in frame_locals:
                        pid = frame_locals['prompt_id']
                        if pid and isinstance(pid, str):
                            prompt_id = pid
                            print(f"[WebSocketSavePromptID] Found prompt_id in stack locals: {prompt_id}")
                            break
                    
                    # Check for objects containing prompt_id
                    for var_name, var_value in frame_locals.items():
                        if prompt_id:
                            break
                        
                        # Check if object has prompt_id attribute
                        if hasattr(var_value, 'prompt_id'):
                            pid = getattr(var_value, 'prompt_id')
                            if pid:
                                prompt_id = str(pid)
                                print(f"[WebSocketSavePromptID] Found prompt_id in {var_name}.prompt_id: {prompt_id}")
                                break
                        
                        # Check if it's a dict with prompt_id
                        if isinstance(var_value, dict):
                            if 'prompt_id' in var_value:
                                pid = var_value['prompt_id']
                                if pid:
                                    prompt_id = str(pid)
                                    print(f"[WebSocketSavePromptID] Found prompt_id in dict {var_name}: {prompt_id}")
                                    break
                            # Also check for 'id' key
                            elif 'id' in var_value and var_name in ['prompt', 'workflow', 'job']:
                                pid = var_value['id']
                                if pid and isinstance(pid, str) and len(pid) > 20:
                                    prompt_id = str(pid)
                                    print(f"[WebSocketSavePromptID] Found id in {var_name}: {prompt_id}")
                                    break
                    
                    frame = frame.f_back
                    
            except Exception as e:
                pass
        
        # Method 4: Check thread local storage
        if not prompt_id:
            try:
                current_thread = threading.current_thread()
                if hasattr(current_thread, 'prompt_id'):
                    prompt_id = str(current_thread.prompt_id)
                    print(f"[WebSocketSavePromptID] Found prompt_id in thread: {prompt_id}")
            except Exception as e:
                pass
        
        # Method 5: Try to get from global context
        if not prompt_id:
            try:
                import __main__
                if hasattr(__main__, 'prompt_id'):
                    prompt_id = str(__main__.prompt_id)
                    print(f"[WebSocketSavePromptID] Found prompt_id in __main__: {prompt_id}")
            except Exception as e:
                pass
        
        return prompt_id
    
    def save_via_websocket(self, images, filename_prefix="ComfyUI", 
                          prompt=None, extra_pnginfo=None, unique_id=None):
        """
        Save images via WebSocket with metadata including the real prompt_id
        """
        
        if not COMFY_AVAILABLE:
            print("[WebSocketSavePromptID] Error: ComfyUI not available")
            return {}
        
        # Get the real prompt_id from the execution context
        prompt_id = self.get_real_prompt_id()
        
        # If no prompt_id found, generate a fallback
        if not prompt_id:
            # Use timestamp-based fallback
            prompt_id = f"noid_{int(time.time() * 1000)}"
            print(f"[WebSocketSavePromptID] Warning: Could not find real prompt_id, using fallback: {prompt_id}")
        else:
            print(f"[WebSocketSavePromptID] Successfully captured real prompt_id: {prompt_id}")
        
        # Process and send images
        try:
            pbar = comfy.utils.ProgressBar(images.shape[0])
            
            print(f"[WebSocketSavePromptID] Processing {images.shape[0]} image(s)")
            
            for idx, image in enumerate(images):
                # Convert tensor to numpy array and then to PIL Image
                img_numpy = image.cpu().numpy()
                img_array = np.clip(img_numpy * 255.0, 0, 255).astype(np.uint8)
                pil_image = Image.fromarray(img_array)
                
                # Prepare metadata with the real prompt_id
                metadata = {
                    "prompt_id": prompt_id,  # The real prompt_id from the request
                    "node_id": str(unique_id) if unique_id else "unknown",
                    "image_index": idx,
                    "total_images": images.shape[0],
                    "filename_prefix": filename_prefix,
                    "timestamp": time.time(),
                    "timestamp_str": time.strftime("%Y%m%d_%H%M%S")
                }
                
                # Convert metadata to JSON string
                metadata_json = json.dumps(metadata, ensure_ascii=False)
                
                # Send via WebSocket: (format, image, metadata)
                pbar.update_absolute(idx, images.shape[0], ("PNG", pil_image, metadata_json))
                
                print(f"[WebSocketSavePromptID] Sent image {idx+1}/{images.shape[0]} with prompt_id: {prompt_id}")
            
            print(f"[WebSocketSavePromptID] ✅ Successfully sent all images with prompt_id: {prompt_id}")
            
        except Exception as e:
            print(f"[WebSocketSavePromptID] ❌ Error sending images: {e}")
            import traceback
            traceback.print_exc()
            return {}
        
        return {}
    
    @classmethod
    def IS_CHANGED(cls, **kwargs):
        """
        Force the node to always execute (never cache)
        """
        return float("nan")


# Node registration
NODE_CLASS_MAPPINGS = {
    "WebSocketSavePromptID": WebSocketSavePromptID,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "WebSocketSavePromptID": "Save Image WebSocket (with Prompt ID)",
}

# Confirmation message
print("=" * 60)
print("[WebSocketSavePromptID] Custom node loaded successfully!")
print("[WebSocketSavePromptID] This node captures the real prompt_id")
print("[WebSocketSavePromptID] from ComfyUI execution requests")
print("=" * 60)
