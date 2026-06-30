/**
 * EPE Network — Google Forms Auto-Creator
 *
 * HOW TO USE:
 * 1. Go to https://script.google.com → "New project"
 * 2. Delete the placeholder code and paste this entire file
 * 3. Click Run → createEPEForms
 * 4. Approve the permissions popup (Forms + Sheets + Drive)
 * 5. Click "Execution log" at the bottom to see the two form URLs
 * 6. Copy the fill URLs into js/app.js, register.html, and index.html
 */

// ── Shared option lists ─────────────────────────────────────────────────────

var EPE_TOPIC_OPTIONS = [
  'Care economy and social reproduction',
  'Climate, green transition, and energy policy',
  'Comparative capitalism and varieties of capitalism',
  'Corporate governance and ownership',
  'Development economics and state capacity',
  'Digital economy and platform labor',
  'Feminist political economy',
  'Financialization and financial markets',
  'Global value chains and trade',
  'Housing, land, and urban economy',
  'Industrial policy and structural transformation',
  'Inequality and redistribution',
  'Labor markets, unions, and employment',
  'Migration and labor mobility',
  'Monetary policy, central banking, and debt',
  'Post-colonial and decolonial political economy',
  'Racial capitalism and economic justice',
  'Social protection and welfare state',
  'State-market relations and regulation',
  'Technology, automation, and AI',
  'Other (please describe below)'
];

var REGION_OPTIONS = [
  'North America',
  'Latin America and the Caribbean',
  'Europe',
  'Sub-Saharan Africa',
  'Middle East and North Africa',
  'South Asia',
  'East and Southeast Asia',
  'Oceania',
  'Global / Cross-regional'
];

var COUNTRY_OPTIONS = [
  'Argentina', 'Australia', 'Austria', 'Belgium', 'Bolivia', 'Brazil',
  'Canada', 'Chile', 'China', 'Colombia', 'Costa Rica', 'Denmark',
  'Ecuador', 'Egypt', 'Ethiopia', 'Finland', 'France', 'Germany',
  'Ghana', 'India', 'Indonesia', 'Israel', 'Italy', 'Japan',
  'Kenya', 'Mexico', 'Morocco', 'Netherlands', 'New Zealand', 'Nigeria',
  'Norway', 'Pakistan', 'Peru', 'Philippines', 'Portugal', 'Senegal',
  'Singapore', 'South Africa', 'South Korea', 'Spain', 'Sweden',
  'Switzerland', 'Taiwan', 'Tanzania', 'Thailand', 'Turkey',
  'United Kingdom', 'United States', 'Uruguay', 'Venezuela',
  'Zimbabwe', 'Other (please specify below)'
];

var CENTER_NAMES = [
  'Brazilian Center of Analysis and Planning (CEBRAP)',
  'Center for Studies on Economic Development (CEDE) — Universidad de los Andes',
  'Pathways Beyond Neoliberalism — American University in Cairo',
  'New Political Economy Initiative (NPEI) — IIT Bombay',
  'Program for the Economic Analysis of Mexico — El Colegio de México',
  'Southern Centre for Inequality Studies (SCIS) — University of the Witwatersrand',
  'Reimagining Cohesive Capitalism — LSE (STICERD)',
  'Institute for Innovation and Public Purpose (IIPP) — UCL',
  'Columbia Center for Political Economy — Columbia University',
  'Reimagining the Economy Initiative — Harvard Kennedy School',
  'Center for Equitable Economy and Sustainable Society — Howard University',
  'Center on Economy and Society (CES) — Johns Hopkins University',
  'Work of the Future — MIT',
  'Emergent Political Economies — Santa Fe Institute',
  'Berkeley Economy and Society Initiative (BESI) — UC Berkeley',
  'Center for Critical Imagination — University of Campinas (Unicamp)',
  'Other / Independent'
];

var YEAR_OPTIONS = (function() {
  var years = [];
  for (var y = 1970; y <= 2025; y++) years.push(String(y));
  years.push('Before 1970');
  return years;
})();


// ── Topic section helper: checkbox list + free-text overflow ───────────────

function addTopicSection(form, sectionTitle, sectionHelp, checkLabel, checkHelp, textLabel, textHelp, isRequired) {
  form.addSectionHeaderItem()
    .setTitle(sectionTitle)
    .setHelpText(sectionHelp);

  form.addCheckboxItem()
    .setTitle(checkLabel)
    .setRequired(isRequired || false)
    .setHelpText(checkHelp)
    .setChoiceValues(EPE_TOPIC_OPTIONS);

  form.addParagraphTextItem()
    .setTitle(textLabel)
    .setRequired(false)
    .setHelpText(textHelp);
}


// ═══════════════════════════════════════════════════════════════════════════
//  MAIN — creates both forms and logs the URLs
// ═══════════════════════════════════════════════════════════════════════════

function createEPEForms() {

  // ─────────────────────────────────────────────────────────────────────────
  //  FORM 1 — CENTER REGISTRATION
  // ─────────────────────────────────────────────────────────────────────────

  var cf = FormApp.create('EPE Network — Center Registration');
  cf.setDescription(
    'Register your research center with the Emerging Political Economy (EPE) Network. ' +
    'One submission per center; filled out by the director or designated administrator. ' +
    'You may resubmit at any time to update your information.'
  );
  cf.setConfirmationMessage(
    'Thank you! Your center registration has been received. ' +
    'The EPE Network team will add your center to the directory soon.'
  );
  cf.setShowLinkToRespondAgain(true);
  cf.setLimitOneResponsePerUser(false);

  /* ── SECTION: Basic Information ────────────────────────────────────── */
  cf.addSectionHeaderItem()
    .setTitle('Center Information');

  cf.addTextItem()
    .setTitle('Center Name')
    .setRequired(true)
    .setHelpText('Official name of your center. Used as the unique key for deduplication.');

  cf.addTextItem()
    .setTitle('Institution / University')
    .setRequired(true);

  cf.addTextItem()
    .setTitle('City')
    .setRequired(true);

  cf.addTextItem()
    .setTitle('State / Province (if applicable)')
    .setRequired(false)
    .setHelpText('US centers: use abbreviation e.g. "MD", "NY", "MA". Leave blank otherwise.');

  cf.addListItem()
    .setTitle('Country')
    .setRequired(true)
    .setChoiceValues(COUNTRY_OPTIONS);

  cf.addTextItem()
    .setTitle('Country (if "Other" above)')
    .setRequired(false)
    .setHelpText('Fill in only if you selected "Other" for Country.');

  cf.addListItem()
    .setTitle('Region')
    .setRequired(true)
    .setHelpText('Select the primary geographic region your center operates in.')
    .setChoiceValues(REGION_OPTIONS);

  cf.addTextItem()
    .setTitle('Website URL')
    .setRequired(false)
    .setHelpText('Full URL including https://, e.g. https://ces.jhu.edu');

  cf.addTextItem()
    .setTitle('Logo Image URL (optional)')
    .setRequired(false)
    .setHelpText('Direct link to a .png or .svg logo. Leave blank to use an initials badge on the site.');

  /* ── SECTION: Contact ───────────────────────────────────────────────── */
  cf.addSectionHeaderItem()
    .setTitle('Director & Contact');

  cf.addTextItem()
    .setTitle('Director / Primary Contact Name')
    .setRequired(true);

  cf.addTextItem()
    .setTitle('Contact Email')
    .setRequired(true)
    .setHelpText('Shown in the directory for network correspondence.');

  cf.addListItem()
    .setTitle('Year Established')
    .setRequired(false)
    .setChoiceValues(YEAR_OPTIONS);

  /* ── SECTION: Current Research Topics ─────────────────────────────── */
  cf.addSectionHeaderItem()
    .setTitle('Current Research Topics')
    .setHelpText('Topics your center actively researches right now.');

  cf.addCheckboxItem()
    .setTitle('Select all that apply')
    .setRequired(false)
    .setChoiceValues(EPE_TOPIC_OPTIONS);

  cf.addParagraphTextItem()
    .setTitle('Additional current topics not listed above')
    .setRequired(false)
    .setHelpText('Comma- or semicolon-separated.');

  /* ── SECTION: Anticipated Research Topics ──────────────────────────── */
  cf.addSectionHeaderItem()
    .setTitle('Anticipated Research Topics')
    .setHelpText('Topics you expect to move toward in the near future.');

  cf.addCheckboxItem()
    .setTitle('Select all that apply')
    .setRequired(false)
    .setChoiceValues(EPE_TOPIC_OPTIONS);

  cf.addParagraphTextItem()
    .setTitle('Additional anticipated topics not listed above')
    .setRequired(false)
    .setHelpText('Comma- or semicolon-separated.');

  /* ── SECTION: Topics You Would Like to Work On ─────────────────────── */
  cf.addSectionHeaderItem()
    .setTitle('Topics You Would Like to Work On')
    .setHelpText('Aspirational or collaborative interests — topics you\'d like to explore, even if not yet active.');

  cf.addCheckboxItem()
    .setTitle('Select all that apply')
    .setRequired(false)
    .setChoiceValues(EPE_TOPIC_OPTIONS);

  cf.addParagraphTextItem()
    .setTitle('Additional "would like" topics not listed above')
    .setRequired(false)
    .setHelpText('Comma- or semicolon-separated.');

  /* ── SECTION: Center Profile ────────────────────────────────────────── */
  cf.addSectionHeaderItem()
    .setTitle('Center Profile');

  cf.addParagraphTextItem()
    .setTitle('Thematic Focus Areas (general profile)')
    .setRequired(false)
    .setHelpText('Broad description of your center\'s research identity. Comma-separated phrases are fine.');

  cf.addParagraphTextItem()
    .setTitle('Current Research Projects')
    .setRequired(false)
    .setHelpText('1–3 sentences describing your most active current work.');

  cf.addParagraphTextItem()
    .setTitle('Funding Sources')
    .setRequired(false)
    .setHelpText('e.g. "NSF, Ford Foundation, university endowment"');

  /* ── SECTION: Network Collaboration ────────────────────────────────── */
  cf.addSectionHeaderItem()
    .setTitle('Network Collaboration');

  cf.addParagraphTextItem()
    .setTitle('Organizational Challenges / Problems')
    .setRequired(false)
    .setHelpText('Funding gaps, political constraints, capacity limitations, methodological challenges, etc.');

  cf.addParagraphTextItem()
    .setTitle('Opportunities (offering or seeking)')
    .setRequired(false)
    .setHelpText('e.g. "seeking comparative partners on platform labor", "offering visiting fellowship"');

  cf.addParagraphTextItem()
    .setTitle('Connected External Networks & Meetings')
    .setRequired(false)
    .setHelpText('Other networks your center participates in, comma-separated. e.g. "SASE, CLACSO, ISA"');

  cf.addParagraphTextItem()
    .setTitle('Anything else you would like to share')
    .setRequired(false);

  /* ── Link to Sheet ──────────────────────────────────────────────────── */
  var centerSheet = SpreadsheetApp.create('EPE Network — Center Registration Responses');
  cf.setDestination(FormApp.DestinationType.SPREADSHEET, centerSheet.getId());


  // ─────────────────────────────────────────────────────────────────────────
  //  FORM 2 — SCHOLAR REGISTRATION
  // ─────────────────────────────────────────────────────────────────────────

  var sf = FormApp.create('EPE Network — Scholar Registration');
  sf.setDescription(
    'Register as a scholar with the Emerging Political Economy (EPE) Network. ' +
    'Add your research profile and affiliation to connect with colleagues across the network. ' +
    'You may resubmit at any time to update your profile.'
  );
  sf.setConfirmationMessage(
    'Thank you! Your scholar profile has been received. ' +
    'You will appear in the EPE Network directory soon.'
  );
  sf.setShowLinkToRespondAgain(true);
  sf.setLimitOneResponsePerUser(false);

  /* ── SECTION: Basic Information ────────────────────────────────────── */
  sf.addSectionHeaderItem()
    .setTitle('Personal Information');

  sf.addTextItem()
    .setTitle('Full Name')
    .setRequired(true);

  sf.addTextItem()
    .setTitle('Title / Position')
    .setRequired(false)
    .setHelpText('e.g. "Associate Professor", "Postdoctoral Fellow", "Research Director"');

  sf.addListItem()
    .setTitle('Center Affiliation')
    .setRequired(true)
    .setHelpText('Select your primary EPE Network center. If your center is not listed, choose "Other / Independent".')
    .setChoiceValues(CENTER_NAMES);

  sf.addTextItem()
    .setTitle('Institution')
    .setRequired(true)
    .setHelpText('Your university or research institution.');

  sf.addListItem()
    .setTitle('Country')
    .setRequired(true)
    .setHelpText('Your current location.')
    .setChoiceValues(COUNTRY_OPTIONS);

  sf.addTextItem()
    .setTitle('Country (if "Other" above)')
    .setRequired(false)
    .setHelpText('Fill in only if you selected "Other" for Country.');

  sf.addTextItem()
    .setTitle('Email')
    .setRequired(true)
    .setHelpText('Used as the unique key for deduplication. Your email will not be publicly displayed on the site.');

  sf.addTextItem()
    .setTitle('Personal / Academic Website')
    .setRequired(false)
    .setHelpText('Full URL including https://');

  /* ── SECTION: Current Research Topics ─────────────────────────────── */
  sf.addSectionHeaderItem()
    .setTitle('Current Research Topics')
    .setHelpText('Topics you actively research right now.');

  sf.addCheckboxItem()
    .setTitle('Select all that apply')
    .setRequired(true)
    .setChoiceValues(EPE_TOPIC_OPTIONS);

  sf.addParagraphTextItem()
    .setTitle('Additional current topics not listed above')
    .setRequired(false)
    .setHelpText('Comma- or semicolon-separated.');

  /* ── SECTION: Anticipated Research Topics ──────────────────────────── */
  sf.addSectionHeaderItem()
    .setTitle('Anticipated Research Topics')
    .setHelpText('Topics you expect to move toward in the near future.');

  sf.addCheckboxItem()
    .setTitle('Select all that apply')
    .setRequired(false)
    .setChoiceValues(EPE_TOPIC_OPTIONS);

  sf.addParagraphTextItem()
    .setTitle('Additional anticipated topics not listed above')
    .setRequired(false)
    .setHelpText('Comma- or semicolon-separated.');

  /* ── SECTION: Topics You Would Like to Work On ─────────────────────── */
  sf.addSectionHeaderItem()
    .setTitle('Topics You Would Like to Work On')
    .setHelpText('Aspirational or collaborative interests — topics you\'d want to explore with partners.');

  sf.addCheckboxItem()
    .setTitle('Select all that apply')
    .setRequired(false)
    .setChoiceValues(EPE_TOPIC_OPTIONS);

  sf.addParagraphTextItem()
    .setTitle('Additional "would like" topics not listed above')
    .setRequired(false)
    .setHelpText('Comma- or semicolon-separated.');

  /* ── SECTION: Teaching ──────────────────────────────────────────────── */
  sf.addSectionHeaderItem()
    .setTitle('Teaching');

  sf.addCheckboxItem()
    .setTitle('Teaching – Regional Focus')
    .setRequired(false)
    .setHelpText('Select all regions you primarily teach about.')
    .setChoiceValues(REGION_OPTIONS.concat(['I do not teach']));

  sf.addCheckboxItem()
    .setTitle('Teaching – Level')
    .setRequired(false)
    .setChoiceValues(['Undergraduate', 'Graduate', 'Executive education', 'Other']);

  /* ── SECTION: Network Collaboration ────────────────────────────────── */
  sf.addSectionHeaderItem()
    .setTitle('Network Collaboration');

  sf.addParagraphTextItem()
    .setTitle('Connected External Networks & Meetings')
    .setRequired(false)
    .setHelpText('Other networks you participate in beyond EPE. Comma-separated.');

  sf.addParagraphTextItem()
    .setTitle('Problems (research, funding, organizational)')
    .setRequired(false)
    .setHelpText('Open field — share any challenges you\'re navigating.');

  sf.addParagraphTextItem()
    .setTitle('Opportunities (offering or seeking)')
    .setRequired(false)
    .setHelpText('Collaborations you\'re looking for, fellowships you offer, data you can share, etc.');

  sf.addParagraphTextItem()
    .setTitle('Anything else you would like to share')
    .setRequired(false);

  /* ── Link to Sheet ──────────────────────────────────────────────────── */
  var scholarSheet = SpreadsheetApp.create('EPE Network — Scholar Registration Responses');
  sf.setDestination(FormApp.DestinationType.SPREADSHEET, scholarSheet.getId());


  // ─────────────────────────────────────────────────────────────────────────
  //  OUTPUT URLS
  // ─────────────────────────────────────────────────────────────────────────

  Logger.log('');
  Logger.log('════════════════════════════════════════════════════');
  Logger.log('  EPE NETWORK FORMS CREATED SUCCESSFULLY');
  Logger.log('════════════════════════════════════════════════════');
  Logger.log('');
  Logger.log('CENTER FORM');
  Logger.log('  Edit:       ' + cf.getEditUrl());
  Logger.log('  Share URL:  ' + cf.getPublishedUrl());
  Logger.log('  Sheet:      ' + centerSheet.getUrl());
  Logger.log('');
  Logger.log('SCHOLAR FORM');
  Logger.log('  Edit:       ' + sf.getEditUrl());
  Logger.log('  Share URL:  ' + sf.getPublishedUrl());
  Logger.log('  Sheet:      ' + scholarSheet.getUrl());
  Logger.log('');
  Logger.log('════════════════════════════════════════════════════');
  Logger.log('UPDATE THESE THREE FILES with the Share URLs above:');
  Logger.log('');
  Logger.log('1.  js/app.js  (first 2 lines):');
  Logger.log('      FORM_URL_CENTER     = "<center share URL>"');
  Logger.log('      FORM_URL_INDIVIDUAL = "<scholar share URL>"');
  Logger.log('');
  Logger.log('2.  register.html  (inline <script>, ~line 268):');
  Logger.log('      CENTER_FORM_URL     = "<center share URL>"');
  Logger.log('      INDIVIDUAL_FORM_URL = "<scholar share URL>"');
  Logger.log('');
  Logger.log('3.  index.html  (hero-actions section):');
  Logger.log('      href="https://forms.gle/REPLACE_CENTER_FORM"');
  Logger.log('      href="https://forms.gle/REPLACE_INDIVIDUAL_FORM"');
  Logger.log('════════════════════════════════════════════════════');
}
