# L43 — photography source

Supplied by the photographer (photographer.ramee@gmail.com) as a Google Drive folder,
shared "anyone with the link, reader" on 2 Sep 2026:

https://drive.google.com/drive/folders/1H0uRgJOpDNugSgPPmj1mWnxNjh6wp8Nk

## Why the frames are not in this folder yet

The folder is link-shared only, not shared to alex.whayman@gmail.com directly, so its
files are not visible to the Drive API from a build session, and the build environment
cannot reach drive.google.com. The frames therefore have to be pulled by hand once.

## Pulling them in

1. Open the folder link above, select all, and download (Drive gives you a zip).
2. Resize to 1800px on the long edge at quality 72 (the README budget: ~2.4 MB a page
   for three frames against the 16 MB artifact ceiling). For example:

       magick '*.jpg' -resize '1800x1800>' -quality 72 -set filename:f '%t' '%[filename:f].jpg'

3. Name the frames `01-`, `02-`, `03-` ... The first alphabetically becomes the hero,
   the rest form the two-up gallery.
4. Hold back any frame that shows an identifiable person until they have agreed to
   publication. Put it outside `assets/`, not in here.
5. Drop at most one walkthrough video (`.mp4`, `.webm` or `.mov`, target ~8 MB raw) in
   here as well, or leave the `links[]` video entry to the Drive-hosted copy.
6. Rebuild and republish:

       node resale/build/build-resale.mjs

Until then the brochure carries the Drive folder as a "Photography" link instead of an
embedded gallery, and says so.
