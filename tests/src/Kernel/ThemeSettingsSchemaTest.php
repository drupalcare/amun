<?php

declare(strict_types=1);

namespace Drupal\Tests\amun\Kernel;

use Drupal\KernelTests\KernelTestBase;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\Attributes\RunTestsInSeparateProcesses;

/**
 * Amun's settings config has a schema and installs under strict checking.
 *
 * Before config/schema/amun.schema.yml existed this threw
 * "No schema for amun.settings". The type is inherited from the base theme
 * (drupal8_w3css_theme), whose own test guards the key list.
 *
 * @license SPDX-License-Identifier: GPL-2.0-or-later
 */
#[Group('amun')]
#[RunTestsInSeparateProcesses]
class ThemeSettingsSchemaTest extends KernelTestBase {

  /**
   * {@inheritdoc}
   */
  protected static $modules = ['system'];

  /**
   * Installing the theme (and its base) under strict schema is clean.
   */
  public function testInstallUnderStrictSchemaIsClean(): void {
    $this->installConfig(['system']);
    $this->container->get('theme_installer')->install(['amun']);
    $settings = $this->config('amun.settings');
    $this->assertFalse($settings->isNew());
    $this->assertSame('w3-theme-00017', $settings->get('current_theme'));
    $this->assertSame(1, $settings->get('top_region'));
  }

}
