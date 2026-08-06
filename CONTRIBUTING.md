# Contributing to Wannabe Stem

Thanks for helping make rehearsal a little easier.

## Before You Start

- Search existing issues and pull requests before opening a new one.
- For a substantial feature, open an issue or discussion first so the approach can be agreed before implementation.
- Do not commit songs, stems, model downloads, API tokens, personal data, or other large generated files. The repository's `.gitignore` excludes the local `data/` folder for this reason.

## Development Setup

1. Fork the repository and create a branch from `develop`.
2. Start the app with `docker compose up --build api`.
3. Make focused changes and keep the local-first, privacy-first product promise intact.
4. Run the applicable tests or smoke checks before opening a pull request.

## Pull Requests

- Explain the user-visible change and how you verified it.
- Keep unrelated refactors out of the same pull request.
- Update the README when installation, controls, supported formats, storage, or privacy behavior changes.
- Call out any change that makes a network request, downloads a model, or changes how audio is stored or processed.

## Audio Quality Contributions

Separation quality varies from recording to recording. Avoid presenting a heuristic or reconstructed track as a ground-truth isolated stem. Include a short before/after description and settings used when proposing changes to the audio pipeline.
