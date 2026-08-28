import { expect, test, type Locator } from "@playwright/test";

const QUESTION =
  "What constraints should a critical-research run record for later audit?";

const SUMMARY =
  "Stub analysis complete. This fixture is deterministic and is not live research.";

const FINDINGS = [
  "The workflow accepted the submitted question and recorded a run identifier.",
  "No external sources were queried; findings are placeholder text.",
  "Replace stub services with a real backend when integration is in scope.",
];

const SOURCES = [
  { title: "AAMAD PRD (local)", href: /prd\.md/ },
  { title: "AAMAD SAD (local)", href: /sad\.md/ },
] as const;

const SEEDED_RUN_ID = "run-mock-seed";

/** Matches `src/frontend/src/index.css` status-pill colors (spec: gray / blue / green). */
const PILL_RGB = {
  idle: "rgb(141, 141, 141)",
  running: "rgb(47, 111, 237)",
  done: "rgb(46, 139, 79)",
} as const;

async function expectBanner(
  page: { locator: (selector: string) => Locator },
  phase: keyof typeof PILL_RGB,
  options?: { timeout?: number },
) {
  const banner = page.locator(".status-banner");
  await expect(banner.locator("strong")).toHaveText(`Crew: ${phase}`, options);
  const pill = banner.locator(".status-pill");
  await expect(pill).toHaveClass(new RegExp(`status-pill-${phase}`));
  await expect(pill).toHaveCSS("background-color", PILL_RGB[phase]);
  return banner;
}

test("happy path: seeded question reaches Crew: done with fixture results", async ({
  page,
}) => {
  await page.goto("/");

  const banner = await expectBanner(page, "idle");
  const lastUpdated = banner.locator(".last-updated");
  await expect(lastUpdated).toHaveText(/Last updated: \d{4}-\d{2}-\d{2}T/);

  const history = page.getByRole("region", { name: "History" });
  await expect(history.locator(".history-item")).toHaveCount(1);
  await expect(history.locator("code")).toHaveText(SEEDED_RUN_ID);

  await page.getByLabel("Research question").fill(QUESTION);
  await expect(page.getByLabel("Domain")).toHaveValue("general");
  await expect(page.getByLabel("Scope (optional)")).toHaveValue("");

  await page.getByRole("button", { name: "Run" }).click();

  await expectBanner(page, "running", { timeout: 5_000 });
  const stampWhileRunning = await lastUpdated.textContent();
  expect(stampWhileRunning).toMatch(/Last updated: \d{4}-\d{2}-\d{2}T/);

  await expect
    .poll(
      async () => {
        const label = await banner.locator("strong").textContent();
        const stamp = await lastUpdated.textContent();
        if (label !== "Crew: running") {
          return "left-running";
        }
        return stamp !== stampWhileRunning ? "updated" : "waiting";
      },
      { timeout: 8_000, message: "Last updated should change while polling" },
    )
    .toBe("updated");

  await expectBanner(page, "done", { timeout: 10_000 });

  const results = page.getByRole("region", { name: "Results" });
  await expect(results.locator(".lede")).toHaveText(SUMMARY);
  await expect(results.locator("ol li")).toHaveText(FINDINGS);

  const sourceLinks = results.getByRole("link");
  await expect(sourceLinks).toHaveCount(2);
  for (const [index, source] of SOURCES.entries()) {
    const link = sourceLinks.nth(index);
    await expect(link).toHaveText(source.title);
    await expect(link).toHaveAttribute("href", source.href);
    await expect(link).toHaveAttribute("target", "_blank");
  }

  const historyItems = history.locator(".history-item");
  await expect(historyItems).toHaveCount(2);
  const newest = historyItems.first();
  const newRunId = newest.locator("code");
  await expect(newRunId).toHaveText(/^run-mock-\d+$/);
  await expect(newRunId).not.toHaveText(SEEDED_RUN_ID);
  await expect(newest).toContainText(QUESTION);
  await expect(newest).toContainText("Crew: done");
  await expect(historyItems.nth(1).locator("code")).toHaveText(SEEDED_RUN_ID);
});
