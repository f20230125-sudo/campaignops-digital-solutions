# WordPress runbook

## Browser demo

Open Content operations and launch WordPress. This loads a real WordPress 7.0 installation with PHP 8.3 in the browser using the official Playground client. Loading the dashboard alone does not download the WordPress runtime.

The plugin registers a REST-enabled `campaign_asset` post type with native editor, author, custom fields and revision support. Asset/campaign IDs, owner, review date, reference link and mobile readiness are revision-enabled metadata. Native user capabilities control editing and publication. The embedded sandbox is an isolated demonstration with a local administrator, not a shared production CMS.

Open the hepatitis landing asset. Its registration action is deliberately hidden below 600px. In the editor's Settings sidebar, open the post tab and CampaignOps governance, enable **Registration visible on mobile**, save and publish. Visit the page at a narrow width, open the action and complete the fictional registration. The page creates a random session ID; no name or email is collected and nothing is sent.

Refresh the dashboard inventory and test summary. Export the JSON test ledger. Import it separately:

```sh
python -m pipeline.observed wordpress-test-events.json
```

The output is `runtime/observed/observed-metrics.json`, marked `observed_test`. Historical synthetic metrics are never modified. Only registration conversion is measured by this collector; email, attendance and dwell-based engagement metrics remain unavailable.

Use the native Revisions interface to inspect and restore content and governance metadata. Export the sandbox ZIP before closing or refreshing the dashboard page. Your browser sandbox changes are not shared or automatically persisted after the page closes.

## Durable local environment

```sh
npm ci
python scripts/package-wordpress.py
npm run wp:local
```

Open the URL printed by the official Playground CLI. PHP and Docker installations are unnecessary. `scripts/wordpress-local.mjs` explicitly mounts `runtime/wordpress/wp-content`, keeping SQLite and WordPress state under the project directory, including on Windows. That directory is gitignored. Subsequent runs reuse it; the plugin seeds assets only once. Keep a ZIP backup before changing runtime versions. The Blueprint bundle contains its plugin and seed records, so it is portable.

## REST contract and permissions

`/wp-json/campaignops/v1/inventory`: GET, requires `edit_posts` and native WordPress cookie authentication/REST nonce.

`/wp-json/campaignops/v1/events`: GET requires `edit_posts`. POST records a journey only with the page-issued journey nonce, an existing published campaign asset, an allowed event kind/market/device, and constrained random IDs. IDs are idempotent; conflicting IDs return 409. Server UTC timestamps and campaign IDs come from WordPress. The ledger is bounded to 500 records. These controls suit an isolated demo, not a production analytics collector.

Core post editing, statuses and revisions use WordPress's native REST endpoints and capability checks. The dashboard dispatches two fixed native REST reads inside the visitor's administrator sandbox; each endpoint's capability callback still runs; visitors cannot submit PHP code.
