"""
SaveImageWebsocket with Prompt ID support for ComfyUI
Place this file in ComfyUI/custom_nodes/
"""

from PIL import Image
import numpy as np
import json
import time
try:
    import comfy.utils
except ImportError:
    pass


class SaveImageWebsocketWithPromptID:
    """
    Save images through WebSocket with prompt_id metadata
    Enhanced version of the original SaveImageWebsocket node
    """
    
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "images": ("IMAGE", ),
            },
            "optional": {
                "filename_prefix": ("STRING", {"default": "ComfyUI"}),
            },
            "hidden": {
                "prompt": "PROMPT", 
                "extra_pnginfo": "EXTRA_PNGINFO",
                "unique_id": "UNIQUE_ID"
            }
        }

    RETURN_TYPES = ()
    FUNCTION = "save_images"
    OUTPUT_NODE = True
    CATEGORY = "api/image"

    def save_images(self, images, filename_prefix="ComfyUI", 
                   prompt=None, extra_pnginfo=None, unique_id=None):
        
        # Initialize prompt_id
        prompt_id = None
        
        # Method 1: Try to get from extra_pnginfo
        if extra_pnginfo and isinstance(extra_pnginfo, dict):
            # Direct prompt_id
            prompt_id = extra_pnginfo.get("prompt_id")
            
            # From workflow info
            if not prompt_id:
                workflow = extra_pnginfo.get("workflow", {})
                if isinstance(workflow, dict):
                    prompt_id = workflow.get("prompt_id")
        
        # Method 2: Try to get from prompt
        if not prompt_id and prompt:
            if isinstance(prompt, dict):
                prompt_id = prompt.get("prompt_id")
            elif hasattr(prompt, '__dict__'):
                prompt_id = getattr(prompt, 'prompt_id', None)
        
        # Method 3: Try to get from global context
        if not prompt_id:
            try:
                import comfy.model_management as mm
                if hasattr(mm, 'current_prompt_id'):
                    prompt_id = mm.current_prompt_id
            except:
                pass
        
        # Method 4: Try from PromptServer
        if not prompt_id:
            try:
                from server import PromptServer
                if hasattr(PromptServer, 'instance') and PromptServer.instance:
                    server = PromptServer.instance
                    if hasattr(server, 'last_prompt_id'):
                        prompt_id = server.last_prompt_id
            except:
                pass
        
        # Fallback to timestamp if no prompt_id found
        if not prompt_id:
            prompt_id = f"noid_{int(time.time())}"
        
        # Process images
        pbar = comfy.utils.ProgressBar(images.shape[0])
        
        for idx, image in enumerate(images):
            i = 255. * image.cpu().numpy()
            img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
            
            # Create metadata
            metadata = {
                "prompt_id": prompt_id,
                "node_id": unique_id or "unknown",
                "image_index": idx,
                "total_images": images.shape[0],
                "filename_prefix": filename_prefix,
                "timestamp": time.time()
            }
            
            # Send through WebSocket with metadata
            pbar.update_absolute(idx, images.shape[0], ("PNG", img, metadata))
        
        # Return empty dict as per original implementation
        return {}

    @classmethod
    def IS_CHANGED(s, **kwargs):
        # Always execute to ensure WebSocket send
        return time.time()


class SaveImageWebsocketSimple:
    """
    Simplified version - compatible with original SaveImageWebsocket
    but adds prompt_id to the metadata
    """
    
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "images": ("IMAGE", ),
            },
            "hidden": {
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO"
            }
        }

    RETURN_TYPES = ()
    FUNCTION = "save_images"
    OUTPUT_NODE = True
    CATEGORY = "api/image"

    def save_images(self, images, prompt=None, extra_pnginfo=None):
        # Try to get prompt_id
        prompt_id = None
        
        # From extra_pnginfo
        if extra_pnginfo and isinstance(extra_pnginfo, dict):
            prompt_id = extra_pnginfo.get("prompt_id")
        
        # From prompt
        if not prompt_id and prompt and isinstance(prompt, dict):
            prompt_id = prompt.get("prompt_id")
        
        # Fallback
        if not prompt_id:
            prompt_id = f"unknown_{int(time.time())}"
        
        pbar = comfy.utils.ProgressBar(images.shape[0])
        step = 0
        
        for image in images:
            i = 255. * image.cpu().numpy()
            img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
            
            # Add prompt_id as simple JSON string in third parameter
            metadata = json.dumps({"prompt_id": prompt_id, "index": step})
            
            # Send with metadata
            pbar.update_absolute(step, images.shape[0], ("PNG", img, metadata))
            step += 1
        
        return {}

    @classmethod
    def IS_CHANGED(s, **kwargs):
        return time.time()


# Original SaveImageWebsocket for compatibility
class SaveImageWebsocket:
    """
    Original SaveImageWebsocket implementation
    Kept for backward compatibility
    """
    
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "images": ("IMAGE", ),
            }
        }

    RETURN_TYPES = ()
    FUNCTION = "save_images"
    OUTPUT_NODE = True
    CATEGORY = "api/image"

    def save_images(self, images):
        pbar = comfy.utils.ProgressBar(images.shape[0])
        step = 0
        
        for image in images:
            i = 255. * image.cpu().numpy()
            img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
            pbar.update_absolute(step, images.shape[0], ("PNG", img, None))
            step += 1
        
        return {}

    @classmethod
    def IS_CHANGED(s, images):
        return time.time()


# Node class mappings
NODE_CLASS_MAPPINGS = {
    "SaveImageWebsocket": SaveImageWebsocket,
    "SaveImageWebsocketWithPromptID": SaveImageWebsocketWithPromptID,
    "SaveImageWebsocketSimple": SaveImageWebsocketSimple,
}

# Display name mappings
NODE_DISPLAY_NAME_MAPPINGS = {
    "SaveImageWebsocket": "Save Image (WebSocket)",
    "SaveImageWebsocketWithPromptID": "Save Image (WebSocket + Prompt ID)",
    "SaveImageWebsocketSimple": "Save Image (WebSocket Simple + ID)",
}