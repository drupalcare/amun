# Amun changelog

## Next release

- JavaScript: the search behavior is renamed `amunSearchSlide`; the 2.x name `amunThemeBehavior` keeps working as a deprecated alias, so a sub-theme that replaces or reads it is unaffected.
- Navigation: from 62rem the main menu fits its own box. Link padding is tighter between 62rem and 75rem, and the menu wraps onto a second row instead of running under the account menu or past the page edge.
- Accessibility: the heading color is darkened (#c1491a) so headings reach 4.5:1 on the light grey ground too.
- W3CSS Theme 3.x scheme tokens: the heading color and footer menu form border re-point the new `--w3css-custom-*` tokens of Midnight Ember (the old `--w-h1` and `--w-fm-inner-f-v` are no longer read), so amun's darker heading color shows again.
- CSS layers: the stylesheet is written in W3CSS Theme 3.x layers (`w3css.subtheme`, tokens, base, locked), with css-layers.json and scripts/css-layers-check.py; the library uses `drupal8_w3css_theme/base-layers` instead of the deprecated `d8w3css-global-styling`.
- Extend and Appearance pages: every module and theme description is a short, professional statement that begins with a verb; credits, links and version notes moved out of the info files.
- New W3CSS Theme logo as the theme's default logo (replace or turn it off in Appearance settings).

- Text follows the drupal.org standards: the theme description begins with a verb and its demo link no longer opens a new window, and the README follows the drupal.org README template (Installation and Configuration sections, project links, link text instead of bare URLs).
- Accessibility: the fixed search panel is printed only when its opener (in the horizontal main menu) is printed, so a site without a main menu no longer has a hidden but focusable search field.
