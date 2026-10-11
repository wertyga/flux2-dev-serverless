#!/usr/bin/env python3
"""Call the RunPod FLUX.2 ComfyUI Serverless endpoint and save the result.

Examples:
  export RUNPOD_API_KEY=...
  python client.py --endpoint YOUR_ENDPOINT_ID --output scene.png
  python client.py --endpoint YOUR_ENDPOINT_ID --character character.png --style style.png --output scene.png

Uses Python standard library only. The two-reference mode matches workflows/flux2_two_refs_api.json.
"""
import argparse
import base64
import copy
import json
import mimetypes
import os
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent


def api_json(method, url, api_key, data=None):
    headers = {"Authorization": "Bearer " + api_key, "Content-Type": "application/json"}
    body = json.dumps(data).encode("utf-8") if data is not None else None
    request = Request(url, data=body, headers=headers, method=method)
    try:
        with urlopen(request, timeout=120) as response:
            return json.load(response)
    except HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"RunPod HTTP {error.code}: {detail[:3000]}") from error


def encode_image(filename, name):
    path = Path(filename)
    raw = path.read_bytes()
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    if not mime.startswith("image/"):
        raise ValueError(f"Not an image file: {path}")
    return {"name": name, "image": f"data:{mime};base64," + base64.b64encode(raw).decode("ascii")}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--endpoint", default=os.environ.get("RUNPOD_ENDPOINT_ID"), required=not bool(os.environ.get("RUNPOD_ENDPOINT_ID")))
    parser.add_argument("--prompt", help="Override the default prompt")
    parser.add_argument("--character", help="Character reference image (requires --style)")
    parser.add_argument("--style", help="Style reference image (requires --character)")
    parser.add_argument("--width", type=int, default=1344)
    parser.add_argument("--height", type=int, default=768)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--steps", type=int, default=24)
    parser.add_argument("--output", default="scene.png")
    parser.add_argument("--timeout", type=int, default=1800)
    args = parser.parse_args()

    api_key = os.environ.get("RUNPOD_API_KEY")
    if not api_key:
        parser.error("Set RUNPOD_API_KEY as an environment variable; do not commit it.")
    if bool(args.character) != bool(args.style):
        parser.error("Provide --character and --style together.")

    workflow_name = "flux2_two_refs_api.json" if args.character else "flux2_t2i_api.json"
    workflow = json.loads((ROOT / "workflows" / workflow_name).read_text(encoding="utf-8"))
    if args.prompt:
        workflow["4"]["inputs"]["text"] = args.prompt
    workflow["6"]["inputs"].update(width=args.width, height=args.height)
    workflow["8"]["inputs"].update(width=args.width, height=args.height, steps=args.steps)
    workflow["7"]["inputs"]["noise_seed"] = args.seed
    job_input = {"workflow": workflow}
    if args.character:
        job_input["images"] = [
            encode_image(args.character, "character.png"),
            encode_image(args.style, "style.png"),
        ]

    base = f"https://api.runpod.ai/v2/{args.endpoint}"
    answer = api_json("POST", base + "/run", api_key, {"input": job_input})
    job_id = answer.get("id")
    if not job_id:
        raise RuntimeError(f"RunPod did not return job id: {answer}")
    print("Submitted:", job_id)
    deadline = time.monotonic() + args.timeout
    previous_status = None
    while time.monotonic() < deadline:
        result = api_json("GET", base + "/status/" + job_id, api_key)
        status = result.get("status")
        if status != previous_status:
            print("Status:", status)
            previous_status = status
        if status == "COMPLETED":
            images = (result.get("output") or {}).get("images") or []
            if not images:
                raise RuntimeError(f"No images returned: {result}")
            first = images[0]
            if first.get("type") == "s3_url":
                print("Image URL:", first.get("data"))
                return
            b64 = first.get("data", "")
            if b64.startswith("data:"):
                b64 = b64.split(",", 1)[1]
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(base64.b64decode(b64))
            print("Saved:", output_path.resolve())
            return
        if status in ("FAILED", "CANCELLED", "TIMED_OUT"):
            raise RuntimeError(f"Job {status}: {json.dumps(result, ensure_ascii=False)[:4000]}")
        time.sleep(5)
    raise TimeoutError(f"Job {job_id} still running after {args.timeout}s; check RunPod Requests.")


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, TimeoutError, URLError) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
