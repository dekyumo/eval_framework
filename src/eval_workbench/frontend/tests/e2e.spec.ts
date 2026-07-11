import { test, expect } from '@playwright/test';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

/** UI assertions: visibility, form state, selecting a row */
const UI_TIMEOUT = 10_000;
/** Single flash LLM call (case draft, extractor code) */
const LLM_TIMEOUT = 60_000;
/** Dataset batch: ~30s per case with google_search (3 cases) */
const RUN_BATCH_TIMEOUT = 180_000;
/** Agent scan / code-explorer workflows */
const SCAN_TIMEOUT = 60_000;
/** Two-model campaign matrix */
const CAMPAIGN_TIMEOUT = 180_000;

async function selectSnapshotAndDataset(page: import('@playwright/test').Page) {
  const snapshotSelect = page.locator('select[aria-label="Snapshot"]');
  const datasetSelect = page.locator('select[aria-label="Dataset"]');
  await expect(snapshotSelect.locator('option')).not.toHaveCount(1, { timeout: UI_TIMEOUT });
  await snapshotSelect.selectOption({ index: 1 });
  await expect(datasetSelect.locator('option', { hasText: 'DayTrip Tests' })).toBeAttached({ timeout: UI_TIMEOUT });
  await datasetSelect.selectOption({ label: 'DayTrip Tests' });
}

async function waitForCaseSave(page: import('@playwright/test').Page) {
  const saveResponse = page.waitForResponse(
    (r) => r.url().includes('/api/cases/') && r.request().method() === 'POST',
  );
  await page.getByRole('button', { name: 'Save Case' }).click();
  await saveResponse;
  await expect(page.getByLabel('Case Name')).toHaveValue('');
}

async function waitForAsyncJobButton(
  button: import('@playwright/test').Locator,
  busyLabel: string,
  idleLabel: string,
  timeout = RUN_BATCH_TIMEOUT,
) {
  await expect(button).toBeEnabled({ timeout: UI_TIMEOUT });
  await button.click();
  await expect(button).toHaveText(busyLabel, { timeout: UI_TIMEOUT }).catch(() => {});
  await expect(button).toHaveText(idleLabel, { timeout });
}

test.describe('E2E Eval Framework Flow - Day Trip Agent', () => {
  
  test.beforeAll(async () => {
    const workspaceRoot = process.cwd();
    const evalFrameworkDir = path.resolve(workspaceRoot, '../../../adk_tutorial/eval_framework');
    if (fs.existsSync(evalFrameworkDir)) {
      fs.rmSync(evalFrameworkDir, { recursive: true, force: true });
    }
  });

  test.afterAll(async () => {
    const workspaceRoot = process.cwd();
    const evalFrameworkDir = path.resolve(workspaceRoot, '../../../adk_tutorial/eval_framework');
    expect(fs.existsSync(evalFrameworkDir)).toBeTruthy();
    expect(fs.existsSync(path.join(evalFrameworkDir, 'eval.kuzu'))).toBeTruthy();
    const extractorsDir = path.join(evalFrameworkDir, 'extractors');
    expect(fs.existsSync(extractorsDir)).toBeTruthy();
    const extractorFiles = fs.readdirSync(extractorsDir).filter((name) => name.endsWith('.py'));
    expect(extractorFiles.length).toBeGreaterThan(0);
    const mockedToolsDir = path.join(evalFrameworkDir, 'mocked_tools');
    expect(fs.existsSync(mockedToolsDir)).toBeTruthy();
    const mockedToolFiles = fs.readdirSync(mockedToolsDir).filter((name) => name.endsWith('.py'));
    expect(mockedToolFiles.length).toBeGreaterThan(0);
  });

  test('Complete evaluation lifecycle', async ({ page }) => {
    test.setTimeout(600_000);

    // Forward browser console logs to the test runner terminal
    page.on('console', msg => console.log('BROWSER LOG:', msg.text()));

    // ==========================================
    // 0. RESET DATABASE STATE
    // ==========================================
    await page.context().request.post('http://127.0.0.1:5000/api/test/reset');
    await page.goto('/');

    // ==========================================
    // 1. SCAN AGENT
    // ==========================================
    await test.step('Scan the Day Trip Agent', async () => {
      await page.goto('/agents');
      await expect(page.getByRole('heading', { name: 'Agents Graph & Lineage' })).toBeVisible();

      await page.getByLabel('Agent path').fill('a_single_agent.day_trip:root_agent');
      await page.getByRole('button', { name: 'Scan Agent' }).click();

      await expect(page.getByRole('button', { name: 'Scan Agent' })).toBeEnabled({ timeout: SCAN_TIMEOUT });
      await expect(page.getByLabel('In Distribution')).toBeVisible({ timeout: SCAN_TIMEOUT });
    });

    // ==========================================
    // 2. AGENT DISTRIBUTION DEFINITION
    // ==========================================
    await test.step('Define Agent Distribution', async () => {
      // Scan auto-selects the new snapshot; distribution fields are already visible.
      await page.getByLabel('In Distribution').fill('a day in <SOME TOWN> with a budget of $n.nn');
      await page.getByLabel('Out of Distribution').fill('everything else');
      await page.getByRole('button', { name: 'Save Distribution' }).click();
    });

    await test.step('Save NIST AI RMF profile business justification', async () => {
      await expect(page.getByRole('heading', { name: 'NIST AI RMF Profile' })).toBeVisible({ timeout: UI_TIMEOUT });
      const businessCase = 'Agent run costs about $0.10 vs $1.00 for a human reviewer.';
      await page.getByLabel('Business case').fill(businessCase);
      await page.getByRole('button', { name: 'Save Profile' }).click();
      await expect(page.getByLabel('Business case')).toHaveValue(businessCase);
    });

    // ==========================================
    // 3. REGISTRIES (Tags, Extractors, Rubrics, Datasets)
    // ==========================================
    await test.step('Create dependencies in Registries', async () => {
      await page.getByRole('link', { name: 'Registries' }).click();
      await expect(page).toHaveURL(/\/registries/);

      const clickWithRetry = async (testId: string, text: string, expectedButtonName: string, containerSelector?: string) => {
        await page.waitForTimeout(1000);
        
        // Try programmatically clicking the test ID first to bypass any click propagation issue
        await page.evaluate((id) => {
          const el = document.querySelector(`[data-testid="${id}"]`);
          if (el) (el as HTMLElement).click();
        }, testId);

        let isVisible = await page.getByRole('button', { name: expectedButtonName }).isVisible();
        if (!isVisible) {
          // Try clicking via Playwright's click on the test ID locator
          try {
            await page.getByTestId(testId).first().click({ timeout: 2000 });
            isVisible = await page.getByRole('button', { name: expectedButtonName }).isVisible();
          } catch (e) {}
        }
        
        if (!isVisible) {
          // Try clicking via text locator programmatically
          await page.evaluate((txt) => {
            const el = Array.from(document.querySelectorAll('*')).find(x => x.textContent === txt);
            if (el) (el as HTMLElement).click();
          }, text);
          isVisible = await page.getByRole('button', { name: expectedButtonName }).isVisible();
        }

        if (!isVisible) {
          // Try standard Playwright click on text
          try {
            await page.getByText(text).first().click({ timeout: 2000 });
            isVisible = await page.getByRole('button', { name: expectedButtonName }).isVisible();
          } catch (e) {}
        }

        await expect(page.getByRole('button', { name: expectedButtonName })).toBeVisible({ timeout: 5000 });
      };

      // A. Create, update, and delete Tag
      await page.getByRole('button', { name: 'tags', exact: true }).click();
      await page.waitForLoadState('networkidle');
      await page.getByLabel('Tag Name').fill('europe-trips-temp');
      await page.getByRole('button', { name: 'Save Tag' }).click();
      
      // Select the tag to edit it
      await clickWithRetry('tag-pill-europe-trips-temp', 'europe-trips-temp', 'Update Tag', 'div');
      
      await page.getByLabel('Tag Name').clear();
      await page.getByLabel('Tag Name').fill('europe-trips');
      await page.getByRole('button', { name: 'Update Tag' }).click();
      await expect(page.getByRole('button', { name: 'Save Tag' })).toBeVisible({ timeout: UI_TIMEOUT });

      // Create and delete empty tag
      await page.getByLabel('Tag Name').fill('temp-tag');
      await page.getByRole('button', { name: 'Save Tag' }).click();
      await page.locator('[data-testid="tag-pill-temp-tag"]').getByRole('button', { name: 'Delete' }).click();

      // B. Create, generate with agent, update, and delete Extractor for the budget
      await page.getByRole('button', { name: 'extractors', exact: true }).click();
      await page.waitForLoadState('networkidle');

      // Test agent-assisted extractor generation
      await page.getByPlaceholder('e.g. Find the last dollar value in the trace and convert it to float').fill('Find the final budget and return float');
      await page.getByRole('button', { name: 'Generate Code' }).click();
      await expect(page.getByRole('button', { name: 'Generate Code' })).not.toBeDisabled({ timeout: LLM_TIMEOUT });
      await expect(page.locator('#extractor_python_code')).not.toHaveValue('def extract(trace):\n    return True', { timeout: LLM_TIMEOUT });

      // Fill Name and Type and save
      await page.getByLabel('Name').fill('extract_budget_float_temp');
      await page.getByLabel('Return Type').selectOption('float');
      await page.getByLabel('Python Code').fill('def extract(trace):\n    # Extracts $nnnn.nn\n    return 500.00');
      await page.getByRole('button', { name: 'Save Extractor' }).click();

      // Update name
      await clickWithRetry('extractor-item-extract_budget_float_temp', 'extract_budget_float_temp', 'Update Extractor', 'div');
      await page.getByLabel('Name').clear();
      await page.getByLabel('Name').fill('extract_budget_float');
      await page.getByRole('button', { name: 'Update Extractor' }).click();
      await expect(page.getByRole('button', { name: 'Save Extractor' })).toBeVisible({ timeout: UI_TIMEOUT });

      // Create and delete unused extractor
      await page.getByLabel('Name').fill('temp_extractor');
      await page.getByRole('button', { name: 'Save Extractor' }).click();
      await page.locator('[data-testid="extractor-item-temp_extractor"]').getByRole('button', { name: 'Delete' }).click();

      // C. Create, update, and delete Rubric
      await page.getByRole('button', { name: 'rubrics', exact: true }).click();
      await page.waitForLoadState('networkidle');
      await page.getByLabel('Rubric Name').fill('Quality of Itinerary Temp');
      await page.getByLabel('Instructions').fill('You are a travel critic...');
      await page.getByRole('button', { name: 'Add Field' }).click();
      await page.getByLabel('Field Name').fill('is_achievable');
      await page.getByLabel('Type').selectOption('bool');
      await page.getByRole('button', { name: 'Save Rubric' }).click();

      // Update Rubric Name
      await clickWithRetry('rubric-item-Quality of Itinerary Temp', 'Quality of Itinerary Temp', 'Update Rubric', 'div');
      await page.getByLabel('Rubric Name').clear();
      await page.getByLabel('Rubric Name').fill('Quality of Itinerary');
      await page.getByRole('button', { name: 'Update Rubric' }).click();
      await expect(page.getByRole('button', { name: 'Save Rubric' })).toBeVisible({ timeout: UI_TIMEOUT });

      // Create and delete unused rubric
      await page.getByLabel('Rubric Name').fill('Temp Rubric');
      await page.getByRole('button', { name: 'Save Rubric' }).click();
      await page.locator('[data-testid="rubric-item-Temp Rubric"]').getByRole('button', { name: 'Delete' }).click();

      // Paris afternoon multimodal rubric (float 0-100)
      await page.getByLabel('Rubric Name').fill('Contains advice for an afternoon in Paris');
      await page.getByLabel('Instructions').fill(
        'Score how well the agent advises spending an afternoon in Paris. 0 means no relevant advice; 100 means excellent, specific Paris afternoon guidance.'
      );
      await page.getByRole('button', { name: 'Add Field' }).click();
      await page.getByLabel('Field Name').fill('paris_afternoon_score');
      await page.getByLabel('Type').selectOption('float');
      await page.locator('#rubric_field_desc_0').fill('Float score from 0 to 100');
      await page.getByRole('button', { name: 'Save Rubric' }).click();
      await expect(page.getByRole('button', { name: 'Save Rubric' })).toBeVisible({ timeout: UI_TIMEOUT });

      // D. Create, update, and delete Dataset
      await page.getByRole('button', { name: 'datasets', exact: true }).click();
      await page.waitForLoadState('networkidle');
      await page.getByLabel('Dataset Name').fill('DayTrip Tests Temp');
      await page.getByRole('button', { name: 'Save Dataset' }).click();

      // Edit dataset name
      await clickWithRetry('dataset-item-DayTrip Tests Temp', 'DayTrip Tests Temp', 'Update Dataset', 'div');
      await page.getByLabel('Dataset Name').clear();
      await page.getByLabel('Dataset Name').fill('DayTrip Tests');
      await page.getByRole('button', { name: 'Update Dataset' }).click();
      await expect(page.getByRole('button', { name: 'Save Dataset' })).toBeVisible({ timeout: UI_TIMEOUT });

      // Create and delete empty dataset
      await page.getByLabel('Dataset Name').fill('Unused Dataset');
      await page.getByRole('button', { name: 'Save Dataset' }).click();
      await page.locator('[data-testid="dataset-item-Unused Dataset"]').getByRole('button', { name: 'Delete' }).click();
    });

    // ==========================================
    // 4. CASES & EVAL BUILDER
    // ==========================================
    await test.step('Build test cases', async () => {
      await page.getByRole('link', { name: 'Cases & Evals' }).click();
      await expect(page).toHaveURL(/\/cases/);

      // Generate case draft via AGENT5
      const userMessage = page.getByLabel('User message');
      await userMessage.clear();
      await expect(userMessage).toHaveValue('');
      await page.getByLabel('Case generation prompt').fill(
        'Plan a day in Paris with a budget of $500.00, in-distribution happy path'
      );
      await page.getByRole('button', { name: 'Generate Case' }).click();
      await expect(userMessage).not.toHaveValue('', { timeout: LLM_TIMEOUT });
      const generatedText = await userMessage.inputValue();
      console.log('Generated user message:', generatedText);

      // Create Case 1
      await page.getByLabel('Case Name').fill('Paris 500 Budget');
      await page.getByLabel('Dataset').selectOption({ label: 'DayTrip Tests' });
      await page.getByLabel('Distribution Position').selectOption('in');
      await page.getByLabel('Split').selectOption('test');

      // Add Rubric metric
      await page.getByRole('button', { name: '+ Add Metric' }).click();
      await page.locator('[data-testid="metric-row"]').first().locator('input').first().fill('budget_polite');
      const row1 = page.locator('[data-testid="metric-row"]').first();
      await row1.locator('select').first().selectOption('rubric');
      await row1.locator('select').nth(1).selectOption({ label: 'Quality of Itinerary' });

      // Add Deterministic metric
      await page.getByRole('button', { name: '+ Add Metric' }).click();
      await page.locator('[data-testid="metric-row"]').nth(1).locator('input').first().fill('budget_correct');
      const row2 = page.locator('[data-testid="metric-row"]').nth(1);
      await row2.locator('select').first().selectOption('deterministic');
      await row2.locator('select').nth(1).selectOption({ label: 'extract_budget_float' });
      await row2.locator('input').nth(1).fill('500.00');

      // Paris afternoon rubric metric
      await page.getByRole('button', { name: '+ Add Metric' }).click();
      await page.locator('[data-testid="metric-row"]').nth(2).locator('input').first().fill('paris_afternoon');
      const row3 = page.locator('[data-testid="metric-row"]').nth(2);
      await row3.locator('select').first().selectOption('rubric');
      await row3.locator('select').nth(1).selectOption({ label: 'Contains advice for an afternoon in Paris' });

      // Tool fault injection on google_search
      await page.getByLabel('Tool fault mode').selectOption('enabled');
      await page.getByLabel('Tool fault tool name').fill('google_search');
      await page.getByLabel('Tool fault type').selectOption('interface');

      await waitForCaseSave(page);

      // Create Case 2: multimodal Eiffel Tower afternoon
      await page.locator('.new-case-btn').click();
      await page.getByLabel('Case Name').fill('Eiffel Tower Afternoon');
      await page.getByLabel('Dataset').selectOption({ label: 'DayTrip Tests' });
      await page.getByLabel('Distribution Position').selectOption('in');
      await page.getByLabel('User message').fill('I want to spend an afternoon there, I have $30');
      await page.getByRole('button', { name: '+ Add Turn' }).click();
      await page.locator('[data-testid="conversation-turn-1"] select').selectOption('user_media');
      const imagePath = path.join(__dirname, 'eiffel_tap.png');
      await page.getByTestId('user-media-upload-1').setInputFiles(imagePath);
      await expect(page.getByTestId('media-ready-1')).toBeVisible({ timeout: UI_TIMEOUT });
      await expect(page.getByText('eiffel_tap.png')).toBeVisible({ timeout: UI_TIMEOUT });
      await page.getByRole('button', { name: '+ Add Metric' }).click();
      await page.locator('[data-testid="metric-row"]').first().locator('input').first().fill('paris_afternoon');
      const eiffelMetric = page.locator('[data-testid="metric-row"]').first();
      await eiffelMetric.locator('select').first().selectOption('rubric');
      await eiffelMetric.locator('select').nth(1).selectOption({ label: 'Contains advice for an afternoon in Paris' });
      await waitForCaseSave(page);

      // Create Case 3 (Out of distribution)
      await page.locator('.new-case-btn').click();
      await page.getByLabel('Case Name').fill('Mars Colonization');
      await page.getByLabel('Dataset').selectOption({ label: 'DayTrip Tests' });
      await page.getByLabel('Distribution Position').selectOption('ood');
      //do not add a user turn, there's already an empty one by default await page.getByRole('button', { name: '+ Add Turn' }).click();
      await page.locator('textarea').last().fill('Plan a trip to Mars.');
      await waitForCaseSave(page);
    });

    // ==========================================
    // 5. RUN GENERATION
    // ==========================================
    await test.step('Generate traces against the dataset', async () => {
      await page.getByRole('link', { name: 'Run Generation' }).click();
      await expect(page).toHaveURL(/\/runs/);

      await page.waitForLoadState('networkidle');

      await selectSnapshotAndDataset(page);

      const generateBtn = page.locator('#generate-traces-btn');
      await waitForAsyncJobButton(generateBtn, 'Generating...', 'Generate Traces', RUN_BATCH_TIMEOUT);

      const parisTrace = page.locator('.trace-item').filter({ hasText: 'Paris 500 Budget' });
      await expect(parisTrace.getByText('ran', { exact: true })).toBeVisible({ timeout: RUN_BATCH_TIMEOUT });
    });

    // ==========================================
    // 6. RUN EVALS
    // ==========================================
    await test.step('Score the traces', async () => {
      await page.getByRole('link', { name: 'Run Evals' }).click();
      await expect(page).toHaveURL(/\/evals/);

      await selectSnapshotAndDataset(page);

      const evalBtn = page.getByRole('button', { name: 'Run Evaluations' });
      await waitForAsyncJobButton(evalBtn, 'Evaluating...', 'Run Evaluations', RUN_BATCH_TIMEOUT);

      const parisEval = page.locator('.eval-item').filter({ hasText: 'Paris 500 Budget' });
      await expect(parisEval.getByText('ran', { exact: true })).toBeVisible({ timeout: RUN_BATCH_TIMEOUT });
      await parisEval.click();

      await expect(page.getByText('budget_polite')).toBeVisible({ timeout: UI_TIMEOUT });
      await expect(page.getByText('budget_correct')).toBeVisible({ timeout: UI_TIMEOUT });
      await expect(page.getByText('paris_afternoon')).toBeVisible({ timeout: UI_TIMEOUT });
    });

    // ==========================================
    // 7. CAMPAIGNS (IRT / Response Matrix)
    // ==========================================
    await test.step('Launch model comparison campaign', async () => {
      await page.getByRole('link', { name: 'Campaigns' }).click();
      await expect(page).toHaveURL(/\/campaigns/);

      await page.getByPlaceholder('e.g. Model Size Eval').fill('DayTrip Multi-Model Test');
      await page.getByLabel('Dataset').selectOption({ label: 'DayTrip Tests' });
      await page.getByLabel('Base Snapshot').selectOption({ index: 1 });
      await page.getByLabel('Models (comma-separated)').fill('gemini-2.5-flash, gemini-2.5-flash-lite');
      
      // Assume a confirm card appears for expensive actions
      await page.getByRole('button', { name: 'Launch' }).click();
      
      const confirmCard = page.getByText(/Confirm/i);
      if (await confirmCard.isVisible()) {
        await page.getByRole('button', { name: 'Confirm' }).click();
      }
      
      await expect(page.locator('.matrix-row').first()).toBeVisible({ timeout: CAMPAIGN_TIMEOUT });
    });

    // ==========================================
    // 8. HUMAN EVAL
    // ==========================================
    await test.step('Perform a human override/grading', async () => {
      await page.getByRole('link', { name: 'Human Eval' }).click();
      await expect(page).toHaveURL(/\/human-eval/);

      const runSelect = page.getByLabel('Run to grade');
      await expect(runSelect.locator('option').nth(1)).toBeAttached({ timeout: UI_TIMEOUT });

      const runId = await runSelect.locator('option').nth(1).getAttribute('value');
      await runSelect.selectOption(runId!);
      await expect(page.getByText('Select a rubric and grade the trace.')).toBeVisible({ timeout: UI_TIMEOUT });

      await page.getByLabel('Rubric').selectOption({ label: 'Quality of Itinerary' });
      await expect(page.getByLabel('is_achievable')).toBeVisible({ timeout: UI_TIMEOUT });
      await page.getByLabel('is_achievable').selectOption('True');
      
      await page.getByRole('button', { name: 'Submit Grade' }).click();
    });

  });
});
