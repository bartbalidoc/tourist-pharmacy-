// Central site constants — single source of truth for brand, contact and compliance data.
// Reused across Nav, Footer, About, Booking and product pages.

export const SITE = {
  name: 'Tourist Pharmacy',
  tagline: 'Your English-speaking pharmacy in Bali',
  domain: 'touristpharmacy.com',
  url: 'https://touristpharmacy.com',
  description:
    'A licensed, BPOM-compliant online pharmacy catalog for English-speaking tourists and ' +
    'expats in Bali. Browse medicines, consult a licensed doctor, and get your prescription ' +
    'dispensed by a trusted Bali pharmacy.',
};

// WhatsApp — must appear on every page (nav + sticky/footer).
export const WHATSAPP = {
  display: '+62 895-1802-3363',
  number: '6289518023363',
  link: 'https://wa.me/6289518023363',
  message: "Hi Tourist Pharmacy, I'd like some help with a medication.",
};

export function waLink(prefilled?: string): string {
  const text = encodeURIComponent(prefilled ?? WHATSAPP.message);
  return `${WHATSAPP.link}?text=${text}`;
}

export const CONSULT_PRICE_USD = 25;

// --- Compliance data (About page) -------------------------------------------
// Values in [BRACKETS] are TODO placeholders the operator will provide.
export const PHARMACY = {
  name: 'Apotek Pharmacare Sidakarya (PharmaCare)',
  address:
    'Jl. Sidakarya No.92, Sidakarya, Denpasar Selatan, Kota Denpasar, Bali 80224',
  license: '25032400306790002', // Izin Apotek No.
  licenseAuthority: 'DPMPTSP Kota Denpasar',
  // Approximate — geocoded from the address (OpenStreetMap). TODO: operator to confirm the
  // exact storefront coordinate. The map pins by business name+address for accuracy regardless.
  gpsCoordinates: '-8.7087864, 115.2376373',
  gpsApproximate: true,
};

export const PHARMACIST = {
  name: 'apt. Ayu Pradnya Paramita, S.Farm',
  str: 'YZ00001647709423', // STR valid for life (Seumur Hidup)
  sipa: '570/SIPA/0025/III/DPMPTSP/2025', // from SIPA certificate (DPMPTSP Kota Denpasar, 10 Mar 2025)
  schedule: '[PHARMACIST_SCHEDULE]', // TODO: replace — e.g. Mon–Sat, 08:00–20:00 WITA (not in the SIPA doc)
};

export const OPERATOR = {
  name: 'PT Sehat Investasi Digital',
  nib: '0609230031427',
  office: 'Jakarta, Indonesia', // TODO: replace with full Jakarta office address from current site
  runs: 'BaliDoc and Tourist Pharmacy',
};

// BaliDoc — the operator's established English-speaking telehealth service (the licensed
// doctors behind the consultations). Used as the trust anchor: "In association with BaliDoc".
export const BALIDOC = {
  name: 'BaliDoc',
  url: 'https://balidoc.com',
  tagline: "Bali's English-speaking telehealth",
  logo: '', // TODO: add a BaliDoc logo path (e.g. '/balidoc.svg'); text used until then
};

// Controlled / psychiatric medicines: classified in products.json (controlled:true) and
// labelled "specialist consultation required". Flip this to hide them site-wide at any time.
export const HIDE_CONTROLLED = false;

// --- Review / feedback mode --------------------------------------------------
// REVIEW_MODE shows the floating feedback widget (for the private review deployment).
// Set false for the public production build. FEEDBACK_ENDPOINT is the serverless
// function that AI-structures the note + commits it to the repo's feedback/ folder.
export const REVIEW_MODE = true;
export const FEEDBACK_ENDPOINT = '/api/feedback'; // served by server.mjs on the droplet

// --- Third-party placeholders ------------------------------------------------
export const CALENDLY_URL = '[CALENDLY_URL]'; // TODO: replace — operator's BaliDoc Calendly link

// Currency API — exchangerate-api.com free tier.
export const CURRENCY_API_KEY = '5b56fb3710d8d03b7853a02a';
export const CURRENCY_ENDPOINT = `https://v6.exchangerate-api.com/v6/${CURRENCY_API_KEY}/latest/IDR`;

export const NAV_LINKS = [
  { href: '/products', label: 'Products' },
  { href: '/booking', label: 'How it works' },
  { href: '/about', label: 'About' },
];

// =============================================================================
// MARKET CONFIG — everything market-specific lives here so the site can be
// replicated to another country by swapping this block (light replication-readiness).
// =============================================================================
export const MARKET = {
  country: 'Indonesia (Bali)',
  regulator: 'BPOM',
  regNumberLabel: 'NIE (BPOM marketing authorization)',
  currency: 'IDR',
  // CRO: concrete speed promise. TODO: confirm real dispensing turnaround with operator.
  deliveryPromise: 'Delivered across Bali, often same-day',
  deliveryEtaHours: '[X]', // TODO: real turnaround, e.g. "2"
  // Prescription-upload submit handler. Default: WhatsApp (send photo). Set a form endpoint
  // (Netlify Forms / Formspree / BaliDoc backend) to accept real file uploads.
  uploadEndpoint: '', // TODO: e.g. 'https://formspree.io/f/xxxx' — empty = WhatsApp fallback
};

// Condition tiles — curate the raw product `Type` values into intuitive, plain-English
// groups Westerners recognise. Each tile deep-links to the catalog filtered to its types.
export interface CategoryGroup { slug: string; label: string; icon: string; types: string[]; }
export const CATEGORY_GROUPS: CategoryGroup[] = [
  { slug: 'infection',   label: 'Infection & Antibiotics', icon: 'shield-check', types: ['Infection'] },
  { slug: 'pain',        label: 'Pain, Fever & Joints',    icon: 'thermometer',  types: ['Fever & Pain', 'Bone & Joint Pain', 'Bones & Joints'] },
  { slug: 'skin',        label: 'Skin',                    icon: 'droplet',      types: ['Skin Conditions'] },
  { slug: 'digestion',   label: 'Stomach & Digestion',     icon: 'leaf',         types: ['Digestive Problems'] },
  { slug: 'allergy',     label: 'Allergy & Asthma',        icon: 'wind',         types: ['Allergy', 'Asthma', 'Inhalers'] },
  { slug: 'diabetes',    label: 'Diabetes',                icon: 'droplet',      types: ['Diabetes', 'Insulin'] },
  { slug: 'ent',         label: 'Eyes, Ear, Nose & Throat',icon: 'eye',          types: ['Eye Problems', 'ENT problems'] },
  { slug: 'women',       label: "Women's Health",          icon: 'venus',        types: ['Female Hormones', 'Oral Contraception', 'Fertility & More', 'Woman'] },
  { slug: 'men',         label: "Men's Health",            icon: 'mars',         types: ['Erectile Dysfunction'] },
  { slug: 'everyday',    label: 'Everyday & Supplements',  icon: 'sun',          types: ['For Everyday', 'Health & Immune', 'Self Care', 'Medicines & Supplements', 'Special Supplements'] },
  { slug: 'specialist',  label: 'Specialist Care',         icon: 'stethoscope',  types: ['Cancer Medicine', 'Immunosuppressant Drugs'] },
  { slug: 'general',     label: 'General Medicines',       icon: 'pill',         types: ['Drug', 'Other Medications', 'Mature'] },
];
export function groupForType(type: string): CategoryGroup | undefined {
  return CATEGORY_GROUPS.find((g) => g.types.includes(type));
}

// Trust badges (CRO: shown beside CTAs and in a strip). Plain-English, scannable.
export const TRUST_BADGES = [
  { icon: 'shield-check', label: 'Licensed & BPOM-compliant', sub: 'Every medicine registered & regulated' },
  { icon: 'stethoscope',  label: 'Real licensed doctors',     sub: 'Prescriptions issued, never guessed' },
  { icon: 'heart-pulse',  label: 'Named pharmacist',          sub: 'Accountable, not anonymous' },
  { icon: 'truck',        label: 'Local Bali delivery',       sub: 'Pickup or delivery on the island' },
];

// Social proof. CRO: reviews lift conversion a lot — but use REAL ones.
// TODO: replace these SAMPLES with real, verifiable testimonials before launch (no fake 5.0★).
export const TESTIMONIALS = [
  { quote: 'Got sick on holiday and had no idea where to turn. They sorted my prescription and delivered to my villa the same day.', name: 'Sarah M.', location: 'Australia · visiting Canggu', rating: 5 },
  { quote: 'As an expat I rely on a regular medication. Uploaded my prescription, a pharmacist checked it, and it arrived fast. So easy.', name: 'Daniel R.', location: 'UK · living in Sanur', rating: 5 },
  { quote: 'English-speaking and actually responsive on WhatsApp. Felt safe the whole way through.', name: 'Lena K.', location: 'Germany · visiting Ubud', rating: 4 },
];
export const TESTIMONIALS_ARE_SAMPLES = true; // TODO: set false once real reviews are in

