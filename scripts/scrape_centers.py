#!/usr/bin/env python3
"""
scrape_centers.py — Use Playwright to open all center websites in parallel
tabs and extract name, description, director, focus areas, and logo URL.

Usage:
  python3 scripts/scrape_centers.py

Outputs: data/scraped_centers.json (review before merging into centers.json)
"""

import json, re, asyncio
from pathlib import Path
from playwright.async_api import async_playwright

CENTERS = [
    {"id": "cebrap",          "name": "Brazilian Center of Analysis and Planning",
     "url": "https://cebrap.org.br/en/"},
    {"id": "cede-uniandes",   "name": "Center for Studies on Economic Development (CEDE)",
     "url": "https://economia.uniandes.edu.co/cede"},
    {"id": "auc-mena",        "name": "Beyond Neoliberalism: Voices from MENA",
     "url": "https://www.aucegypt.edu/"},
    {"id": "iitb-npe",        "name": "New Political Economy Initiative",
     "url": "https://www.iitb.ac.in/"},
    {"id": "colmex-pae",      "name": "Program for the Economic Analysis of Mexico",
     "url": "https://www.colmex.mx/"},
    {"id": "wits-scis",       "name": "Southern Centre for Inequality Studies",
     "url": "https://scis.wits.ac.za/"},
    {"id": "lse-rcc",         "name": "Reimagining Cohesive Capitalism",
     "url": "https://www.lse.ac.uk/"},
    {"id": "ucl-iipp",        "name": "Institute for Innovation and Public Purpose",
     "url": "https://www.ucl.ac.uk/bartlett/public-purpose/"},
    {"id": "columbia-ccpe",   "name": "Columbia Center for Political Economy",
     "url": "https://politicaleconomy.columbia.edu/"},
    {"id": "harvard-rie",     "name": "Reimagining the Economy",
     "url": "https://reimaginingtheeconomy.hks.harvard.edu/"},
    {"id": "howard-cees",     "name": "Center for Equitable Economy and Sustainable Society",
     "url": "https://howard.edu/"},
    {"id": "ces-jhu",         "name": "Center on Economy and Society",
     "url": "https://snfagora.jhu.edu/our-work/labs/center-for-economy-society/"},
    {"id": "mit-sfw",         "name": "Shaping the Future of Work",
     "url": "https://workofthefuture.mit.edu/"},
    {"id": "sfi-epe",         "name": "Emergent Political Economies",
     "url": "https://www.santafe.edu/"},
    {"id": "besi-berkeley",   "name": "Berkeley Economy and Society Initiative",
     "url": "https://besi.berkeley.edu/"},
]

async def scrape_one(page, center):
    result = {**center, "title": "", "description": "", "text_excerpt": "",
              "logo_url": "", "error": ""}
    try:
        await page.goto(center["url"], wait_until="networkidle", timeout=25000)
        result["title"] = await page.title()
        # Try to get meta description
        desc = await page.evaluate(
            "() => document.querySelector('meta[name=\"description\"]')?.content || ''"
        )
        result["description"] = desc

        # Extract logo src
        logo = await page.evaluate("""() => {
            const imgs = [...document.querySelectorAll('header img, .logo img, img.logo, a[href="/"] img')];
            return imgs[0]?.src || '';
        }""")
        result["logo_url"] = logo

        # Get first 400 chars of body text as context
        body_text = await page.inner_text("body")
        result["text_excerpt"] = re.sub(r'\s+', ' ', body_text)[:400]
    except Exception as e:
        result["error"] = str(e)
    return result


async def scrape_all():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=[
            '--disable-blink-features=AutomationControlled',
            '--no-sandbox',
        ])
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/125.0.0.0 Safari/537.36"
        )

        # Open all pages in parallel
        pages = [await context.new_page() for _ in CENTERS]
        tasks = [scrape_one(pages[i], CENTERS[i]) for i in range(len(CENTERS))]
        results = await asyncio.gather(*tasks)

        await browser.close()
        return results


if __name__ == "__main__":
    print("Scraping all center websites in parallel…")
    results = asyncio.run(scrape_all())

    out = Path(__file__).parent.parent / "data" / "scraped_centers.json"
    out.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\nResults written to {out}\n")
    for r in results:
        status = "✓" if not r["error"] else f"✗ {r['error'][:60]}"
        print(f"  [{status}] {r['name'][:50]}")

    print("\nReview data/scraped_centers.json and merge into data/centers.json")
