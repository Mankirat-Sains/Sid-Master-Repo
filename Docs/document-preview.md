# Document Editor / Desktop Agent Mode

- **Detection**: streaming chat still watches `workflow`, `task_type`, or `node` for `desktop_agent`/`docgen`. When detected, `useDocumentWorkflow` switches the active workflow and opens the document pane instead of the 3D viewer.
- **New UI**: `DocumentPreviewPanel` now embeds the OnlyOffice Document Editor (real Word-like ribbon, docx-native editing). The old styled preview/PDF renderer is removed.
- **Chat wiring**: doc/agent chats still include `document_context` (structured JSON state) alongside the workflow hint so the backend can keep track of document intent. The editor itself is driven by OnlyOffice.
- **Document source**: the panel loads a document from one of:
  - `documentState.docUrl` / `documentState.onlyoffice.docUrl` / `documentState.metadata.docUrl`
  - `ONLYOFFICE_DOCUMENT_URL` (public runtime config fallback)
- **Server config**: requires an OnlyOffice Document Server reachable at `ONLYOFFICE_SERVER_URL` (e.g. `http://localhost` when running the Docker image).
- **Optional**: `ONLYOFFICE_CALLBACK_URL`, `ONLYOFFICE_USER_NAME`, `ONLYOFFICE_USER_ID` and per-document `onlyoffice.permissions` to control save/user details.
- **How to test**:
  1) Run OnlyOffice locally: `docker run -d -p 80:80 -e JWT_ENABLED=false --name onlyoffice-document-server onlyoffice/documentserver`.
  2) Set envs before `npm run dev` inside `Frontend/Frontend`:
     - `ONLYOFFICE_SERVER_URL=http://localhost`
     - `ONLYOFFICE_DOCUMENT_URL=http://localhost/documents/sample.docx` (or any docx the server can fetch)
  3) Open the workspace; when doc/agent workflow is active, the right pane should show the OnlyOffice ribbon and an editable document instead of the old modal preview.
  4) Changing the document URL or workflow metadata should reinitialise the editor; errors show inline guidance if the server/doc is missing.
