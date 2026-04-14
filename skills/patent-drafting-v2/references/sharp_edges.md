# Patent Drafting — Sharp Edges

Critical failures, why they happen, and how to fix them.
Severity: **critical** = application-killing | **high** = likely rejection | **medium** = scope loss risk

---

## [CRITICAL] Means-Plus-Function Invokes 35 USC 112(f)

**ID:** `means-plus-function-trap`

**Summary:** `means for [function]` limits claim scope to spec embodiments only.

**Why it happens:**
Using "means for [function]" triggers 112(f). The claim is then limited to the corresponding structure disclosed in the specification, plus its equivalents. If only one implementation is described, that's all the claim covers — a competitor using a different implementation won't infringe.

**Gotcha:**
```
Claim:  "means for processing data"
Spec:   "Processing module 102 uses algorithm X"
Result: Claim covers ONLY algorithm X and its equivalents.
        Algorithm Y achieving the same result → NOT covered.
```

**Fix:**
```
BAD:  "means for processing data"
GOOD: "a processor configured to execute instructions that cause
       the processor to process the data"

BAD:  "means for storing data"
GOOD: "a memory storing instructions that, when executed, cause
       the processor to store the data in a database"
```
Also include multiple embodiments in the spec for every functional term.

---

## [CRITICAL] New Matter Cannot Be Added After Filing

**ID:** `new-matter-added`

**Summary:** Amendments must be supported by the original specification (35 USC 132).

**Why it happens:**
The specification is frozen at the filing date. Any feature not disclosed on that date cannot be claimed — ever. Continuations don't help because they share the same specification.

**Gotcha:**
```
Original spec:  "The widget processes data using algorithm A."
Later amendment: "...wherein the widget uses machine learning."
Result:         REJECTED — machine learning was never disclosed.
```

**Fix — at drafting time, include:**
- All known embodiments and variations
- Future features you might want to claim
- Open-ended language for flexibility:

```
"In some embodiments, the processing includes machine learning,
 neural networks, statistical models, or rule-based systems."

"The system may use any suitable algorithm, including but not
 limited to gradient descent, decision trees, or transformer models."
```

---

## [HIGH] Missing Antecedent Basis Causes 112(b) Rejection

**ID:** `antecedent-basis-missing`

**Summary:** `the [noun]` references something never introduced with `a [noun]`.

**Why it happens:**
Every noun introduced with `the` must have been previously introduced with `a` or `an`. Without a prior introduction, the claim is indefinite — the examiner cannot determine what "the data" refers to.

**Gotcha:**
```
WRONG: "A method comprising: processing the data..."
       ↑ What data? Never introduced.

WRONG: "A system comprising:
         wherein the controller performs..."
       ↑ What controller? Never introduced.
```

**Fix:**
```
RIGHT: "A method comprising:
          receiving a data packet from a network interface;
          processing the data packet..."
                   ↑ Now "the data packet" has antecedent basis.

For multiple items:
  "a first sensor... a second sensor...
   wherein the first sensor communicates with the second sensor"
```

**Tracking tip:** For every `the [noun]` in a claim, find `a [noun]` earlier in the same claim. If you can't find it, add it.

---

## [HIGH] Software Claims Rejected as Abstract Ideas (Alice/101)

**ID:** `abstract-idea-101`

**Summary:** Post-*Alice*, software claims without specific technical grounding face 101 rejection.

**Why it happens:**
*Alice Corp. v. CLS Bank* (2014) established a two-step test. Step 1: is it an abstract idea? Step 2: does it add "significantly more"? Generic computer implementation ("do it on a computer") does not satisfy Step 2.

**Gotcha:**
```
Claim: "A method comprising:
          receiving user input;
          calculating a result based on the input;
          displaying the result."

Examiner: "This is the abstract idea of performing calculations.
           Generic computer implementation adds nothing."
```

**Fix — integrate practical application:**
```
1. Claim specific technical improvement:
   "...thereby reducing network latency by at least 30%
    compared to sequential processing approaches."

2. Claim unconventional technical architecture:
   "...using a sparse attention transformer operating on
    tokenized sensor streams at 10ms intervals."

3. Anchor to specific hardware/real-world data:
   "...wherein the accelerometer captures motion data at 200Hz
    and the processor applies a Kalman filter to the raw signal."

4. Cite precedent: Enfish (data structure improvement), McRO (specific
   rules for animation), DDR Holdings (internet-specific solution).
```

**CNIPA difference:** In China, software claims are examined under 技术特征 (technical character) standards — generally more permissive than Alice. A claim that fails USPTO 101 may still pass CNIPA if it has a technical character producing a technical effect. See `cnipa_guidelines.md`.

---

## [HIGH] Single Embodiment Limits Claim Scope

**ID:** `single-embodiment-spec`

**Summary:** If the spec describes only one way to implement a feature, broad claim language will be construed narrowly to match.

**Why it happens:**
Courts and examiners construe claim terms in light of the specification. If only one embodiment is disclosed, "processing" may be construed to mean only the specific processing method described — not processing in general.

**Gotcha:**
```
Claim:  "A method for processing images..."
Spec:   Only describes processing with Gaussian blur algorithm.

Court:  "Processing" = Gaussian blur, because that's all the spec shows.
        Competitor using median filter → no infringement found.
```

**Fix:**
```
"In one embodiment, image processing uses a Gaussian blur algorithm.
 In another embodiment, a median filter or bilateral filter may be used.
 In yet another embodiment, machine learning models such as CNNs,
 autoencoders, or diffusion models may be employed for image processing."

Also use: "Processing may include, but is not limited to..."
```

---

## [HIGH] Prosecution History Estoppel Traps

**ID:** `prosecution-history-estoppel`

**Summary:** Arguments made to overcome rejections during prosecution permanently narrow claim scope — even if the words aren't changed.

**Why it happens:**
Under the doctrine of equivalents, a patent can cover things "equivalent" to what's literally claimed. But if during prosecution you argued "my invention is different from X because it doesn't do Y," you can never later claim something that does Y — even under equivalents.

**Gotcha:**
```
Examiner rejects Claim 1 over prior art that "uses batch processing."
Applicant argues: "Our invention uses real-time processing, which is
                   fundamentally different from the cited reference."
Claim allowed.

Later in litigation, competitor uses near-real-time processing.
Court: Estoppel bars the equivalents argument. Applicant surrendered
       anything resembling batch processing AND near-real-time.
```

**Fix:**
- Amend claims narrowly rather than making broad distinctions in arguments
- If you must make arguments, qualify them: "at least with respect to this limitation..."
- Never characterize your invention more broadly in arguments than the claim requires

---

## [MEDIUM] Continuation Strategy Ignored

**ID:** `no-continuation-strategy`

**Summary:** Failing to file continuation applications forfeits the ability to pursue broader or different claims on the same invention.

**Why it happens:**
Once a patent issues, prosecution is closed. But if a continuation application was pending, you can file new claims on the same disclosure — targeting new infringing products, broader scope, or different claim types.

**Gotcha:**
```
Patent issues. Competitor launches product that doesn't literally
infringe the issued claims but clearly uses the same invention.

No continuation pending → no path to new claims.
Patent issues → prosecution closed forever.
```

**Fix:**
- For valuable inventions, file a continuation before the parent issues
- Keep at least one continuation "pending" in your portfolio
- Use continuations to pursue: (a) broader claims the examiner rejected, (b) claims targeting competitor products, (c) claim types not in the original (e.g., add CRM claim later)

---

## [MEDIUM] Freedom-to-Operate Ignored at Filing

**ID:** `fto-not-assessed`

**Summary:** Filing a patent doesn't give you the right to practice the invention — a third party's patent may block you.

**Why it happens:**
Inventors focus on protecting their IP and forget to check whether practicing their own invention would infringe someone else's patent.

**Gotcha:**
```
Startup files patent on "Method X."
Patent granted.

Startup begins selling product → receives cease-and-desist from
BigCo whose patent covers a foundational step of Method X.

Having your own patent doesn't protect you from infringement claims.
```

**Fix:**
- Conduct FTO search before commercializing (separate from patentability search)
- FTO searches look at CLAIMS of in-force patents, not just publications
- Flag any blocking patents identified during prior art review

---

## [MEDIUM] Priority Date Not Preserved in Continuations

**ID:** `priority-date-lost`

**Summary:** Incorrect continuation filing breaks the chain back to the original priority date.

**Why it happens:**
A continuation must be filed before the parent issues or abandons, and must explicitly claim priority to the parent. Missing either requirement breaks the chain, and all intervening prior art becomes available against the new application.

**Fix:**
- File continuation before parent issues (not after)
- Always include: "This application claims priority to Application No. [X], filed [date]..."
- Check that the continuation spec is identical to the parent (or is a CIP with new matter properly flagged)
