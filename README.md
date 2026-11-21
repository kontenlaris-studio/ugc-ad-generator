# AI UGC Ad Generator

One product in — ten filmable UGC-style ad variants out. Sellers normally pay $50–150 for a single human UGC video; this kit writes the whole set as production paperwork: a script, a shot list, timed captions and a hook overlay line for every angle, ready to film yourself or hand to any creator.

**Landing:** https://kontenlaris-studio.github.io/ugc-ad-generator/

## The 10 angles

| # | Angle | What it does |
|---|---|---|
| 1 | Problem / solution | Names the daily pain, then the product as the fix |
| 2 | Unboxing | First-impression walkthrough of what is actually inside |
| 3 | Testimonial **template** | A labelled script template — placeholders for the creator's own real experience, never a fabricated review |
| 4 | Comparison | Old way vs. this way, side by side |
| 5 | Before / after | Same work, different process — describes the workflow change, makes no result claims |
| 6 | FAQ | Answers the one question every buyer asks |
| 7 | Myth-bust | Corrects a misconception about the product category |
| 8 | Routine | The product inside a daily routine |
| 9 | Gift angle | For buyers shopping for someone else |
| 10 | Honest urgency | A real reason to act now — never invented scarcity or fake deadlines |

## Run (free, offline, stdlib only)

```
python3 ugc.py --product product.json --out my-ads/
python3 ugc.py --selftest        # 9/9 checks
```

Product JSON: `{"name": "…", "price": "…", "benefits": ["…", "…"], "audience": "…", "platform": "tiktok|shorts|reels", "language": "en|id"}` — benefits are the only claims a script can make, and they come from you. Each variant folder holds `script.txt` (the exact Talking-Head pipeline format), `shotlist.md`, `captions.srt` (word-timed at 150 wpm) and `hook.txt`.

## The compliance guard is a feature

Every generated line — and any `custom_lines` you add — passes a deterministic banned-claim checker before it reaches the pack: no invented results, no fake discounts, no false scarcity or deadlines, no medical or financial promises, no invented social proof. Hits land in `compliance.md`; a variant whose assembled script trips the guard is withheld, not shipped. A real generated sample (the studio's own Starter Kit UMKM Digital, in Indonesian) is in `sample-pack/` — its compliance report is clean.

## The chain

Trend Scout angles → this kit's ad-angle engine → [Talking-Head Kit](https://github.com/kontenlaris-studio/talking-head-kit) renders script + photo + voice → [ClipSmith](https://github.com/kontenlaris-studio/clipsmith) caption/clip plan. Script structure follows the [Story-to-Shorts](https://github.com/kontenlaris-studio/story-to-shorts) framework (hook ≤ 3s, one idea per sentence, mid-point turn, comment-earning close).

## Honest scope

- **This kit writes and guards scripts; it does not fabricate proof.** The testimonial variant is a template with bracketed placeholders — film it only with your own real experience, or a real customer's, with their permission.
- **Voice is yours**: record it yourself, hire a creator, or use any TTS service you choose — rendering needs one audio file per video via the Talking-Head pipeline. No voice cloning is built in or claimed.
- **Facts are yours**: a script can only repeat the benefits in your product JSON, and the guard rejects the classic fake-claim patterns — but you are still responsible for your ads complying with your marketplace's and country's rules.

## Get it

The generator (this repo) is free and MIT. The **kit — $39 one-time** — adds 40 extra angle templates, worked packs for 6 product categories and a creator-brief template: order by email to kontenlaris.studio@gmail.com (PayPal). **Done-for-you packs**: 5 finished videos **$29** · 10 finished videos **$49**, same email. Also on SkillSafe as a scan-verified skill + hosted studio app.

By Kontenlaris Studio · MIT.
