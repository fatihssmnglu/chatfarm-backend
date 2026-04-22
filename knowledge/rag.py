import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
CHUNKS_FILE = BASE_DIR / "dataset" / "chunks.jsonl"


def load_chunks():
    chunks = []

    if not CHUNKS_FILE.exists():
        return chunks

    with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                chunks.append(json.loads(line))

    return chunks


def infer_keywords_from_rule(rule):
    condition = rule.get("condition", "").lower()
    effect = rule.get("effect", "").lower()
    action = rule.get("action", "").lower()
    combined = f"{condition} {effect} {action}"

    keywords = []
    preferred_tags = []
    preferred_sections = []

    if "temperature" in combined or "temp" in combined or "sicak" in combined:
        keywords += ["sicaklik", "yüksek sıcaklık", "düşük sıcaklık", "meyve tutumu"]
        preferred_tags += ["sicaklik"]
        preferred_sections += ["yetiştirme_kosullari", "yetiştirme", "sicaklik", "mikroklima"]

    if "humidity" in combined or "nem" in combined:
        keywords += ["nem", "yüksek nem", "düşük nem", "hastalık riski"]
        preferred_tags += ["nem"]
        preferred_sections += ["yetiştirme_kosullari", "mikroklima", "nem"]

    if "light" in combined or "isik" in combined:
        keywords += ["ışık", "düşük ışık", "gelişim", "meyve dökülmesi"]
        preferred_tags += ["isik"]
        preferred_sections += ["yetiştirme_kosullari", "isik", "transpirasyon"]

    if "vpd" in combined:
        keywords += ["vpd", "transpirasyon", "su kaybı"]
        preferred_tags += ["vpd", "transpirasyon"]
        preferred_sections += ["transpirasyon", "mikroklima"]

    if "water" in combined or "sulama" in combined or "irrigation" in combined:
        keywords += ["sulama", "su ihtiyacı", "su stresi", "toprak nemi"]
        preferred_tags += ["sulama"]
        preferred_sections += ["sulama"]

    if "co2" in combined:
        keywords += ["co2", "fotosentez"]
        preferred_tags += ["co2"]
        preferred_sections += ["yetiştirme_kosullari"]

    if "salinity" in combined or "tuz" in combined:
        keywords += ["tuzluluk", "verim düşer"]
        preferred_tags += ["tuzluluk"]
        preferred_sections += ["toprak", "hassasiyet"]

    if "calcium" in combined or "kalsiyum" in combined:
        keywords += ["kalsiyum", "çiçek burnu çürüklüğü"]
        preferred_tags += ["kalsiyum", "hastalik"]
        preferred_sections += ["hassasiyet"]

    return {
        "keywords": list(set(keywords)),
        "preferred_tags": list(set(preferred_tags)),
        "preferred_sections": list(set(preferred_sections)),
    }


def score_chunk(chunk, keyword_info):
    score = 0

    content = chunk.get("content", "").lower()
    tags = [t.lower() for t in chunk.get("tags", [])]
    section = chunk.get("section", "").lower()
    subsection = chunk.get("subsection", "").lower()

    for keyword in keyword_info["keywords"]:
        if keyword in content:
            score += 3

    for tag in keyword_info["preferred_tags"]:
        if tag in tags:
            score += 5

    for sec in keyword_info["preferred_sections"]:
        if sec == section:
            score += 4
        if sec == subsection:
            score += 2

    # Küçük ceza: çok alakasız alanlar geriye düşsün
    unrelated_sections = ["gubreleme", "sera", "bitki_yogunluk"]
    if section in unrelated_sections and score < 5:
        score -= 2

    return score


def retrieve_chunks_for_rules(matched_rules, top_k=3):
    chunks = load_chunks()
    scored = []

    for rule in matched_rules:
        keyword_info = infer_keywords_from_rule(rule)

        for chunk in chunks:
            score = score_chunk(chunk, keyword_info)
            if score > 0:
                scored.append((score, chunk))

    scored.sort(key=lambda x: x[0], reverse=True)

    selected = []
    seen_ids = set()
    seen_contents = set()

    for score, chunk in scored:
        chunk_id = chunk.get("id")
        content = chunk.get("content", "").strip()

        if chunk_id in seen_ids:
            continue
        if content in seen_contents:
            continue

        selected.append(chunk)
        seen_ids.add(chunk_id)
        seen_contents.add(content)

        if len(selected) >= top_k:
            break

    return selected