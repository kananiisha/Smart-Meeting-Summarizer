import os
import json
from flask import current_app


# ── Transcription ──────────────────────────────────────────────────────────────

def transcribe_audio(audio_path: str) -> str:
    try:
        from faster_whisper import WhisperModel
        model = WhisperModel("tiny", device="cpu", compute_type="int8")
        segments, _ = model.transcribe(audio_path, beam_size=5)
        return " ".join(segment.text.strip() for segment in segments)
    except Exception as e:
        raise RuntimeError(f"Transcription failed: {str(e)}")


# ── Summarization ──────────────────────────────────────────────────────────────

PROMPT_TEMPLATE = """You are an expert meeting analyst. Given a meeting transcript, extract structured insights.

Respond with ONLY a valid JSON object — no markdown, no explanation, no code fences.

The JSON must have exactly these keys:
{{
  "summary": "A concise 3-5 sentence paragraph summarizing the overall meeting.",
  "action_items": [
    {{"task": "Description of the task", "owner": "Person responsible or 'Unassigned'", "deadline": "Deadline if mentioned or 'Not specified'"}}
  ],
  "key_decisions": [
    "Decision 1 made during the meeting"
  ]
}}

Rules:
- summary: paragraph form, factual, no bullet points
- action_items: extract every clear task or follow-up; if no owner is named write "Unassigned"
- key_decisions: only definitive decisions, not discussions or suggestions
- If action_items or key_decisions are empty, return empty lists []
- Return ONLY the JSON object, nothing else

Here is the meeting transcript:

{transcript}"""


def summarize_transcript(transcript: str) -> dict:
    from groq import Groq
    api_key = current_app.config.get('GROQ_API_KEY')
    if not api_key:
        raise ValueError("GROQ_API_KEY is not set.")

    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": PROMPT_TEMPLATE.format(transcript=transcript)}]
    )

    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    result = json.loads(raw)
    result.setdefault("summary", "No summary available.")
    result.setdefault("action_items", [])
    result.setdefault("key_decisions", [])
    return result


# ── Unified pipeline ───────────────────────────────────────────────────────────

def process_meeting(input_type: str, audio_path: str = None, transcript_text: str = None) -> dict:
    print(f"[DEBUG] process_meeting() called with input_type='{input_type}'")

    if input_type == 'audio':
        if not audio_path or not os.path.exists(audio_path):
            raise FileNotFoundError("Audio file not found.")
        print("[DEBUG] Starting audio transcription...")
        transcript = transcribe_audio(audio_path)
        print(f"[DEBUG] Transcription done. Length: {len(transcript)} characters")

    elif input_type == 'transcript':
        if not transcript_text or not transcript_text.strip():
            raise ValueError("Transcript text is empty.")
        transcript = transcript_text.strip()
        print(f"[DEBUG] Transcript received. Length: {len(transcript)} characters")

    else:
        raise ValueError(f"Unknown input_type: {input_type}")

    print("[DEBUG] Calling summarize_transcript()...")
    structured = summarize_transcript(transcript)
    structured['transcript'] = transcript

    print("[DEBUG] process_meeting() completed successfully!")
    return structured