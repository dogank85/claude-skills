# HeroKid - Fresh Eyes Production Readiness Report

**Date:** December 6, 2025
**Scope:** Full Codebase & Architecture Review

---

## 1. User Journey & Feature Validation

### ✅ Story Generation (Core Loop)
The "Happy Path" for story generation is well-implemented:
-   **Logic:** `generateStoryAsync` in `packages/api` correctly orchestrates the Text -> Image -> Storage pipeline.
-   **State Management:** Uses `StoryGenerationJob` table to track async progress, which is robust against timeouts.
-   **UX:** The API exposes granular progress updates (30% -> 70% -> 100%), allowing for a polished frontend loading state.

### ⚠️ Monetization Flow
-   **Credits:** The backend logic in `credits.ts` is excellent. It uses `prisma.$transaction` with row locking (`FOR UPDATE` equivalent) to prevent double-spending and race conditions.
-   **Purchase:** The `createStripeCheckout` mutation exists but relies on **placeholder environment variables**, meaning it will fail in production.
-   **Mobile IAP:** Code analysis of `apps/mobile/src/screens/PurchaseScreen.tsx` reveals a critical TODO: `// TODO: Initialize IAP when react-native-iap is added`. This suggests the mobile app cannot currently process in-app purchases, despite the backend being ready.

### ✅ Compliance & Privacy (COPPA)
-   **Photo Deletion:** The `delete-expired-photos.mjs` script is correctly set up as a Cron job.
-   **Consent:** Parental consent flows are implemented.

---

## 2. Technical Health Assessment

### 🔴 Build & Test Status
-   **Type Check Failed:** Running `pnpm typecheck` in `packages/api` failed with **35 errors**.
    -   *Locations:* `src/routers/library.test.ts` and `src/routers/story.integration.test.ts`.
    -   *Cause:* Malformed code/comments and duplicate imports (copy-paste errors).
    -   *Impact:* CI/CD pipelines will likely fail, preventing deployment.

### 🟡 Code Quality & Tech Debt
-   **Hardcoded Values:** In `packages/api/src/lib/generateStoryAsync.ts`, the safety score is hardcoded:
    ```typescript
    safetyScore: 1.0, // TODO: Use actual safety score from result
    ```
    **Risk:** High. This effectively disables the automated safety filter for generated images, potentially allowing inappropriate content to be shown to children.

-   **Dependencies:** `apps/mobile` lists `react-native-iap` in `package.json`, but the UI code comments suggest it's not fully integrated.

---

## 3. Critical Issues & Blockers

| ID | Severity | Issue | Impact |
|----|----------|-------|--------|
| **BLK-01** | **CRITICAL** | **Stripe Keys Missing** | Users cannot purchase credits on Web. |
| **BLK-02** | **CRITICAL** | **Mobile IAP Incomplete** | Users cannot purchase credits on Mobile (`PurchaseScreen.tsx` TODOs). |
| **BLK-03** | **CRITICAL** | **Safety Score Bypass** | AI content safety checks are effectively disabled. |
| **BLK-04** | **HIGH** | **Broken Tests** | `packages/api` has 35 compilation errors, blocking CI/CD. |

---

## 4. Go/No-Go Recommendation

**VERDICT: NO-GO**

The project is **85-90% complete** but fails on the "Last Mile" of integration.

**Immediate Remediation Plan:**
1.  **Fix Tests:** Spend 1-2 hours fixing the syntax errors in `library.test.ts` and `story.integration.test.ts`.
2.  **Connect Safety Score:** Update `generateStoryAsync.ts` to use the actual `safetyScore` returned from `nanoBananaClient`.
3.  **Verify Mobile IAP:** Manually verify if the Mobile Purchase Screen works. If not, implement the missing wiring.
4.  **Config:** Inject real Stripe Test keys and verify a purchase flow.

Once these 4 items are resolved, the project will be ready for a "Soft Launch".
