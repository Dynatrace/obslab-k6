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

=== "Run in Cloud"
    --8<-- "snippets/codespace-details-warning-box.md"

    Click this button to launch the demo in a new tab.

    [![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/dynatrace/obslab-k6){target=_blank}

=== "Run Locally"
    * Clone the repository to your local machine

    ```
    git clone https://github.com/dynatrace/obslab-k6
    ```

    * Open the folder in Visual Studio code
    * Ensure the [Microsoft Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers){target=_blank} and [Dev Containers CLI](https://code.visualstudio.com/docs/devcontainers/devcontainer-cli#_installation){target=_blank} are installed in VSCode
    * Open a new terminal in VSCode and set your environment variables as appropriate:

    ```
    set DT_ENVIRONMENT_ID=abc12345
    set DT_ENVIRONMENT_TYPE=live
    set DT_API_TOKEN=dt0c01.******.***********
    ```

    * Start Docker / Podman
    * Create the environment

    ```
    devcontainer up
    ```

    It will take a few moments but you should see:

    ```
    {"outcome":"success","containerId":"...","remoteUser":"root","remoteWorkspaceFolder":"/workspaces/obslab-k6"}
    ```

    * Connect to the demo environment. This will launch a new Visual Studio Code window
    ```
    devcontainer open
    ```

    In the new Visual Studio code window, open a new terminal and continue with the tutorial.

<div class="grid cards" markdown>
- [Click Here to Run the Demo :octicons-arrow-right-24:](run-demo.md)
</div>