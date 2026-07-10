import { test, expect } from '@playwright/test';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

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
    // We increase timeout for the full E2E flow since it encompasses many steps
    test.setTimeout(600000);

    // Forward browser console logs to the test runner terminal
    page.on('console', msg => console.log('BROWSER LOG:', msg.text()));

    // ==========================================
    // 0. RESET DATABASE STATE
    // ==========================================
    await page.context().request.post('http://127.0.0.1:5000/api/test/reset');
    await page.goto('/');

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
      await expect(page).toHaveURL(/\/agents/, { timeout: 90000 });
      await expect(page.getByRole('heading', { name: 'Agents Graph & Lineage' })).toBeVisible();
    });

    // ==========================================
    // 2. AGENT DISTRIBUTION DEFINITION
    // ==========================================
    await test.step('Define Agent Distribution', async () => {
      // Select the snapshot we just created (assuming it's the first non-empty option)
      await page.getByRole('combobox').first().selectOption({ index: 1 });
      
      // Fill out the distribution boundaries
      await page.getByLabel('In Distribution').fill('a day in <SOME TOWN> with a budget of $n.nn');
      await page.getByLabel('Out of Distribution').fill('everything else');
      await page.getByRole('button', { name: 'Save Distribution' }).click();
    });

    await test.step('Save NIST AI RMF profile business justification', async () => {
      await expect(page.getByRole('heading', { name: 'NIST AI RMF Profile' })).toBeVisible({ timeout: 15000 });
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
      await expect(page.getByRole('button', { name: 'Save Tag' })).toBeVisible({ timeout: 10000 });

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
      await expect(page.getByRole('button', { name: 'Generate Code' })).not.toBeDisabled({ timeout: 60000 });
      await expect(page.locator('#extractor_python_code')).not.toHaveValue('def extract(trace):\n    return True', { timeout: 30000 });

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
      await expect(page.getByRole('button', { name: 'Save Extractor' })).toBeVisible({ timeout: 10000 });

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
      await expect(page.getByRole('button', { name: 'Save Rubric' })).toBeVisible({ timeout: 10000 });

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
      await expect(page.getByRole('button', { name: 'Save Rubric' })).toBeVisible({ timeout: 10000 });

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
      await expect(page.getByRole('button', { name: 'Save Dataset' })).toBeVisible({ timeout: 10000 });

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
      await expect(userMessage).not.toHaveValue('', { timeout: 120000 });
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

      await page.getByRole('button', { name: 'Save Case' }).click();

      // Create Case 2: multimodal Eiffel Tower afternoon
      await page.waitForLoadState('networkidle');
      await page.locator('.new-case-btn').click();
      await page.getByLabel('Case Name').fill('Eiffel Tower Afternoon');
      await page.getByLabel('Dataset').selectOption({ label: 'DayTrip Tests' });
      await page.getByLabel('Distribution Position').selectOption('in');
      await page.getByLabel('User message').fill('I want to spend an afternoon there, I have $30');
      await page.getByRole('button', { name: '+ Add Turn' }).click();
      await page.locator('[data-testid="conversation-turn-1"] select').selectOption('user_media');
      const imagePath = path.join(__dirname, 'eiffel_tap.png');
      await page.getByTestId('user-media-upload-1').setInputFiles(imagePath);
      await expect(page.getByTestId('media-ready-1')).toBeVisible({ timeout: 10000 });
      await expect(page.getByText('eiffel_tap.png')).toBeVisible({ timeout: 5000 });
      await page.getByRole('button', { name: '+ Add Metric' }).click();
      await page.locator('[data-testid="metric-row"]').first().locator('input').first().fill('paris_afternoon');
      const eiffelMetric = page.locator('[data-testid="metric-row"]').first();
      await eiffelMetric.locator('select').first().selectOption('rubric');
      await eiffelMetric.locator('select').nth(1).selectOption({ label: 'Contains advice for an afternoon in Paris' });
      await page.getByRole('button', { name: 'Save Case' }).click();

      // Create Case 3 (Out of distribution)
      await page.waitForLoadState('networkidle');
      await page.locator('.new-case-btn').click();
      await page.getByLabel('Case Name').fill('Mars Colonization');
      await page.getByLabel('Dataset').selectOption({ label: 'DayTrip Tests' });
      await page.getByLabel('Distribution Position').selectOption('ood');
      //do not add a user turn, there's already an empty one by default await page.getByRole('button', { name: '+ Add Turn' }).click();
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
      await expect(page.locator('.trace-item').first()).toBeVisible({ timeout: 120000 });
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
      await expect(page.locator('.eval-item').first()).toBeVisible({ timeout: 120000 });

      // Click the first scored run to load its detail
      await page.locator('.eval-item').first().click();

      // Ensure the metrics we added (budget_polite, budget_correct) are displayed
      await expect(page.getByText('budget_polite')).toBeVisible({ timeout: 10000 });
      await expect(page.getByText('budget_correct')).toBeVisible({ timeout: 10000 });
      await expect(page.getByText('paris_afternoon')).toBeVisible({ timeout: 10000 });
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
      
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(3000);

      // Matrix should populate after a while
      await expect(page.locator('.matrix-row').first()).toBeVisible({ timeout: 360000 });
    });

    // ==========================================
    // 8. HUMAN EVAL
    // ==========================================
    await test.step('Perform a human override/grading', async () => {
      await page.getByRole('link', { name: 'Human Eval' }).click();
      await expect(page).toHaveURL(/\/human-eval/);

      const runSelect = page.getByLabel('Run to grade');
      await expect(runSelect.locator('option').nth(1)).toBeAttached({ timeout: 15000 });

      const runId = await runSelect.locator('option').nth(1).getAttribute('value');
      await runSelect.selectOption(runId!);
      await expect(page.getByText('Select a rubric and grade the trace.')).toBeVisible({ timeout: 15000 });

      await page.getByLabel('Rubric').selectOption({ label: 'Quality of Itinerary' });
      await expect(page.getByLabel('is_achievable')).toBeVisible({ timeout: 15000 });
      await page.getByLabel('is_achievable').selectOption('True');
      
      await page.getByRole('button', { name: 'Submit Grade' }).click();
    });

  });
});
