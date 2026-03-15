import { test, expect } from '@playwright/test';

const mockProject = {
  id: 1,
  project_unique_id: 'proj-001',
  directory: 'test-project',
  name: 'Test Project',
  branch: 'main',
  gmt_create: Date.now(),
  gmt_modified: Date.now(),
  latest_active_time: null,
};

const mockWorkspaces = [
  {
    id: 1,
    workspace_unique_id: 'ws-001',
    project_unique_id: 'proj-001',
    branch: 'main',
    directory: 'feature-one',
    extra: null,
    gmt_create: Date.now() - 86400000,
    gmt_modified: Date.now() - 86400000,
    latest_active_time: null,
  },
  {
    id: 2,
    workspace_unique_id: 'ws-002',
    project_unique_id: 'proj-001',
    branch: 'develop',
    directory: 'feature-two',
    extra: null,
    gmt_create: Date.now() - 172800000,
    gmt_modified: Date.now() - 172800000,
    latest_active_time: null,
  },
];

const mockSessions = [
  {
    id: 1,
    session_unique_id: 'sess-001',
    external_session_id: 'ext-001',
    project_unique_id: 'proj-001',
    workspace_unique_id: 'ws-001',
    directory: 'feature-one',
    title: 'First Session',
    gmt_create: Date.now() - 3600000,
    gmt_modified: Date.now() - 3600000,
    time_compacting: null,
    time_archived: null,
  },
  {
    id: 2,
    session_unique_id: 'sess-002',
    external_session_id: 'ext-002',
    project_unique_id: 'proj-001',
    workspace_unique_id: 'ws-001',
    directory: 'feature-one',
    title: 'Second Session',
    gmt_create: Date.now() - 7200000,
    gmt_modified: Date.now() - 7200000,
    time_compacting: null,
    time_archived: null,
  },
];

test.describe('Session Management', () => {
  test.beforeEach(async ({ page }) => {
    await page.route('**/projects/**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([mockProject]),
      });
    });

    await page.route('**/workspaces/**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockWorkspaces),
      });
    });

    await page.route('**/sessions/**', async (route) => {
      const url = route.request().url();
      if (url.includes('ws-002')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([]),
        });
      } else {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(mockSessions),
        });
      }
    });
  });

  test('should display empty state when no workspace selected', async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.clear();
    });

    await page.goto('/');

    await expect(page.getByText('Select workspace to start')).toBeVisible();
    await expect(page.getByText('Choose a workspace from the sidebar to begin chatting')).toBeVisible();
  });

  test('should show workspace selected state when clicked', async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.clear();
    });

    await page.addInitScript((project) => {
      localStorage.setItem('buwai-project-storage', JSON.stringify({
        state: { selectedProject: project },
        version: 0,
      }));
    }, mockProject);

    await page.goto('/');

    await page.waitForSelector('text=feature-one');

    await page.getByRole('button', { name: /feature-one/ }).click();

    await expect(page.getByText('Select workspace to start')).not.toBeVisible();
    
    await expect(page.getByRole('button', { name: 'Polling' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Streaming' })).toBeVisible();
  });

  test('should load sessions when workspace is selected', async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.clear();
    });

    await page.addInitScript((project) => {
      localStorage.setItem('buwai-project-storage', JSON.stringify({
        state: { selectedProject: project },
        version: 0,
      }));
    }, mockProject);

    await page.goto('/');

    await expect(page.getByRole('heading', { name: 'Workspaces' })).toBeVisible();

    await page.getByRole('button', { name: /feature-one/ }).click();

    await page.waitForSelector('text=First Session');
    
    await expect(page.getByText('First Session')).toBeVisible();
    await expect(page.getByText('Second Session')).toBeVisible();
  });

  test('should auto-select last session when workspace switches', async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.clear();
    });

    await page.addInitScript((project) => {
      localStorage.setItem('buwai-project-storage', JSON.stringify({
        state: { selectedProject: project },
        version: 0,
      }));
    }, mockProject);

    await page.goto('/');

    await page.waitForSelector('text=feature-one');

    await page.getByRole('button', { name: /feature-one/ }).click();

    await page.waitForSelector('text=First Session');
    
    const firstSessionButton = page.getByRole('button', { name: /First Session/ });
    await expect(firstSessionButton).toBeVisible();

    await page.getByRole('button', { name: /feature-two/ }).click();

    await expect(page.getByText('No sessions yet')).toBeVisible();
  });

  test('should create new session when new chat button clicked', async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.clear();
    });

    await page.addInitScript((project) => {
      localStorage.setItem('buwai-project-storage', JSON.stringify({
        state: { selectedProject: project },
        version: 0,
      }));
    }, mockProject);

    await page.goto('/');

    await page.waitForSelector('text=feature-one');
    await page.getByRole('button', { name: /feature-one/ }).click();

    await page.waitForSelector('text=First Session');

    const sidebar = page.locator('aside');
    const sessionsHeading = sidebar.getByRole('heading', { name: 'Sessions' });
    await sessionsHeading.waitFor();
    
    const newSessionButton = sidebar.locator('button').filter({ has: page.locator('svg.lucide-plus') }).last();
    await newSessionButton.click();

    await expect(page.getByText('New Chat')).toBeVisible();
  });

  test('should display new session indicator', async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.clear();
    });

    await page.addInitScript((project) => {
      localStorage.setItem('buwai-project-storage', JSON.stringify({
        state: { selectedProject: project },
        version: 0,
      }));
    }, mockProject);

    await page.goto('/');

    await page.waitForSelector('text=feature-one');
    await page.getByRole('button', { name: /feature-one/ }).click();
    await page.waitForSelector('text=First Session');

    const sidebar = page.locator('aside');
    const sessionsHeading = sidebar.getByRole('heading', { name: 'Sessions' });
    await sessionsHeading.waitFor();
    
    const newSessionButton = sidebar.locator('button').filter({ has: page.locator('svg.lucide-plus') }).last();
    await newSessionButton.click();

    await expect(page.locator('text=New').first()).toBeVisible();
    
    await expect(page.getByText('New Chat')).toBeVisible();
  });
});
