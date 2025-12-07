## QA Audit – Task 18d133c1 (Reviewing Gemini Task 341eedf4)

**Verdict:** DISAGREE with Gemini’s “READY FOR LAUNCH.” All four previously flagged blockers remain and fail in code, not just docs/tests. Gemini’s assessment appears to rely on planning docs rather than executable paths.

### Blocker Validations

1) **Story generation (CONFIRMED broken)**
- The async generator imports a non-existent `env` export, so the module fails to compile and cannot initialize Supabase (`packages/api/src/lib/generateStoryAsync.ts:1-12`). Only `apiEnv` is exported from `packages/api/src/env.ts`, so any call to `story.generateStory` will throw at import time.
- The router references `verifyChildProfileOwnership` without importing/defining it (`packages/api/src/routers/story.ts:405, 440`), causing runtime reference errors on reads/lists.
- Generated data is written to `content` while retrieval expects `storyContent` (`generateStoryAsync.ts:82-103` vs. `story.ts:385-414`), so even if the module loaded, returned stories would have empty scenes/images.
- Impact: story generation cannot execute; polling and retrieval fail. This contradicts “<30s generation” readiness claims.

2) **Web auth (CONFIRMED broken)**
- Server auth only trusts bearer/x-supabase headers (`packages/api/src/context.ts:37-103`), but the web client never sends them—`createApiClient` is called with no headers (`apps/web/app/providers.tsx:25`).
- Login sets a cookie (`sb-access-token`) client-side only (`apps/web/app/(auth)/login/page.tsx:20-37`); middleware then tries `supabase-auth-token`, which Supabase sets as a JSON array, so token verification can misparse (`apps/web/middleware.ts:63-103`).
- Result: protected tRPC calls (e.g., `auth.me`, credits, story actions) return UNAUTHORIZED despite a “signed-in” UI; dashboards and story creation cannot function.

3) **PDF export (CONFIRMED broken)**
- The API route imports `db` from `@herokid/database`, but that package exports `prisma`, not `db` (`apps/web/app/api/generate-pdf/route.tsx:13-23`). This crashes on import.
- It also expects `SUPABASE_SERVICE_KEY`, while the validated env uses `SUPABASE_SERVICE_ROLE_KEY`; the client would be instantiated with `undefined`.
- Impact: PDF exports fail before running, so downloadable storybooks are unavailable.

4) **Payments/verification (CONFIRMED incomplete)**
- The main credit purchase endpoint is explicitly a mock: it creates credit packs and increments balances without verifying any payment (`packages/api/src/routers/credits.ts:52-107`, comment “Mock purchase for now” line 68).
- Mobile purchase UI only shows an alert “Payment Integration Required” and does not hit a real payment flow (`apps/mobile/app/credits/purchase.tsx:64-107`), so users cannot buy credits legitimately.
- Stripe checkout exists, but the unverifiable `purchaseCredits` path remains exposed to clients and tests (used in mobile hooks/tests), leaving payments non-production-ready.

### Reconciliation with Gemini’s Report
- Gemini’s “credit model production-ready” claim conflicts with the mock purchase path and missing auth wiring. Evidence shows runtime failures that block core flows (auth, story generation, PDFs).
- The optimistic assessment likely stems from architectural docs and specs; the implemented code still contains stubs/placeholders and import errors.

### Required Actions Before Launch
- Fix the API env import and remove missing references (`generateStoryAsync` should use `apiEnv`; add/import `verifyChildProfileOwnership`; persist to `storyContent` and align readers).
- Add authenticated request propagation for web (attach Supabase access tokens to tRPC requests or parse cookies in context; remove reliance on the JSON `supabase-auth-token` cookie).
- Correct the PDF export route to use the exported Prisma client and the right Supabase service env var.
- Replace `purchaseCredits` mock logic with real Stripe/IAP verification (or lock it down), and wire the mobile/web purchase UI to the verified flow only.
