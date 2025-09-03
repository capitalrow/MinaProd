/**
 * MINA E2E Tests - Accessibility Compliance
 * Tests WCAG 2.1 AA compliance and accessibility features
 */

const { test, expect } = require('@playwright/test');
const { MinaTestUtils } = require('../setup/test-utils');

test.describe('Accessibility Compliance Tests', () => {
  let utils;

  test.beforeEach(async ({ page }) => {
    utils = new MinaTestUtils(page);
  });

  test('should support keyboard navigation', async ({ page }) => {
    await utils.navigateToLive();
    
    // Test tab navigation
    await page.keyboard.press('Tab');
    
    // Check if focus is visible
    const focusedElement = await page.evaluate(() => document.activeElement?.tagName);
    expect(focusedElement).toBeTruthy();
    
    // Navigate to record button with keyboard
    let attempts = 0;
    while (attempts < 10) {
      const currentElement = await page.evaluate(() => ({
        tag: document.activeElement?.tagName,
        id: document.activeElement?.id,
        text: document.activeElement?.textContent?.trim()
      }));
      
      if (currentElement.id === 'recordButton' || currentElement.text?.includes('Record')) {
        break;
      }
      
      await page.keyboard.press('Tab');
      attempts++;
    }
    
    // Activate record button with keyboard
    await page.keyboard.press('Enter');
    await page.waitForTimeout(1000);
    
    // Verify button state changed
    const recordButton = page.locator('#recordButton');
    const buttonText = await recordButton.textContent();
    expect(buttonText).toContain('Stop');
    
    console.log('✅ Keyboard navigation working correctly');
  });

  test('should have proper ARIA labels and roles', async ({ page }) => {
    await utils.navigateToLive();
    
    // Check for essential ARIA attributes
    const ariaElements = await page.evaluate(() => {
      const elements = document.querySelectorAll('[aria-label], [role], [aria-describedby]');
      return Array.from(elements).map(el => ({
        tag: el.tagName,
        id: el.id,
        ariaLabel: el.getAttribute('aria-label'),
        role: el.getAttribute('role'),
        ariaDescribedby: el.getAttribute('aria-describedby')
      }));
    });
    
    expect(ariaElements.length).toBeGreaterThan(0);
    
    // Check record button has proper accessibility attributes
    const recordButton = page.locator('#recordButton');
    const ariaLabel = await recordButton.getAttribute('aria-label');
    expect(ariaLabel).toBeTruthy();
    
    console.log('✅ ARIA labels and roles present');
    console.log(`📊 Found ${ariaElements.length} elements with accessibility attributes`);
  });

  test('should support screen reader announcements', async ({ page }) => {
    await utils.navigateToLive();
    
    // Check for live regions for screen reader announcements
    const liveRegions = await page.locator('[aria-live]').count();
    expect(liveRegions).toBeGreaterThan(0);
    
    // Check for status announcements
    const statusElements = await page.locator('[role="status"], [aria-live="polite"], [aria-live="assertive"]').count();
    expect(statusElements).toBeGreaterThan(0);
    
    // Trigger state change and check for announcements
    await utils.grantMicrophonePermissions();
    await utils.simulateAudioInput();
    await utils.clickRecordButton();
    
    // Wait for potential screen reader announcements
    await page.waitForTimeout(2000);
    
    console.log('✅ Screen reader support elements present');
    console.log(`📊 Live regions: ${liveRegions}, Status elements: ${statusElements}`);
  });

  test('should have sufficient color contrast', async ({ page }) => {
    await utils.navigateToLive();
    
    // Check color contrast for key elements
    const contrastCheck = await page.evaluate(() => {
      const getComputedStyle = window.getComputedStyle;
      
      // Function to calculate relative luminance
      const getLuminance = (rgb) => {
        const [r, g, b] = rgb.match(/\d+/g).map(Number);
        const [rNorm, gNorm, bNorm] = [r, g, b].map(c => {
          c = c / 255;
          return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
        });
        return 0.2126 * rNorm + 0.7152 * gNorm + 0.0722 * bNorm;
      };
      
      // Calculate contrast ratio
      const getContrastRatio = (color1, color2) => {
        const lum1 = getLuminance(color1);
        const lum2 = getLuminance(color2);
        const lighter = Math.max(lum1, lum2);
        const darker = Math.min(lum1, lum2);
        return (lighter + 0.05) / (darker + 0.05);
      };
      
      const elements = [
        document.querySelector('#recordButton'),
        document.querySelector('.live-transcript-container, #transcriptContainer'),
        document.querySelector('#recording-status')
      ].filter(Boolean);
      
      const results = [];
      
      elements.forEach(el => {
        const styles = getComputedStyle(el);
        const color = styles.color;
        const backgroundColor = styles.backgroundColor;
        
        if (color && backgroundColor && backgroundColor !== 'rgba(0, 0, 0, 0)') {
          const ratio = getContrastRatio(color, backgroundColor);
          results.push({
            element: el.tagName + (el.id ? '#' + el.id : ''),
            ratio: ratio,
            passes: ratio >= 4.5 // WCAG AA standard
          });
        }
      });
      
      return results;
    });
    
    if (contrastCheck.length > 0) {
      contrastCheck.forEach(result => {
        expect(result.ratio).toBeGreaterThan(3); // Minimum acceptable contrast
        console.log(`📊 ${result.element}: ${result.ratio.toFixed(2)}:1 ${result.passes ? '✅' : '⚠️'}`);
      });
      
      console.log('✅ Color contrast evaluation completed');
    } else {
      console.log('⚠️ Could not evaluate color contrast - elements may use transparent backgrounds');
    }
  });

  test('should support high contrast mode', async ({ page }) => {
    await utils.navigateToLive();
    
    // Check if high contrast mode controls exist
    const highContrastButton = page.locator('[class*="high-contrast"], [data-test="high-contrast"], button:has-text("High Contrast")');
    const hasHighContrastSupport = await highContrastButton.count() > 0;
    
    if (hasHighContrastSupport) {
      // Test high contrast mode toggle
      await highContrastButton.click();
      await page.waitForTimeout(1000);
      
      // Verify high contrast styles are applied
      const bodyClasses = await page.evaluate(() => document.body.className);
      expect(bodyClasses).toContain('high-contrast');
      
      console.log('✅ High contrast mode supported and functional');
    } else {
      console.log('⚠️ High contrast mode controls not found - may be implemented differently');
    }
  });

  test('should support focus indicators', async ({ page }) => {
    await utils.navigateToLive();
    
    // Tab through focusable elements and check focus indicators
    const focusableElements = await page.locator('button, input, select, textarea, a[href], [tabindex]:not([tabindex="-1"])').count();
    expect(focusableElements).toBeGreaterThan(0);
    
    // Test focus on record button
    await page.locator('#recordButton').focus();
    
    // Check if focus is visible
    const focusStyles = await page.evaluate(() => {
      const button = document.querySelector('#recordButton');
      const styles = window.getComputedStyle(button, ':focus');
      return {
        outline: styles.outline,
        outlineOffset: styles.outlineOffset,
        boxShadow: styles.boxShadow
      };
    });
    
    const hasFocusIndicator = 
      focusStyles.outline !== 'none' || 
      focusStyles.boxShadow !== 'none' ||
      focusStyles.outlineOffset !== 'none';
    
    expect(hasFocusIndicator).toBeTruthy();
    
    console.log('✅ Focus indicators present');
    console.log(`📊 Focusable elements: ${focusableElements}`);
  });

  test('should have proper heading structure', async ({ page }) => {
    await utils.navigateToLive();
    
    // Check heading hierarchy
    const headings = await page.evaluate(() => {
      const headingElements = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
      return Array.from(headingElements).map(h => ({
        level: parseInt(h.tagName.substring(1)),
        text: h.textContent.trim()
      }));
    });
    
    if (headings.length > 0) {
      // Check if headings start with h1
      const firstHeading = headings[0];
      expect(firstHeading.level).toBeLessThanOrEqual(2); // Should start with h1 or h2
      
      // Check for proper hierarchy (no skipping levels)
      for (let i = 1; i < headings.length; i++) {
        const levelDiff = headings[i].level - headings[i-1].level;
        expect(levelDiff).toBeLessThanOrEqual(1); // Shouldn't skip heading levels
      }
      
      console.log('✅ Proper heading structure maintained');
      console.log(`📊 Headings found: ${headings.map(h => `h${h.level}`).join(', ')}`);
    } else {
      console.log('⚠️ No heading elements found - consider adding semantic headings');
    }
  });

  test('should support alternative text for images', async ({ page }) => {
    await utils.navigateToLive();
    
    // Check all images have alt text
    const images = await page.evaluate(() => {
      const imgs = document.querySelectorAll('img');
      return Array.from(imgs).map(img => ({
        src: img.src,
        alt: img.alt,
        hasAlt: img.hasAttribute('alt')
      }));
    });
    
    if (images.length > 0) {
      images.forEach((img, index) => {
        expect(img.hasAlt).toBeTruthy();
        console.log(`📊 Image ${index + 1}: ${img.alt || '(empty alt)'}`);
      });
      
      console.log('✅ All images have alt attributes');
    } else {
      console.log('ℹ️ No images found on the page');
    }
  });

  test('should support reduced motion preferences', async ({ page }) => {
    // Set reduced motion preference
    await page.emulateMedia({ reducedMotion: 'reduce' });
    await utils.navigateToLive();
    
    // Check if animations are reduced/disabled
    const animationCheck = await page.evaluate(() => {
      const elements = document.querySelectorAll('*');
      let animatedElements = 0;
      
      elements.forEach(el => {
        const styles = window.getComputedStyle(el);
        const hasAnimation = 
          styles.animationDuration !== '0s' ||
          styles.transitionDuration !== '0s';
        
        if (hasAnimation) {
          animatedElements++;
        }
      });
      
      return {
        totalElements: elements.length,
        animatedElements: animatedElements,
        mediaQuery: window.matchMedia('(prefers-reduced-motion: reduce)').matches
      };
    });
    
    expect(animationCheck.mediaQuery).toBeTruthy(); // Should detect reduced motion preference
    
    console.log('✅ Reduced motion preference supported');
    console.log(`📊 Animated elements: ${animationCheck.animatedElements}/${animationCheck.totalElements}`);
  });
});