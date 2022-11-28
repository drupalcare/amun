/**
 * @file
 * This file is to add any custom js for amun theme.
 */
(function ($, Drupal, once) {
  'use strict';
  Drupal.behaviors.amunThemeBehavior = {
    attach: function (context, settings) {
      $(once('body', '.close-search', context)).on('click', function () {
        document.getElementById('search-slide').style.display = 'none';
      });
      $(once('body', '.open-search', context)).on('click', function () {
        document.getElementById('search-slide').style.display = 'block';
      });
    }
  };
})(jQuery, Drupal, once);


