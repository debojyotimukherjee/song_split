# Open-Source Notices

Wannabe Stem depends on several open-source projects. Their licenses apply to their respective code and, where relevant, downloaded model files.

| Project | Role in Wannabe Stem | License / attribution |
|---|---|---|
| [Demucs](https://github.com/facebookresearch/demucs) | Baseline music source separation | MIT License. Demucs supplies the `htdemucs_6s` model used for the baseline stems. |
| [Audio Separator](https://github.com/nomadkaraoke/python-audio-separator) and [Ultimate Vocal Remover](https://github.com/Anjok07/ultimatevocalremovergui) | Optional specialist separation experiments | MIT License. Please retain attribution to Audio Separator, UVR, and their model authors when integrating related models. |
| [AccordoAI](https://pypi.org/project/accordoai/) | Chord classification | MIT License. |
| [PyMusicKit](https://pypi.org/project/pymusickit/) | Key-estimation support | MIT License. |
| [librosa](https://librosa.org/) | Audio analysis and tempo estimation | ISC License. |
| [FFmpeg](https://ffmpeg.org/) | Audio conversion, filters, and rendering | LGPL/GPL components may apply depending on the distributed build. The Docker image uses the distribution-provided FFmpeg package. |

Model weights can have terms separate from the libraries that download or run them. Before adding, redistributing, or enabling a new model by default, review that model's own license and usage terms.

Names and trademarks belong to their respective owners. This project is not affiliated with or endorsed by those projects or their maintainers.
