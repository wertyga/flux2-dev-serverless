# FLUX.2 dev FP8 · RunPod Serverless (experimental)

Custom RunPod Serverless **ComfyUI** worker for `FLUX.2 dev FP8mixed`. Designed for creating detailed dark-fantasy graphic-novel frames via API, then animating those frames with a separate Wan2.2 endpoint.

> **Status: files committed; Docker build and GPU inference NOT YET TESTED.** Do not assume deployment succeeded until the build completes and a job returns an image.

## Repository contents

- `Dockerfile` — derives from the official `runpod/worker-comfyui:5.10.0-base`, downloads the three required FLUX.2 model files **at Docker build time**, and uses RunPod's existing handler.
- `workflows/flux2_t2i_api.json` — text-to-image graph using native FLUX.2 ComfyUI nodes.
- `workflows/flux2_two_refs_api.json` — image generation with **two reference images**, named `character.png` and `style.png`, using `ReferenceLatent`.
- `examples/first_request.json` — entire RunPod request for the text-to-image graph. Copy it into **Requests**.

The `examples/first_request.json` file contains an illustrative prompt and can be edited. Images are returned by the normal RunPod ComfyUI worker (Base64 output by default).

## Model files (in the Docker image, NOT in Git)

| ComfyUI folder | Model |
|---|---|
| `models/diffusion_models/` | `flux2_dev_fp8mixed.safetensors` |
| `models/text_encoders/` | `mistral_3_small_flux2_fp8.safetensors` |
| `models/vae/` | `flux2-vae.safetensors` |

Sources: [Comfy-Org FLUX.2](https://huggingface.co/Comfy-Org/flux2-dev) and [official FP8 ComfyUI workflow](https://github.com/Comfy-Org/workflow_templates/blob/main/templates/image_flux2_fp8.json).

These weights collectively exceed **50 GB**, in addition to the base image. Building, pushing, pulling, and unpacking the image requires substantial storage and network bandwidth. A GitHub-source build may fail if the build system lacks disk space; check RunPod build logs.

## Deploy

1. Open RunPod → **Serverless → New Endpoint → Import Git Repository**.
2. Select this repository, branch `main`, Dockerfile path `Dockerfile`.
3. Select **Queue**, **A100/H100 80 GB**, **GPU count 1**, **Active Workers 0**, **Max Workers 1**.
4. For testing, avoid additional GPU fallback choices that could unexpectedly increase costs. Choose a sufficiently large container-disk setting, e.g. **100+ GB**, if offered.
5. Build and check **Builds**. Do not repeatedly send generation requests while the worker is still downloading the image.
6. Open **Requests**, paste `examples/first_request.json`, press Run, and check the worker logs/output.

`Active Workers = 0` allows GPU scale-to-zero. It does **not** mean builds/storage/persistent volumes are automatically free.

## Change your prompt or image size

In the RunPod request, edit:
- `input.workflow["4"].inputs.text` — image prompt
- `input.workflow["7"].inputs.noise_seed` — seed
- `input.workflow["6"].inputs.width/height` — latent size
- `input.workflow["8"].inputs.width/height` — scheduler size (must match latent size)
- `input.workflow["8"].inputs.steps` — sampling steps (example 24)

## References through API

Use `workflows/flux2_two_refs_api.json` as your `input.workflow`, and pass files as `input.images`:

```json
{
  "input": {
    "images": [
      {"name": "character.png", "image": "data:image/png;base64,REPLACE_WITH_REAL_BASE64"},
      {"name": "style.png", "image": "data:image/png;base64,REPLACE_WITH_REAL_BASE64"}
    ],
    "workflow": { "...": "paste the entire flux2_two_refs_api.json graph here" }
  }
}
```

Both images must be valid base64 (the sample above is **NOT runnable**). Resize very large reference images before encoding to reduce payload and VAE memory demand. The official RunPod worker supports images as `input.images`, but the **multi-reference graph remains untested** until a full GPU run verifies it. Never attach references only to the text-to-image graph: in that graph they would be ignored.

## Licensing and safety

**FLUX.2 dev has a non-commercial self-hosting license by default.** A monetized YouTube pipeline needs appropriate commercial licensing/permissions. This repo includes **no weights, tokens, API keys, or user images**. Never commit secrets to public git: use RunPod secret environment variables if needed.

## Sources

- [RunPod worker ComfyUI customization](https://github.com/runpod-workers/worker-comfyui/blob/main/docs/customization.md)
- [RunPod worker ComfyUI request format](https://github.com/runpod-workers/worker-comfyui/blob/main/README.md)
- [Official FLUX.2 image workflow](https://github.com/Comfy-Org/workflow_templates/blob/main/templates/image_flux2_fp8.json)
