import { test, expect } from '@playwright/test';
import fs from 'fs';
import path from 'path';

test.describe('E2E Eval Framework Flow - Day Trip Agent', () => {
  
  test.beforeAll(async () => {
    // Clean up kuzu database before the run
    const kuzuPath = path.resolve(process.cwd(), '../../../../adk_tutorial/.kuzu');
    if (fs.existsSync(kuzuPath)) {
      fs.rmSync(kuzuPath, { recursive: true, force: true });
    }
  });

  test('Complete evaluation lifecycle', async ({ page }) => {
    // We increase timeout for the full E2E flow since it encompasses many steps
    test.setTimeout(300000);

    // ==========================================
    // 1. ONBOARDING & SCANNING
    // ==========================================
    await test.step('Scan the Day Trip Agent', async () => {
      await page.goto('/');
      await expect(page.getByRole('heading', { name: 'Add target & scan' })).toBeVisible();
      
      // Ensure the repo is dynamically loaded from the CLI args via API
      await expect(page.locator('input[placeholder="Loading repository path..."]')).not.toHaveValue('', { timeout: 30000 });
      await expect(page.locator('input[placeholder="Loading repository path..."]')).toHaveValue(/adk_tutorial/);

      // Input the specific agent path
      await page.getByPlaceholder('src.agent:my_agent').fill('a_single_agent.day_trip:root_agent');
      await page.getByRole('button', { name: 'Scan Agent' }).click();

      // Ensure we navigate to agents and the graph renders
      await expect(page).toHaveURL(/\/agents/);
      await expect(page.getByRole('heading', { name: 'Agents Graph & Lineage' })).toBeVisible();
    });

    // ==========================================
    // 2. AGENT DOMAIN DEFINITION
    // ==========================================
    await test.step('Define Agent Domain', async () => {
      // Select the snapshot we just created (assuming it's the first non-empty option)
      await page.getByRole('combobox').first().selectOption({ index: 1 });
      
      // Fill out the domain boundaries
      await page.getByLabel('In Domain').fill('a day in <SOME TOWN> with a budget of $n.nn');
      await page.getByLabel('Out of Domain').fill('everything else');
      await page.getByRole('button', { name: 'Save Domain' }).click();
    });

    // ==========================================
    // 3. REGISTRIES (Tags, Extractors, Rubrics, Datasets)
    // ==========================================
    await test.step('Create dependencies in Registries', async () => {
      await page.getByRole('link', { name: 'Registries' }).click();
      await expect(page).toHaveURL(/\/registries/);

      // A. Create Tag
      await page.getByRole('button', { name: 'tags', exact: true }).click();
      await page.waitForLoadState('networkidle');
      await page.getByLabel('Tag Name').fill('europe-trips');
      await page.getByRole('button', { name: 'Save Tag' }).click();

      // B. Create Extractor for the budget
      await page.getByRole('button', { name: 'extractors', exact: true }).click();
      await page.waitForLoadState('networkidle');
      await page.getByLabel('Name').fill('extract_budget_float');
      await page.getByLabel('Return Type').selectOption('float');
      await page.getByLabel('Python Code').fill('def extract(trace):\n    # Extracts $nnnn.nn\n    return 500.00');
      await page.getByRole('button', { name: 'Save Extractor' }).click();

      // C. Create Rubric
      await page.getByRole('button', { name: 'rubrics', exact: true }).click();
      await page.waitForLoadState('networkidle');
      await page.getByLabel('Rubric Name').fill('Quality of Itinerary');
      await page.getByLabel('Instructions').fill('You are a travel critic...');
      await page.getByRole('button', { name: 'Add Field' }).click();
      await page.getByLabel('Field Name').fill('is_achievable');
      await page.getByLabel('Field Type').selectOption('Boolean');
      await page.getByRole('button', { name: 'Save Rubric' }).click();

      // D. Create Dataset
      await page.getByRole('button', { name: 'datasets', exact: true }).click();
      await page.waitForLoadState('networkidle');
      await page.getByLabel('Dataset Name').fill('DayTrip Tests');
      await page.getByRole('button', { name: 'Save Dataset' }).click();
    });

    // ==========================================
    // 4. CASES & EVAL BUILDER
    // ==========================================
    await test.step('Build test cases', async () => {
      await page.getByRole('link', { name: 'Cases & Evals' }).click();
      await expect(page).toHaveURL(/\/cases/);

      // Create Case 1
      await page.getByLabel('Case Name').fill('Paris 500 Budget');
      await page.getByLabel('Dataset').selectOption({ label: 'DayTrip Tests' });
      await page.getByLabel('Domain Position').selectOption('in');
      await page.getByLabel('Split').selectOption('judging');
      
      // Add conversation turns
      await page.getByRole('button', { name: '+ Add Turn' }).click();
      await page.locator('textarea').last().fill('Plan a day in Paris with a budget of $500.00');
      await page.getByRole('button', { name: 'Save Case' }).click();

      // Create Case 2 (Out of domain)
      await page.waitForLoadState('networkidle');
      await page.locator('.new-case-btn').click();
      await page.getByLabel('Case Name').fill('Mars Colonization');
      await page.getByLabel('Dataset').selectOption({ label: 'DayTrip Tests' });
      await page.getByLabel('Domain Position').selectOption('ood');
      await page.getByRole('button', { name: '+ Add Turn' }).click();
      await page.locator('textarea').last().fill('Plan a trip to Mars.');
      await page.getByRole('button', { name: 'Save Case' }).click();
    });

    // ==========================================
    // 5. RUN GENERATION
    // ==========================================
    await test.step('Generate traces against the dataset', async () => {
      await page.getByRole('link', { name: 'Run Generation' }).click();
      await expect(page).toHaveURL(/\/runs/);

      await page.waitForLoadState('networkidle');

      await page.locator('select[aria-label="Snapshot"]').selectOption({ index: 1 }); // Snapshot
      await page.locator('select[aria-label="Dataset"]').selectOption({ label: 'DayTrip Tests' }); // Dataset
      
      await page.locator('#generate-traces-btn').click();
      
      // Wait for it to become idle so traces can be set
      await page.waitForTimeout(500); // Give the event loop a moment
      
      await page.waitForTimeout(100);

      // Verify a trace shows up in the list
      await expect(page.locator('.trace-item').first()).toBeVisible({ timeout: 60000 });
    });

    // ==========================================
    // 6. RUN EVALS
    // ==========================================
    await test.step('Score the traces', async () => {
      await page.getByRole('link', { name: 'Run Evals' }).click();
      await expect(page).toHaveURL(/\/evals/);

      await page.locator('select[aria-label="Snapshot"]').selectOption({ index: 1 }); // Snapshot
      await page.locator('select[aria-label="Dataset"]').selectOption({ label: 'DayTrip Tests' }); // Dataset
      await page.getByRole('button', { name: 'Run Evaluations' }).click();

      await page.waitForLoadState('networkidle');

      // Wait for it to become idle so traces can be set
      await page.waitForTimeout(3000);

      // Wait for scored traces to appear
      await expect(page.locator('.eval-item').first()).toBeVisible({ timeout: 60000 });
    });

    // ==========================================
    // 7. CAMPAIGNS (IRT / Response Matrix)
    // ==========================================
    await test.step('Launch model comparison campaign', async () => {
      await page.getByRole('link', { name: 'Campaigns' }).click();
      await expect(page).toHaveURL(/\/campaigns/);

      await page.getByPlaceholder('e.g. Model Size Eval').fill('DayTrip Multi-Model Test');
      await page.getByLabel('Dataset').selectOption({ label: 'DayTrip Tests' });
      await page.getByLabel('Models (comma-separated)').fill('gemini-2.5-flash, gemini-2.5-flash-lite, gemini-3.1-pro-preview');
      
      // Assume a confirm card appears for expensive actions
      await page.getByRole('button', { name: 'Launch' }).click();
      
      const confirmCard = page.getByText(/Confirm/i);
      if (await confirmCard.isVisible()) {
        await page.getByRole('button', { name: 'Confirm' }).click();
      }
      
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(3000);

      // Matrix should populate after a while
      await expect(page.locator('.matrix-row').first()).toBeVisible({ timeout: 120000 });
    });

    // ==========================================
    // 8. HUMAN EVAL
    // ==========================================
    await test.step('Perform a human override/grading', async () => {
      await page.getByRole('link', { name: 'Human Eval' }).click();
      await expect(page).toHaveURL(/\/human-eval/);

      // Select the first trace
      await page.locator('select').first().selectOption({ index: 1 });
      
      // Expect our rubric to be present
      await expect(page.getByText('is_achievable')).toBeVisible();
      await page.getByLabel(/is_achievable/).selectOption('True');
      
      await page.getByRole('button', { name: 'Submit Grade' }).click();
    });

    // ==========================================
    // 9. CHAT OPERATOR
    // ==========================================
    await test.step('Talk to AGENT1', async () => {
      await page.getByRole('link', { name: 'Chat Operator' }).click();
      await expect(page).toHaveURL(/\/chat/);

      const chatInput = page.getByPlaceholder(/Ask the operator/i);
      await chatInput.fill('Can you show me the latest snapshot for the Day Trip agent?');
      await page.getByRole('button', { name: 'Send' }).click();

      // Ensure our message shows up in the chat window
      await expect(page.getByText('Can you show me the latest snapshot for the Day Trip agent?')).toBeVisible();
    });

  });
});
