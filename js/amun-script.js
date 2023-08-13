/**
 * @file
 * This file is to add any custom js for amun theme.
 */
((Drupal, once) => {
  'use strict';
Drupal.behaviors.amunThemeBehavior = {
  attach: function (context, settings) {

      const ulParent = document.querySelector('.main-navigation-wrapper .ul-parent');
      const ulChildren = document.querySelector('.main-navigation-wrapper .ul-parent .ul-child');
      const searchBlock = document.getElementById('search-slide');
      const openSearch = document.querySelector('.open-search');
      const closeSearch = document.querySelector('.close-search');

      const removeActiveClass = () => {
        searchBlock.classList.remove('show');
      }

      const closeSearchHandler = () => {
        searchBlock.style.height = "0px";
        searchBlock.addEventListener('transitionend', removeActiveClass, {once: true});
      }

      const openSearchHandler = () => {
        searchBlock.classList.add('show');
        searchBlock.style.height = "auto";
        let height = searchBlock.clientHeight + "px";
        searchBlock.style.height = "0px";
        setTimeout(() => {
          searchBlock.style.height = height;
        }, 0);
      }

      closeSearch?.addEventListener('click', closeSearchHandler);
      openSearch?.addEventListener('click', openSearchHandler);

  }
};

})(Drupal, once);

