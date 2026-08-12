import os
import logging
import torch
import folder_paths
import comfy.utils

logger = logging.getLogger(__name__)

class MiniMaxH3RefPatchLoader:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "model": ("MODEL",),
                "patch_name": (folder_paths.get_filename_list("model_patches"), ),
                "ref_strength": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 10.0, "step": 0.05}),
            }
        }
    
    RETURN_TYPES = ("MODEL",)
    FUNCTION = "apply_patch"
    CATEGORY = "MiniMax"
    
    def apply_patch(self, model, patch_name, ref_strength):
        model_out = model.clone()
        
        patch_path = folder_paths.get_full_path("model_patches", patch_name)
        if not patch_path:
            raise FileNotFoundError(f"File not found: {patch_name}")
            
        patch_sd = comfy.utils.load_torch_file(patch_path)
        model_sd_keys = set(model_out.model.state_dict().keys())
        
        patches = {}
        matched_count = 0
        
        for k, v in patch_sd.items():
            target_key = k
            if target_key not in model_sd_keys:
                if f"diffusion_model.{k}" in model_sd_keys:
                    target_key = f"diffusion_model.{k}"
                elif k.startswith("diffusion_model.") and k[len("diffusion_model."):] in model_sd_keys:
                    target_key = k[len("diffusion_model."):]
                    
            if target_key in model_sd_keys:
                patches[target_key] = (v,)
                matched_count += 1
            else:
                logger.warning(f"Target key not found in model: {k}")
                
        if matched_count == 0:
            logger.error("Matching failed! 0 keys were applied. Please check the model type.")
        else:
            loaded_keys = model_out.add_patches(
                patches, 
                strength_patch=ref_strength, 
                strength_model=1.0
            )
            logger.info(f"Successfully applied {len(loaded_keys)}/{len(patch_sd)} keys to the model! (Ref Strength: {ref_strength})")
            
        return (model_out,)

NODE_CLASS_MAPPINGS = {
    "MiniMaxH3RefPatchLoader": MiniMaxH3RefPatchLoader
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MiniMaxH3RefPatchLoader": "MiniMax H3 Ref-Patch Loader"
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']