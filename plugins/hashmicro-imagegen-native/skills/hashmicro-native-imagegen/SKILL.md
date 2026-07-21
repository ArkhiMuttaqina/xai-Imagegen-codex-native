---
name: hashmicro-native-imagegen
description: "Generate or edit raster images through the active HashMicro XAI gateway and return them as native MCP image results. Use by default for image generation and editing when XAI_URL points to HashMicro; supports aspect-ratio intent, background edits, and recoverable local output paths."
---

# HashMicro Native Image Generation

Use the plugin-provided MCP tools `hashmicro_generate_image` and `hashmicro_edit_image` for image work whenever `XAI_URL` is configured to a HashMicro gateway.

## Routing

- New image: call `hashmicro_generate_image`.
- Existing/reference image: call `hashmicro_edit_image` and pass every local image path in the intended order. It starts a background job and promptly returns a job id.
- Poll that job with `hashmicro_get_image_result` until it returns the native image result. A running status is expected; do not submit the edit again while the job is running.
- Pass the active request model explicitly when known. UI `5.6-sol` maps to `codex/gpt-5.6-sol`; do not substitute an older image default.
- If model is unavailable, omit it. The server checks `CODEX_REQUEST_MODEL`, `CODEX_SESSION_MODEL`, `CODEX_MODEL`, and then `XAI_IMAGE_MODEL`; it fails clearly instead of silently selecting a legacy model when none is configured.
- UI reasoning effort `light` maps to `low`. If effort is unavailable, omit only `reasoning_effort` so the server can use `XAI_REASONING_EFFORT` from `.env`.
- Pass aspect-ratio requests such as `9:16`, `16:9`, `3:4`, or `1:1` directly in `size`. The server maps them to a gateway-safe size and adds crop-safe framing instructions while preserving the requested composition.
- For edits without a requested ratio, use `1024x1024`, `1536x1024`, or `1024x1536`; edits default to square.
- Use `quality: "medium"` for ordinary edits; reserve `high` for explicit user requests because it can make edit jobs much slower.
- Do not call the old CLI/EXE, `view_image`, or `generatedImage` for ordinary completion. The MCP result already contains the image plus its saved local path.
- Do not issue a second generation merely to improve a non-critical detail. Return the first valid result unless the user requested variants or the result materially violates the prompt.
- A completed background edit remains retrievable for a limited TTL. Poll the same job id again if result delivery is interrupted; restarting the MCP server expires in-memory job state.
- If a request times out, report it and ask before retrying. The upstream request may still complete or be billed, so never automatically resubmit it.

## Output

- Save outputs under the current workspace `outputs/` folder unless the user supplies another path.
- `hashmicro_generate_image` and a completed `hashmicro_get_image_result` call return an image content block for inline rendering and a text block containing the recoverable local path.
- Report the effective model, saved path, and any aspect-ratio-to-pixel-size mapping returned by the tool.
