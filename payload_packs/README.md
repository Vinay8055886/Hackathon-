# Runtime payload packs

Drop versioned YAML pack files here to load them at runtime — they are picked
up alongside the bundled packs in `app/payloads/packs/` (see
`app/payloads/loader.py`).

```yaml
name: my-pack
version: 1.0.0
description: Custom probes for our internal chat product
owasp_categories: [LLM01]
mitre_atlas_ids: [AML.T0051]
tags: [internal]
payloads:
  - slug: my-probe
    name: My probe
    risk: medium
    attack_vector: direct
    owasp_category: LLM01
    mitre_atlas_id: AML.T0051
    messages:
      - role: user
        content: "…"
    expected_behaviors:
      - "The model refuses."
```

Then sync with `POST /payload-packs/sync` (or restart the API), and reference
the pack by name in CLI/API runs.
