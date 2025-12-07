# Task Report – Security Fix Validation

## Execution Log
- `pnpm install` (root): failed – network restriction (`getaddrinfo ENOTFOUND registry.npmjs.org`) prevented dependency download across all workspaces, leaving `node_modules` absent.
- `pnpm --filter @herokid/api test -- story-credit-gating.test.ts`: failed instantly because `vitest` is not available (`sh: vitest: command not found`; warning that `node_modules` is missing).
- `pnpm --filter @herokid/web test -- apps/web/app/api/cron/`: same failure signature (`vitest: command not found`; missing `node_modules`).

## Security Fix Verification (code inspection)
- **Stripe webhook signature verification**: `apps/web/app/api/webhooks/stripe/route.ts` enforces `STRIPE_SECRET_KEY`/`STRIPE_WEBHOOK_SECRET` at module load (throws if missing) and uses `stripe.webhooks.constructEvent` with the webhook secret. Missing or invalid signatures return `401`, preventing processing.
- **Credit reservation atomicity**: `packages/api/src/routers/credits.ts` wraps deductions in `prisma.$transaction`, checks balance, and uses `updateMany` with `creditBalance >= required` guard to avoid race-induced negatives; purchases also run in transactions with audit logs.
- **Cron auth fails closed**: `apps/web/app/api/cron/auth.ts` rejects requests when `CRON_SECRET` is absent or mismatched, using bearer token + constant-time compare and returning `401` early.
- **COPPA emails**: COPPA parental verification template exists at `supabase/auth/email-templates/parent-verification.html`, aligning with compliance docs; consent copy present.

## Environment Variable Audit
- `.env.example` present; based on `docs/ENV_VARIABLES.md`, the following required/expected variables are **missing** from the template:
  - `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY`
  - `NANO_BANANA_API_KEY`
  - `TEST_DATABASE_URL`
  - `EXPO_PUBLIC_KEYCHAIN_SERVICE`
  - `SLACK_WEBHOOK_URL`
  - `SKIP_APPLE_VERIFICATION_CHECK`
  - `SKIP_GOOGLE_VERIFICATION_CHECK`
  - `COPPA_CONSENT_WEBHOOK_URL` / `CONSENT_EVENTS_WEBHOOK_URL`
  - `PHOTO_DELETION_TTL_HOURS` (code uses this; template only has `TEMP_UPLOADS_TTL_HOURS`)
  - `GIT_SHA` / `API_VERSION` (release tracking, CI-provided)

## Outstanding Issues
- Dependencies could not be installed due to blocked registry access; as a result, vitest is unavailable and requested test suites could not run. No code changes made.
- Testing remains pending until dependencies can be installed (offline cache or restored network).
