<?php

/**
 * @file
 * Amun Theme.theme.
 */

use Drupal\Core\Form\FormStateInterface;

/**
 * Implements hook_form_system_theme_settings_alter().
 */
function amun_form_system_theme_settings_alter(&$form, FormStateInterface $form_state) {
  $form['amun_settings']['w3_external_libraries'] = [
    '#type' => 'details',
    '#title' => t('Load External Libraries locally - Amun'),
    '#collapsible' => TRUE,
    '#collapsed' => FALSE,
    '#description'   => t('<p>Load google fonts locally. It is with Amun Sub-Theme</p>'),
  ];
  $form['amun_settings']['w3_external_libraries']['amun_google_font'] = [
    '#type' => 'checkbox',
    '#title' => t('Load google font locally'),
    '#default_value' => theme_get_setting('amun_google_font'),
  ];

}
