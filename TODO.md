# TODO

Open work to finish shipping this integration through HACS. `git log` and the latest `Validate` run record what is already done; everything below is forward-looking.

## 1. Flip the repository to public

The HACS validator reads `custom_components/helios_kwl_ec300/manifest.json` and `hacs.json` over `raw.githubusercontent.com`, which 404s while the repo is private. That pins HACS validation at 2/9 and blocks every user from adding the repo as a custom repository. Public clears both.

- [ ] `gh repo edit frommf/helios-kwl-ec300 --visibility public --accept-visibility-change-consequences`
- [ ] Re-run `Validate` until the HACS job is green

**Done when** the raw manifest URL returns 200 and HACS validation reports 9/9.

## 2. Cut release v0.3.0

HACS takes the remote version from the newest GitHub Release tag; with none it shows a bare commit hash and offers no upgrade. The tag equals `manifest.json`'s `version` (rule in `AGENTS.md`).

- [ ] `git tag v0.3.0 && git push origin v0.3.0`
- [ ] `gh release create v0.3.0 --generate-notes`

**Done when** a Release exists whose tag matches the manifest version and HACS offers it as an upgrade.

## 3. Reach the HACS store (after 1–2)

A store listing makes the integration findable without a custom-repository URL. Open a PR to `hacs/default` (integration category) as the repo owner; it rides on the same green HACS + hassfest checks.

## 4. Polish (optional)

- [x] Swap the generated `brand/icon.png` and `brand/logo.png` for real brand art
- [x] Delete the unused `icon.svg` in the integration directory — the `brand/` folder is the icon source
