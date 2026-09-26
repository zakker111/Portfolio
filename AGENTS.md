# AGENTS.md — guide for AI agents working on this site

Single-file static portfolio on GitHub Pages.
One project = one `<article class="project">` in `#projectList` with `id="p-<slug>"`, `data-num`, `data-title`, `style --acc`, and links `a.u-live` / `a.u-src` / `a.u-rd`, a `.p-status` block and one `canvas[data-tile]` (`aetheria` | `roguelike` | `voxel` | `keikat`).

To add a project: copy the TEMPLATE block, uncomment, and edit.
Colors/fonts: only the `:root` block at the top of `<style>`.
Content is plain HTML; the script only enhances. The page must stay usable with JavaScript off.
