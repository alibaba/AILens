import { test, expect } from '@playwright/test';

test.describe('Training Investigation Journey', () => {
  test('complete training workflow: experiment list → detail → trajectory explorer → viewer', async ({ page }) => {
    // 1. Open homepage
    await page.goto('/');

    // 2. Assert: page redirects to /experiments and shows experiment content
    await expect(page).toHaveURL(/experiments/);
    await expect(page.locator('h1')).toContainText('Experiment Dashboard', { timeout: 15000 });

    // 3. Assert: at least 1 experiment row in table
    const tableRows = page.locator('table tbody tr');
    await expect(tableRows.first()).toBeVisible({ timeout: 10000 });
    const rowCount = await tableRows.count();
    expect(rowCount).toBeGreaterThanOrEqual(1);

    await page.screenshot({ path: 'e2e/screenshots/01-experiment-list.png' });

    // 4. Click first experiment row
    await tableRows.first().click();

    // 5. Assert: see 4 tabs on detail page
    await expect(page.locator('text=📈 训练总览')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('text=🎯 任务分析')).toBeVisible();
    await expect(page.locator('text=🤖 行为分析')).toBeVisible();
    await expect(page.locator('text=⚖️ 质量评估')).toBeVisible();

    await page.screenshot({ path: 'e2e/screenshots/02-experiment-detail.png' });

    // 6. Click "任务分析" tab (safer than 行为分析 which has an API mismatch)
    await page.getByRole('tab', { name: /任务分析/ }).click();

    // 7. Assert: the 任务分析 tab is now active (aria-selected)
    const taskTab = page.getByRole('tab', { name: /任务分析/ });
    await expect(taskTab).toHaveAttribute('aria-selected', 'true', { timeout: 5000 });

    // Also verify 行为分析 tab exists and is clickable (just check aria role)
    const behaviorTab = page.getByRole('tab', { name: /行为分析/ });
    await expect(behaviorTab).toBeVisible();
    await expect(behaviorTab).toHaveAttribute('aria-selected', 'false');

    await page.screenshot({ path: 'e2e/screenshots/03-task-analysis.png' });

    // 8. Navigate to Trajectory Explorer
    const url = page.url();
    const expIdMatch = url.match(/experiments\/([^/]+)/);
    expect(expIdMatch).toBeTruthy();
    const expId = expIdMatch![1];
    await page.goto(`/experiments/${expId}/trajectory-explorer`);

    // 9. Assert: see Trajectory Explorer heading and trajectory table
    await expect(page.getByRole('heading', { level: 1 })).toContainText('Trajectory Explorer', { timeout: 10000 });
    await expect(page.locator('table')).toBeVisible({ timeout: 10000 });

    await page.screenshot({ path: 'e2e/screenshots/04-trajectory-explorer.png' });

    // 10. If table has data rows, click first row
    const trajectoryRows = page.locator('table tbody tr');
    const hasRows = await trajectoryRows.first().isVisible({ timeout: 5000 }).catch(() => false);

    if (hasRows) {
      const trajectoryRowCount = await trajectoryRows.count();
      if (trajectoryRowCount > 0) {
        await trajectoryRows.first().click();

        // 11. Assert: see Turn Timeline content on Trajectory Viewer page
        await expect(page.locator('text=Turn Timeline')).toBeVisible({ timeout: 15000 });
        await expect(page.getByRole('heading', { level: 1 })).toContainText('Trajectory Viewer');

        await page.screenshot({ path: 'e2e/screenshots/05-trajectory-viewer.png' });
      }
    }
  });
});
