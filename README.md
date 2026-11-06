# Amun

Amun is a sub-theme of W3CSS Theme (machine name `drupal8_w3css_theme`). It puts
a sticky navigation bar with the main menu, the account menu and a search button
at the top of the page, and the site header below it.

- Project page: [drupal.org/project/amun](https://www.drupal.org/project/amun)
- Issue queue:
  [drupal.org/project/issues/amun](https://www.drupal.org/project/issues/amun)


## Requirements

- Drupal 11.3 or later, or Drupal 12.
- W3CSS Theme 3.0. Install it first. Amun does not work without it, and it is
  the release that Amun's class names and settings follow.


## Installation

1. Install W3CSS Theme 3.0 (for example `composer require drupal/d8w3css`).
1. Install Amun into `themes/contrib`, for example
   `composer require drupal/amun`.
1. Go to Appearance (`/admin/appearance`) and scroll to "Amun".
1. Click "Install and set as default".

With Drush: `drush theme:enable drupal8_w3css_theme amun`, then
`drush config:set system.theme default amun -y`, then `drush cr`.

Installing the theme also adds its default block placements (main menu, account
menu, search, branding, footer menu and the page blocks). Check them at
`/admin/structure/block` for the Amun theme and move any that clash with blocks
you already have.


## What is different from W3CSS Theme

Amun changes the top of the page and nothing else. Everything below the header
comes from the base theme.

- **Sticky navigation bar above the header.** The main menu and the account menu
  sit in one row, with the account menu at the far end. After you scroll past
  the bar, it stays at the top of the window and gets a shadow.
- **Search panel.** The Search block goes in the "Fixed Search Bar" region. It
  does not show on the page. A search button in the navigation bar opens it as a
  full-width panel at the top of the window. A close button, the Escape key, or
  a click outside the panel closes it. Opening the search closes the side menu.
- **Side menu button.** If you place a menu in "Primary Menu Vertical", a menu
  button appears in the navigation bar and opens that menu as a side panel. With
  no block in that region, there is no button.
- **Centered branding.** The Site branding block in "Header" is centered.
- **Small screens.** Below 993 pixels the bar shows a menu button. It opens the
  main and account menus one under the other.
- **Footer order.** On the front page, the three footer regions show first. On
  every page, the bottom regions, the footer menu and the copyright follow, in
  one footer.
- **Colors.** The default color scheme is `w3-theme-00017` (DarkOrange
  MidnightBlue). Amun adds a few contrast fixes for this scheme: dark text in
  the orange navigation bar, a lighter footer menu text and a darker input focus
  border. They apply only while this scheme is selected. If you pick another
  scheme, you get that scheme's own colors.
- **Focus and motion.** Links, buttons and fields show a visible outline on
  keyboard focus. Visitors who ask their system for less motion get no
  transitions.

The regions are the base theme's 22, plus "Fixed Search Bar" (23 in total).


## Configuration

Amun has no settings of its own. It uses the settings form of W3CSS Theme: go to
`/admin/appearance/settings/amun` to set the website width, color scheme and
region colors, fonts, social links, copyright and the rest. Amun's own defaults
are the color scheme above and the copyright text "Copyright %year% - All Rights
Reserved". Social links are empty and turned off, and the credit link is off.


## Checking that it works

1. Open the front page. The navigation bar is above the header, with the account
   menu at the right end.
1. Scroll down. The bar stays at the top and gets a shadow.
1. Click the search button. The search panel slides down from the top and the
   cursor is in the search field. Press Escape. The panel closes.
1. Make the window narrower than 993 pixels. A menu button replaces the menu
   row. Click it to open the menus.
1. Press the Tab key. A visible outline moves with the focus.


## Custom CSS and JavaScript

Amun 3.0 uses the `w3css-` class names and ids of W3CSS Theme 3.0, for example
`w3css-main-nav--horizontal` and `w3css-header`. W3.CSS library classes that
start with `w3-` are unchanged. Custom CSS or JavaScript written against the old
names must be renamed. The base theme ships a script for it and a table of old
and new names: `docs/CLASS-MIGRATION.md` in the W3CSS Theme folder.

Put your own CSS, JavaScript and templates in a sub-theme of Amun. The folder
`amun_subtheme` in this package is an empty starter. Copy it to `themes/custom`,
and rename the folder, its files, the library name inside them and the name in
the `.info.yml` file before you enable it.


## Helpful links

- [W3CSS Theme project page](https://www.drupal.org/project/d8w3css)
- [W3CSS Theme documentation](https://www.drupal.org/node/2866181)
- [Predefined color themes](https://www.w3css.flashwebcenter.com/w3css-predefined-color-themes)
- [Amun demo site](https://www.amun.flashwebcenter.com/)
- [Amun issue queue](https://www.drupal.org/project/issues/amun)
