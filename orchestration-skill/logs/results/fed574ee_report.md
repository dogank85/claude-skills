# Production Readiness Report: Environment & Configuration Audit

**Date:** December 6, 2025
**Auditor:** Gemini CLI Agent

## 1. Executive Summary
The HeroKid application is largely prepared for production deployment, but several critical configuration gaps exist, primarily related to environment variable consistency and payment provider setup details. The Stripe integration for credit packs uses server-side dynamic pricing, reducing reliance on specific Stripe Price IDs for one-off purchases, but subscription logic (not fully audited here but referenced) likely requires them. Security for Cron jobs and Webhooks is implemented but requires strict secret management.

## 2. Environment Variable Audit

### 2.1. Critical Missing Variables in `.env.example`
The following variables are referenced in the codebase or documentation but are missing from `.env.example`. They should be added to ensure developers and Ops have a complete configuration template.

| Variable | Priority | Status | Impact |
| :--- | :--- | :--- | :--- |
| `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` | High | Missing | Required for client-side Stripe Elements (if used in future) and listed in `docs/ENV_VARIABLES.md`. |
| `NANO_BANANA_API_KEY` | Medium | Missing | Required for future Avatar generation features. |
| `TEST_DATABASE_URL` | Medium | Missing | Essential for running integration tests without polluting the dev database. |
| `EXPO_PUBLIC_KEYCHAIN_SERVICE` | Low | Missing | Mobile auth token storage (has hardcoded fallback). |

### 2.2. Configuration Consistency
*   **Stripe Price IDs:** `apps/web/app/purchase/page.tsx` references `NEXT_PUBLIC_STRIPE_PRICE_*_CREDIT`, but the backend mutation `createStripeCheckout` in `packages/api/src/routers/credits.ts` uses hardcoded values (`CREDIT_PACK_PRICES`). This discrepancy should be reconciled to avoid pricing mismatch between UI labels and actual charges.
*   **Cron Secrets:** `CRON_SECRET` is correctly implemented in `apps/web/app/api/cron/*` routes, protecting them from unauthorized access.

## 3. Service Configuration Requirements

### 3.1. Stripe (Payments)
*   **Mode:** `hosted` (Stripe Checkout).
*   **Required Secrets:**
    *   `STRIPE_SECRET_KEY`: For server-side API calls.
    *   `STRIPE_WEBHOOK_SECRET`: For verifying webhook signatures (CRITICAL for security).
*   **Pricing Strategy:**
    *   **Credit Packs:** Dynamic pricing via `price_data` in `credits.ts` (0.99/4.49/7.99).
    *   **Subscriptions:** Likely requires configured Price IDs in Stripe Dashboard mapped to `STRIPE_PRICE_*` env vars.

### 3.2. Resend (Transactional Emails)
*   **Required Secrets:**
    *   `RESEND_API_KEY`: For sending emails.
    *   `TRANSACTIONAL_EMAIL_FROM`: Verified sender domain (e.g., `privacy@herokid.com`).
    *   `HEALTH_ALERT_EMAIL_FROM` / `_TO`: For monitoring alerts.

### 3.3. Security & Infrastructure
*   **Cron Jobs:** `CRON_SECRET` must be a strong, random string set in Vercel/Infra and used by the scheduler (e.g., GitHub Actions or Vercel Cron).
*   **Supabase:** Production keys (`SUPABASE_PROD_*`) must be rotated and distinct from Dev keys.

## 4. Deployment Checklist

### Pre-Launch
1.  [ ] **Environment Setup:** Copy `.env.example` to `.env.production` (or Vercel env vars) and fill in ALL values.
2.  [ ] **Stripe Setup:**
    *   Create Webhook Endpoint in Stripe Dashboard pointing to `https://<prod-domain>/api/webhooks/stripe`.
    *   Copy Webhook Signing Secret to `STRIPE_WEBHOOK_SECRET`.
    *   (If Subscriptions used) Create Products/Prices in Stripe and map IDs to `STRIPE_PRICE_*` vars.
3.  [ ] **Resend Setup:** Verify domain DNS records for `TRANSACTIONAL_EMAIL_FROM` to ensure deliverability.
4.  [ ] **Secret Generation:** Generate a strong `CRON_SECRET` and add to Vercel Env Vars.
5.  [ ] **Testing:** Run `pnpm test` locally with `TEST_DATABASE_URL` configured to ensure no regressions.

### Post-Launch
1.  [ ] **Monitor:** Check Sentry for `CRON_SECRET` auth failures or Stripe Webhook signature errors.
2.  [ ] **Verify:** Perform a real $0.99 credit purchase to verify the end-to-end flow (Stripe -> Webhook -> DB).

## 5. Risk Assessment
*   **High Risk:** Deploying without `STRIPE_WEBHOOK_SECRET` allows attackers to forge payment events, potentially granting unlimited free credits.
*   **High Risk:** Deploying without `CRON_SECRET` exposes resource-intensive operations (photo deletion, account wiping) to public DoS attacks.
*   **Medium Risk:** Pricing mismatch if `credits.ts` hardcoded values differ from marketing pages or Stripe Dashboard configurations.

## 6. Recommendations
1.  **Immediate:** Add missing variables to `.env.example`.
2.  **Refactor:** Update `credits.ts` to use Environment Variables for pricing instead of hardcoded values, ensuring a "Single Source of Truth" for pricing.
3.  **Documentation:** Update `docs/ENV_VARIABLES.md` with the "Missing Variables" identified.
