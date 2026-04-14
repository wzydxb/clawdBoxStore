# Patent Drafting — Patterns

## Golden Rules

| Rule | Reason |
|------|--------|
| Claim first, then spec | Claims define what you protect; spec must support the claims, not the other way around |
| One chance for specification | Can't add new matter after filing (35 USC 132); disclose everything upfront |
| Antecedent basis required | Every "the [noun]" must have a prior "a [noun]" — no exceptions |
| Means-plus-function = narrow | Triggers 112(f); tied to spec embodiments + equivalents only |
| Dependent claims = fallback | If independent claim fails prosecution or litigation, dependents may survive |
| Broadest first | Draft the widest defensible claim, then narrow in dependents |
| Multiple embodiments | Describe 2–3 alternatives per key feature; single embodiment = narrow claim scope |

---

## Application Structure

### Required Sections (USPTO)

| Section | Content | Notes |
|---------|---------|-------|
| Title | Concise, descriptive (≤500 chars) | Avoid trademarked terms |
| Abstract | 150-word summary of the invention | Written last; one paragraph |
| Background | Prior art limitations and problem to be solved | Don't admit prior art you don't need to |
| Summary | Brief overview of the invention and advantages | Echo broadest claim in plain language |
| Brief Description of Drawings | List of figures with short description | Required if drawings included |
| Detailed Description | Full enabling disclosure; all embodiments | Must enable "one of ordinary skill in the art" |
| Claims | Legal scope of protection | Drafted first; numbered sequentially |

### Detailed Description — Must Include
- Reference numerals for every element shown in drawings
- At least one working example (best mode preferred)
- Alternative embodiments for every major feature: `"In some embodiments... In other embodiments..."`
- Definition of any non-standard technical terms used in claims
- Explicit support for every limitation in every claim

---

## Claim Categories

### Method Claim
```
A method of [verb + object], the method comprising:
  [gerund phrase — step 1];
  [gerund phrase — step 2]; and
  [gerund phrase — step 3].
```
**Covers:** The process itself. Anyone practicing the steps infringes regardless of implementation.

### System Claim
```
A system comprising:
  a [component A] configured to [function];
  a [component B] coupled to the [component A], the [component B]
    configured to [function based on output of A]; and
  a [component C] configured to [final function].
```
**Covers:** The product/device. Requires all recited components to be present simultaneously.

### Apparatus Claim
```
An apparatus for [purpose], comprising:
  a [physical element] having [property];
  a [second element] connected to the [physical element].
```
**Use when:** The invention is a physical device distinct from a computing system.

### CRM Claim (Computer-Readable Medium)
```
A non-transitory computer-readable medium storing instructions that,
when executed by a processor, cause the processor to:
  [verb phrase — instruction 1];
  [verb phrase — instruction 2]; and
  [verb phrase — instruction 3].
```
**Always include for software inventions.** Covers distribution of the software itself.
**"Non-transitory"** is required to exclude transient signals (Nuijten rejection).

### Product-by-Process Claim
```
A [product] produced by a process comprising:
  [step 1]; and
  [step 2].
```
**Use when:** The product is only distinguishable by how it's made.

---

## Transitional Phrases

| Phrase | Type | Effect | When to Use |
|--------|------|--------|-------------|
| `comprising` | Open | Additional unlisted elements allowed | Default choice — always preferred |
| `consisting of` | Closed | No additional elements permitted | Chemical compositions; exact formulations |
| `consisting essentially of` | Partially open | Only non-material additions allowed | Rare; pharma/materials |
| `including` | Open | Similar to comprising | Informal; avoid in claims |
| `having` | Ambiguous | Jurisdiction-dependent | Avoid; use comprising instead |

---

## Claim Scope Strategy — Pyramid Structure

```
Independent Claim 1
│   Broadest — captures the core concept with minimal limitations
│   Goal: Cover competitors who implement differently
│
├── Dependent Claim 2
│     Adds ONE specific limitation (preferred method, specific range, etc.)
│     Fallback if Claim 1 is rejected for obviousness
│
├── Dependent Claim 3
│     Adds ANOTHER specific limitation
│     Fallback if Claims 1–2 fail
│
├── Dependent Claim 4
│     Preferred embodiment — exactly how you build it
│     Last line of defense
│
└── Dependent Claim 5
      Alternative embodiment — variation not covered by Claims 2–4
      Blocks design-arounds
```

**Rule of thumb:** 3–5 dependents per independent claim minimum. For high-value inventions, 8–12.

---

## Patentability Tests

### Novelty — 35 USC 102
- **Test:** ALL elements of the claim must appear in a SINGLE prior art reference to be anticipated
- **Strategy:** If a prior art reference has 9 of 10 elements, the claim is novel — protect that 10th element
- **Watch out for:** Public use, on-sale bar, prior filed applications

### Non-Obviousness — 35 USC 103
- **Test:** Would the combination of references be obvious to a person of ordinary skill in the art (POSITA)?
- **Examiner must show:** Each element in a reference + motivation to combine
- **Counter-arguments:**
  - Unexpected results (surprising synergy)
  - Teaching away (references suggest NOT combining)
  - Long-felt need solved
  - Commercial success (secondary considerations)

### Patent Eligibility — 35 USC 101 (Alice/Mayo Two-Step)
- **Step 1:** Is the claim directed to an abstract idea / law of nature / natural phenomenon?
- **Step 2A Prong 1:** Does the claim integrate into a practical application?
- **Step 2A Prong 2:** Does it add "significantly more" than the abstract idea?
- **Safe strategies:**
  - Claim specific technical architecture (not just functional results)
  - Claim measurable technical improvements ("reduces latency by X%")
  - Anchor to specific hardware or real-world data

### Enablement — 35 USC 112(a)
- **Test:** Can a POSITA make and use the full scope of the claimed invention based on the spec?
- **Risk:** Broad claim + narrow spec = enablement rejection
- **Fix:** Describe multiple embodiments; use "such as" and "including but not limited to"

---

## Office Action Response Patterns

### Responding to 102 Anticipation Rejection
1. Find the element missing from the cited reference
2. Argue the reference does not disclose that element
3. If needed, amend claim to add that missing element as a limitation
4. Never argue what the reference "teaches" — argue what it literally discloses

### Responding to 103 Obviousness Rejection
1. Challenge the motivation to combine: "The references teach away from combination because..."
2. Argue unexpected results with evidence (test data, declarations)
3. Amend to add a non-obvious limitation not suggested by any reference
4. File a 1.132 declaration from inventor/expert if needed

### Responding to 101 Abstract Idea Rejection
1. Step 2A Prong 1: Argue the claim is directed to a specific technical improvement, not an abstract idea
2. Step 2A Prong 2: Point to unconventional technical steps that add "significantly more"
3. Amend to add specific technical implementation details
4. Cite *Enfish* (self-referential table), *McRO* (specific rules), *Berkheimer* (factual issues)

### Responding to 112(b) Indefiniteness Rejection
1. Provide specification support for the disputed term
2. Amend claim to use more precise language
3. Argue the term has a well-understood meaning to a POSITA

---

## Anti-Patterns

| Anti-Pattern | Problem | Solution |
|-------------|---------|---------|
| Too-narrow independent claim | Easy to design around; competitors add one element to avoid | Start broad; narrow only in dependents |
| Missing antecedent basis | 112(b) indefiniteness rejection | Track every `the` — must follow an `a` or `an` |
| `means for [function]` language | 112(f) narrow scope tied to spec embodiments | Use structural language: `a processor configured to...` |
| No dependent claims | No fallback when independent fails | Draft 3–5 dependents per independent |
| Spec too brief | Enablement rejection (112(a)) | Include alternatives and examples per key feature |
| Jargon without definition | 112(b) indefiniteness | Define all non-standard technical terms in spec |
| Claiming only the result | Alice 101 rejection | Claim specific technical means, not just the goal |
| Single embodiment in spec | Claims construed narrowly | Describe 2–3 alternative embodiments per feature |
| Admitting prior art unnecessarily | Limits claim scope; creates prosecution history estoppel | Say "prior approaches" not "prior art" in background |
