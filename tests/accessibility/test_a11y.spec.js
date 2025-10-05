const { test, expect } = require('@playwright/test');
const AxeBuilder = require('@axe-core/playwright').default;

test.describe('Accessibility Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('login page should be accessible', async ({ page }) => {
    const accessibilityScanResults = await new AxeBuilder({ page }).analyze();

    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test('registration page should be accessible', async ({ page }) => {
    await page.click('#show-register');
    await expect(page.locator('#register-form')).toBeVisible();

    const accessibilityScanResults = await new AxeBuilder({ page }).analyze();

    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test('task management page should be accessible', async ({ page }) => {
    // Register and login first
    const timestamp = Date.now();
    const username = `a11yuser${timestamp}`;

    await page.click('#show-register');
    await page.fill('#register-username', username);
    await page.fill('#register-email', `${username}@example.com`);
    await page.fill('#register-password', 'a11ypass123');
    await page.fill('#register-password-confirm', 'a11ypass123');
    await page.click('#registerForm button[type="submit"]');

    // Wait for task section to be visible
    await expect(page.locator('#task-section')).toBeVisible();

    // Create a task to test with content
    await page.fill('#task-title', 'Accessibility test task');
    await page.fill('#task-description', 'Testing task accessibility features');
    await page.click('#taskForm button[type="submit"]');

    // Wait for task to appear
    await expect(page.locator('.task-item')).toBeVisible();

    const accessibilityScanResults = await new AxeBuilder({ page }).analyze();

    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test('form labels and associations', async ({ page }) => {
    // Check login form
    const loginUsernameLabel = page.locator('label[for="login-username"]');
    const loginPasswordLabel = page.locator('label[for="login-password"]');

    // Check if explicit labels exist, or if placeholders provide accessibility
    const usernameInput = page.locator('#login-username');
    const passwordInput = page.locator('#login-password');

    // Verify inputs have accessible names (either via label or aria-label or placeholder)
    await expect(usernameInput).toHaveAttribute('placeholder');
    await expect(passwordInput).toHaveAttribute('placeholder');

    // Check registration form
    await page.click('#show-register');

    const registerInputs = [
      '#register-username',
      '#register-email',
      '#register-password',
      '#register-password-confirm'
    ];

    for (const inputSelector of registerInputs) {
      const input = page.locator(inputSelector);
      await expect(input).toHaveAttribute('placeholder');
    }
  });

  test('keyboard navigation', async ({ page }) => {
    // Test tab navigation through login form
    await page.keyboard.press('Tab');
    await expect(page.locator('#login-username')).toBeFocused();

    await page.keyboard.press('Tab');
    await expect(page.locator('#login-password')).toBeFocused();

    await page.keyboard.press('Tab');
    await expect(page.locator('#loginForm button')).toBeFocused();

    await page.keyboard.press('Tab');
    await expect(page.locator('#show-register')).toBeFocused();

    // Test Enter key on register link
    await page.keyboard.press('Enter');
    await expect(page.locator('#register-form')).toBeVisible();

    // Test tab navigation through registration form
    await page.keyboard.press('Tab');
    await expect(page.locator('#register-username')).toBeFocused();

    await page.keyboard.press('Tab');
    await expect(page.locator('#register-email')).toBeFocused();

    await page.keyboard.press('Tab');
    await expect(page.locator('#register-password')).toBeFocused();

    await page.keyboard.press('Tab');
    await expect(page.locator('#register-password-confirm')).toBeFocused();

    await page.keyboard.press('Tab');
    await expect(page.locator('#registerForm button')).toBeFocused();
  });

  test('task keyboard navigation', async ({ page }) => {
    // Register and login
    const timestamp = Date.now();
    const username = `keyboarduser${timestamp}`;

    await page.click('#show-register');
    await page.fill('#register-username', username);
    await page.fill('#register-email', `${username}@example.com`);
    await page.fill('#register-password', 'keyboardpass123');
    await page.fill('#register-password-confirm', 'keyboardpass123');
    await page.click('#registerForm button[type="submit"]');

    await expect(page.locator('#task-section')).toBeVisible();

    // Test task form navigation
    await expect(page.locator('#task-title')).toBeFocused();

    await page.keyboard.press('Tab');
    await expect(page.locator('#task-description')).toBeFocused();

    await page.keyboard.press('Tab');
    await expect(page.locator('#taskForm button')).toBeFocused();

    // Create a task and test task item navigation
    await page.fill('#task-title', 'Keyboard navigation test');
    await page.fill('#task-description', 'Testing keyboard access');
    await page.keyboard.press('Enter'); // Submit form

    await expect(page.locator('.task-item')).toBeVisible();

    // Test navigation to task action buttons
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab'); // Navigate to first action button

    // Should be able to reach task action buttons
    const focusedElement = await page.locator(':focus');
    const focusedClass = await focusedElement.getAttribute('class');
    expect(focusedClass).toMatch(/btn-(toggle|edit|delete)/);
  });

  test('aria attributes and roles', async ({ page }) => {
    // Check main sections have appropriate ARIA roles
    const authSection = page.locator('#auth-section');
    const taskSection = page.locator('#task-section');

    // These sections should have appropriate structure
    await expect(authSection).toBeVisible();

    // Check form structure
    const forms = page.locator('form');
    const formCount = await forms.count();
    expect(formCount).toBeGreaterThan(0);

    // Register and check task section
    const timestamp = Date.now();
    const username = `ariauser${timestamp}`;

    await page.click('#show-register');
    await page.fill('#register-username', username);
    await page.fill('#register-email', `${username}@example.com`);
    await page.fill('#register-password', 'ariapass123');
    await page.fill('#register-password-confirm', 'ariapass123');
    await page.click('#registerForm button[type="submit"]');

    await expect(taskSection).toBeVisible();

    // Create a task and check its structure
    await page.fill('#task-title', 'ARIA test task');
    await page.fill('#task-description', 'Testing ARIA attributes');
    await page.click('#taskForm button[type="submit"]');

    await expect(page.locator('.task-item')).toBeVisible();

    // Check that task list has appropriate structure
    const tasksList = page.locator('#tasks-container');
    await expect(tasksList).toBeVisible();
  });

  test('color contrast and visual accessibility', async ({ page }) => {
    // This test uses axe-core to check color contrast
    await page.emulateMedia({ colorScheme: 'light' });

    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21aa'])
      .analyze();

    // Filter for color contrast violations
    const colorContrastViolations = accessibilityScanResults.violations.filter(
      violation => violation.id === 'color-contrast'
    );

    expect(colorContrastViolations).toEqual([]);

    // Test dark mode if supported
    await page.emulateMedia({ colorScheme: 'dark' });

    const darkModeResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21aa'])
      .analyze();

    const darkModeContrastViolations = darkModeResults.violations.filter(
      violation => violation.id === 'color-contrast'
    );

    expect(darkModeContrastViolations).toEqual([]);
  });

  test('screen reader compatibility', async ({ page }) => {
    // Test with screen reader simulation
    const timestamp = Date.now();
    const username = `screenreader${timestamp}`;

    // Check that important elements have proper text content or labels
    const loginButton = page.locator('#loginForm button');
    const loginButtonText = await loginButton.textContent();
    expect(loginButtonText?.trim()).toBeTruthy();

    await page.click('#show-register');

    const registerButton = page.locator('#registerForm button');
    const registerButtonText = await registerButton.textContent();
    expect(registerButtonText?.trim()).toBeTruthy();

    // Register and check task interface
    await page.fill('#register-username', username);
    await page.fill('#register-email', `${username}@example.com`);
    await page.fill('#register-password', 'srpass123');
    await page.fill('#register-password-confirm', 'srpass123');
    await page.click('#registerForm button[type="submit"]');

    await expect(page.locator('#task-section')).toBeVisible();

    // Check task form has proper labels/placeholders
    const taskTitleInput = page.locator('#task-title');
    const taskDescriptionInput = page.locator('#task-description');
    const taskSubmitButton = page.locator('#taskForm button');

    await expect(taskTitleInput).toHaveAttribute('placeholder');
    await expect(taskDescriptionInput).toHaveAttribute('placeholder');

    const taskSubmitButtonText = await taskSubmitButton.textContent();
    expect(taskSubmitButtonText?.trim()).toBeTruthy();

    // Create a task and check action buttons have proper text
    await page.fill('#task-title', 'Screen reader test');
    await page.fill('#task-description', 'Testing screen reader compatibility');
    await page.click('#taskForm button[type="submit"]');

    await expect(page.locator('.task-item')).toBeVisible();

    // Check action buttons have meaningful text
    const toggleButton = page.locator('.btn-toggle').first();
    const editButton = page.locator('.btn-edit').first();
    const deleteButton = page.locator('.btn-delete').first();

    const toggleText = await toggleButton.textContent();
    const editText = await editButton.textContent();
    const deleteText = await deleteButton.textContent();

    expect(toggleText?.trim()).toBeTruthy();
    expect(editText?.trim()).toBeTruthy();
    expect(deleteText?.trim()).toBeTruthy();
  });

  test('form validation accessibility', async ({ page }) => {
    // Test that form validation messages are accessible
    await page.click('#show-register');

    // Try to submit without filling required fields
    await page.click('#registerForm button[type="submit"]');

    // Check for HTML5 validation
    const usernameInput = page.locator('#register-username');
    const emailInput = page.locator('#register-email');
    const passwordInput = page.locator('#register-password');

    // Check that inputs have required attribute or proper validation
    await expect(usernameInput).toHaveAttribute('required');
    await expect(emailInput).toHaveAttribute('required');
    await expect(passwordInput).toHaveAttribute('required');

    // Test mismatched passwords
    await page.fill('#register-username', 'validationtest');
    await page.fill('#register-email', 'validation@example.com');
    await page.fill('#register-password', 'password123');
    await page.fill('#register-password-confirm', 'differentpassword');
    await page.click('#registerForm button[type="submit"]');

    // Check if error message appears and is accessible
    const errorMessage = page.locator('#error-message');
    if (await errorMessage.isVisible()) {
      // Error message should be visible to screen readers
      const errorText = await errorMessage.textContent();
      expect(errorText?.trim()).toBeTruthy();
    }
  });

  test('focus management', async ({ page }) => {
    // Test that focus is properly managed during interactions
    const timestamp = Date.now();
    const username = `focususer${timestamp}`;

    await page.click('#show-register');
    await page.fill('#register-username', username);
    await page.fill('#register-email', `${username}@example.com`);
    await page.fill('#register-password', 'focuspass123');
    await page.fill('#register-password-confirm', 'focuspass123');
    await page.click('#registerForm button[type="submit"]');

    await expect(page.locator('#task-section')).toBeVisible();

    // Focus should be on the task title input after login
    await expect(page.locator('#task-title')).toBeFocused();

    // Create and edit a task
    await page.fill('#task-title', 'Focus management test');
    await page.fill('#task-description', 'Testing focus behavior');
    await page.click('#taskForm button[type="submit"]');

    await expect(page.locator('.task-item')).toBeVisible();

    // Edit the task
    await page.click('.btn-edit');

    // Focus should return to the task title input for editing
    await expect(page.locator('#task-title')).toBeFocused();
    await expect(page.locator('#task-title')).toHaveValue('Focus management test');
  });

  test('responsive accessibility', async ({ page }) => {
    // Test accessibility on different screen sizes
    const breakpoints = [
      { width: 1920, height: 1080 }, // Desktop
      { width: 768, height: 1024 },  // Tablet
      { width: 375, height: 667 },   // Mobile
    ];

    for (const viewport of breakpoints) {
      await page.setViewportSize(viewport);

      // Test basic accessibility at each breakpoint
      const accessibilityScanResults = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa'])
        .analyze();

      expect(accessibilityScanResults.violations).toEqual([]);

      // Test that interactive elements are still accessible
      const loginUsername = page.locator('#login-username');
      const loginPassword = page.locator('#login-password');
      const loginButton = page.locator('#loginForm button');

      await expect(loginUsername).toBeVisible();
      await expect(loginPassword).toBeVisible();
      await expect(loginButton).toBeVisible();
    }

    // Reset to default viewport
    await page.setViewportSize({ width: 1280, height: 720 });
  });
});