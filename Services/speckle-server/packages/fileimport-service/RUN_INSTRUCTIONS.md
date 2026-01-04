# How to Run File Import Service

## To process IFC files (and other 3D models):

The file import service needs to be running separately to process uploaded IFC files.

### Steps:

1. **Open a NEW terminal window**

2. **Navigate to the fileimport-service directory:**

   ```bash
   cd C:\Users\shine\speckle1\speckle-server\packages\fileimport-service
   ```

3. **Run the development server:**

   ```bash
   yarn dev
   ```

   Or if you're using npm:

   ```bash
   npm run dev
   ```

4. **The service will:**
   - Build TypeScript files
   - Start watching for changes
   - Poll the database for new file uploads
   - Process IFC files and convert them to Speckle objects

### What to expect:

- You should see logs indicating the service is running
- When you upload an IFC file through the frontend, the service will pick it up
- Processing logs will appear in this terminal
- Once processed, the IFC will become viewable in the 3D viewer

### Troubleshooting:

- **If IFCs still aren't processing:** Check the terminal logs for errors
- **Make sure database is running:** The service needs access to PostgreSQL
- **Check file upload status:** Look at the file upload status in the database or UI

### Note:

The file import service is separate from the main server. You need both running:

- Main server (`yarn dev:minimal` or `yarn dev` from root)
- File import service (`yarn dev` from `packages/fileimport-service`)

