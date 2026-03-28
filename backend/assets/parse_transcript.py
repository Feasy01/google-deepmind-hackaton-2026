import json
import re
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(script_dir, 'Improve Your Lymphatic System for Overall Health & Appearance.txt')
output_path = os.path.join(script_dir, 'Improve Your Lymphatic System for Overall Health & Appearance.json')

with open(file_path, 'r', encoding='utf-8') as f:
    lines = [l.rstrip('\n') for l in f.readlines()]

timestamp_re = re.compile(r'^\d+:\d{2}(:\d{2})?$')

transcript = []
i = 0
while i < len(lines):
    line = lines[i]
    if timestamp_re.match(line.strip()):
        ts = line.strip()
        # Collect all text lines until next timestamp or section header
        text_parts = []
        i += 1
        while i < len(lines):
            cur = lines[i]
            # If this line is a timestamp, stop
            if timestamp_re.match(cur.strip()):
                break
            # If this line is non-empty and the NEXT line is a timestamp, it's text (last line before next ts)
            # If this line is non-empty and next line is also non-timestamp-non-empty, check if it's a section header
            # Section headers: non-empty lines where the next non-empty line is a timestamp
            if cur.strip():
                # Look ahead: is the next non-empty line a timestamp?
                j = i + 1
                while j < len(lines) and not lines[j].strip():
                    j += 1
                if j < len(lines) and timestamp_re.match(lines[j].strip()):
                    # This could be a section header OR the last text line
                    # Heuristic: if there's already text collected, this is likely a section header
                    # If no text collected yet, it's text
                    if not text_parts:
                        text_parts.append(cur.strip())
                    # else: it's a section header, skip it
                    i = j
                    break
                else:
                    text_parts.append(cur.strip())
            i += 1

        text = " ".join(text_parts)
        if text:
            transcript.append({
                "timestamp": ts,
                "text": text
            })
    else:
        i += 1

data = {
    "title": "Improve Your Lymphatic System for Overall Health & Appearance",
    "speaker": "Andrew Huberman",
    "source": "Huberman Lab Podcast",
    "transcript": transcript
}

with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"Wrote {len(transcript)} segments to {output_path}")
