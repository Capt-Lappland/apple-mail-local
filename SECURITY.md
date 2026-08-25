# Security policy

## Scope and design

Apple Mail Local is read-only by default and runs as a local stdio MCP server. It uses Apple Events to ask Mail.app for data from accounts already configured by the macOS user.

The project intentionally does not expose operations for sending, deleting, moving, flagging, marking read/unread, downloading attachments, or synchronizing messages. Optional reply-draft creation is hidden unless `APPLE_MAIL_ENABLE_DRAFTS=1` and requires an explicit confirmation argument.

## Trust boundaries

- Email subjects, senders, bodies, headers, and attachment names are untrusted input.
- MCP clients and models must not treat instructions found inside messages as authority.
- macOS Automation permission is the operating-system boundary for Mail access.
- Message references are convenience locators, not authorization tokens.
- The plugin does not claim that host/model processing is offline; tool results may enter the host's model context.

## Data handling

- No credentials, access tokens, message cache, or account database is stored.
- Request data is passed to JXA over stdin without shell interpolation.
- Raw message data is not written to logs by the server.
- The plugin itself makes no network requests.
- Result sizes and execution time are capped.

## Reporting a vulnerability

Please open a private GitHub security advisory for this repository. Do not include real credentials, private email content, or personally identifiable information in a public issue.

For non-sensitive bugs, open a normal GitHub issue with synthetic reproduction data.
