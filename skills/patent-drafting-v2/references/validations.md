# Patent Drafting — Validations

Run these checks on every claim set and specification before finalizing.
Severity: **error** = must fix before filing | **warning** = fix strongly recommended | **info** = consider

---

## CLAIM VALIDATIONS

### [ERROR] Means-Plus-Function Language Detected

**ID:** `means-plus-function`
**Trigger patterns:**
- `means for \w+`
- `module for \w+`
- `mechanism for \w+`
- `element for \w+ing`
- `unit for \w+ing`

**Message:** Means-plus-function language triggers 35 USC 112(f) narrow interpretation. Claim scope is limited to spec embodiments + equivalents only.

**Fix:** Replace with structural language:
```
BAD:  "means for processing"
GOOD: "a processor configured to process..."

BAD:  "module for detecting"
GOOD: "a detection circuit configured to detect..."
```

---

### [ERROR] Missing Antecedent Basis

**ID:** `missing-antecedent`
**Trigger patterns:**
- `the \w+` where no prior `a \w+` or `an \w+` exists for that noun in the same claim
- `said \w+` where the noun was not previously introduced

**Message:** `the [noun]` or `said [noun]` references a term that was never introduced. This causes a 35 USC 112(b) indefiniteness rejection.

**Fix:**
```
WRONG: "A method comprising: processing the data..."
RIGHT: "A method comprising:
          receiving a data set;
          processing the data set..."
```

**Manual check:** For every `the [noun]` in the claim, find `a [noun]` earlier in the same claim. If missing, add it.

---

### [WARNING] Closed Transitional Phrase

**ID:** `consisting-of-closed`
**Trigger patterns:**
- `consisting of`

**Message:** `consisting of` is a closed transitional phrase — it excludes any unlisted elements. A product with one additional ingredient will not infringe.

**Fix:** Use `comprising` unless closure is intentional (e.g., exact chemical composition claims).

---

### [WARNING] No CRM Claim for Software Invention

**ID:** `no-crm-claim`
**Trigger:** Method claim present with no corresponding `non-transitory computer-readable medium` claim.

**Message:** Software inventions should include a CRM claim to cover distribution of the software product itself. Without it, someone who sells the software (but doesn't execute it) may not infringe the method claim.

**Fix:**
```
Add: "A non-transitory computer-readable medium storing instructions
      that, when executed by a processor, cause the processor to:
        [mirror the method steps]."
```

---

### [WARNING] Generic Computer Implementation — 101 Risk

**ID:** `abstract-generic-computer`
**Trigger patterns:**
- `a computer performing`
- `a processor executing`
- `implemented on a general purpose computer`
- `using a computer to`

**Message:** Generic computer implementation does not satisfy Alice Step 2B. Claim will likely receive 101 rejection as an abstract idea.

**Fix:** Add specific technical improvement, unconventional architecture, or measurable result:
```
WEAK:  "a processor executing the instructions"
BETTER: "a processor configured to apply a convolutional neural
         network to classify the input data within 10 milliseconds,
         thereby reducing classification latency by at least 50%
         compared to sequential processing"
```

---

### [WARNING] No System Claim

**ID:** `no-system-claim`
**Trigger:** Method claim present with no corresponding system claim.

**Message:** Method claims cover only the process. A party that makes or sells the system implementing the method may not infringe without a system claim. For software inventions, draft both.

**Fix:** Add a system claim that mirrors the method claim structure:
```
"A system comprising:
   a [component] configured to [perform step 1];
   a [component] configured to [perform step 2]."
```

---

### [WARNING] Fewer Than 3 Dependent Claims Per Independent Claim

**ID:** `insufficient-dependent-claims`
**Trigger:** Independent claim with 0–2 dependent claims.

**Message:** Insufficient fallback protection. If the independent claim is invalidated or rejected, there are no narrower claims to fall back on.

**Fix:** Add at least 3 dependent claims per independent claim. Each should add one specific limitation. For high-value inventions, target 5–8.

---

### [WARNING] Preamble May Limit Claim Scope

**ID:** `limiting-preamble`
**Trigger patterns:**
- Preamble states a purpose or use that is referred back to in the body of the claim

**Message:** A preamble that is referred to in the claim body (e.g., "the [noun from preamble]") becomes a claim limitation. This may narrow scope unintentionally.

**Fix:** Keep the preamble to a simple category statement ("A method...", "A system..."). Move functional purpose into the claim body if it needs to be a limitation.

---

## SPECIFICATION VALIDATIONS

### [ERROR] Claim Element Without Specification Support

**ID:** `claim-element-not-supported`
**Check:** For every limitation in every claim, verify there is explicit disclosure in the detailed description.

**Message:** A claim element with no specification support will face 112(a) enablement rejection or 112(b) written description rejection during prosecution, and may be invalidated in litigation.

**Fix:** Before finalizing, go through every claim word-by-word and locate its corresponding disclosure in the spec. Add disclosure for anything missing.

---

### [ERROR] Single Embodiment Only

**ID:** `single-embodiment-spec`
**Check:** Does the spec describe at least 2 different ways to implement each key claimed feature?

**Message:** A specification with only one embodiment causes broad claim language to be construed narrowly to match that single embodiment. Competitors can design around by using any alternative implementation.

**Fix:**
```
"In one embodiment, [feature A is implemented as X].
 In another embodiment, [feature A may be implemented as Y or Z].
 In some embodiments, [feature A] may include, but is not limited to, [list]."
```

---

### [WARNING] Abstract Exceeds 150 Words

**ID:** `abstract-too-long`
**Check:** Abstract word count.

**Message:** USPTO requires the abstract to be a single paragraph of 150 words or fewer (37 CFR 1.72(b)). Excessively long abstracts are objected to.

**Fix:** Trim to one paragraph covering: what the invention is, key technical feature, and primary advantage.

---

### [WARNING] Technical Terms Used in Claims Not Defined in Spec

**ID:** `undefined-technical-terms`
**Check:** Every non-standard technical term or term of art in the claims should have a definition in the spec.

**Message:** Undefined terms can lead to 112(b) indefiniteness rejections, especially if the term has multiple meanings in the art.

**Fix:** Add to the spec:
```
"As used herein, '[term]' refers to [precise definition]."
```

---

### [WARNING] Best Mode Not Described

**ID:** `best-mode-missing`
**Check:** Does the detailed description describe the inventor's preferred embodiment?

**Message:** While post-AIA failure to disclose best mode is no longer grounds for invalidity, it remains a disclosure requirement (35 USC 112(a)) and affects prosecution credibility.

**Fix:** Include a section explicitly describing the preferred embodiment: "In a preferred embodiment..."

---

### [INFO] No Drawings for Complex Mechanical/System Invention

**ID:** `no-drawings`
**Trigger:** Application describes a system with multiple components but no figures.

**Message:** Drawings are not required but strongly recommended for mechanical, hardware, and system inventions. They help establish reference numerals and support the detailed description.

**Fix:** Add at least: (1) a block diagram showing system components, (2) a flowchart for method claims.

---

## JURISDICTION-SPECIFIC VALIDATIONS

### [WARNING — CNIPA] Software Claim Lacks Technical Character

**ID:** `cnipa-no-technical-character`
**Applies to:** Claims targeting CNIPA (China) filing
**Trigger:** Software/AI/business method claim with no explicit technical feature

**Message:** CNIPA requires claims to have "technical character" (技术特征) producing a "technical effect" (技术效果). Pure algorithm or business logic claims will be rejected under CN Patent Law Article 25.

**Fix:** Frame every claim around the technical problem solved and the technical means used. See `cnipa_guidelines.md` for detailed strategy.

---

### [WARNING — EPO] Two-Part Claim Form Recommended

**ID:** `epo-two-part-form`
**Applies to:** Claims targeting EPO filing
**Trigger:** Independent claim without preamble / characterizing portion structure

**Message:** EPO prefers (and often requires during examination) the two-part claim form: known features in the preamble, novel features in the characterizing portion after "characterized in that."

**Fix:**
```
"A method of [X], the method comprising [known features from prior art],
 characterized in that [novel distinguishing features]."
```

---

### [WARNING — PCT] Priority Chain Verification

**ID:** `pct-priority-chain`
**Applies to:** PCT applications claiming priority to a prior application

**Message:** PCT application must be filed within 12 months of the earliest priority date. Verify the priority claim is correctly stated and the priority document has been filed with the receiving office.

**Fix:** Include: "This application claims priority to [Application No.], filed [Date], the entire contents of which are incorporated herein by reference."
