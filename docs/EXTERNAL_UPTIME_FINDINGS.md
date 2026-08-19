# External uptime findings

Source: https://huggingface.co/docs/hub/en/spaces-overview

The official Hugging Face Spaces overview states that free hardware Spaces go to sleep after a period of inactivity and stop executing. It also states that upgraded hardware can run indefinitely, while free compute has non-persistent disk by default.

Source: https://huggingface.co/docs/huggingface_hub/en/package_reference/space_runtime

The official runtime reference states that a free `cpu-basic` Space goes to sleep after 48 hours by default, while an upgraded hardware Space does not automatically go to sleep. The runtime API exposes lifecycle operations such as restart, pause, logs and hardware management.

Source: https://huggingface.co/docs/huggingface_hub/en/guides/manage-spaces

The official management guide documents `get_space_runtime`, `fetch_space_logs`, `restart_space`, `pause_space`, `request_space_hardware`, secrets/variables management and Space runtime lifecycle behavior. It states that `cpu-basic` cannot configure a custom sleep time and is automatically paused after 48 hours of inactivity.

Observed project state on 2026-08-19:

- Space `Qalam/Nuclear-Intelligence` was running on `cpu-basic` with one replica.
- The Space commit after deployment was `4c1ca65503f6370f768ea2b236e2542cfe8373f7`.
- Dataset commits appeared immediately after the Space started, proving one startup cycle occurred, but this alone does not prove continuous uptime.
- The existing keep-alive workflow only requested the Hugging Face web page and `/health`; it did not restart a failed Space, inspect runtime stage, or recover from sleep/build failure.
- `scripts/keep_alive.py` referenced `requests` without importing it and ran an infinite local loop that was not the GitHub Actions implementation.

Conclusion: free `cpu-basic` Space hosting cannot be truthfully described as guaranteed 24/7. A real always-on deployment requires upgraded Space hardware or a separate persistent worker/host, plus external state persistence and watchdog/restart logic.
