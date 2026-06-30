# Google Forms Field Specification

Two separate forms. Create each in Google Forms, link to its own Google Sheet.
**Enable email notifications:** Responses tab → three-dot menu → "Get email notifications for new responses."

---

## Form 1 — Center Registration

One submission per center. Filled out by the director or a designated admin.

| # | Field Label | Type | Required | Notes |
|---|------------|------|----------|-------|
| 1 | Center Name | Short answer | ✓ | Used as the unique key for deduplication |
| 2 | Institution / University | Short answer | ✓ | |
| 3 | City | Short answer | ✓ | |
| 4 | State / Province (if applicable) | Short answer | | For US centers: e.g. "MD", "NY", "MA". Leave blank for other countries. |
| 5 | Country | Short answer | ✓ | Must match a known country name for flag/region lookup |
| 6 | Website URL | Short answer | | Full URL, e.g. https://ces.jhu.edu |
| 7 | Logo Image URL (optional) | Short answer | | Direct URL to a .png or .svg logo; leave blank to use initials badge |
| 8 | Director / Primary Contact Name | Short answer | ✓ | |
| 9 | Contact Email | Short answer | ✓ | |
| 10 | Year Established | Short answer | | 4-digit year |
| 11 | Current Research Topics | Paragraph | | Comma- or semicolon-separated. Topics your center actively researches *now*. |
| 12 | Anticipated Research Topics | Paragraph | | Topics you expect to move toward in the near future. |
| 13 | Topics You Would Like to Work On | Paragraph | | Topics you'd like to explore with collaborators, even if not yet active. |
| 14 | Thematic Focus Areas (general profile) | Paragraph | | Broad description of the center's research identity; comma-separated. |
| 15 | Current Research Projects | Paragraph | | 1–3 sentences describing active work |
| 16 | Funding Sources | Paragraph | | e.g. "NSF, Ford Foundation, university endowment" |
| 17 | Organizational Challenges / Problems | Paragraph | | Open: funding gaps, political constraints, capacity, etc. |
| 18 | Opportunities (offering or seeking) | Paragraph | | e.g. "seeking comparative partners on X", "offering visiting fellowship" |
| 19 | Connected External Networks & Meetings | Paragraph | | Comma-separated, e.g. "SASE, CLACSO, ISA" |
| 20 | Anything else you would like to share | Paragraph | | Open field |

**Topic category note:** Questions 11–13 use the same three-category system as the individual scholar form:
- **Current**: active research now
- **Anticipated**: likely near-term direction
- **Would Like**: aspirational/collaborative interests

**Resubmission policy:** If a center's situation changes, they can submit again.
The synthesize.py script keeps the latest submission by center name.

---

## Form 2 — Scholar Registration

One submission per scholar. Filled out individually.

| # | Field Label | Type | Required | Notes |
|---|------------|------|----------|-------|
| 1 | Full Name | Short answer | ✓ | |
| 2 | Title / Position | Short answer | | e.g. "Associate Professor", "Postdoctoral Fellow" |
| 3 | Center Affiliation | Dropdown | ✓ | List all center names; add "Other / Independent" |
| 4 | Institution | Short answer | ✓ | University or research institution |
| 5 | Country | Short answer | ✓ | Current location |
| 6 | Email | Short answer | ✓ | Used as the unique key for deduplication |
| 7 | Personal / Academic Website | Short answer | | Full URL |
| 8 | Current Research Topics | Paragraph | ✓ | Comma- or semicolon-separated |
| 9 | Anticipated Research Topics | Paragraph | | Topics you expect to move toward |
| 10 | Topics You Would Like to Work On | Paragraph | | Topics you'd want to explore with collaborators |
| 11 | Teaching – Regional Focus | Short answer | | e.g. "Latin America", "Sub-Saharan Africa, Southeast Asia" |
| 12 | Teaching – Level | Checkboxes | | Options: Undergraduate / Graduate / Executive / Other |
| 13 | Connected External Networks & Meetings | Paragraph | | Other networks beyond this one |
| 14 | Problems (research, funding, organizational) | Paragraph | | Open |
| 15 | Opportunities (offering or seeking) | Paragraph | | Open |
| 16 | Anything else you would like to share | Paragraph | | Open |

**Resubmission policy:** Scholars can resubmit to update their profile.
The synthesize.py script keeps the latest submission by email address.

---

## QR Code Generation

After creating each form, get the sharable URL (Form → Send → link icon).
Generate a QR code at qr-code-generator.com or qrcode.me.

Suggested label for Center QR code: **"Register Your Center"**
Suggested label for Individual QR code: **"Register as a Scholar"**

Update the two `href` values in `index.html`:
```html
<a class="hero-link" href="https://forms.gle/YOUR_CENTER_FORM_URL">Register Your Center ↗</a>
<a class="hero-link" href="https://forms.gle/YOUR_INDIVIDUAL_FORM_URL">Register as a Scholar ↗</a>
```

---

## Refreshing the Site Data

1. Open each Google Sheet → File → Download → Comma-separated values (.csv)
2. Save as `data/centers_responses.csv` and `data/individuals_responses.csv`
3. Run: `python3 scripts/synthesize.py`
4. Review any warnings in the output
5. `git add data/centers.json data/individuals.json && git commit -m "data: refresh from form responses"`
6. `git push` — GitHub Pages rebuilds automatically

---

## Email Notification Setup

In Google Forms → Responses tab → three-dot menu → **"Get email notifications for new responses."**
This sends an email to the form owner's Google account on every submission.
No code required.
