/**
 * @file
 * This file is to add any custom js for amun theme.
 */
(function ($, Drupal) {
   'use strict';
    Drupal.behaviors.amunThemeBehavior = {
        attach: function (context, settings) {
            $(context)
                .find('.close-search')
                .once('.close-search')
                .on(
                    'click',
                    function () {
                        document.getElementById('search-slide').style.display = 'none';
                    }
                );
            $(context)
                .find('.open-search')
                .once('.open-search')
                .on(
                    'click',
                    function () {
                        document.getElementById('search-slide').style.display = 'block';
                    }
                );

        }
    };
})(jQuery, Drupal);
