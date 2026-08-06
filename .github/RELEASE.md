# Release Checklist

Use this checklist when publishing a public version of Wannabe Stem.

1. Merge the release branch into `develop`, then verify a clean checkout.
2. Update `pyproject.toml` and `CHANGELOG.md` with the version and user-visible changes.
3. Build the Docker image and smoke-test an MP3 and a WAV on Mac and Windows when available.
4. Create the bandmate package with `./scripts/make_release_package.sh`.
5. Attach the SHA-256 checksum file generated beside the ZIP and include its value in the GitHub Release notes.
6. Create an annotated Git tag such as `v0.1.0`, then create the matching GitHub Release.
7. Attach the generated ZIP, checksum, and concise release notes. Do not attach copyrighted music, processed stems, or cached model files unless their licenses explicitly allow redistribution.
8. Confirm the release page, README links, Docker instructions, and issue links work while signed out of GitHub.
