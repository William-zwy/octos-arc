const { chromium, expect } = require(process.env.OCTOS_ARC_TEST_PLAYWRIGHT_PACKAGE || "@playwright/test");

async function main() {
  const launch = { headless: true };
  if (process.env.OCTOS_ARC_TEST_CHROMIUM_PATH) {
    launch.executablePath = process.env.OCTOS_ARC_TEST_CHROMIUM_PATH;
  }
  const browser = await chromium.launch(launch);
  try {
    const page = await browser.newPage();
    await page.setContent(`
      <div role="dialog" aria-label="Note editor">
        <label>Title <input value="Draft title"></label>
        <label>Note content <textarea></textarea></label>
        <button type="button" aria-expanded="false">More options</button>
        <fieldset hidden>
          <legend>Labels</legend>
          <label><input type="checkbox" name="label">Work</label>
          <button type="button">Close labels</button>
        </fieldset>
        <button id="close-editor" type="button">Close</button>
      </div>
      <script>
        const editor = document.querySelector('[role="dialog"]');
        const trigger = editor.querySelector('button[aria-expanded]');
        const properties = editor.querySelector('fieldset');
        trigger.addEventListener('click', () => {
          properties.hidden = false;
          trigger.setAttribute('aria-expanded', 'true');
        });
        properties.querySelector('button').addEventListener('click', () => {
          properties.hidden = true;
          trigger.setAttribute('aria-expanded', 'false');
          trigger.focus();
        });
        editor.querySelector('#close-editor').addEventListener('click', () => {
          editor.hidden = true;
        });
      </script>
    `);

    const editor = page.getByRole("dialog", { name: /^Note editor$/i });
    const content = editor.getByRole("textbox", { name: /^Note content$/i });
    await content.fill("Unsaved body stays in the editor");
    const moreOptions = editor.getByRole("button", { name: /^More options$/i });
    await moreOptions.click();
    await editor.getByRole("checkbox", { name: /^Work$/i }).check();
    await expect(content).toHaveValue("Unsaved body stays in the editor");
    await editor.getByRole("button", { name: /^Close labels$/i }).click();
    await expect(editor).toBeVisible();
    await expect(content).toHaveValue("Unsaved body stays in the editor");
    await expect(moreOptions).toBeFocused();
    await editor.getByRole("button", { name: /^Close$/i }).click();
    await expect(editor).not.toBeVisible();
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
