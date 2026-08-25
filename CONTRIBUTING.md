# Contributing

Contributions are welcome, especially focused improvements to compatibility, validation, privacy, and tests.

## Before opening a pull request

1. Keep the default MCP tool catalog read-only.
2. Do not add send, delete, move, flag, read-state, attachment-download, or synchronization operations.
3. Do not add credential storage or direct access to Mail's private database.
4. Validate every new tool argument server-side and bound its work and output.
5. Use synthetic mail data in tests and issue reports.
6. Run the non-invasive suite:

   ```sh
   /usr/bin/python3 -m unittest discover \
     -s ./plugins/apple-mail-local/tests \
     -p 'test_*.py' -v
   ```

For security-sensitive reports, follow [SECURITY.md](SECURITY.md) instead of opening a public issue.
