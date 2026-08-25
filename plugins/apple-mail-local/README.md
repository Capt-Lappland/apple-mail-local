# Apple Mail Local

Read Apple Mail safely from ChatGPT/Codex on macOS—using the accounts already configured in Mail.app, without storing mail credentials.

> [!IMPORTANT]
> This is an independent community project and is not affiliated with or endorsed by Apple or OpenAI.

## What it does

Apple Mail Local is a bundled, dependency-free MCP server for the ChatGPT/Codex desktop app. It uses Mail.app's supported Apple Events automation interface through JXA (`osascript -l JavaScript`).

By default, it exposes four read-only tools:

| Tool | Purpose |
| --- | --- |
| `mail_list_accounts` | List configured account IDs, names, types, enabled state, and addresses |
| `mail_list_mailboxes` | List mailbox paths and unread counts |
| `mail_search_messages` | Search recent messages with bounded scans and results |
| `mail_get_message` | Read metadata, recipients, attachment metadata, and a bounded body |

An optional `mail_create_reply_draft` tool can save an **unsent** reply draft after a separate local opt-in and explicit confirmation. The plugin has no tools for sending, deleting, moving, flagging, marking read/unread, downloading attachments, or synchronizing mail.

## Requirements

- macOS with Apple Mail.app configured and working.
- The ChatGPT/Codex desktop app with plugin support.
- `/usr/bin/python3` (normally supplied by the Xcode Command Line Tools on current macOS installations).
- Permission for the requesting app to automate Mail.

No mail-provider API keys, OAuth tokens, IMAP passwords, or duplicate account setup are required.

## Install from GitHub

Add this GitHub repository as a Codex marketplace, then install the plugin:

```sh
codex plugin marketplace add Capt-Lappland/apple-mail-local
codex plugin add apple-mail-local@apple-mail-local
```

Fully quit and reopen the ChatGPT/Codex desktop app, then start a **new task** so it loads the bundled MCP server.

The repository follows OpenAI's repo-marketplace layout: `.agents/plugins/marketplace.json` points to `./plugins/apple-mail-local`.

## First use and macOS permissions

1. Open Mail.app once and confirm the desired accounts work normally.
2. In a new Codex task, ask: **“List the accounts configured in Apple Mail.”**
3. When macOS asks whether ChatGPT/Codex may control Mail, choose **Allow**.
4. Review or change access at **System Settings > Privacy & Security > Automation**, under the requesting application, with **Mail** enabled.

Accessibility permission is **not required**. This plugin sends Apple Events to Mail instead of clicking its interface. Do not grant Accessibility unless you separately use a UI-automation tool.

You can trigger a count-only permission probe from Terminal:

```sh
/usr/bin/python3 ./plugins/apple-mail-local/scripts/server.py --probe-permissions
```

Apple Events permission is granted per requesting app. Allowing Terminal does not automatically allow ChatGPT/Codex.

## Example prompts

- “List the accounts and inboxes configured in Apple Mail.”
- “Find unread messages from the last three days.”
- “Search my inbox for messages from Alice about the launch.”
- “Read and summarize this message, but do not take any action.”

Message content is untrusted input. The server instructions explicitly tell the model not to follow commands embedded in email.

## Safety and privacy model

- **Read-only by default:** the default tool catalog cannot modify Mail state.
- **No credential storage:** Mail.app remains responsible for account authentication and Keychain access.
- **No plugin network client:** this code makes no network requests and does not run a background service.
- **Bounded access:** queries, mailbox listings, scans, body output, runtime, and process output have limits.
- **No shell interpolation:** validated request data is passed to JXA over stdin, not through a shell or command-line arguments.
- **Opaque references:** message lookups use bounded, validated references returned by search.
- **No raw-content logging:** the MCP server does not log prompts, message bodies, or credentials.

The integration is local, but ChatGPT/Codex may place tool results in model context and process them according to the product's configuration and privacy terms. Do not interpret “local” as meaning that displayed mail content is necessarily processed offline.

See [SECURITY.md](SECURITY.md) for the threat model and vulnerability-reporting guidance.

## Optional reply drafts

The draft tool is absent from `tools/list` by default. Enable it for the current macOS user environment only when wanted:

```sh
launchctl setenv APPLE_MAIL_ENABLE_DRAFTS 1
```

Fully quit and reopen the desktop app and start a new task. The added tool:

- requires `confirm_create_draft: true` after an explicit user request;
- saves an unsent draft in Mail;
- is annotated as state-changing but non-destructive;
- still cannot send the draft.

Disable it again with:

```sh
launchctl unsetenv APPLE_MAIL_ENABLE_DRAFTS
```

Then fully quit/reopen the app and start a new task.

## Architecture

```text
ChatGPT/Codex
  -> bundled stdio MCP server (Python standard library)
  -> strict input validation and bounded results
  -> JSON over stdin
  -> /usr/bin/osascript -l JavaScript
  -> macOS Apple Events Automation permission
  -> Mail.app and its already-configured accounts
```

The project does not parse Mail's private on-disk database and does not run an HTTP server.

## Development and tests

The normal suite uses mocks and does **not** access Mail:

```sh
/usr/bin/python3 -m unittest discover \
  -s ./plugins/apple-mail-local/tests \
  -p 'test_*.py' -v
```

It covers input validation, read-only defaults, draft confirmation, opaque references, forbidden-action checks, MCP initialization/tool listing, and an end-to-end JXA stdin/stdout health check.

An opt-in live smoke test lists account and mailbox data but does not read message bodies:

```sh
APPLE_MAIL_LIVE_TESTS=1 /usr/bin/python3 -m unittest \
  ./plugins/apple-mail-local/tests/live_smoke_test.py -v
```

Inspect the active tool schemas without accessing Mail:

```sh
/usr/bin/python3 ./plugins/apple-mail-local/scripts/server.py --print-tools
```

## Updating

Refresh the Git marketplace snapshot and reinstall the current plugin version:

```sh
codex plugin marketplace upgrade apple-mail-local
codex plugin add apple-mail-local@apple-mail-local
```

Start a new task after updating.

## Uninstalling

```sh
codex plugin remove apple-mail-local@apple-mail-local
codex plugin marketplace remove apple-mail-local
launchctl unsetenv APPLE_MAIL_ENABLE_DRAFTS
```

Removing the plugin does not change or remove accounts or messages in Mail.app.

## Limitations

- macOS only; it depends on Mail.app's Apple Events dictionary.
- Mail automation can be slower than a provider API, especially across many mailboxes.
- Search is deliberately bounded and is not intended to replace Mail's full search UI.
- The plugin reads the plain/rich text exposed by Mail and does not render HTML or open attachments.
- Draft creation is opt-in and uses Mail's reply automation; it is not a sending API.

## License

[MIT](LICENSE)
