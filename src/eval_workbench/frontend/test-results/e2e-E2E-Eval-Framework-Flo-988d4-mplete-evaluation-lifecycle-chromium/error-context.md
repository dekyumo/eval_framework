# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: e2e.spec.ts >> E2E Eval Framework Flow - Day Trip Agent >> Complete evaluation lifecycle
- Location: tests\e2e.spec.ts:85:3

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: getByLabel('In Distribution')
Expected: visible
Timeout: 60000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" with timeout 60000ms
  - waiting for getByLabel('In Distribution')

```

```yaml
- navigation:
  - text: science Lab Instrument Eval Workbench
  - link "account_tree Agents":
    - /url: /agents
  - link "fact_check View Cases":
    - /url: /cases
  - link "edit_note Case Editor":
    - /url: /cases_editor
  - link "play_circle Run Generation":
    - /url: /runs
  - link "checklist Run Evals":
    - /url: /evals
  - link "difference Compare":
    - /url: /compare
  - link "rocket_launch Campaigns":
    - /url: /campaigns
  - link "storage Registries":
    - /url: /registries
  - link "person Human Eval":
    - /url: /human-eval
- banner: "Target: C:\\Users\\Raph\\Prj\\kaggle_ai_agent_course\\eval_framework\\adk_tutorial"
- main:
  - heading "Agents Graph & Lineage" [level=1]
  - paragraph: Scan the agent repo, then pick a snapshot to inspect its manifest and lineage.
  - text: Agent path
  - textbox "Agent path":
    - /placeholder: src.agent:my_agent
    - text: a_single_agent.day_trip:root_agent
  - text: Commit / ref
  - textbox "Commit": HEAD
  - button "Scan Agent"
  - text: Failed to fetch
  - heading "Snapshot" [level=3]
  - combobox "Snapshot":
    - option "Select a snapshot..." [selected]
  - text: No snapshot selected. Scan an agent or pick one from the dropdown.
```

```
Error: expect(received).toBeTruthy()

Received: false
```

# Test source

```ts
  1   | import { test, expect } from '@playwright/test';
  2   | import fs from 'fs';
  3   | import path from 'path';
  4   | import { fileURLToPath } from 'url';
  5   | 
  6   | const __dirname = path.dirname(fileURLToPath(import.meta.url));
  7   | 
  8   | /** UI assertions: visibility, form state, selecting a row */
  9   | const UI_TIMEOUT = 10_000;
  10  | /** Single flash LLM call (case draft, extractor code) */
  11  | const LLM_TIMEOUT = 60_000;
  12  | /** Dataset batch: ~30s per case with google_search (3 cases) */
  13  | const RUN_BATCH_TIMEOUT = 180_000;
  14  | /** Agent scan / code-explorer workflows */
  15  | const SCAN_TIMEOUT = 60_000;
  16  | /** Two-model campaign matrix */
  17  | const CAMPAIGN_TIMEOUT = 180_000;
  18  | 
  19  | async function selectSnapshotAndDataset(page: import('@playwright/test').Page) {
  20  |   const snapshotSelect = page.locator('select[aria-label="Snapshot"]');
  21  |   const datasetSelect = page.locator('select[aria-label="Dataset"]');
  22  |   await expect(snapshotSelect.locator('option')).not.toHaveCount(1, { timeout: UI_TIMEOUT });
  23  |   await snapshotSelect.selectOption({ index: 1 });
  24  |   await expect(datasetSelect.locator('option', { hasText: 'DayTrip Tests' })).toBeAttached({ timeout: UI_TIMEOUT });
  25  |   await datasetSelect.selectOption({ label: 'DayTrip Tests' });
  26  | }
  27  | 
  28  | async function waitForCaseSave(page: import('@playwright/test').Page) {
  29  |   const saveResponse = page.waitForResponse(
  30  |     (r) => r.url().includes('/api/cases/') && r.request().method() === 'POST',
  31  |   );
  32  |   await page.getByRole('button', { name: /Save case/ }).click();
  33  |   await saveResponse;
  34  |   await expect(page).toHaveURL(/\/cases/);
  35  |   await page.getByRole('link', { name: 'Case Editor' }).click();
  36  |   await expect(page).toHaveURL(/\/cases_editor/);
  37  | }
  38  | 
  39  | async function waitForCaseSaveAndView(page: import('@playwright/test').Page) {
  40  |   const saveResponse = page.waitForResponse(
  41  |     (r) => r.url().includes('/api/cases/') && r.request().method() === 'POST',
  42  |   );
  43  |   await page.getByRole('button', { name: /Save case/ }).click();
  44  |   await saveResponse;
  45  |   await expect(page).toHaveURL(/\/cases/);
  46  | }
  47  | 
  48  | async function waitForAsyncJobButton(
  49  |   button: import('@playwright/test').Locator,
  50  |   busyLabel: string,
  51  |   idleLabel: string,
  52  |   timeout = RUN_BATCH_TIMEOUT,
  53  | ) {
  54  |   await expect(button).toBeEnabled({ timeout: UI_TIMEOUT });
  55  |   await button.click();
  56  |   await expect(button).toHaveText(busyLabel, { timeout: UI_TIMEOUT }).catch(() => {});
  57  |   await expect(button).toHaveText(idleLabel, { timeout });
  58  | }
  59  | 
  60  | test.describe('E2E Eval Framework Flow - Day Trip Agent', () => {
  61  |   
  62  |   test.beforeAll(async () => {
  63  |     const workspaceRoot = process.cwd();
  64  |     const evalFrameworkDir = path.resolve(workspaceRoot, '../../../adk_tutorial/eval_framework');
  65  |     if (fs.existsSync(evalFrameworkDir)) {
  66  |       fs.rmSync(evalFrameworkDir, { recursive: true, force: true });
  67  |     }
  68  |   });
  69  | 
  70  |   test.afterAll(async () => {
  71  |     const workspaceRoot = process.cwd();
  72  |     const evalFrameworkDir = path.resolve(workspaceRoot, '../../../adk_tutorial/eval_framework');
  73  |     expect(fs.existsSync(evalFrameworkDir)).toBeTruthy();
  74  |     expect(fs.existsSync(path.join(evalFrameworkDir, 'eval.kuzu'))).toBeTruthy();
  75  |     const extractorsDir = path.join(evalFrameworkDir, 'extractors');
> 76  |     expect(fs.existsSync(extractorsDir)).toBeTruthy();
      |                                          ^ Error: expect(received).toBeTruthy()
  77  |     const extractorFiles = fs.readdirSync(extractorsDir).filter((name) => name.endsWith('.py'));
  78  |     expect(extractorFiles.length).toBeGreaterThan(0);
  79  |     const mockedToolsDir = path.join(evalFrameworkDir, 'mocked_tools');
  80  |     expect(fs.existsSync(mockedToolsDir)).toBeTruthy();
  81  |     const mockedToolFiles = fs.readdirSync(mockedToolsDir).filter((name) => name.endsWith('.py'));
  82  |     expect(mockedToolFiles.length).toBeGreaterThan(0);
  83  |   });
  84  | 
  85  |   test('Complete evaluation lifecycle', async ({ page }) => {
  86  |     test.setTimeout(600_000);
  87  | 
  88  |     // Forward browser console logs to the test runner terminal
  89  |     page.on('console', msg => console.log('BROWSER LOG:', msg.text()));
  90  | 
  91  |     // ==========================================
  92  |     // 0. RESET DATABASE STATE
  93  |     // ==========================================
  94  |     const resetResponse = await page.context().request.post('http://127.0.0.1:5000/api/test/reset');
  95  |     expect(resetResponse.ok()).toBeTruthy();
  96  |     await page.goto('/');
  97  | 
  98  |     // ==========================================
  99  |     // 1. SCAN AGENT
  100 |     // ==========================================
  101 |     await test.step('Scan the Day Trip Agent', async () => {
  102 |       await page.goto('/agents');
  103 |       await expect(page.getByRole('heading', { name: 'Agents Graph & Lineage' })).toBeVisible();
  104 | 
  105 |       await page.getByLabel('Agent path').fill('a_single_agent.day_trip:root_agent');
  106 |       await page.getByRole('button', { name: 'Scan Agent' }).click();
  107 | 
  108 |       await expect(page.getByRole('button', { name: 'Scan Agent' })).toBeEnabled({ timeout: SCAN_TIMEOUT });
  109 |       await expect(page.getByLabel('In Distribution')).toBeVisible({ timeout: SCAN_TIMEOUT });
  110 |     });
  111 | 
  112 |     // ==========================================
  113 |     // 2. AGENT DISTRIBUTION DEFINITION
  114 |     // ==========================================
  115 |     await test.step('Define Agent Distribution', async () => {
  116 |       // Scan auto-selects the new snapshot; distribution fields are already visible.
  117 |       await page.getByLabel('In Distribution').fill('a day in <SOME TOWN> with a budget of $n.nn');
  118 |       await page.getByLabel('Out of Distribution').fill('everything else');
  119 |       await page.getByRole('button', { name: 'Save Distribution' }).click();
  120 |     });
  121 | 
  122 |     await test.step('Save NIST AI RMF profile business justification', async () => {
  123 |       await expect(page.getByRole('heading', { name: 'NIST AI RMF Profile' })).toBeVisible({ timeout: UI_TIMEOUT });
  124 |       const businessCase = 'Agent run costs about $0.10 vs $1.00 for a human reviewer.';
  125 |       await page.getByLabel('Business case').fill(businessCase);
  126 |       await page.getByRole('button', { name: 'Save Profile' }).click();
  127 |       await expect(page.getByLabel('Business case')).toHaveValue(businessCase);
  128 |     });
  129 | 
  130 |     // ==========================================
  131 |     // 3. REGISTRIES (Tags, Extractors, Rubrics, Datasets)
  132 |     // ==========================================
  133 |     await test.step('Create dependencies in Registries', async () => {
  134 |       await page.getByRole('link', { name: 'Registries' }).click();
  135 |       await expect(page).toHaveURL(/\/registries/);
  136 | 
  137 |       const clickWithRetry = async (testId: string, text: string, expectedButtonName: string, containerSelector?: string) => {
  138 |         await page.waitForTimeout(1000);
  139 |         
  140 |         // Try programmatically clicking the test ID first to bypass any click propagation issue
  141 |         await page.evaluate((id) => {
  142 |           const el = document.querySelector(`[data-testid="${id}"]`);
  143 |           if (el) (el as HTMLElement).click();
  144 |         }, testId);
  145 | 
  146 |         let isVisible = await page.getByRole('button', { name: expectedButtonName }).isVisible();
  147 |         if (!isVisible) {
  148 |           // Try clicking via Playwright's click on the test ID locator
  149 |           try {
  150 |             await page.getByTestId(testId).first().click({ timeout: 2000 });
  151 |             isVisible = await page.getByRole('button', { name: expectedButtonName }).isVisible();
  152 |           } catch (e) {}
  153 |         }
  154 |         
  155 |         if (!isVisible) {
  156 |           // Try clicking via text locator programmatically
  157 |           await page.evaluate((txt) => {
  158 |             const el = Array.from(document.querySelectorAll('*')).find(x => x.textContent === txt);
  159 |             if (el) (el as HTMLElement).click();
  160 |           }, text);
  161 |           isVisible = await page.getByRole('button', { name: expectedButtonName }).isVisible();
  162 |         }
  163 | 
  164 |         if (!isVisible) {
  165 |           // Try standard Playwright click on text
  166 |           try {
  167 |             await page.getByText(text).first().click({ timeout: 2000 });
  168 |             isVisible = await page.getByRole('button', { name: expectedButtonName }).isVisible();
  169 |           } catch (e) {}
  170 |         }
  171 | 
  172 |         await expect(page.getByRole('button', { name: expectedButtonName })).toBeVisible({ timeout: 5000 });
  173 |       };
  174 | 
  175 |       // A. Create, update, and delete Tag
  176 |       await page.getByRole('button', { name: 'tags', exact: true }).click();
```