# Analytics and Error Tracking Setup

Maxwell includes optional but recommended analytics and error tracking integrations.

## PostHog Analytics

PostHog tracks key user actions to help understand product usage and identify improvement opportunities.

### Setup

1. Create a free account at [posthog.com](https://posthog.com)
2. Get your Project API Key from Settings → Project
3. Add to `frontend/.env`:
   ```
   VITE_POSTHOG_KEY=phc_your_key_here
   VITE_POSTHOG_HOST=https://app.posthog.com
   ```
4. Restart the frontend dev server

### Events Tracked

- **Manuscript Events**: Created, opened, deleted
- **Chapter Events**: Created, deleted
- **Feature Usage**: Codex, Timeline, Analytics, Coach, Recap, Time Machine
- **Export Events**: Started, completed (with format and word count)
- **Onboarding**: Started, completed, skipped, tour completed/skipped
- **Writing**: Words written (session tracking)

### Privacy

- Analytics is **disabled by default** without a VITE_POSTHOG_KEY
- No personally identifiable information is collected
- User IDs are only set when authentication is added (Phase 3+)

---

## Sentry Error Tracking

Sentry captures JavaScript errors and provides debugging context including:
- Stack traces
- User actions leading to the error (breadcrumbs)
- Browser and OS information
- Session replay for errors (with sensitive data masked)

### Setup

1. Create a free account at [sentry.io](https://sentry.io)
2. Create a new project (JavaScript/React)
3. Get your DSN from Settings → Client Keys (DSN)
4. Add to `frontend/.env`:
   ```
   VITE_SENTRY_DSN=https://your_key@sentry.io/your_project
   ```
5. Restart the frontend dev server

### Configuration

- **Production**: 10% performance tracing, 10% session replay, 100% error replay
- **Development**: Errors are logged to console by default
- **Force in Dev**: Set `VITE_SENTRY_ENABLED=true` to test Sentry locally

### Error Handling

The app includes:
- **Error Boundary**: Catches React component errors and shows a friendly fallback UI
- **Auto-filtering**: Ignores common harmless errors (e.g., ResizeObserver)
- **Source Maps**: Enabled for debugging production errors

### Test Error Tracking

To verify Sentry is working, you can trigger a test error:
```javascript
// In browser console
throw new Error('Test error for Sentry');
```

The error should appear in your Sentry dashboard within seconds.

---

## Development Workflow

### With Analytics/Error Tracking (Recommended for Beta+)

```bash
# Frontend
cd frontend
cp .env.example .env
# Add your VITE_POSTHOG_KEY and VITE_SENTRY_DSN
npm run dev
```

### Without Analytics/Error Tracking (Local Development)

Just don't set the environment variables. The app will:
- Log warnings to console that analytics/tracking isn't configured
- Function normally without sending any data
- Show initialization messages only if keys are present

---

## Key Metrics for Phase 1 Launch

Track these in PostHog to measure beta success:

1. **Activation**: % of users who create their first manuscript
2. **Engagement**: Average manuscripts per user
3. **Feature Usage**: % using Codex, Timeline, Analytics, Export
4. **Export Rate**: % of users who export (validates writing intent)
5. **Onboarding**: Completion rate of welcome flow and tour

---

## Files Modified

- `/frontend/src/lib/analytics.ts` - PostHog integration
- `/frontend/src/lib/sentry.ts` - Sentry integration
- `/frontend/src/main.tsx` - Initialize both services
- `/frontend/src/App.tsx` - Track navigation and onboarding
- `/frontend/src/components/Export/ExportModal.tsx` - Track exports
- `/frontend/src/components/ManuscriptLibrary.tsx` - Track manuscript CRUD
- `/frontend/.env.example` - Environment variable template

---

## Next Steps for Phase 2+

When adding user authentication:
- Call `identifyUser(userId, { email, name })` after login
- Call `setUserContext(userId, email)` for Sentry
- Track user cohorts (e.g., beta users, YouTuber referrals)
- Add A/B testing flags via PostHog feature flags
