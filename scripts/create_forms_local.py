#!/usr/bin/env python3
"""
EPE Network — Forms Creator (local)
Uses clasp's OAuth client to get a one-time Forms API token,
then creates both Google Forms with all questions.

Run: python3 scripts/create_forms_local.py
"""
import json, sys, socket, threading, webbrowser, urllib.request, urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler

# ── Reuse clasp's OAuth client (already trusted by user's Google account) ──
CLASPRC       = "/Users/louishyman/.clasprc.json"
rc            = json.load(open(CLASPRC))["tokens"]["default"]
CLIENT_ID     = rc["client_id"]
CLIENT_SECRET = rc["client_secret"]

SCOPES = [
    "https://www.googleapis.com/auth/forms.body",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]

# ── Find a free local port for the OAuth redirect ─────────────────────────
sock = socket.socket(); sock.bind(('', 0)); PORT = sock.getsockname()[1]; sock.close()
REDIRECT_URI = f"http://localhost:{PORT}"

auth_code_holder = [None]

class OAuthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        params = dict(urllib.parse.parse_qsl(urllib.parse.urlparse(self.path).query))
        auth_code_holder[0] = params.get("code")
        self.send_response(200); self.send_header("Content-Type","text/html"); self.end_headers()
        self.wfile.write(b"<h2 style='font-family:sans-serif;padding:40px'>Done! You can close this tab.</h2>")
    def log_message(self, *args): pass

def api(path, token, body=None):
    """JSON call to a Google API; returns parsed response."""
    url = f"https://forms.googleapis.com{path}" if path.startswith("/v1") else path
    data = json.dumps(body).encode() if body is not None else None
    req  = urllib.request.Request(
        url, data=data,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST" if data else "GET",
    )
    try:
        return json.loads(urllib.request.urlopen(req, timeout=60).read())
    except urllib.error.HTTPError as e:
        print("API error:", e.code, json.loads(e.read())); sys.exit(1)

def sheets_api(path, token, body=None):
    url = f"https://sheets.googleapis.com{path}"
    data = json.dumps(body).encode() if body is not None else None
    req  = urllib.request.Request(
        url, data=data,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST" if data else "GET",
    )
    try:
        return json.loads(urllib.request.urlopen(req, timeout=30).read())
    except urllib.error.HTTPError as e:
        print("Sheets API error:", e.code, json.loads(e.read())); return None

# ── OAuth flow ──────────────────────────────────────────────────────────────
auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode({
    "client_id":    CLIENT_ID,
    "redirect_uri": REDIRECT_URI,
    "response_type":"code",
    "scope":        " ".join(SCOPES),
    "access_type":  "offline",
    "prompt":       "consent",
})

print("\n─── EPE Network Forms Creator ───────────────────────────────────")
print("Opening browser for Google authorization (one-time)...")
webbrowser.open(auth_url)

server = HTTPServer(('localhost', PORT), OAuthHandler)
print(f"Waiting for authorization on localhost:{PORT} ...")
server.handle_request()

if not auth_code_holder[0]:
    print("Authorization cancelled."); sys.exit(1)

# Exchange code for token
token_resp = json.loads(urllib.request.urlopen(
    urllib.request.Request(
        "https://oauth2.googleapis.com/token",
        data=urllib.parse.urlencode({
            "code": auth_code_holder[0], "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET, "redirect_uri": REDIRECT_URI,
            "grant_type": "authorization_code",
        }).encode(),
    ), timeout=15
).read())

TOKEN = token_resp.get("access_token")
if not TOKEN:
    print("Failed to get access token:", token_resp); sys.exit(1)

print("Authorized. Building forms...\n")

# ── Shared option lists ─────────────────────────────────────────────────────

EPE_TOPICS = [
    "Care economy and social reproduction",
    "Climate, green transition, and energy policy",
    "Comparative capitalism and varieties of capitalism",
    "Corporate governance and ownership",
    "Development economics and state capacity",
    "Digital economy and platform labor",
    "Feminist political economy",
    "Financialization and financial markets",
    "Global value chains and trade",
    "Housing, land, and urban economy",
    "Industrial policy and structural transformation",
    "Inequality and redistribution",
    "Labor markets, unions, and employment",
    "Migration and labor mobility",
    "Monetary policy, central banking, and debt",
    "Post-colonial and decolonial political economy",
    "Racial capitalism and economic justice",
    "Social protection and welfare state",
    "State-market relations and regulation",
    "Technology, automation, and AI",
    "Other (please describe below)",
]

REGIONS = [
    "North America",
    "Latin America and the Caribbean",
    "Europe",
    "Sub-Saharan Africa",
    "Middle East and North Africa",
    "South Asia",
    "East and Southeast Asia",
    "Oceania",
    "Global / Cross-regional",
]

COUNTRIES = [
    "Argentina","Australia","Austria","Belgium","Bolivia","Brazil",
    "Canada","Chile","China","Colombia","Costa Rica","Denmark",
    "Ecuador","Egypt","Ethiopia","Finland","France","Germany",
    "Ghana","India","Indonesia","Israel","Italy","Japan",
    "Kenya","Mexico","Morocco","Netherlands","New Zealand","Nigeria",
    "Norway","Pakistan","Peru","Philippines","Portugal","Senegal",
    "Singapore","South Africa","South Korea","Spain","Sweden",
    "Switzerland","Taiwan","Tanzania","Thailand","Turkey",
    "United Kingdom","United States","Uruguay","Venezuela",
    "Zimbabwe","Other (please specify below)",
]

CENTER_NAMES = [
    "Brazilian Center of Analysis and Planning (CEBRAP)",
    "Center for Studies on Economic Development (CEDE) — Universidad de los Andes",
    "Pathways Beyond Neoliberalism — American University in Cairo",
    "New Political Economy Initiative (NPEI) — IIT Bombay",
    "Program for the Economic Analysis of Mexico — El Colegio de México",
    "Southern Centre for Inequality Studies (SCIS) — University of the Witwatersrand",
    "Reimagining Cohesive Capitalism — LSE (STICERD)",
    "Institute for Innovation and Public Purpose (IIPP) — UCL",
    "Columbia Center for Political Economy — Columbia University",
    "Reimagining the Economy Initiative — Harvard Kennedy School",
    "Center for Equitable Economy and Sustainable Society — Howard University",
    "Center on Economy and Society (CES) — Johns Hopkins University",
    "Work of the Future — MIT",
    "Emergent Political Economies — Santa Fe Institute",
    "Berkeley Economy and Society Initiative (BESI) — UC Berkeley",
    "Center for Critical Imagination — University of Campinas (Unicamp)",
    "Other / Independent",
]

YEARS = [str(y) for y in range(1970, 2026)] + ["Before 1970"]

# ── Helpers ─────────────────────────────────────────────────────────────────

def short(title, desc="", required=False):
    return {"title": title, "description": desc,
            "questionItem": {"question": {"required": required, "textQuestion": {"paragraph": False}}}}

def para(title, desc="", required=False):
    return {"title": title, "description": desc,
            "questionItem": {"question": {"required": required, "textQuestion": {"paragraph": True}}}}

def dropdown(title, choices, desc="", required=False):
    return {"title": title, "description": desc,
            "questionItem": {"question": {"required": required, "choiceQuestion": {
                "type": "DROP_DOWN",
                "options": [{"value": c} for c in choices],
            }}}}

def checkbox(title, choices, desc="", required=False):
    return {"title": title, "description": desc,
            "questionItem": {"question": {"required": required, "choiceQuestion": {
                "type": "CHECKBOX",
                "options": [{"value": c} for c in choices],
            }}}}

def section(title, desc=""):
    return {"title": title, "description": desc, "pageBreakItem": {}}

def build_requests(items):
    return [{"createItem": {"item": item, "location": {"index": i}}} for i, item in enumerate(items)]

# ── CENTER FORM ─────────────────────────────────────────────────────────────

print("Creating Center Registration Form...")

center_form = api("/v1/forms", TOKEN, {
    "info": {
        "title": "EPE Network — Center Registration",
        "documentTitle": "EPE Network — Center Registration",
    }
})
cf_id  = center_form["formId"]
cf_url = f"https://docs.google.com/forms/d/{cf_id}/viewform"

center_items = [
    # Basic Info
    section("Center Information"),
    short("Center Name",
          "Official name of your center. Used as the unique identifier across submissions.",
          required=True),
    short("Institution / University", required=True),
    short("City", required=True),
    short("State / Province (if applicable)",
          "US centers: abbreviation e.g. 'MD', 'NY', 'MA'. Leave blank otherwise."),
    dropdown("Country", COUNTRIES, required=True),
    short("Country (if 'Other' above)", "Fill in only if you selected 'Other' above."),
    dropdown("Region", REGIONS,
             "Select the primary geographic region your center operates in.", required=True),
    short("Website URL", "Full URL including https://, e.g. https://ces.jhu.edu"),
    short("Logo Image URL (optional)",
          "Direct link to a .png or .svg logo. Leave blank to use an initials badge on the site."),

    # Contact
    section("Director & Contact"),
    short("Director / Primary Contact Name", required=True),
    short("Contact Email", "Shown in the directory for network correspondence.", required=True),
    dropdown("Year Established", YEARS),

    # Topics — Current
    section("Current Research Topics",
            "Topics your center actively researches right now."),
    checkbox("Select all that apply", EPE_TOPICS),
    para("Additional current topics not listed above",
         "Comma- or semicolon-separated."),

    # Topics — Anticipated
    section("Anticipated Research Topics",
            "Topics you expect to move toward in the near future."),
    checkbox("Select all that apply", EPE_TOPICS),
    para("Additional anticipated topics not listed above",
         "Comma- or semicolon-separated."),

    # Topics — Would Like
    section("Topics You Would Like to Work On",
            "Aspirational or collaborative interests — topics you'd like to explore, even if not yet active."),
    checkbox("Select all that apply", EPE_TOPICS),
    para("Additional 'would like' topics not listed above",
         "Comma- or semicolon-separated."),

    # Profile
    section("Center Profile"),
    para("Thematic Focus Areas (general profile)",
         "Broad description of your center's research identity. Comma-separated phrases are fine."),
    para("Current Research Projects",
         "1–3 sentences describing your most active current work."),
    para("Funding Sources",
         "e.g. 'NSF, Ford Foundation, university endowment'"),

    # Network
    section("Network Collaboration"),
    para("Organizational Challenges / Problems",
         "Funding gaps, political constraints, capacity limitations, methodological challenges, etc."),
    para("Opportunities (offering or seeking)",
         "e.g. 'seeking comparative partners on platform labor', 'offering visiting fellowship'"),
    para("Connected External Networks & Meetings",
         "Other networks your center participates in, comma-separated. e.g. 'SASE, CLACSO, ISA'"),
    para("Anything else you would like to share"),
]

api(f"/v1/forms/{cf_id}:batchUpdate", TOKEN, {
    "requests": [
        {"updateFormInfo": {
            "info": {
                "description": (
                    "Register your research center with the Emerging Political Economy (EPE) Network. "
                    "One submission per center; filled out by the director or administrator. "
                    "You may resubmit at any time to update your information."
                )
            },
            "updateMask": "description"
        }},
        *build_requests(center_items)
    ]
})
print(f"  ✓ Center form created: {cf_url}")

# ── SCHOLAR FORM ────────────────────────────────────────────────────────────

print("Creating Scholar Registration Form...")

scholar_form = api("/v1/forms", TOKEN, {
    "info": {
        "title": "EPE Network — Scholar Registration",
        "documentTitle": "EPE Network — Scholar Registration",
    }
})
sf_id  = scholar_form["formId"]
sf_url = f"https://docs.google.com/forms/d/{sf_id}/viewform"

scholar_items = [
    # Basic Info
    section("Personal Information"),
    short("Full Name", required=True),
    short("Title / Position",
          "e.g. 'Associate Professor', 'Postdoctoral Fellow', 'Research Director'"),
    dropdown("Center Affiliation", CENTER_NAMES,
             "Select your primary EPE Network center. Choose 'Other / Independent' if your center is not listed.",
             required=True),
    short("Institution", "Your university or research institution.", required=True),
    dropdown("Country", COUNTRIES, "Your current location.", required=True),
    short("Country (if 'Other' above)", "Fill in only if you selected 'Other' above."),
    short("Email",
          "Used as the unique key for deduplication. Not displayed publicly on the site.",
          required=True),
    short("Personal / Academic Website", "Full URL including https://"),

    # Topics — Current
    section("Current Research Topics",
            "Topics you actively research right now."),
    checkbox("Select all that apply", EPE_TOPICS, required=True),
    para("Additional current topics not listed above",
         "Comma- or semicolon-separated."),

    # Topics — Anticipated
    section("Anticipated Research Topics",
            "Topics you expect to move toward in the near future."),
    checkbox("Select all that apply", EPE_TOPICS),
    para("Additional anticipated topics not listed above",
         "Comma- or semicolon-separated."),

    # Topics — Would Like
    section("Topics You Would Like to Work On",
            "Topics you'd want to explore with partners, even if not yet active."),
    checkbox("Select all that apply", EPE_TOPICS),
    para("Additional 'would like' topics not listed above",
         "Comma- or semicolon-separated."),

    # Teaching
    section("Teaching"),
    checkbox("Teaching – Regional Focus",
             REGIONS + ["I do not currently teach"],
             "Select all regions you primarily teach about."),
    checkbox("Teaching – Level", ["Undergraduate", "Graduate", "Executive education", "Other"]),

    # Network
    section("Network Collaboration"),
    para("Connected External Networks & Meetings",
         "Other networks you participate in beyond EPE. Comma-separated."),
    para("Problems (research, funding, organizational)",
         "Open field — share any challenges you're navigating."),
    para("Opportunities (offering or seeking)",
         "Collaborations you're looking for, fellowships you offer, data you can share, etc."),
    para("Anything else you would like to share"),
]

api(f"/v1/forms/{sf_id}:batchUpdate", TOKEN, {
    "requests": [
        {"updateFormInfo": {
            "info": {
                "description": (
                    "Register as a scholar with the Emerging Political Economy (EPE) Network. "
                    "Add your research profile and affiliation to connect with colleagues across the network. "
                    "You may resubmit at any time to update your profile."
                )
            },
            "updateMask": "description"
        }},
        *build_requests(scholar_items)
    ]
})
print(f"  ✓ Scholar form created: {sf_url}")

# ── LINK TO SHEETS ──────────────────────────────────────────────────────────

print("\nCreating linked Google Sheets...")

def create_sheet(name, token):
    resp = sheets_api("/v4/spreadsheets", token, {
        "properties": {"title": name}
    })
    return resp.get("spreadsheetUrl", "?") if resp else None

center_sheet  = create_sheet("EPE Network — Center Registration Responses", TOKEN)
scholar_sheet = create_sheet("EPE Network — Scholar Registration Responses", TOKEN)

if center_sheet:  print(f"  ✓ Center sheet:  {center_sheet}")
if scholar_sheet: print(f"  ✓ Scholar sheet: {scholar_sheet}")
print("  (Note: open each form → Responses tab → Link to Sheets → select the sheet above)")

# ── OUTPUT ──────────────────────────────────────────────────────────────────

print("""
════════════════════════════════════════════════════════
  FORMS CREATED — update three files with these URLs:
════════════════════════════════════════════════════════
""")
print(f"CENTER FORM (share this URL):   {cf_url}")
print(f"SCHOLAR FORM (share this URL):  {sf_url}")
print("""
Update:
  1. js/app.js         → FORM_URL_CENTER / FORM_URL_INDIVIDUAL
  2. register.html     → CENTER_FORM_URL / INDIVIDUAL_FORM_URL
  3. index.html        → two href="https://forms.gle/..." in hero-actions
════════════════════════════════════════════════════════
""")
