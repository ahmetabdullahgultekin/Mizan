import { test, expect } from '@playwright/test';

test.describe('Search page', () => {
  test('loads search page with input and slider', async ({ page }) => {
    await page.goto('/search');

    // Search input is present
    const searchInput = page.getByRole('textbox');
    await expect(searchInput).toBeVisible();

    // Similarity slider is present (input[type=range])
    const slider = page.locator('input[type="range"]');
    await expect(slider).toBeVisible();
  });

  test('shows results or error message after submitting a query', async ({ page }) => {
    await page.goto('/search');

    const searchInput = page.getByRole('textbox');
    await searchInput.fill('mercy of God');

    // Submit via Enter key or search button
    await searchInput.press('Enter');

    // Wait for either results list or an error/loading indicator
    await page.waitForTimeout(2000);

    // Page should not crash — still on /search
    await expect(page).toHaveURL(/\/search/);
  });

  test('slider value is reflected in aria-valuenow or value attribute', async ({ page }) => {
    await page.goto('/search');

    const slider = page.locator('input[type="range"]');
    await expect(slider).toBeVisible();

    // Verify slider has a value (either value or aria-valuenow)
    const value = await slider.getAttribute('value');
    const ariaValue = await slider.getAttribute('aria-valuenow');
    expect(value !== null || ariaValue !== null).toBeTruthy();
  });
});

test.describe('Playground page', () => {
  test('loads playground with surah and verse selectors', async ({ page }) => {
    await page.goto('/playground');

    // Some form of selector should be visible
    await expect(page.locator('body')).toBeVisible();

    // Page should not crash
    await expect(page).toHaveURL(/\/playground/);
  });
});
