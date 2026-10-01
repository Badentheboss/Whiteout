# Manual steps

1. Run the README setup commands, then open `chrome://extensions`.
2. Turn on **Developer mode**, select **Load unpacked**, and choose `extension/dist`.
3. Open `http://127.0.0.1:8765/recipe.html` while the local fixture server is running; inspect the Parallax popup/report.
4. Create a Chrome Web Store developer account, pay its one-time fee, then use **New item** → upload `store/parallax-0.1.0.zip`. Copy the text from `store/LISTING.md`, review the privacy policy, complete store-specific disclosures, and submit.
5. To add a real-agent measurement, create a budget-capped API/local-model configuration outside the repo, run only against localhost canaries, and record model/version/budget/run ID.
6. For the rating study, open `parallax dashboard`, rate 30 queued findings for visibility and instruction intent, export `ratings.jsonl`, then run the agreement report once implemented with those ratings.
