# Video source attribution

- Local source file: `video_base_cc0.webm`
- Derived file: `video_base_cc0.mp4`
- Title: Incoherent sum of speckles.webm
- Author: Jacopo Bertolotti (Wikimedia Commons user: Berto)
- Source: https://commons.wikimedia.org/wiki/File:Incoherent_sum_of_speckles.webm
- License: CC0 1.0 Universal Public Domain Dedication
- Original publication date: 2022-07-29
- Download date: 2026-10-25
- Local format: MP4
- Conversion: The local MP4 file was derived from the original CC0 WebM file using CloudConvert

# Synthetic video dataset

The test videos derived from this source have synthetic GPS metadata
inserted exclusively for functional tests of GeoEvidence Correlator.

They do not represent real recordings, real locations or forensic evidence.

- `con_gps.mp4`: valid GPS metadata.
- `senza_gps.mp4`: no GPS metadata.
- `corrotto.mp4`: intentionally invalid file used to test error handling.

To regenerate the dataset, run:

```powershell
python .\scripts\genera_dataset_video.py --exiftool "PATH\TO\exiftool.exe" --overwrite