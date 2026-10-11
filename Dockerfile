# Experimental FLUX.2 dev FP8mixed serverless worker
# Official RunPod ComfyUI worker with no baked-in FLUX.1 checkpoint
FROM runpod/worker-comfyui:5.10.0-base

# ComfyUI's FLUX.2 graph uses core nodes. No custom handler is required:
# the base image serves input.workflow through the standard RunPod API.
# Baking weights into the image eliminates per-request model downloads,
# but requires a large Docker build (allow 100+ GB of build disk).
RUN comfy model download \
    --url https://huggingface.co/Comfy-Org/flux2-dev/resolve/main/split_files/diffusion_models/flux2_dev_fp8mixed.safetensors \
    --relative-path models/diffusion_models \
    --filename flux2_dev_fp8mixed.safetensors

RUN comfy model download \
    --url https://huggingface.co/Comfy-Org/flux2-dev/resolve/main/split_files/text_encoders/mistral_3_small_flux2_fp8.safetensors \
    --relative-path models/text_encoders \
    --filename mistral_3_small_flux2_fp8.safetensors

RUN comfy model download \
    --url https://huggingface.co/Comfy-Org/flux2-dev/resolve/main/split_files/vae/flux2-vae.safetensors \
    --relative-path models/vae \
    --filename flux2-vae.safetensors

# Entrypoint is supplied by the official RunPod base worker image.
