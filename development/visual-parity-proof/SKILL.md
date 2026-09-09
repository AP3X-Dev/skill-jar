---
name: visual-parity-proof
description: "Use when proving whether a bounded candidate rendering matches bound reference pixels across declared pages, states, viewports, images, frames, or PDF pages. Produces a read-only, identity-bound comparison package with frozen rules, typed measurements, regional review, and weakest-surface verdicts. NOT for visual design, implementation or CSS fixes, functional or accessibility testing, aesthetic critique, performance testing, source-only review, reference approval, or release approval."
---

# Visual Parity Proof

Evaluate rendered evidence without changing the thing being evaluated. Bind the
reference and candidate, freeze the comparison plan before candidate results,
measure only comparable pairs, inspect material regions, and return one
canonical proof package. A small diff score is not itself parity, and a
screenshot proves pixels rather than interaction, semantics, or release safety.

## Operating boundary

This skill is read-only. It may accept supplied captures or perform an
explicitly permitted capture whose semantic effect is demonstrably `none`.
Never edit implementation files, regenerate or bless a reference, adjust rules
after seeing results, install tooling, send application actions, commit, push,
deploy, publish, or approve a release. A request to repair a mismatch is a
separate task.

Before any browser, renderer, image, or PDF action, bind its destinations,
expected requests, permission, credential handle, privacy exposure, cost,
timeout, cleanup, and expected semantic effect. Navigation is not inherently
read-only: analytics, session creation, lazy loading, and application writes
may occur. If bounded read-only behavior cannot be established, do not execute
the action; record a planned blocked acquisition and an Unknown instead.

## Required sequence

1. Bind the comparison goal, both Subjects, owners, repository identity when
   applicable, environment, requested proof boundary, and allowed acquisition
   actions.
2. Before examining candidate results, freeze the complete required/optional
   Surface matrix and each Surface's state, rendering conditions, authority,
   Regions, Rules, Transforms, and Masks.
3. Mark comparison start with one current `comparison_start` Evidence row. Do
   not backdate or move this instant to validate late criteria.
4. Acquire or accept captures under the safety contract. Retain original pixels
   and bind each artifact and derived output with SHA-256.
5. Establish one reference/candidate Comparison per evaluated Surface. Treat
   crop, alignment, resize, resampling, recoloring, redaction, and masking as
   material operations, never invisible normalization.
6. Execute only pre-authorized Measurements with fully resolved safety fields.
   Cover every required Rule and inspect every material Region.
7. Derive Region Verdicts, then each Surface Verdict, then the single overall
   Verdict. The weakest required Surface controls the result; optional Surfaces
   do not affect it.
8. Emit the package below and stop. Do not convert visual evidence into claims
   about application behavior, accessibility, performance, or deployment
   approval.

## Canonical package

Emit these fourteen root fields exactly, with no additional root field:

1. `schema_version: visual-parity-proof/v1`
2. `comparison_goal`
3. `reference_subject`
4. `candidate_subject`
5. `repository_root`
6. `worktree`
7. `revision`
8. `environment`
9. `requested_boundary`
10. `matrix_frozen_at`
11. `comparison_started_at`
12. `comparison_start_evidence_id`
13. `generated_at`
14. `verdict`

`reference_subject` and `candidate_subject` point to the two Subject rows.
`requested_boundary` is one of `supplied_capture`, `local_render`,
`hosted_render`, `live_render`, `production_render`, or `unknown`.
`verdict` is one of `exact-raster-match`, `within-declared-tolerance`,
`material-mismatch`, or `blocked-incomparable-evidence`.

After the root, emit exactly these seventeen sections in this order:

1. `Conclusion`
2. `Subjects`
3. `Actors`
4. `BoundaryBindings`
5. `Surfaces`
6. `Acquisitions`
7. `Captures`
8. `Comparisons`
9. `Transforms`
10. `Masks`
11. `Rules`
12. `Regions`
13. `Measurements`
14. `Differences`
15. `Evidence`
16. `Verdicts`
17. `Unknowns`

Every material sentence in `Conclusion` ends with a compact JSON array of the
Verdict IDs that support it. Do not create a Claims section or Claim IDs. The
primary result sentence cites the one overall Verdict.

### Section schemas

Use exactly these columns, in order:

- `Subjects`: `id, role, locator, content_identity, artifact_or_revision, boundary, boundary_binding_id, owner_actor_id, provenance, freshness, evidence_ids`
- `Actors`: `id, role, identity, organization, evidence_ids`
- `BoundaryBindings`: `id, subject_id, boundary, repository, worktree, revision, environment, deployment_identity, configuration_identity, asset_identity, url, tenant_or_scope, captured_at, evidence_ids, freshness, completeness`
- `Surfaces`: `id, name, route_or_page, state, viewport_css_px, dpr, zoom, scroll_or_page, capture_mode, locale, timezone, theme, color_profile, renderer, os, fonts, data_fixture, auth_state, determinism, wait_condition, required, requiredness_owner_actor_id, requiredness_approval_evidence_ids, frozen_at, reference_capture_id, candidate_capture_id, rule_ids, evidence_ids`
- `Acquisitions`: `id, subject_id, surface_id, capture_id, actor_id, mode, exact_action, cwd_or_url, permission, credential_handle, network_destinations, expected_requests, semantic_side_effect, privacy_scope, cost_bound, timeout_ms, cleanup, result, evidence_ids`
- `Captures`: `id, subject_id, surface_id, producer_actor_id, locator, content_identity, captured_at, pixel_dimensions, format, alpha_mode, acquisition_id, transform_ids, evidence_ids`
- `Comparisons`: `id, surface_id, reference_capture_id, candidate_capture_id, condition_binding, transform_ids, mask_ids, overlap_pixels, comparability, reason, evidence_ids`
- `Transforms`: `id, operation, parameters, reference_input_id, candidate_input_id, reference_output_id, candidate_output_id, symmetric, frozen_at, owner_actor_id, approval_evidence_ids, validity`
- `Masks`: `id, surface_id, region_id, applicable_rule_ids, selector_or_geometry, reason, area_ratio, max_area_ratio, immaterial_to_goal, frozen_at, owner_actor_id, approval_evidence_ids, validity, invalid_reasons`
- `Rules`: `id, surface_id, region_id, required, dimension, metric, tolerance, materiality, rationale, frozen_at, owner_actor_id, approval_evidence_ids`
- `Regions`: `id, surface_id, name, semantic_role, geometry, priority, reference_evidence_ids, candidate_evidence_ids`
- `Measurements`: `id, comparison_id, surface_id, region_id, rule_id, tool, tool_version, exact_command, cwd, permission, network_destinations, semantic_side_effect, privacy_scope, cost_bound, timeout_ms, cleanup, input_identities, parameters, overlap_pixels, result, value, output_identity, executed_at, exit_status, proves, limits, evidence_ids`
- `Differences`: `id, surface_id, region_id, dimension, observation, magnitude, rule_id, material, reference_evidence_ids, candidate_evidence_ids, measurement_ids, derived_artifact_ids`
- `Evidence`: `id, kind, locator, content_identity, captured_at, boundary, subject_id, boundary_binding_id, environment, observation, proves, limits, freshness, actor_id, surface_id, region_id, reference_capture_id, candidate_capture_id`
- `Verdicts`: `id, level, scope_ids, outcome, required_rule_ids, difference_ids, unknown_ids, evidence_ids, confidence, reviewer_evidence_ids, rationale`
- `Unknowns`: `id, surface_id, question, why_unknown, impact, discriminator_acquisition_id, required_access, owner_actor_id`

## Identity, references, and scope

IDs use one package-wide namespace and match `[A-Z][A-Z0-9]*-[0-9]+`. Every ID
resolves once to a row in its declared section. Encode every `*_ids` value as a
compact JSON array; encode a singular link as one typed ID. Use the literal
`unknown` for an unknown scalar. Use `not_applicable` only where this contract
explicitly permits it.

Content identity is `sha256:<64-lowercase-hex>`. Git identity is
`git:sha1:<40-lowercase-hex>` or `git:sha256:<64-lowercase-hex>`.
Actor `identity` is a SHA identity or `unknown`. Boundary deployment,
configuration, and asset identities are SHA identities; use `not_applicable`
only when the selected boundary does not require that identity, or `unknown`
when the identity is required but unavailable.
Repository, worktree, and revision may be `not_applicable` only for a supplied
artifact unrelated to a repository. If they apply but cannot be established,
use `unknown` and block.

The comparison-start reference points to exactly one current Evidence row with
`kind=comparison_start`; its `captured_at` equals `comparison_started_at`, and
its `proves` says the candidate comparison began then.

Enforce these reference types:

- Subject boundary/owner/evidence links resolve to BoundaryBindings, Actors,
  and Evidence. Actor evidence resolves to Evidence. A BoundaryBinding resolves
  to its Subject and Evidence.
- Surface capture links resolve to Captures. Either may be `unknown` only when
  the Surface has a linked Unknown and a blocked Verdict. Surface rule links
  resolve to Rules; evidence and requiredness approval links resolve to
  Evidence, with each approval row using `kind=approval`.
- Acquisition links resolve to its Subject, Surface, Actor, Evidence, and when
  present, Capture. `capture_id=not_applicable` is allowed only for a `failed`
  or `blocked` result.
- Capture links resolve to Subject, Surface, producer Actor, Acquisition,
  Transforms, and Evidence.
- Comparison links resolve to one Surface, the exact two Captures for that
  Surface, and its Transforms, Masks, and Evidence.
- Transform owners resolve to Actors; input/output links resolve to Captures.
  Output may equal input only for `operation=none`. Mask owners resolve to
  Actors; mask Surface/Region/Rule/evidence links resolve to their named rows.
- Rule owners resolve to Actors and approvals to Evidence. A whole-Surface Rule
  alone may use `region_id=not_applicable`.
- Region evidence resolves to Evidence. Measurement links resolve to its
  Comparison, Surface, Rule, Evidence, and either its Region or
  `not_applicable`. Difference links resolve to Surface, Rule, Measurements,
  Evidence, and either Region or `not_applicable`.
- Verdict `scope_ids` contains Regions for `level=region`, exactly one Surface
  for `level=surface`, and every and only required Surface for `level=overall`.
  Its other ID arrays resolve to their named sections.
- Evidence Subject and BoundaryBinding fields resolve normally or are both
  `not_applicable`; a non-applicable binding also requires
  `environment=not_applicable`. Tool evidence may use
  `actor_id=not_applicable`; human evidence resolves to an Actor. Evidence
  surface, region, and capture fields resolve or use `not_applicable`.
  `visual_inspection` requires an Actor, Surface, Region, and both Capture IDs.
- Unknown Surface resolves to a Surface, or uses `not_applicable` for a global
  gap. Its owner resolves to an Actor. Its discriminator is a `planned`
  Acquisition; `not_applicable` is allowed only when no safe bounded
  acquisition can be described.

Reject any wrong-role, wrong-Surface, wrong-pair, or identity-crossing link:

- A Surface's two captures belong to that Surface and to the respective
  reference/candidate Subjects. Its Rules and approvals belong to it.
- Acquisition and Capture Subject/Surface pairs agree. Capture producer,
  transform outputs, and Evidence stay with the same bound artifact.
- A Comparison uses exactly the capture pair recorded by its Surface. Every
  Transform keeps reference endpoints on the reference Subject and candidate
  endpoints on the candidate Subject, all within that Surface.
- Region, Rule, Mask, Measurement, Difference, inspection Evidence, and Surface
  Verdict all stay within one Surface. A Measurement uses that Surface's unique
  Comparison, and its Rule and Region belong there.
- Measurement `input_identities` exactly equals the SHA identities of the two
  Captures used by its Comparison. Difference Evidence, Measurements, Rule,
  and Region agree on Surface. Inspection Evidence cites that same pair.
- Subject boundary Evidence agrees with the Subject, binding, boundary, and
  environment. The overall Verdict has the exact closure of required Surfaces
  and required Rules.

## Cardinality and coverage

Require exactly one reference Subject and one candidate Subject. Actors and
BoundaryBindings are non-empty, and each Subject has exactly one
BoundaryBinding. The candidate Subject has an `implementation_owner`; the
reference Subject has the applicable decision or implementation owner.

Require at least one Surface and at least one `required=yes` Surface. A fully
evaluated required Surface has exactly one reference Capture, one candidate
Capture, one Comparison, at least one required Rule, one valid Measurement for
every required Rule, a Verdict for every material Region, and one Surface
Verdict. A material Region has priority `critical`, `major`, or `minor`;
`informational` Regions need no Region Verdict. Informational Rules cannot be
required or appear in `required_rule_ids`.

A blocked Surface may have an unknown capture link only with a linked Unknown
and blocked Surface Verdict. An optional Surface uses `required=no`: if tested,
it meets the same completeness rules; if omitted, it has unknown capture links,
a linked Unknown, and a blocked Surface Verdict, but never affects overall.

Each Surface Verdict lists exactly its `required=yes` Rules. The overall
Verdict lists their exact union across required Surfaces and scopes every and
only required Surface. Do not add or remove required coverage after results.
There is exactly one overall Verdict.

For any non-blocked overall outcome, Captures, Comparisons, Rules, Regions,
Evidence, and Verdicts are non-empty. Transforms, Masks, Differences, and
Unknowns may be empty. Every Capture, including a supplied one, has exactly one
Acquisition. A planned or attempted acquisition has no Capture and uses
`capture_id=not_applicable` while retaining a Subject and Surface.

## Encodings and closed values

Use compact JSON in all JSON-valued cells:

- `viewport_css_px` and `pixel_dimensions`:
  `{"width":n,"height":n}`, with nonnegative integer origins where applicable
  and positive width/height.
- Region geometry: `{"x":n,"y":n,"width":n,"height":n}` with nonnegative
  integers and positive width/height.
- `scroll_or_page`: `{"kind":"scroll","x":n,"y":n}` with nonnegative
  integers, or `{"kind":"page","number":n}` with a positive integer.
- `condition_binding`: exactly the string keys `viewport`, `dpr`, `zoom`,
  `scroll_or_page`, `capture_mode`, `locale`, `timezone`, `theme`,
  `color_profile`, `renderer`, `os`, `fonts`, `data_fixture`, `auth_state`,
  `determinism`, and `wait_condition`.
- `input_identities`:
  `{"reference":"sha256:<64-hex>","candidate":"sha256:<64-hex>"}`.
- `selector_or_geometry`: either
  `{"kind":"selector","value":"<nonempty-selector>"}` or
  `{"kind":"rect","x":n,"y":n,"width":n,"height":n}`.
- `cost_bound`: `{"value":<nonnegative-number-or-"unknown">,"unit":"seconds|requests|bytes|usd|unknown"}`.

`dpr` and `zoom` are positive numbers or `unknown`. Ratios are numbers in
`[0,1]`. Timeouts are nonnegative integers or `unknown`, subject to acquisition
status rules below. For an executed raster comparison or Measurement,
`overlap_pixels` is a positive integer; zero or `unknown` blocks.

Use RFC 3339 UTC for `generated_at`. Root freeze/start times and every
BoundaryBinding/Capture/Evidence `captured_at`, plus Surface/Rule/Transform/Mask
`frozen_at`, are RFC 3339 UTC or `unknown`. Measurement time uses the
result-specific encoding below. Do not introduce other time sentinels.

Closed vocabularies:

- Subject role: `reference|candidate`.
- Actor role: `capture_producer|implementation_owner|independent_reviewer|decision_owner|other`.
- Boundary: `supplied_capture|local_render|hosted_render|live_render|production_render|unknown`.
- Freshness: `current|stale|unbound|conflicting|unknown`.
- Binding completeness: `complete|incomplete|unknown`.
- Required/symmetric/immaterial booleans: `yes|no`.
- Acquisition mode: `supplied|planned|attempted|performed`.
- Semantic side effect: `none|possible|mutating|unknown`.
- Acquisition result: `supplied|passed|failed|blocked`.
- Comparability: `comparable|conditionally_comparable|incomparable|unknown`.
- Transform operation: `none|crop|resize|align|resample|color_convert|redact`.
- Transform validity: `valid|post_result|asymmetric|unapproved|unknown`.
- Mask validity: `valid|post_result|asymmetric|unapproved|excessive|unknown`.
- Mask `invalid_reasons`: a compact JSON array of unique values selected from
  `post_result|asymmetric|unapproved|excessive|unknown`, sorted in that exact
  precedence order. Capture every applicable defect rather than selecting one.
  A valid Mask uses `validity=valid` and `invalid_reasons=[]`. An invalid Mask
  sets `validity` to the first entry in its non-empty `invalid_reasons` array.
- Dimension: `canvas|geometry|typography|color|asset|content|overflow|layering|pixel|responsive`.
- Metric: `exact_pixel_diff|different_pixel_ratio|geometry_delta_px|typography_match|color_delta_e|asset_identity_match|content_presence|overflow_pixels|stacking_match|responsive_state_match`.
- Priority/materiality: `critical|major|minor|informational`.
- Difference material: `yes|no|unknown`.
- Measurement result: `passed|failed|error|unavailable|not_run`.
- Verdict level: `region|surface|overall`.
- Verdict outcome: `exact-raster-match|within-declared-tolerance|material-mismatch|blocked-incomparable-evidence`.
- Confidence: `reported|identity_bound|measured|independently_reviewed`.
- Evidence kind: `user_request|source|reference_capture|candidate_capture|capture_metadata|comparison_start|measurement_output|visual_inspection|approval|acquisition_record|derived_artifact|other`.

## Freeze and authority

For any non-blocked result, every included Surface, Rule, Transform, and Mask is
frozen at or before `matrix_frozen_at`, and the matrix is frozen at or before
`comparison_started_at`. Preserve the real timestamps. A late Surface or Rule
blocks. A late Transform or Mask also has `validity=post_result` and blocks.
For a late Mask, include `post_result` in `invalid_reasons`; also retain every
other applicable Mask defect under the ordered multi-defect encoding.

The comparison start is no later than any Measurement execution or candidate
`visual_inspection`. If this ordering cannot be demonstrated, block. Root
`generated_at` is at or after the start and every included freeze, capture,
binding, Evidence, and executed Measurement time; an earlier report time is a
conflict, not an invitation to rewrite history.

Every required Surface and Rule binds a responsible Actor and non-empty
approval Evidence captured before comparison begins. Missing or late authority
makes requiredness unknown and blocks. Never infer that desktop, tablet,
mobile, modal, or any other state is required merely from convention; record
the owner's pre-result decision.

## Acquisition records

Acquisition `network_destinations` and `expected_requests` are compact JSON
arrays. Both use `not_applicable` only for supplied acquisition and may use
literal `unknown` only for a planned blocked Acquisition. Measurement
`network_destinations` is a resolved compact array for executed work and may be
`unknown` only for `unavailable|not_run`. Measurement cost and timeout are
never `not_applicable`; acquisition cost and timeout use it only in supplied
mode.

The mode/result/capture mapping is exact:

- `supplied` has an existing Capture and `result=supplied`. Set exact action,
  cwd/URL, permission, credential, destinations, expected requests, cost,
  timeout, and cleanup to `not_applicable`; semantic effect is `none`.
- `planned` is not executed, has `capture_id=not_applicable`, and
  `result=blocked`.
- `attempted` produced no usable Capture, has `capture_id=not_applicable`, and
  `result=failed`.
- `performed` has an existing Capture and `result=passed`.

Planned and attempted rows retain truthful bounded safety fields. A run-time
capture may proceed only with explicit permission, a credential handle rather
than a secret, resolved destinations and requests, bounded privacy/cost/
timeout, declared cleanup, and `semantic_side_effect=none`. Never expose
credentials or personal data.

Redaction creates a derived Capture through a `redact` Transform. Retain the
restricted original's identity. A redacted artifact cannot support exact
raster.

## Transforms and masks

Always preserve original Captures. Apply each Transform symmetrically to the
reference and candidate and bind the two inputs and outputs. Parameters contain
exactly the keys for the selected operation:

- `none`: `{}`; only this operation may reuse input IDs as output IDs.
- `crop`: nonnegative integer `x,y` and positive integer `width,height`.
- `resize`: positive integer `width,height` plus
  `filter=nearest|bilinear|bicubic|lanczos`.
- `align`: integer `x_offset,y_offset` plus
  `anchor=top_left|center|feature_bound`.
- `resample`: positive-number `scale_x,scale_y` plus the resize filter enum.
- `color_convert`: nonempty `from_profile,to_profile` plus
  `intent=perceptual|relative_colorimetric|absolute_colorimetric|saturation`.
- `redact`: the exact selector/geometry object plus a nonempty `reason`.

Encode redact parameters with exactly the keys
`{"selector_or_geometry":<selector-or-rect-object>,"reason":"<nonempty>"}`.
For validity, use `post_result` for a late Transform, `asymmetric` when the two
sides are not treated identically, `unapproved` when required approval is
absent, and `unknown` when validity cannot be determined; only a pre-frozen,
approved, symmetric operation is `valid`.

Any non-`none` Transform makes the pair at most
`conditionally_comparable`. Exact raster prohibits transforms, including
`none` rows whose presence would contradict the required empty transform list.

A Mask binds one Surface and Region, applicable Rules, exact selector or
rectangle, reason, actual and predeclared maximum area ratios, immateriality,
owner, approval, and freeze time. It is valid only when symmetric, approved,
frozen before comparison, `area_ratio <= max_area_ratio`, and excludes proven
nondeterministic content immaterial to the goal. It may apply only to
`different_pixel_ratio` or `color_delta_e` Rules.

Never mask geometry, overflow, focus, modals, validation, content presence, or
other meaningful state. Determine all defects independently: a late freeze adds
`post_result`; unequal application adds `asymmetric`; missing valid approval
adds `unapproved`; `area_ratio > max_area_ratio` adds `excessive`; and an
unresolved validity condition adds `unknown`. Encode all applicable reasons
once in the required order, then derive the single primary `validity` from the
first array entry. Thus a late and excessive Mask records both reasons while
using only `post_result` as its primary validity. Any non-empty reason array
invalidates the Surface. Always report the masked ratio. To adopt a newly
recognized dynamic area, freeze a new approved plan and recapture/recompare;
do not retrofit the current result.

## Rules, metrics, and measurements

Rule `tolerance` is
`{"operator":"<operator>","value":<typed-value>,"unit":"<unit>"}`.
Measurement `value` is `{"value":<typed-value>,"unit":"<unit>"}`.
Allowed combinations are exact:

| Dimension | Metric | Tolerance |
|---|---|---|
| `canvas` or `pixel` | `exact_pixel_diff` | `eq`, nonnegative integer, `pixels` |
| `canvas` or `pixel` | `different_pixel_ratio` | `lte`, number in `[0,1]`, `ratio` |
| `geometry` | `geometry_delta_px` | `lte`, nonnegative number, `pixels` |
| `typography` | `typography_match` | `eq`, `true`, `boolean` |
| `color` | `color_delta_e` | `lte`, nonnegative number, `delta_e` |
| `asset` | `asset_identity_match` | `eq`, `true`, `boolean` |
| `content` | `content_presence` | `eq`, `true`, `boolean` |
| `overflow` | `overflow_pixels` | `lte`, nonnegative number, `pixels` |
| `layering` | `stacking_match` | `eq`, `true`, `boolean` |
| `responsive` | `responsive_state_match` | `eq`, `true`, `boolean` |

Observed numeric values use the corresponding range and unit. Observed boolean
values are `true` or `false`. No other dimension/metric pair is valid.

Measurement `parameters` is compact JSON with exactly
`{"mask_ids":[],"transform_ids":[],"channel":"rgba|rgb|luma|not_applicable"}`.
Pixel-diff and ratio metrics use `rgba`, `rgb`, or `luma`; color delta uses
`rgb` or `luma`; other metrics use `not_applicable`. Exact-pixel Rules require
Measurements with empty mask/transform arrays and `rgba` or `rgb`.

Measurement `transform_ids` exactly matches its Comparison. Its `mask_ids`
exactly lists the Comparison Masks whose frozen `applicable_rule_ids` include
that Rule. No mask is valid for exact pixel, canvas, geometry, typography,
asset, content, overflow, layering, or responsive Rules.

Derive `passed` exactly when the typed value satisfies the Rule tolerance and
`failed` exactly when it does not. A value/result inconsistency invalidates the
row. Status encoding is exact:

- `passed|failed`: typed value, SHA output identity, RFC 3339 execution time,
  integer exit status, and complete safety fields. Raster metrics require a
  positive integer `overlap_pixels`; non-raster metrics use `not_applicable`.
- `error`: `value=not_applicable`, RFC 3339 execution time, integer exit status,
  `output_identity=not_applicable`, and complete safety fields. Overlap is a
  nonnegative integer when known or `not_applicable`; state the failure bound
  in `limits`.
- `unavailable|not_run`: value, overlap, output, execution time, and exit status
  are all `not_applicable`.

Errors, unavailable checks, and checks not run never satisfy a Rule. Empty
rasters, missing pages or frames, absent output, and zero raster overlap are
`error`, not zero difference.

Before execution, resolve cwd, permission, destinations,
`semantic_side_effect=none`, privacy scope, cost, timeout, and cleanup. If
semantic writes, unbounded network/privacy, missing permission, or unknown
cost/timeout cannot be excluded, record `not_run`, preserve the unsafe or
unknown fields, and block the Surface. A Measurement command may consume only
authorized capture inputs; it cannot install tools, mutate source or artifacts,
send application actions, or acquire additional hosted/runtime data.

A failed required Rule creates a material Difference with its Rule materiality.
An independent visual review may identify a material issue outside the frozen
Rules. Only that inspection-only Difference may use
`rule_id=not_applicable`; it has `measurement_ids=[]`, `material=yes`, and
current `visual_inspection` Evidence bound to the exact Region and capture pair.
It cannot support a no-difference assertion or change a tolerance.

## Comparability and exactness

Set `comparability=comparable` only when all bound conditions and UI state
match. A symmetric pre-frozen Transform permits at most
`conditionally_comparable`. Unknown or mismatched material state, canvas,
viewport, crop, or capture conditions produces `incomparable` or `unknown`;
even a low numeric score cannot promote that pair.

`exact-raster-match` requires original byte-addressable equal-size captures,
no masks, no transforms, an identical `condition_binding`, a required exact
pixel Rule, positive full-canvas overlap, and zero different pixels. The bound
conditions include renderer/version, OS raster stack, viewport, DPR, zoom,
color profile, fonts and their load state, locale/timezone/theme, data/auth/UI
state, determinism, motion/time/randomness control, and wait condition.
Perceptual or aggregate similarity never establishes exactness.

`within-declared-tolerance` requires comparable or conditionally comparable
identity-bound captures, a valid executed Measurement for every frozen
required Rule, no failed required Rule, and independent visual review of every
material Region. A single whole-image percentage cannot excuse displaced
actions, clipped text, missing content or modal state, incorrect breakpoints,
overflow, or stacking defects.

## Confidence and boundary promotion

Assign confidence as the highest fully demonstrated tier:

- `reported`: assertions exist but required identity or freshness is absent.
- `identity_bound`: both Subjects, original Captures, frozen Surface conditions
  and Rules, current BoundaryBindings, and Comparison are SHA-bound.
- `measured`: identity-bound, every required Rule has one valid executed
  Measurement, and every result has a Difference or explicit no-difference
  Evidence.
- `independently_reviewed`: measured plus current `visual_inspection` Evidence
  for every material Region. Each review binds reviewer, exact capture pair,
  time, observation, and limits. The reviewer Actor has
  `role=independent_reviewer`, a known identity, and an identity different from
  every capture producer and candidate implementation owner.

A BoundaryBinding is current only when every identity required for that
boundary has current Evidence agreeing on Subject, BoundaryBinding, boundary,
and environment, with no referenced stale, unbound, conflicting, or unknown
Evidence. Otherwise reduce freshness/completeness and do not claim
identity-bound confidence.

Promotion by boundary is weakest-link:

- `supplied_capture` proves only supplied pixels and metadata. Repository,
  worktree, revision, deployment, configuration, asset, URL, and tenant may be
  `not_applicable`.
- `local_render` requires a complete binding and passed Acquisition tied to
  repository/worktree/revision, the local environment, URL or process asset
  identity, and capture conditions. Deployment and tenant may be
  `not_applicable`.
- `hosted_render`, `live_render`, and `production_render` require a complete,
  current binding with known environment, deployment, configuration, asset,
  URL, tenant/scope, capture time, and repository/worktree/revision when the
  Subject is repository-built, plus a permitted passed Acquisition at that
  exact boundary.

Never promote local proof to hosted, live, or production. Reference pixels do
not establish intended semantics, function, or access correctness.

## Verdict derivation

Derive each material Region first, then one Verdict per Surface, then one
overall Verdict. Use this precedence for a Surface:

1. `blocked-incomparable-evidence` when a foundational Subject/root/boundary,
   requiredness authority, capture pair, Rule, Measurement, or boundary
   identity is absent, stale, or unknown; when conditions/state do not match;
   when a Transform or Mask is invalid or late; when a required Measurement is
   error/unavailable/not-run, empty, lacks output, or has zero raster overlap;
   or when comparability is incomparable/unknown. Also block a non-exact
   Surface or tolerance-level overall result lacking current independent review.
2. `material-mismatch` when comparable evidence shows a failed required Rule,
   missing required content/state, a responsive overflow/clipping/layering
   defect, or an inspection-only material Difference.
3. `exact-raster-match` only when all exact-raster requirements hold and
   confidence is at least `measured`.
4. `within-declared-tolerance` only when all frozen Rules pass, confidence is
   `independently_reviewed`, and no unrecorded material Difference remains.

Aggregate overall using required Surfaces only:

- Any blocked required Surface -> `blocked-incomparable-evidence`.
- Otherwise, any mismatching required Surface -> `material-mismatch`.
- Otherwise, all required Surfaces exact -> `exact-raster-match`.
- Otherwise, a set containing only exact and within-tolerance required Surfaces
  -> `within-declared-tolerance`, but only when every required Surface is
  independently reviewed.

No other combination is valid. Optional Surfaces never promote or demote the
overall result. Root `verdict` exactly equals the unique overall Verdict
outcome. There is no provisional-pass outcome.

## Derived visual artifacts

Heatmaps, blink views, and overlays are derived Evidence. Bind their exact
input identities, tool and parameters, output SHA, color legend, crop/scale,
and limitations. They supplement but never replace original Captures or
Measurements. Label transformed or masked output honestly; do not present it as
an untouched reference or candidate.

## Pressure defenses

| Pressure | Required handling |
|---|---|
| A resized or cropped pair reports only a small difference and is called pixel-perfect. | Preserve the originals. The transform prevents an exact-raster verdict and may conceal layout drift; block when native conditions are unbound. |
| A low aggregate number is offered without captures, conditions, tool identity, or a frozen threshold. | Keep it at `reported` confidence. Require the bound Measurement, frozen Rule, and material-region review before deriving parity. |
| Desktop appears close, tablet is missing, and mobile overflows. | Use owner-approved pre-result requiredness. A missing required tablet Surface blocks overall; required mobile overflow is a material mismatch. Do not issue a provisional pass. |
| Reference and candidate show different modal or UI states. | Mark the pair incomparable and block that required Surface until state is aligned under a new frozen comparison. |
| A timestamp region is proposed for masking after its difference is visible. | Mark the Mask post-result and the Surface invalid. A future run needs a pre-approved symmetric mask and fresh captures/comparison. |
| Rendering noise is blamed on fonts or anti-aliasing. | Bind fonts/load state, renderer/version, OS raster stack, DPR, and color pipeline. Unknown conditions block exactness rather than excusing pixels. |
| The tool emitted no artifact or compared zero pixels. | Record an error and block. Missing output, empty input, or zero overlap is never evidence of no difference. |
| Someone asks to open a live page because navigation is supposedly read-only. | Bind permission, requests, destinations, semantic effect, privacy, cost, timeout, and cleanup first. Do not navigate if writes or unbounded exposure cannot be excluded. |
| Matching screenshots are used to claim the UI works or is accessible. | Limit the conclusion to rendered evidence and direct functional/accessibility work to separate proof. |
| The mismatch is obvious, so the evaluator is asked to fix CSS immediately. | Finish the evidence package and stop. Implementation requires separate authorization. |

## Final validation

Reject rather than guess if any of these checks fails:

- exactly fourteen root fields and the seventeen sections in canonical order;
- global ID uniqueness, typed reference resolution, exact scope consistency,
  pair identity, and cardinality;
- owner-approved required Surface/Rule coverage frozen before comparison;
- valid SHA/Git identities, RFC 3339 ordering, compact JSON, and closed enums;
- bounded acquisition and Measurement safety, privacy, cost, timeout, cleanup,
  and actual non-empty execution evidence;
- symmetric pre-result Transforms and Masks with valid applicability/area;
- exact dimension/metric/tolerance/value/result typing and one Measurement per
  required Rule;
- complete material Region, Surface, and overall Verdict closure;
- correct confidence tier and no promotion beyond the evidenced environment;
- no claims of functionality, accessibility, performance, or release approval;
- no implementation, reference mutation, publication, or other side effect.
