## Feature Validation
- **Auth/Sign-up:** tRPC register/login rely on Supabase admin auth with rate limits and audit logging (`packages/api/src/routers/auth.ts`). Works in code but requires `SUPABASE_URL`/`SUPABASE_SERVICE_ROLE_KEY` at runtime; not exercised in this assessment.
- **Photo upload & avatars:** Uploads use Supabase signed URLs and COPPA consent checks (`packages/api/src/routers/avatar.ts`), but avatar generation imports the Vertex AI client singleton that throws when `GOOGLE_CLOUD_PROJECT` is missing (`packages/ai/src/imagen/client.ts:489-505`). `.env.example` does not supply Google project/credentials, so the flow currently fails before the server starts.
- **Story generation:** Uses Gemini + Nano Banana via `generateStoryAsync` (`packages/api/src/lib/generateStoryAsync.ts`) and the Gemini client that also requires `GOOGLE_CLOUD_PROJECT` (`packages/ai/src/gemini/client.ts:55-60`). Without Google credentials/buckets configured, stories cannot generate.
- **Credits & payments:** Stripe checkout and webhook handling are implemented with signature verification (`apps/web/app/api/webhooks/stripe/route.ts`). Apple/Google IAP verification exists but depends on `APPLE_SHARED_SECRET` and `GOOGLE_PLAY_SERVICE_ACCOUNT`; missing secrets return errors and there is no bundle/package validation beyond product ids.
- **PDF export:** Serverless route renders PDFs, uploads to Supabase Storage, and requires the service role key and `story-pdfs` bucket (`apps/web/app/api/generate-pdf/route.tsx:19-35`). Not validated in this run.
- **End-to-end:** Critical flows (avatar/story generation, PDF export) depend on Google/Supabase config that is absent by default; no end-to-end run performed.

## Code Quality & Correctness
- Good separation of concerns with tRPC routers, Prisma models, audit logs, and rate limiting; ownership and consent checks present for sensitive actions (`packages/api/src/routers/avatar.ts`, `auth.ts`).
- Environment validation enforces Supabase/Stripe in production (`packages/api/src/env.ts`) but omits required Google settings, allowing import-time crashes from AI clients.
- Singleton exports of AI clients are eager and will throw during module load when env is missing, blocking server startup (`packages/ai/src/imagen/client.ts:489-505`, `packages/ai/src/gemini/client.ts:55-60`).
- Prisma migrations exist but migration status against target databases was not checked; only two migration folders are present, risking drift.
- Testing footprint is sizable (54 test files detected), but no lint/test/build commands were run in this assessment; current pass/fail status unknown.

## Security Audit
- Stripe webhook handler verifies signatures and limits processing to credit purchases (`apps/web/app/api/webhooks/stripe/route.ts`).
- Cron routes enforce a bearer secret with constant-time comparison (`apps/web/app/api/cron/auth.ts:10-44`).
- Supabase service role keys are required for PDF export and storage; ensure deployment keeps them server-only to avoid leakage (`apps/web/app/api/generate-pdf/route.tsx:19-35`).
- IAP verification performs server-side receipt checks but lacks stricter bundle/package validation and depends on secrets not validated at startup.
- COPPA consent gating is enforced before photo uploads/avatars, and audit logging is pervasive across auth and credit flows.

## Blocking Issues
1. `GOOGLE_CLOUD_PROJECT` (and corresponding Google credentials) are missing from configuration; AI client singletons throw at import time, preventing the server from starting (`packages/ai/src/imagen/client.ts:489-505`, `packages/ai/src/gemini/client.ts:55-60`).
2. Vertex AI service account setup/credentials are not documented in `.env.example`, so avatar and story generation cannot run in production without manual, undocumented setup.
3. Pipeline health is unknown: lint/test/build were not executed, and Prisma migration status against the production DB is unverified.

## Nice-to-Have Improvements
- Add env validation and graceful fallbacks for Google/Vertex AI so non-AI routes still boot, and document required service account keys/buckets alongside `.env.example`.
- Add integration tests/mocks for avatar and story generation to validate credit reservation/refund logic without hitting external AI services.
- Include migration status checks in CI and a provisioning checklist for Supabase buckets (`temp-uploads`, `stories`, `story-pdfs`) and cron secrets.
