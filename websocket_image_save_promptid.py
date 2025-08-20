"""
WebSocket Image Save with Prompt ID - No Conflicts Version
Custom nodes that don't conflict with existing ComfyUI nodes
Place in: ComfyUI/custom_nodes/
"""

from PIL import Image
import numpy as np
import json
import time
import struct

# Safe import of ComfyUI modules
try:
    import comfy.utils
    COMFY_AVAILABLE = True
except ImportError:
    COMFY_AVAILABLE = False
    print("[WebSocketPromptID] Warning: comfy.utils not available")


class WSImageSavePromptID:
    """
    WebSocket Image Save with Prompt ID metadata
    New node that doesn't conflict with existing nodes
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE", ),
            },
            "optional": {
                "prefix": ("STRING", {"default": "ComfyUI", "multiline": False}),
            }
        }
    
    RETURN_TYPES = ()
    RETURN_NAMES = ()
    FUNCTION = "execute"
    OUTPUT_NODE = True
    CATEGORY = "image/websocket"
    
    def execute(self, images, prefix="ComfyUI"):
        if not COMFY_AVAILABLE:
            print("[WSImageSavePromptID] Error: ComfyUI not available")
            return {}
        
        # Generate unique prompt_id with timestamp
        prompt_id = f"{prefix}_{int(time.time() * 1000)}"
        
        try:
            pbar = comfy.utils.ProgressBar(images.shape[0])
            
            for idx, image in enumerate(images):
                # Convert tensor to numpy array
                img_numpy = image.cpu().numpy()
                img_array = (255. * img_numpy).astype(np.uint8)
                
                # Clip values to valid range
                img_array = np.clip(img_array, 0, 255)
                
                # Create PIL Image
                img = Image.fromarray(img_array)
                
                # Prepare metadata
                metadata = {
                    "prompt_id": prompt_id,
                    "image_index": idx,
                    "total_images": images.shape[0],
                    "prefix": prefix,
                    "timestamp": time.time(),
                    "node_type": "WSImageSavePromptID"
                }
                
                # Convert metadata to JSON string
                metadata_json = json.dumps(metadata)
                
                # Send through WebSocket with metadata
                pbar.update_absolute(idx, images.shape[0], ("PNG", img, metadata_json))
            
            print(f"[WSImageSavePromptID] Sent {images.shape[0]} images with prompt_id: {prompt_id}")
            
        except Exception as e:
            print(f"[WSImageSavePromptID] Error: {e}")
            return {}
        
        return {}
    
    @classmethod
    def IS_CHANGED(cls, **kwargs):
        # Force re-execution every time
        return float("nan")


class WSImageSaveMetadata:
    """
    WebSocket Image Save with Extended Metadata
    Advanced version with more options
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE", ),
            },
            "optional": {
                "prefix": ("STRING", {"default": "ComfyUI", "multiline": False}),
                "add_timestamp": ("BOOLEAN", {"default": True}),
                "add_counter": ("BOOLEAN", {"default": True}),
            }
        }
    
    RETURN_TYPES = ()
    RETURN_NAMES = ()
    FUNCTION = "execute"
    OUTPUT_NODE = True
    CATEGORY = "image/websocket"
    
    def execute(self, images, prefix="ComfyUI", add_timestamp=True, add_counter=True):
        if not COMFY_AVAILABLE:
            print("[WSImageSaveMetadata] Error: ComfyUI not available")
            return {}
        
        # Build prompt_id
        prompt_id_parts = [prefix]
        if add_timestamp:
            prompt_id_parts.append(str(int(time.time() * 1000)))
        if add_counter:
            prompt_id_parts.append(f"n{images.shape[0]}")
        
        prompt_id = "_".join(prompt_id_parts)
        
        try:
            pbar = comfy.utils.ProgressBar(images.shape[0])
            
            for idx, image in enumerate(images):
                # Process image
                img_numpy = image.cpu().numpy()
                img_array = np.clip(255. * img_numpy, 0, 255).astype(np.uint8)
                img = Image.fromarray(img_array)
                
                # Rich metadata
                metadata = {
                    "prompt_id": prompt_id,
                    "image_index": idx,
                    "total_images": images.shape[0],
                    "prefix": prefix,
                    "timestamp": time.time(),
                    "timestamp_str": time.strftime("%Y%m%d_%H%M%S"),
                    "node_type": "WSImageSaveMetadata",
                    "settings": {
                        "add_timestamp": add_timestamp,
                        "add_counter": add_counter
                    }
                }
                
                # Send with metadata
                pbar.update_absolute(idx, images.shape[0], ("PNG", img, json.dumps(metadata)))
            
            print(f"[WSImageSaveMetadata] Sent {images.shape[0]} images with prompt_id: {prompt_id}")
            
        except Exception as e:
            print(f"[WSImageSaveMetadata] Error: {e}")
            return {}
        
        return {}
    
    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("nan")


class WSImageSaveBasic:
    """
    Basic WebSocket Image Save
    Simple version without conflicts
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE", ),
            }
        }
    
    RETURN_TYPES = ()
    RETURN_NAMES = ()
    FUNCTION = "execute"
    OUTPUT_NODE = True
    CATEGORY = "image/websocket"
    
    def execute(self, images):
        if not COMFY_AVAILABLE:
            print("[WSImageSaveBasic] Error: ComfyUI not available")
            return {}
        
        try:
            pbar = comfy.utils.ProgressBar(images.shape[0])
            
            for idx, image in enumerate(images):
                img_numpy = image.cpu().numpy()
                img_array = np.clip(255. * img_numpy, 0, 255).astype(np.uint8)
                img = Image.fromarray(img_array)
                
                # Send without metadata (compatible with original)
                pbar.update_absolute(idx, images.shape[0], ("PNG", img, None))
            
            print(f"[WSImageSaveBasic] Sent {images.shape[0]} images")
            
        except Exception as e:
            print(f"[WSImageSaveBasic] Error: {e}")
            return {}
        
        return {}
    
    @classmethod
    def IS_CHANGED(cls, images):
        return float("nan")


# Test node to verify installation
class WSTestNode:
    """Test node to verify custom nodes are loading"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {"default": "test", "multiline": False}),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("output",)
    FUNCTION = "execute"
    CATEGORY = "utils/test"
    
    def execute(self, text):
        output = f"[WSTestNode] Received: {text}"
        print(output)
        return (output,)


# IMPORTANT: Use unique names to avoid conflicts
NODE_CLASS_MAPPINGS = {
    "WSImageSavePromptID": WSImageSavePromptID,
    "WSImageSaveMetadata": WSImageSaveMetadata,
    "WSImageSaveBasic": WSImageSaveBasic,
    "WSTestNode": WSTestNode,
}

# Display names in the UI
NODE_DISPLAY_NAME_MAPPINGS = {
    "WSImageSavePromptID": "WS Image Save (Prompt ID)",
    "WSImageSaveMetadata": "WS Image Save (Metadata)",
    "WSImageSaveBasic": "WS Image Save (Basic)",
    "WSTestNode": "WS Test Node",
}

# Optional: Category icons (if supported by your ComfyUI version)
WEB_DIRECTORY = "./web"

print("[WebSocketPromptID] Custom nodes loaded successfully!")
print(f"[WebSocketPromptID] Registered nodes: {list(NODE_CLASS_MAPPINGS.keys())}")
