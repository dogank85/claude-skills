## Findings
- Schema models (29): Parent, ChildProfile, Avatar, PetCompanion, PhotoUpload, CreditPack, CreditTransaction, Subscription, SubscriptionUsage, PaymentTransaction, CancellationFeedback, WebhookEvent, AuditLog, PhotoDeletionAudit, PhotoDeletionJob, ParentConsentEvent, DataExportRequest, AccountDeletionRequest, Story, StoryGenerationJob, StoryMetadata, StorySafetyIncident, StoryProgress, StoryImage, StoryExport, OfflineCacheEntry, AuthRateLimit, PasswordRecoveryEvent, HealthSnapshot.
- API-used models (23, excluding tests): parent, childProfile, avatar, petCompanion, photoUpload, creditPack, creditTransaction, webhookEvent, auditLog, photoDeletionAudit, photoDeletionJob, parentConsentEvent, dataExportRequest, accountDeletionRequest, story, storyGenerationJob, storyMetadata, storySafetyIncident, storyProgress, storyImage, authRateLimit, passwordRecoveryEvent, healthSnapshot.
- Orphaned models (not referenced by API runtime code): Subscription, SubscriptionUsage, PaymentTransaction, CancellationFeedback, StoryExport, OfflineCacheEntry.
- Index recommendations: (1) child_profiles(parent_id, created_at) to speed ordered child lookups in privacy dashboard and credit balance helpers; (2) account_deletion_requests(parent_id, status, created_at) to accelerate active deletion checks; (3) data_export_requests(parent_id, status, created_at) to support recent pending-export lookups with status filtering.

## Method
- Reviewed packages/database/prisma/schema.prisma to enumerate models and existing indexes.
- Scanned packages/api/src (excluding tests/specs) for prisma/transaction delegate usage to map referenced models (`rg -o "(?:ctx\\.prisma|prisma|tx)\\.[a-zA-Z]+" ...`).
- Compared schema models to API usage to flag unused models and assess query patterns for potential missing composite indexes.
