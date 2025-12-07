# Error Message Audit Summary

**Date:** December 7, 2025
**Files Reviewed:** 14 router files in `packages/api/src/routers/`
**Total Error Messages Reviewed (examples):** ~15 unique user-facing error messages, with 5 identified as needing improvement.

## Technical Errors Found (5 examples)

Here are 5 examples of error messages identified as too technical or potentially exposing internal details, along with suggested user-friendly alternatives:

### 1. `Authentication service is not configured. Please contact support.`

*   **File(s) Found:** `auth.ts` (in `register`, `login`, `refreshSession`, `resendVerificationEmail`)
*   **Issue:** Exposes internal system configuration details ("Authentication service is not configured").
*   **Suggested Improvement:** `We're experiencing a technical issue with our authentication system. Please try again in a few minutes or contact support if the problem persists.`

### 2. `Supabase is not configured`

*   **File(s) Found:** `auth.ts` (in `completePasswordReset`)
*   **Issue:** Highly technical, reveals internal infrastructure detail ("Supabase").
*   **Suggested Improvement:** `We're currently unable to process password reset requests due to a system issue. Please try again later.`

### 3. `INSUFFICIENT_CREDITS`

*   **File(s) Found:** `story.ts` (in `reserveCreditsForStory`)
*   **Issue:** Exposes an internal error code as a user-facing message.
*   **Suggested Improvement:** `You do not have enough credits to generate this story. Please purchase more credits.`

### 4. `Your account is ${parent.status.toLowerCase()}. Please contact support.`

*   **File(s) Found:** `auth.ts` (in `login` when account is not active, e.g., `DELETION_PENDING`)
*   **Issue:** Potentially exposes internal status strings directly to the user (e.g., "deletion_pending").
*   **Suggested Improvement (conditional for DELETION_PENDING):** `Your account is currently being processed for deletion. Please contact support.` (For other inactive states, consider more general messages like "Your account is inactive. Please contact support.")

### 5. `error.message` directly from Supabase resendVerificationEmail

*   **File(s) Found:** `auth.ts` (in `resendVerificationEmail` `if (error)` block)
*   **Issue:** Direct exposure of error messages from an external service (Supabase) can reveal technical details or potentially sensitive information not intended for the end-user.
*   **Suggested Improvement:** `We could not resend the verification email at this time. Please try again later or contact support.`

## Security Concerns

*   **Exposure of Internal Codes/Details:** Direct use of internal codes like `INSUFFICIENT_CREDITS` or infrastructure details like "Supabase is not configured" should be avoided. While not always a direct security vulnerability, it can provide attackers with more information about the system's architecture and implementation details.
*   **External Service Error Messages:** Directly passing `error.message` from external services (e.g., Supabase, Apple/Google verification errors) to the client can expose technical details about those services or even sensitive operational data. It's best to wrap these in generic, user-friendly messages.

---
This concludes the quick UX validation task.
