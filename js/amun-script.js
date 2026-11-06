/**
 * @file
 * Search slide for the amun theme.
 *
 * The opener (.open-search) names the panel in aria-controls. Opening the
 * panel moves focus into its search field; closing it returns focus to the
 * opener. Escape and a click outside the panel close it. A closed panel is
 * inert, so it leaves the tab order and the accessibility tree.
 *
 * This file is identical in amun, amunet and anhur once the theme name is
 * substituted: planning/scripts/check-search-slide-drift.py in the lane root
 * compares the three copies.
 */
((Drupal, once) => {
  // State class on the panel; the theme's CSS animates it.
  const openClass = 'amun-is-open';

  /**
   * Closes the base theme's side menu when it is open.
   *
   * Goes through the base close button, so the base keeps owning the side
   * menu state (its display, submenus and aria-expanded).
   */
  function closeSideMenu() {
    const sideOpener = document.querySelector('.w3css-main-nav__open');
    const sideCloser = document.querySelector('.w3css-main-nav__close');
    if (
      sideOpener &&
      sideCloser &&
      sideOpener.getAttribute('aria-expanded') === 'true'
    ) {
      sideCloser.click();
    }
  }

  /**
   * Finds the first field a visitor can type in.
   *
   * @param {HTMLElement} panel
   *   The search panel.
   *
   * @return {HTMLElement|null}
   *   The search field, or NULL when the region holds none.
   */
  function findField(panel) {
    return panel.querySelector(
      'input[type="search"], input:not([type="hidden"]):not([type="submit"])',
    );
  }

  /**
   * Search slide behavior.
   */
  Drupal.behaviors.amunSearchSlide = {
    attach(context) {
      const openers = once(
        'amun-search-slide',
        '.open-search[aria-controls]',
        context,
      );
      openers.forEach((opener) => {
        const panel = document.getElementById(
          opener.getAttribute('aria-controls'),
        );
        if (!panel) {
          return;
        }
        const closer = panel.querySelector('.close-search');

        const isOpen = () => panel.classList.contains(openClass);

        const setOpen = (open, restoreFocus) => {
          panel.classList.toggle(openClass, open);
          panel.inert = !open;
          opener.setAttribute('aria-expanded', open ? 'true' : 'false');
          if (open) {
            const field = findField(panel);
            if (field) {
              field.focus({ preventScroll: true });
            }
          } else if (restoreFocus) {
            opener.focus({ preventScroll: true });
          }
        };

        // Start closed: out of the tab order until opened.
        setOpen(false, false);

        opener.addEventListener('click', () => {
          if (isOpen()) {
            setOpen(false, true);
            return;
          }
          closeSideMenu();
          setOpen(true, false);
        });

        if (closer) {
          closer.addEventListener('click', () => setOpen(false, true));
        }

        document.addEventListener('keydown', (event) => {
          if (event.key === 'Escape' && isOpen()) {
            setOpen(false, true);
          }
        });

        // A click anywhere else closes the panel, including the side-menu
        // opener; focus stays where the visitor put it.
        document.addEventListener('click', (event) => {
          if (
            isOpen() &&
            !panel.contains(event.target) &&
            !opener.contains(event.target)
          ) {
            setOpen(false, false);
          }
        });
      });
    },
  };
})(Drupal, once);
