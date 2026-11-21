#!/usr/bin/env python3
"""ugc.py — AI UGC Ad Generator (deterministic ad-angle engine).

Turns one product JSON into a complete pack of 10 short UGC-style ad
variants. Each variant ships as production-ready paperwork:

  script.txt    one-paragraph script in the Talking-Head pipeline format
                (hook -> body -> mid turn -> close), ready to feed to
                the Talking-Head Kit pipeline with a photo + voice file
  shotlist.md   timed shot list a creator (or the seller) can film
  captions.srt  word-timed captions estimated at 150 wpm
  hook.txt      the opening line on its own, for the text overlay

The 10 angles: problem-solution, unboxing, testimonial-TEMPLATE (a
clearly labelled script template — the words are placeholders for the
creator's own real experience, never a fabricated review), comparison,
before/after (process-only, claim-free), faq, myth-bust, routine,
gift, honest-urgency (a real reason to act, never invented scarcity).

Compliance guard: every generated line and every user-supplied custom
line is checked against a deterministic banned-claim wordlist
(invented results, fake discounts, medical/financial promises, false
scarcity...). Hits are reported in compliance.md and the offending
variant is withheld from the pack.

Usage:
  python3 ugc.py --product product.json --out pack/
  python3 ugc.py --selftest

Product JSON:
  {"name": "...", "price": "...", "benefits": ["...", "..."],
   "audience": "...", "platform": "tiktok|shorts|reels",
   "language": "en|id", "photo": "optional.png", "audio": "optional.mp3",
   "custom_lines": ["optional extra lines, guard-checked"]}
Stdlib only. Offline. No network.
"""
import argparse, json, os, re, sys, tempfile

WPM = 150  # caption timing estimate, same convention as the studio kits

# ---------------------------------------------------------------- guard
# Deterministic banned-claim patterns (checked case-insensitively).
BANNED = [
    (r"guaranteed (results|income|profit|success)", "guaranteed outcome promise"),
    (r"100%\s*(guaranteed|effective|proven|works)", "absolute efficacy claim"),
    (r"\b(cure|cures|cured|heal|heals)\b.*\b(disease|cancer|diabetes|illness)\b", "medical cure claim"),
    (r"lose \d+\s*(kg|kilo|pounds|lbs)", "specific weight-loss claim"),
    (r"clinically proven|doctor[- ]recommended|dermatologist approved", "unverifiable authority claim"),
    (r"make (money|\$|rp)\s*\d|get rich|passive income guaranteed", "financial promise"),
    (r"\d+\s*%\s*off today only|fake discount|was \$\d+ now", "fake discount"),
    (r"only \d+ left|almost sold out|stock is running out", "false scarcity"),
    (r"sale ends (today|tonight|in \d+)|last chance ever", "false deadline"),
    (r"miracle|magic results|instant results|overnight success", "miracle/instant claim"),
    (r"#1 (in the world|best)|world'?s best|best in the world", "unverifiable superlative"),
    (r"risk[- ]free|no risk at all|zero risk", "risk denial"),
    (r"everyone is buying|thousands of happy customers", "invented social proof"),
    (r"hasil pasti|dijamin (untung|berhasil|laku)|pasti kaya", "janji hasil (id)"),
    (r"diskon \d+% hari ini saja|stok tinggal \d+", "diskon/stok palsu (id)"),
    (r"menyembuhkan (penyakit|kanker|diabetes)", "klaim medis (id)"),
]

def guard_check(lines):
    """Return list of (line, reason) for every banned-claim hit."""
    hits = []
    for line in lines:
        for pat, reason in BANNED:
            if re.search(pat, line, re.I):
                hits.append((line, reason))
    return hits

# ------------------------------------------------------------ templates
# Structural scaffolding per language. Benefit sentences come from the
# product JSON itself, so scripts only ever claim what the seller wrote.
T = {
    "en": {
        "turn": "But here is the part nobody shows you.",
        "close": "Questions? Ask me in the comments — I read every one.",
        "hooks": {
            "problem_solution": "If you sell anything online, you know this pain.",
            "unboxing": "It just arrived — let me open it with you.",
            "testimonial_template": "[TEMPLATE — replace every line with your own real experience before filming.]",
            "comparison": "I compared the old way and this way, side by side.",
            "before_after": "Same shop, same day — just a different process.",
            "faq": "The question everyone keeps asking me about this:",
            "myth_bust": "People keep saying this about {name}. It is not true.",
            "routine": "This is now part of my daily routine. Here is why.",
            "gift": "Looking for a gift that is actually useful? Watch this.",
            "honest_urgency": "No fake countdown — here is the real reason to sort this out now.",
        },
        "bodies": {
            "problem_solution": ["Doing it by hand eats hours and invites mistakes.", "This is {name}. It costs {price} — one payment, no subscription.", "Here is what it actually does:"],
            "unboxing": ["This is {name}, {price}.", "Inside the box — or in the download — you get this:"],
            "testimonial_template": ["[Say what you used before, honestly.]", "[Say the first thing you noticed when you switched to {name}.]", "[Say one specific thing it does for you:]"],
            "comparison": ["The old way: manual, slow, easy to get wrong.", "With {name} ({price}) it looks like this:"],
            "before_after": ["Before: everything manual, notes scattered, totals done twice.", "After setting up {name}: the same work, one flow. What changed is the process:"],
            "faq": ["\"What exactly do I get for {price}?\" Fair question. You get:"],
            "myth_bust": ["The myth: tools like this are only for big businesses.", "The reality: {name} was made for {audience}. It includes:"],
            "routine": ["Every day starts the same way now.", "{name} handles this part of it:"],
            "gift": ["It is {name}, {price}, and it is made for {audience}.", "What they actually receive:"],
            "honest_urgency": ["Busy seasons punish messy systems, and they always come back.", "{name} ({price}) is the fix you set up once:"],
        },
        "shot": ["Hook line to camera, product in hand", "Close-up: the pain point, shown not told", "Screen/hands: walk through each benefit", "Turn line — cut or zoom for the pattern interrupt", "Product beauty shot + price on screen", "Close line to camera, comments prompt"],
    },
    "id": {
        "turn": "Tapi ini bagian yang jarang ditunjukkan orang.",
        "close": "Ada pertanyaan? Tulis di komentar — semuanya saya baca.",
        "hooks": {
            "problem_solution": "Kalau kamu jualan online, pasti kenal rasa capek ini.",
            "unboxing": "Baru saja sampai — kita buka bareng-bareng, yuk.",
            "testimonial_template": "[TEMPLATE — ganti setiap baris dengan pengalaman aslimu sendiri sebelum merekam.]",
            "comparison": "Saya bandingkan cara lama dan cara ini, berdampingan.",
            "before_after": "Toko yang sama, hari yang sama — cuma prosesnya beda.",
            "faq": "Pertanyaan yang paling sering masuk soal ini:",
            "myth_bust": "Banyak yang bilang begini soal {name}. Itu tidak benar.",
            "routine": "Ini sekarang jadi bagian rutinitas harian saya. Ini alasannya.",
            "gift": "Lagi cari hadiah yang benar-benar kepakai? Tonton ini.",
            "honest_urgency": "Tanpa hitung mundur palsu — ini alasan sebenarnya kenapa harus dibenahi sekarang.",
        },
        "bodies": {
            "problem_solution": ["Dikerjakan manual itu makan jam dan gampang salah.", "Ini {name}. Harganya {price} — sekali bayar, tanpa langganan.", "Isinya benar-benar ini:"],
            "unboxing": ["Ini {name}, {price}.", "Di dalam paketnya — atau di file unduhannya — kamu dapat ini:"],
            "testimonial_template": ["[Ceritakan jujur apa yang kamu pakai sebelumnya.]", "[Ceritakan hal pertama yang kamu sadari setelah pindah ke {name}.]", "[Ceritakan satu hal spesifik yang ia kerjakan untukmu:]"],
            "comparison": ["Cara lama: manual, lambat, gampang keliru.", "Pakai {name} ({price}) jadinya seperti ini:"],
            "before_after": ["Sebelum: semua manual, catatan tercecer, total dihitung dua kali.", "Sesudah pasang {name}: pekerjaan yang sama, satu alur. Yang berubah prosesnya:"],
            "faq": ["\"Dapat apa saja sih dengan {price}?\" Pertanyaan wajar. Kamu dapat:"],
            "myth_bust": ["Mitosnya: alat seperti ini cuma untuk bisnis besar.", "Faktanya: {name} dibuat untuk {audience}. Isinya:"],
            "routine": ["Setiap hari sekarang dimulai dengan cara yang sama.", "{name} menangani bagian ini:"],
            "gift": ["Ini {name}, {price}, dan dibuat untuk {audience}.", "Yang benar-benar diterima penerimanya:"],
            "honest_urgency": ["Musim ramai selalu menghukum sistem yang berantakan — dan musim ramai selalu datang lagi.", "{name} ({price}) adalah beres-beres yang kamu pasang sekali:"],
        },
        "shot": ["Baris hook ke kamera, produk di tangan", "Close-up: titik capeknya, ditunjukkan bukan diceritakan", "Layar/tangan: jalani tiap manfaat satu per satu", "Baris turn — potong atau zoom untuk jeda pola", "Shot produk rapi + harga tampil di layar", "Baris penutup ke kamera, ajakan komentar"],
    },
}
ANGLES = ["problem_solution", "unboxing", "testimonial_template", "comparison",
          "before_after", "faq", "myth_bust", "routine", "gift", "honest_urgency"]
PLATFORM_LABEL = {"tiktok": "TikTok", "shorts": "YouTube Shorts", "reels": "Instagram Reels"}

def fmt(template, p):
    return template.format(name=p["name"], price=p["price"], audience=p["audience"])

def build_script(angle, p):
    """Assemble one variant: hook -> body -> benefits -> turn -> close."""
    lang = T[p.get("language", "en")]
    hook = fmt(lang["hooks"][angle], p)
    body = [fmt(b, p) for b in lang["bodies"][angle]]
    benefits = [b.rstrip(".") + "." for b in p["benefits"]]
    sentences = [hook] + body + benefits + [lang["turn"], lang["close"]]
    return " ".join(sentences), sentences, hook

def srt_time(sec):
    h, m = int(sec // 3600), int((sec % 3600) // 60)
    s, ms = int(sec % 60), int(round((sec - int(sec)) * 1000))
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def make_srt(sentences):
    out, t = [], 0.0
    for i, s in enumerate(sentences, 1):
        dur = max(1.2, len(s.split()) / WPM * 60)
        out.append(f"{i}\n{srt_time(t)} --> {srt_time(t + dur)}\n{s}\n")
        t += dur
    return "\n".join(out)

def write_variant(out_dir, idx, angle, p):
    script, sentences, hook = build_script(angle, p)
    lang = T[p.get("language", "en")]
    folder = os.path.join(out_dir, f"{idx:02d}-{angle.replace('_', '-')}")
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, "script.txt"), "w") as f:
        f.write(script + "\n")
    with open(os.path.join(folder, "hook.txt"), "w") as f:
        f.write(hook + "\n")
    with open(os.path.join(folder, "captions.srt"), "w") as f:
        f.write(make_srt(sentences))
    words = len(script.split())
    secs = round(words / WPM * 60)
    shots = lang["shot"]
    with open(os.path.join(folder, "shotlist.md"), "w") as f:
        f.write(f"# Shotlist — {angle.replace('_', ' ')} ({PLATFORM_LABEL.get(p['platform'], p['platform'])})\n\n")
        f.write(f"Product: {p['name']} · {p['price']} · ~{secs}s at {WPM} wpm\n\n")
        per = max(2, secs // len(shots))
        for i, s in enumerate(shots):
            f.write(f"{i + 1}. [{i * per:02d}s–{(i + 1) * per:02d}s] {s}\n")
        f.write("\nRender: feed script.txt + one product photo + your voice file to the "
                "Talking-Head Kit pipeline (`pipeline.py`) for the finished vertical video.\n")
    return folder, script

def generate(p, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    # guard: product copy + custom lines first
    all_lines = [p["name"], p["price"]] + p["benefits"] + p.get("custom_lines", [])
    hits = guard_check(all_lines)
    kept, withheld = [], []
    for idx, angle in enumerate(ANGLES, 1):
        script, _, _ = build_script(angle, p)
        vhits = guard_check([script])
        if vhits:
            withheld.append((angle, vhits[0][1]))
            continue
        folder, _ = write_variant(out_dir, idx, angle, p)
        kept.append((angle, folder))
        if p.get("custom_lines"):
            with open(os.path.join(folder, "custom-lines.txt"), "w") as f:
                f.write("\n".join(p["custom_lines"]) + "\n")
    with open(os.path.join(out_dir, "compliance.md"), "w") as f:
        f.write("# Compliance check — deterministic banned-claim guard\n\n")
        if hits:
            f.write("Hits in the product copy / custom lines you supplied:\n\n")
            for line, reason in hits:
                f.write(f"- ⚠️ {reason}: “{line}”\n")
        else:
            f.write("Product copy and custom lines: clean — no banned claims found.\n")
        if withheld:
            f.write("\nVariants withheld because their assembled script tripped the guard:\n\n")
            for angle, reason in withheld:
                f.write(f"- {angle}: {reason}\n")
        f.write("\nRules enforced: no invented results, no fake discounts, no false "
                "scarcity or deadlines, no medical/financial promises, no invented "
                "social proof. The testimonial variant is a labelled TEMPLATE — its "
                "lines are placeholders for the creator's own real experience.\n")
    with open(os.path.join(out_dir, "pack-summary.md"), "w") as f:
        f.write(f"# UGC Ad Pack — {p['name']}\n\n")
        f.write(f"Price: {p['price']} · Audience: {p['audience']} · Platform: "
                f"{PLATFORM_LABEL.get(p['platform'], p['platform'])}\n\n")
        f.write(f"Variants generated: {len(kept)}/10"
                + (f" · withheld by compliance guard: {len(withheld)}\n\n" if withheld else "\n\n"))
        for angle, folder in kept:
            f.write(f"- {angle.replace('_', ' ')} → `{os.path.basename(folder)}/`\n")
        f.write("\nEach variant: script.txt (Talking-Head format) · shotlist.md · "
                "captions.srt · hook.txt. Voice is yours: record it or use any TTS "
                "you choose, then render with the Talking-Head Kit pipeline.\n")
    return kept, withheld, hits

def selftest():
    checks = []
    def chk(name, cond):
        checks.append((name, bool(cond)))
    good = {"name": "Test Kit", "price": "$39", "audience": "small sellers",
            "platform": "tiktok", "language": "en",
            "benefits": ["A one-file invoice generator", "Four automation workflows"]}
    with tempfile.TemporaryDirectory() as td:
        kept, withheld, hits = generate(good, td)
        chk("10 variants generated", len(kept) == 10)
        chk("clean product passes guard", not hits and not withheld)
        ok_files = all(all(os.path.exists(os.path.join(f, n)) for n in
                           ("script.txt", "shotlist.md", "captions.srt", "hook.txt"))
                       for _, f in kept)
        chk("every variant has 4 files", ok_files)
        srt = open(os.path.join(kept[0][1], "captions.srt")).read()
        chk("srt has timing arrows", " --> " in srt)
        script = open(os.path.join(kept[2][1], "script.txt")).read()
        chk("testimonial variant labelled TEMPLATE", "TEMPLATE" in script)
        bad = dict(good, benefits=["Lose 10 kg in a week", "Only 3 left in stock"])
        _, withheld2, hits2 = generate(bad, os.path.join(td, "bad"))
        chk("guard flags weight-loss claim", any("weight-loss" in r for _, r in hits2))
        chk("guard flags false scarcity", any("scarcity" in r for _, r in hits2))
        chk("guard withholds tripped variants", len(withheld2) > 0)
        idp = dict(good, language="id", name="Kit Uji")
        kept_id, _, _ = generate(idp, os.path.join(td, "id"))
        chk("indonesian pack generates", len(kept_id) == 10)
    failed = [n for n, c in checks if not c]
    for n, c in checks:
        print(("PASS " if c else "FAIL ") + n)
    print(f"SELFTEST {len(checks) - len(failed)}/{len(checks)} passed")
    return 1 if failed else 0

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--product")
    ap.add_argument("--out")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not (a.product and a.out):
        ap.error("--product and --out are required (or use --selftest)")
    p = json.loads(open(a.product).read())
    kept, withheld, hits = generate(p, a.out)
    print(f"pack written to {a.out}: {len(kept)} variants, "
          f"{len(withheld)} withheld, {len(hits)} copy hits")
    return 0

if __name__ == "__main__":
    sys.exit(main())
