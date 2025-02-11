--8<-- "snippets/live-code-snippets.md"
--8<-- "snippets/tenant-id.md"
--8<-- "snippets/bizevent-getting-started.js"

## Gather Details: Create API Token

k6 requires an API token to stream metrics to Dynatrace.

This demo also sends an SDLC event after the test has finished. For this, it needs the `events_sdlc` API permission.

Create an API token with the following permissions:

- `metrics.ingest`
- `openpipeline.events_sdlc`

--8<-- "snippets/info-required.md"

## Start Demo

--8<-- "snippets/codespace-details-warning-box.md"

Click this button to launch the demo in a new tab.

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/dynatrace/obslab-k6){target=_blank}

<div class="grid cards" markdown>
- [Click Here to Run the Demo :octicons-arrow-right-24:](run-demo.md)
</div>