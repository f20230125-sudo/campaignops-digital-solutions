# Verification record — 18 October 2026

The public application is https://campaignops-digital-solutions.vercel.app.

| Check | Result |
| --- | --- |
| Python pipeline, import and report reconciliation tests | 10 passed |
| Native WordPress lifecycle, revisions, permissions and journey-ID assertions | 13 passed |
| Browser checks against the public URL, including the real WordPress editor | 23 passed |
| Desktop and mobile axe scans of representative views | No detected violations |
| Production install and build | Vercel READY using npm ci and Next.js |
| TypeScript and source lint | Passed |
| Local WordPress persistence | Published asset IDs unchanged after a real process restart |

Machine-readable receipts are in [`qa/evidence`](../qa/evidence). The browser run reproduced the seeded mobile defect, changed its governance setting in the native editor, saved the post, completed a new mobile registration and exported the WordPress ledger. Importing those events produced two observed-test sessions and one registration, with no rejected records. This is an isolated functionality test, not measured historical conversion lift.

The browser emitted a ViewTransition opt-in notice during WordPress iframe navigation. The exact message is retained in the browser receipt as `browserNotices`; other page errors fail the check. The actions completed. Accessibility scans only cover issues that automated tools detect and are not a complete accessibility certification.

The reporting artifact contains 8,861 accepted synthetic events, 73 quarantined rows and 228 populated reporting scopes. Input hashes and the calculation fingerprint accompany the downloads. Seventeen weekly PDF summaries are generated. The two currently indexed Gemini drafts have genuine saved provider receipts and match the published scope and data fingerprint.

The GitHub workflow is configured for pushes, manual runs and a weekly schedule. A successful GitHub Actions run is not claimed before source publication; the production build and recorded checks above were actually executed.
