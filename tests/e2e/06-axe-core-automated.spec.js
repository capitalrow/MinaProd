/**
 * MINA E2E Tests - Automated Accessibility Testing with axe-core
 * Tests WCAG 2.1 AA compliance using axe-core automated scans
 * 
 * This test suite performs comprehensive accessibility audits on key pages
 * using axe-core to detect violations automatically.
 */

const { test, expect } = require('@playwright/test');
const AxeBuilder = require('@axe-core/playwright').default;
const fs = require('fs');
const path = require('path');

const RESULTS_DIR = path.join(__dirname, '../results/accessibility');

if (!fs.existsSync(RESULTS_DIR)) {
  fs.mkdirSync(RESULTS_DIR, { recursive: true });
}

function saveReport(testName, results) {
  const reportPath = path.join(RESULTS_DIR, `${testName}_axe_report.json`);
  fs.writeFileSync(reportPath, JSON.stringify(results, null, 2));
  console.log(`📄 Accessibility report saved: ${reportPath}`);
  return reportPath;
}

function formatViolations(violations) {
  if (!violations || violations.length === 0) {
    return '✅ No accessibility violations found';
  }

  const lines = ['', '=' .repeat(60)];
  lines.push(`❌ Found ${violations.length} accessibility violation(s):`);
  lines.push('='.repeat(60));

  violations.forEach((violation, i) => {
    lines.push('');
    lines.push(`${i + 1}. ${violation.id}`);
    lines.push(`   Impact: ${(violation.impact || 'unknown').toUpperCase()}`);
    lines.push(`   Description: ${violation.description}`);
    lines.push(`   Help: ${violation.help}`);
    lines.push(`   Help URL: ${violation.helpUrl}`);
    lines.push(`   Affected elements: ${violation.nodes.length}`);
    
    violation.nodes.slice(0, 3).forEach(node => {
      if (node.html) {
        const htmlSnippet = node.html.length > 100 
          ? node.html.substring(0, 100) + '...' 
          : node.html;
        lines.push(`   - ${htmlSnippet}`);
      }
      if (node.failureSummary) {
        lines.push(`     ${node.failureSummary}`);
      }
    });
  });

  lines.push('='.repeat(60));
  lines.push('');
  return lines.join('\n');
}

test.describe('Axe-Core Automated Accessibility Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 720 });
  });

  test('Home page should have no critical accessibility violations', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const axeResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze();

    saveReport('home_page', axeResults);

    const criticalViolations = axeResults.violations.filter(
      v => v.impact === 'critical' || v.impact === 'serious'
    );

    if (criticalViolations.length > 0) {
      console.log(formatViolations(criticalViolations));
    }

    expect(criticalViolations).toHaveLength(0);
    console.log(`✅ Home page: ${axeResults.passes.length} checks passed, ${axeResults.violations.length} violations`);
  });

  test('Login page should have no accessibility violations', async ({ page }) => {
    await page.goto('/auth/login');
    await page.waitForLoadState('networkidle');

    const axeResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze();

    saveReport('login_page', axeResults);

    if (axeResults.violations.length > 0) {
      console.log(formatViolations(axeResults.violations));
    }

    expect(axeResults.violations).toHaveLength(0);
    console.log(`✅ Login page: ${axeResults.passes.length} checks passed`);
  });

  test('Register page should have no accessibility violations', async ({ page }) => {
    await page.goto('/auth/register');
    await page.waitForLoadState('networkidle');

    const axeResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze();

    saveReport('register_page', axeResults);

    if (axeResults.violations.length > 0) {
      console.log(formatViolations(axeResults.violations));
    }

    expect(axeResults.violations).toHaveLength(0);
    console.log(`✅ Register page: ${axeResults.passes.length} checks passed`);
  });

  test('Live transcription page should have no accessibility violations', async ({ page }) => {
    await page.goto('/live');
    await page.waitForLoadState('networkidle');

    const axeResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze();

    saveReport('live_page', axeResults);

    if (axeResults.violations.length > 0) {
      console.log(formatViolations(axeResults.violations));
    }

    expect(axeResults.violations).toHaveLength(0);
    console.log(`✅ Live page: ${axeResults.passes.length} checks passed`);
  });

  test('Dashboard should have no accessibility violations', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    const axeResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .exclude('#session-secret-notice')
      .analyze();

    saveReport('dashboard', axeResults);

    if (axeResults.violations.length > 0) {
      console.log(formatViolations(axeResults.violations));
    }

    expect(axeResults.violations).toHaveLength(0);
    console.log(`✅ Dashboard: ${axeResults.passes.length} checks passed`);
  });

  test('Settings page should have no accessibility violations', async ({ page }) => {
    await page.goto('/settings');
    await page.waitForLoadState('networkidle');

    const axeResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze();

    saveReport('settings_page', axeResults);

    if (axeResults.violations.length > 0) {
      console.log(formatViolations(axeResults.violations));
    }

    expect(axeResults.violations).toHaveLength(0);
    console.log(`✅ Settings page: ${axeResults.passes.length} checks passed`);
  });

  test('Test specific WCAG 2.1 Level A rules', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const axeResults = await new AxeBuilder({ page })
      .withTags(['wcag21a'])
      .analyze();

    saveReport('wcag21a_specific', axeResults);

    const criticalViolations = axeResults.violations.filter(
      v => v.impact === 'critical'
    );

    if (criticalViolations.length > 0) {
      console.log(formatViolations(criticalViolations));
    }

    expect(criticalViolations).toHaveLength(0);
    console.log(`✅ WCAG 2.1 Level A: ${axeResults.passes.length} checks passed`);
  });

  test('Test keyboard navigation rules', async ({ page }) => {
    await page.goto('/live');
    await page.waitForLoadState('networkidle');

    const axeResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'keyboard'])
      .analyze();

    saveReport('keyboard_navigation', axeResults);

    const keyboardViolations = axeResults.violations.filter(v =>
      v.id.includes('focus') || 
      v.id.includes('keyboard') ||
      v.id.includes('tabindex')
    );

    if (keyboardViolations.length > 0) {
      console.log(formatViolations(keyboardViolations));
    }

    expect(keyboardViolations).toHaveLength(0);
    console.log(`✅ Keyboard navigation: ${axeResults.passes.length} checks passed`);
  });

  test('Test color contrast rules', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const axeResults = await new AxeBuilder({ page })
      .withRules(['color-contrast'])
      .analyze();

    saveReport('color_contrast', axeResults);

    const contrastViolations = axeResults.violations.filter(
      v => v.id === 'color-contrast'
    );

    if (contrastViolations.length > 0) {
      console.log(formatViolations(contrastViolations));
    }

    expect(contrastViolations).toHaveLength(0);
    console.log(`✅ Color contrast: ${axeResults.passes.length} checks passed`);
  });

  test('Test form labels and accessibility', async ({ page }) => {
    await page.goto('/auth/login');
    await page.waitForLoadState('networkidle');

    const axeResults = await new AxeBuilder({ page })
      .withTags(['forms', 'wcag2a', 'wcag2aa'])
      .analyze();

    saveReport('form_accessibility', axeResults);

    const formViolations = axeResults.violations.filter(v =>
      v.id.includes('label') || 
      v.id.includes('input') ||
      v.id.includes('form')
    );

    if (formViolations.length > 0) {
      console.log(formatViolations(formViolations));
    }

    expect(formViolations).toHaveLength(0);
    console.log(`✅ Form accessibility: ${axeResults.passes.length} checks passed`);
  });

  test('Test ARIA attributes and roles', async ({ page }) => {
    await page.goto('/live');
    await page.waitForLoadState('networkidle');

    const axeResults = await new AxeBuilder({ page })
      .withTags(['aria', 'wcag2a', 'wcag2aa'])
      .analyze();

    saveReport('aria_attributes', axeResults);

    const ariaViolations = axeResults.violations.filter(v =>
      v.id.includes('aria')
    );

    if (ariaViolations.length > 0) {
      console.log(formatViolations(ariaViolations));
    }

    expect(ariaViolations).toHaveLength(0);
    console.log(`✅ ARIA attributes: ${axeResults.passes.length} checks passed`);
  });

  test('Comprehensive accessibility audit across multiple pages', async ({ page }) => {
    const pages = [
      { url: '/', name: 'Home' },
      { url: '/live', name: 'Live' },
      { url: '/dashboard', name: 'Dashboard' },
      { url: '/auth/login', name: 'Login' },
    ];

    const allViolations = [];
    const summary = [];

    for (const pageInfo of pages) {
      await page.goto(pageInfo.url);
      await page.waitForLoadState('networkidle');

      const axeResults = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
        .analyze();

      saveReport(`comprehensive_${pageInfo.name.toLowerCase()}`, axeResults);

      const criticalViolations = axeResults.violations.filter(
        v => v.impact === 'critical' || v.impact === 'serious'
      );

      allViolations.push(...criticalViolations);
      
      summary.push({
        page: pageInfo.name,
        url: pageInfo.url,
        passes: axeResults.passes.length,
        violations: axeResults.violations.length,
        criticalViolations: criticalViolations.length
      });
    }

    console.log('\n📊 Comprehensive Accessibility Audit Summary:');
    console.log('='.repeat(60));
    summary.forEach(item => {
      console.log(`${item.page} (${item.url}):`);
      console.log(`  ✅ Passed: ${item.passes}`);
      console.log(`  ⚠️  Violations: ${item.violations}`);
      console.log(`  ❌ Critical: ${item.criticalViolations}`);
    });
    console.log('='.repeat(60));

    if (allViolations.length > 0) {
      console.log(formatViolations(allViolations));
    }

    expect(allViolations).toHaveLength(0);
  });
});
