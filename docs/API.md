# API

## Health

```http
GET /health
```

## Image Generation

```http
POST /v1/images/generations
Content-Type: application/json

{
  "prompt": "A polished AI creator dashboard on a laptop",
  "size": "1024x1024",
  "image_urls": [],
  "return_base64": false,
  "download": true,
  "include_raw": false
}
```

## Video Task

```http
POST /v1/videos
Content-Type: application/json

{
  "prompt": "A smooth camera move across an AI design studio",
  "image": null,
  "extra_images": [],
  "mode": null,
  "width": 1152,
  "height": 768,
  "num_frames": 121,
  "frame_rate": 24,
  "wait": false,
  "poll_seconds": 10,
  "timeout_seconds": 1800,
  "download": false,
  "include_raw": false
}
```

Poll:

```http
GET /v1/videos/{task_id}
```

## OpenAI-Compatible

Use:

```text
Base URL: http://127.0.0.1:8007/v1
Chat: /chat/completions
Models: /models
Images: /images/generations
```
