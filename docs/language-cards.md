# Top Languages maintenance

`Update Top Languages` runs on GitHub Actions daily at 00:17 UTC (09:17 JST), and can also be run manually. Scheduled runs may be delayed by GitHub.

## Data and publication

- Counts one **primary language per owned, non-fork repository**, including public, private, and archived repositories.
- Excludes repositories for which GitHub has not detected a primary language.
- Displays the seven largest language groups, plus `Other`. Percentages measure repository counts, not source-code bytes or proficiency.
- Only queries visibility and language metadata. Repository names, URLs, descriptions, source files, commit messages, and author details are not requested.
- Publishes only `assets/languages-light.svg` and `assets/languages-dark.svg`. Their accessible descriptions contain aggregate language counts.
- The other profile statistics continue to use the public card service.

## One-time credential setup

Create a **fine-grained personal access token** owned by the profile owner:

- Resource owner: `TERUZvxght`.
- Repository access: **All repositories** under that owner, to include future repositories automatically.
- Repository permissions: **Metadata: Read-only** only. No contents, administration, workflow, or write access is needed by this token.
- Account permissions: none.
- Set an expiration and renew the token when needed.

Save it in this repository's **Settings → Secrets and variables → Actions → New repository secret** as `PROFILE_LANGUAGES_TOKEN`. Do not put the token in files, the README, issues, or a chat message.

The dedicated token is provided only to the metadata aggregation step. The separate, built-in GitHub Actions token pushes the two generated images to this profile repository.

Run **Actions → Update Top Languages → Run workflow** after setting or replacing the secret. Confirm the run succeeds and the card date updates. A missing or expired token, incomplete query, wrong token owner, or no visible private repositories stops the update and preserves the existing cards.

## Local verification

With GitHub CLI authenticated as the profile owner:

```sh
python3 -m unittest discover -s scripts -p 'test_*.py'
python3 scripts/update_languages.py --owner TERUZvxght
```

The script does not write raw API responses or echo them in failures. Do not enable shell tracing or HTTP debug logging in the workflow.
