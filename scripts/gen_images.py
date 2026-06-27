#!/usr/bin/env python3
"""Generate site imagery with Google's image models (Gemini / Imagen via AI Studio).

Reads the API key from env GEMINI_API_KEY (or scripts/.gemini_key). Generates the images
defined in IMAGES[] and saves them to public/images/. Tries Imagen 3 first, then falls back
to Gemini 2.0 flash image generation.

Usage:
  GEMINI_API_KEY=xxxx python3 scripts/gen_images.py            # all images
  GEMINI_API_KEY=xxxx python3 scripts/gen_images.py hero       # one by id
"""
import os, sys, json, base64, urllib.request, urllib.error

KEY = os.environ.get("GEMINI_API_KEY") or ""
if not KEY:
    p = os.path.join(os.path.dirname(__file__), ".gemini_key")
    if os.path.exists(p):
        KEY = open(p).read().strip()
OUT_DIR = "public/images"

# Clean, bright, white modern pharmacy — clinical-but-friendly. High-key, minimal.
STYLE = ("Clean bright modern commercial photography, lots of white, soft natural daylight, "
         "high-key lighting, crisp minimal and airy, fresh green accents, professional "
         "healthcare and pharmacy aesthetic, sharp focus, no text, no logos, no watermark.")
IMAGES = [
    {"id": "hero", "ar": "16:9", "file": "hero.jpg",
     "prompt": "A bright, clean, modern pharmacy interior with neat white shelves of medicine, "
               "airy and minimal, soft daylight through large windows, fresh green plant accents, "
               "welcoming and professional. " + STYLE},
    {"id": "consult", "ar": "4:3", "file": "consult.jpg",
     "prompt": "A friendly telehealth video consultation — a relaxed traveller smiling at a laptop "
               "in a bright clean white room, reassuring and professional. " + STYLE},
    {"id": "care", "ar": "4:3", "file": "care.jpg",
     "prompt": "A clean flat-lay of neatly arranged medicine boxes and a crisp white paper pharmacy "
               "bag on a bright white surface, minimal and tidy, soft shadows. " + STYLE},
    {"id": "about", "ar": "3:2", "file": "about.jpg",
     "prompt": "A bright, clean, modern pharmacy storefront with large glass windows and a white "
               "facade, fresh and professional, soft daylight, a few green plants. " + STYLE},
    {"id": "pharmacist", "ar": "3:4", "file": "pharmacist.jpg",
     "prompt": "A friendly, professional Indonesian female pharmacist in her early 30s wearing a "
               "clean white coat, smiling warmly and approachably at the camera in a bright modern "
               "pharmacy with white shelves softly blurred behind her, trustworthy and competent. " + STYLE},
]

def imagen(prompt, ar):
    url = ("https://generativelanguage.googleapis.com/v1beta/models/"
           "imagen-4.0-generate-001:predict?key=" + KEY)
    body = json.dumps({"instances": [{"prompt": prompt}],
                       "parameters": {"sampleCount": 1, "aspectRatio": ar}}).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        d = json.loads(r.read())
    preds = d.get("predictions") or []
    if preds and preds[0].get("bytesBase64Encoded"):
        return base64.b64decode(preds[0]["bytesBase64Encoded"])
    raise RuntimeError("no image in Imagen response: " + json.dumps(d)[:200])

def gemini_image(prompt):
    for model in ("gemini-2.5-flash-image", "gemini-3-pro-image"):
        url = (f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key=" + KEY)
        body = json.dumps({"contents": [{"parts": [{"text": prompt}]}],
                           "generationConfig": {"responseModalities": ["IMAGE", "TEXT"]}}).encode()
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                d = json.loads(r.read())
            for part in d.get("candidates", [{}])[0].get("content", {}).get("parts", []):
                inline = part.get("inlineData") or part.get("inline_data")
                if inline and inline.get("data"):
                    return base64.b64decode(inline["data"])
        except urllib.error.HTTPError:
            continue
    raise RuntimeError("gemini image generation failed")

def main():
    if not KEY:
        print("ERROR: no GEMINI_API_KEY (env or scripts/.gemini_key).", flush=True); sys.exit(2)
    os.makedirs(OUT_DIR, exist_ok=True)
    only = sys.argv[1] if len(sys.argv) > 1 else None
    for img in IMAGES:
        if only and img["id"] != only:
            continue
        print(f"Generating {img['id']} ({img['ar']})…", flush=True)
        try:
            data = imagen(img["prompt"], img["ar"])
        except Exception as e:
            print(f"  Imagen failed ({str(e)[:80]}); trying Gemini…", flush=True)
            data = gemini_image(img["prompt"])
        path = os.path.join(OUT_DIR, img["file"])
        open(path, "wb").write(data)
        print(f"  saved {path} ({len(data)//1024} KB)", flush=True)

if __name__ == "__main__":
    main()
