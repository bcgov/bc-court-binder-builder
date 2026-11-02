# macOS DMG window

What Finder shows when the DMG opens: a 660 x 400 pt background with a navy header band and an
arrow, with the app icon on the left and the `Applications` link on the right. `package.sh` copies
these files into the image; nothing here is generated at build time, so the DMG builds with a plain
`hdiutil create -srcfolder` (no Finder scripting on CI).

Approach adapted from the PdfCraft packaging (`packaging/macos/dmg/` in https://github.com/richfrem/pdfcraft).

| File | What |
|---|---|
| `background.tiff` | The background at 1x (660 x 400 px, 72 dpi) and 2x (1320 x 800 px, 144 dpi) in one HiDPI TIFF (16-colour palette, Deflate, sRGB). Goes to `.background/background.tiff`. |
| `dmg-layout.DS_Store` | Finder's view settings for the volume: window size, icon size 128, `Court binder builder.app` at (170, 215), `Applications` at (490, 215), and the background. Goes to `.DS_Store` in the image; named so it isn't mistaken for (or ignored like) a Finder-generated `.DS_Store`. |
| `generate.py` | Draws `background.tiff` (with Pillow) and writes `dmg-layout.DS_Store`. |

## The volume name has no version

The mounted volume is called `Court binder builder`, not `Court binder builder <version>`. The layout
points at the background through an alias that includes the volume name, and Finder resolves it by
that name: with a versioned name the window keeps its size and icon positions but shows no
background. The DMG file name (`court-binder-builder-<version>-macos-<arch>.dmg`) still carries the
version.

## Rules

- **Finder draws the icon labels in black in light and dark mode** when a window has a background,
  so the area under both icons stays light (the design system's off-white).
- **Nothing goes inside the icon boxes:** artwork keeps clear of each 128 pt icon box and the label
  under it.

## Regenerate

Edit the colours, text or layout constants in `generate.py`, then, on a Mac (the script reads the
system Helvetica font; the committed outputs are then font-independent):

```sh
pip install 'pillow>=12' ds_store==1.3.3 mac_alias==2.2.3
python3 packaging/macos/dmg/generate.py
```

Keep `VOLUME` and `ICONS` in sync with `package.sh`. Colours follow the B.C. Government Design
System tokens (`#013366` navy, `#FAF9F8` surface).
