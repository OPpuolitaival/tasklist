const { test, expect } = require('@playwright/test');

test.describe('Complete User Journey', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('complete user registration and task management flow', async ({ page }) => {
    const timestamp = Date.now();
    const username = `testuser${timestamp}`;
    const email = `testuser${timestamp}@example.com`;
    const password = 'testpass123';

    // Step 1: Navigate to registration
    await expect(page.locator('h2')).toContainText('Login');
    await page.click('#show-register');
    await expect(page.locator('h2')).toContainText('Register');

    // Step 2: Register new user
    await page.fill('#register-username', username);
    await page.fill('#register-email', email);
    await page.fill('#register-password', password);
    await page.fill('#register-password-confirm', password);

    await page.click('#registerForm button[type="submit"]');

    // Step 3: Verify successful registration and redirect to tasks
    await expect(page.locator('#task-section')).toBeVisible();
    await expect(page.locator('#user-info')).toBeVisible();
    await expect(page.locator('#username')).toContainText(username);

    // Step 4: Create first task
    await page.fill('#task-title', 'Buy groceries');
    await page.fill('#task-description', 'Milk, bread, eggs, and cheese');
    await page.click('#taskForm button[type="submit"]');

    // Verify task appears in the list
    await expect(page.locator('.task-item')).toBeVisible();
    await expect(page.locator('.task-title')).toContainText('Buy groceries');
    await expect(page.locator('.task-description')).toContainText('Milk, bread, eggs, and cheese');

    // Step 5: Create second task
    await page.fill('#task-title', 'Walk the dog');
    await page.fill('#task-description', 'Take Rex for a 30-minute walk in the park');
    await page.click('#taskForm button[type="submit"]');

    // Verify both tasks are present (newest first)
    const taskItems = page.locator('.task-item');
    await expect(taskItems).toHaveCount(2);

    const firstTask = taskItems.first();
    await expect(firstTask.locator('.task-title')).toContainText('Walk the dog');

    const secondTask = taskItems.nth(1);
    await expect(secondTask.locator('.task-title')).toContainText('Buy groceries');

    // Step 6: Mark first task as completed
    await firstTask.locator('.btn-toggle').click();
    await expect(firstTask).toHaveClass(/completed/);
    await expect(firstTask.locator('.btn-toggle')).toContainText('Undo');

    // Step 7: Edit second task
    await secondTask.locator('.btn-edit').click();
    await expect(page.locator('#task-title')).toHaveValue('Buy groceries');
    await expect(page.locator('#task-description')).toHaveValue('Milk, bread, eggs, and cheese');

    await page.fill('#task-title', 'Buy groceries and snacks');
    await page.fill('#task-description', 'Milk, bread, eggs, cheese, and some healthy snacks');
    await page.click('#taskForm button[type="submit"]');

    // Verify task was updated
    await expect(secondTask.locator('.task-title')).toContainText('Buy groceries and snacks');
    await expect(secondTask.locator('.task-description')).toContainText('healthy snacks');

    // Step 8: Delete completed task
    await page.on('dialog', dialog => dialog.accept()); // Accept confirmation dialog
    await firstTask.locator('.btn-delete').click();

    // Verify task was deleted
    await expect(taskItems).toHaveCount(1);
    await expect(page.locator('.task-title')).toContainText('Buy groceries and snacks');

    // Step 9: Create third task to verify task ordering
    await page.fill('#task-title', 'Finish homework');
    await page.fill('#task-description', 'Complete math and science assignments');
    await page.click('#taskForm button[type="submit"]');

    // Verify ordering (newest first)
    await expect(taskItems).toHaveCount(2);
    await expect(taskItems.first().locator('.task-title')).toContainText('Finish homework');
    await expect(taskItems.nth(1).locator('.task-title')).toContainText('Buy groceries and snacks');

    // Step 10: Logout
    await page.click('#logout-btn');

    // Verify redirect to login page
    await expect(page.locator('#auth-section')).toBeVisible();
    await expect(page.locator('#task-section')).not.toBeVisible();
    await expect(page.locator('h2')).toContainText('Login');
  });

  test('existing user login flow', async ({ page }) => {
    // This test assumes there's a pre-existing user or uses the one created in previous test
    // For a real test, you might want to use a test database with known users

    const username = 'testuser123';
    const password = 'testpass123';

    // First register a user (in real tests, this would be done in setup)
    await page.click('#show-register');
    await page.fill('#register-username', username);
    await page.fill('#register-email', 'testuser123@example.com');
    await page.fill('#register-password', password);
    await page.fill('#register-password-confirm', password);
    await page.click('#registerForm button[type="submit"]');

    // Add a task to test persistence
    await page.fill('#task-title', 'Persistent task');
    await page.fill('#task-description', 'This should persist after logout/login');
    await page.click('#taskForm button[type="submit"]');

    // Logout
    await page.click('#logout-btn');

    // Now test login
    await page.fill('#login-username', username);
    await page.fill('#login-password', password);
    await page.click('#loginForm button[type="submit"]');

    // Verify successful login
    await expect(page.locator('#task-section')).toBeVisible();
    await expect(page.locator('#username')).toContainText(username);

    // Verify task persistence
    await expect(page.locator('.task-title')).toContainText('Persistent task');
  });

  test('form validation and error handling', async ({ page }) => {
    // Test registration validation
    await page.click('#show-register');

    // Try to register with mismatched passwords
    await page.fill('#register-username', 'testuser');
    await page.fill('#register-email', 'test@example.com');
    await page.fill('#register-password', 'password123');
    await page.fill('#register-password-confirm', 'differentpassword');
    await page.click('#registerForm button[type="submit"]');

    // Should show error message
    await expect(page.locator('#error-message')).toBeVisible();

    // Test login with invalid credentials
    await page.click('#show-login');
    await page.fill('#login-username', 'nonexistentuser');
    await page.fill('#login-password', 'wrongpassword');
    await page.click('#loginForm button[type="submit"]');

    // Should show error message
    await expect(page.locator('#error-message')).toBeVisible();

    // Test task creation without title
    // First need to register and login
    const timestamp = Date.now();
    await page.click('#show-register');
    await page.fill('#register-username', `validuser${timestamp}`);
    await page.fill('#register-email', `validuser${timestamp}@example.com`);
    await page.fill('#register-password', 'validpass123');
    await page.fill('#register-password-confirm', 'validpass123');
    await page.click('#registerForm button[type="submit"]');

    // Try to create task without title
    await page.click('#taskForm button[type="submit"]');
    // The HTML5 validation should prevent submission
    await expect(page.locator('#task-title:invalid')).toBeVisible();
  });

  test('responsive design and mobile layout', async ({ page, isMobile }) => {
    if (isMobile) {
      // Test mobile-specific behavior
      await expect(page.locator('header')).toBeVisible();
      await expect(page.locator('#auth-section')).toBeVisible();

      // Check that forms are properly sized
      await expect(page.locator('.form-container')).toBeVisible();

      // Register user for mobile testing
      const timestamp = Date.now();
      await page.click('#show-register');
      await page.fill('#register-username', `mobileuser${timestamp}`);
      await page.fill('#register-email', `mobileuser${timestamp}@example.com`);
      await page.fill('#register-password', 'mobilepass123');
      await page.fill('#register-password-confirm', 'mobilepass123');
      await page.click('#registerForm button[type="submit"]');

      // Test task creation on mobile
      await page.fill('#task-title', 'Mobile task');
      await page.fill('#task-description', 'Created on mobile device');
      await page.click('#taskForm button[type="submit"]');

      // Verify task appears correctly
      await expect(page.locator('.task-item')).toBeVisible();

      // Test action buttons are accessible on mobile
      await expect(page.locator('.btn-toggle')).toBeVisible();
      await expect(page.locator('.btn-edit')).toBeVisible();
      await expect(page.locator('.btn-delete')).toBeVisible();
    }
  });

  test('session persistence across page refreshes', async ({ page }) => {
    const timestamp = Date.now();
    const username = `persistuser${timestamp}`;

    // Register and login
    await page.click('#show-register');
    await page.fill('#register-username', username);
    await page.fill('#register-email', `${username}@example.com`);
    await page.fill('#register-password', 'persistpass123');
    await page.fill('#register-password-confirm', 'persistpass123');
    await page.click('#registerForm button[type="submit"]');

    // Create a task
    await page.fill('#task-title', 'Session test task');
    await page.fill('#task-description', 'Testing session persistence');
    await page.click('#taskForm button[type="submit"]');

    // Refresh the page
    await page.reload();

    // Should still be logged in
    await expect(page.locator('#task-section')).toBeVisible();
    await expect(page.locator('#username')).toContainText(username);
    await expect(page.locator('.task-title')).toContainText('Session test task');
  });

  test('keyboard navigation and accessibility', async ({ page }) => {
    // Test tab navigation through forms
    await page.keyboard.press('Tab'); // Should focus username
    await expect(page.locator('#login-username')).toBeFocused();

    await page.keyboard.press('Tab'); // Should focus password
    await expect(page.locator('#login-password')).toBeFocused();

    await page.keyboard.press('Tab'); // Should focus submit button
    await expect(page.locator('#loginForm button')).toBeFocused();

    // Test form switching with keyboard
    await page.keyboard.press('Tab'); // Should focus register link
    await expect(page.locator('#show-register')).toBeFocused();

    await page.keyboard.press('Enter'); // Should switch to register form
    await expect(page.locator('#register-form')).toBeVisible();

    // Register user for task testing
    const timestamp = Date.now();
    await page.fill('#register-username', `keyboarduser${timestamp}`);
    await page.fill('#register-email', `keyboarduser${timestamp}@example.com`);
    await page.fill('#register-password', 'keyboardpass123');
    await page.fill('#register-password-confirm', 'keyboardpass123');
    await page.keyboard.press('Enter'); // Submit form

    // Test task form navigation
    await expect(page.locator('#task-title')).toBeFocused();
    await page.keyboard.press('Tab');
    await expect(page.locator('#task-description')).toBeFocused();
    await page.keyboard.press('Tab');
    await expect(page.locator('#taskForm button')).toBeFocused();
  });
});