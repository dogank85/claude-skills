# HeroKid Codebase Report

## Feature Implementation Status (vs. PRD/architecture)
- **User management & consent (partial):** tRPC routers for auth/consent/child profiles exist with password rules and COPPA consent (`packages/api/src/routers/{auth,consent,childProfile}.ts`). Mobile login/consent screens are wired to tRPC. Child profile creation is still TODO in the mobile UI (`apps/mobile/app/(app)/children.tsx`), blocking first-time setup on device.
- **Avatar & pet creation (mostly implemented):** Backend supports signed uploads, Nano Banana generation, daily regen limits, and credit gating (`packages/api/src/routers/avatar.ts`). Mobile onboarding flow uploads photos and calls generation (`apps/mobile/app/(onboarding)/avatar-creation.tsx`), but has a shadowed `AVATAR_COST` constant and assumes balance APIs work. Pet companion generation exists in router but pet UI not fully reviewed.
- **Story generation engine (blocked):** Router handles credit reservation, jobs, and polling (`packages/api/src/routers/story.ts`), but the async worker imports a non-existent `env` export and falls back to anon Supabase keys (`packages/api/src/lib/generateStoryAsync.ts`), so generation will throw before reaching Gemini/Imagen or storage. Monitoring/alerting for failed jobs is not wired.
- **Story library & reading (partial):** Library/generic story routers exist with pagination and favorites (`packages/api/src/routers/library.ts`, `genericStories.ts`). PDF export route exists but is unauthenticated and references `db` that is not exported (`apps/web/app/api/generate-pdf/route.tsx`), so exports are broken and expose storage via service keys. Mobile reader screen exists (`apps/mobile/app/story/[id].tsx`) but depends on story generation working.
- **Monetization (misaligned):** Credit ledger/deduction flows are implemented (`packages/api/src/routers/credits.ts`) and web purchase UI offers packs, but pricing is 1/5/10 credits instead of PRD’s 20/50/100, and IAP verification is explicitly marked incomplete. Stripe checkout creation exists but webhook/receipt validation hardening is pending. Cost alignment (story 10 credits, avatar/pet 4) matches PRD.
- **Web dashboard (incomplete):** Next.js pages for dashboard/billing/consent exist but use static placeholder data and the TRPC client never sends Supabase auth tokens (providers set no headers, context only reads Authorization headers), so protected queries will fail (`apps/web/app/providers.tsx`, `packages/api/src/context.ts`). Middleware checks cookies but API calls ignore them.
- **Compliance & ops (scaffolded):** Photo deletion, privacy export, account deletion, and health cron routes exist with CRON_SECRET gating and Sentry logging (`apps/web/app/api/cron/*`). Supabase env naming is inconsistent (SERVICE_KEY vs SERVICE_ROLE_KEY) across AI/storage/API, increasing misconfig risk.
- **Testing (uneven):** API/AI packages contain many Vitest suites; web has only a landing-page test and mobile tests are stubs. `typescript-errors-report.md` documents hundreds of TS errors across packages—current CI health is unclear and likely failing until rerun/fixed.

## Technical Debt Inventory
- Auth/token plumbing split: API context only accepts Authorization headers, while web login sets Supabase cookies; leads to non-functioning dashboard calls.
- Environment sprawl: SUPABASE_SERVICE_KEY vs SUPABASE_SERVICE_ROLE_KEY vs SUPABASE_SERVICE_KEY usage across modules; async story worker imports missing `env` export and falls back to anon keys.
- Payments: Credit pack sizes/pricing diverge from PRD; IAP verification explicitly “not production-ready”; Stripe webhook/receipt reconciliation not clearly enforced.
- PDF/export pipeline: Unauthenticated route with service key usage and incorrect DB import blocks exports and leaks storage if called externally.
- UI placeholders: Web dashboard stats/activity hard-coded; mobile child creation flow stubbed; offline caching pages exist but lack wiring.
- Monitoring gaps: Sentry used in cron routes, but main API/mobile/web flows lack consistent error/trace instrumentation.
- Legacy artifacts: TypeScript error report indicates prior unresolved syntax/module issues; risk of hidden build failures.

## Security Findings
- **Unauthenticated PDF export:** `apps/web/app/api/generate-pdf/route.tsx` accepts arbitrary story IDs, uses service key, and imports `db` that is not exported—allows unauthorized access or fails open.
- **Story worker key fallback:** `packages/api/src/lib/generateStoryAsync.ts` uses `env.SUPABASE_SERVICE_ROLE_KEY || env.NEXT_PUBLIC_SUPABASE_ANON_KEY`; anon key fallback plus bad import can break storage access and obscures failure modes.
- **Payment verification gaps:** Apple/Google verification marked incomplete in credits router; potential for fake receipts to credit accounts.
- **Cookie/auth mismatch:** TRPC context ignores Supabase cookies, so web relies on client-side headers that aren’t set—causes unauthorized errors and may encourage insecure workarounds.
- **Env naming inconsistency:** Mixed SERVICE_KEY/SERVICE_ROLE_KEY usage increases chance of mis-secreting service role keys into client bundles.

## Prioritized Recommendations (effort: S ≤1d, M 1-3d, L >3d)
1. **Fix story worker env usage (S-M):** Export/use `apiEnv` in `generateStoryAsync`, require `SUPABASE_SERVICE_ROLE_KEY`, remove anon fallback, and add failure alerts on job status transitions.
2. **Wire web auth to API (S-M):** Either read Supabase cookies in `createContext` or set Authorization headers in `apps/web/app/providers.tsx`; replace static dashboard data with real tRPC queries once auth works.
3. **Secure PDF export (S):** Require authenticated parent access, switch to exported Prisma client, and ensure only owner can request exports; avoid embedding service keys in public handlers.
4. **Normalize Supabase env names (S):** Standardize on SERVICE_ROLE_KEY across AI/storage/API, update `.env.example` and validations, and fail fast on missing keys.
5. **Payments hardening and PRD alignment (M):** Align credit pack sizes/prices to PRD (20/50/100), complete Apple/Google receipt verification + Stripe webhook reconciliation, and add tests for credit ledger integrity.
6. **Finish onboarding flows (M):** Implement child profile creation/navigation in mobile and ensure avatar/pet flows gracefully handle missing profiles/credits.
7. **CI/typecheck sweep (M):** Re-run tsc/Vitest across workspaces, resolve the errors noted in `typescript-errors-report.md`, and add coverage reporting for API/AI critical paths.
8. **Observability (S):** Add Sentry/reporting to story generation, auth, and purchase flows; surface cron/job health via `/api/health` extensions or dashboards.
