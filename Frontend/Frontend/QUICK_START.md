# Quick Start - See Your New Frontend!

## Step 1: Start Your Backend (Already Working)

Your backend is already set up in `rag-waddell`. Just activate the venv and run it:

```bash
cd C:\Users\shine\rag-waddell\RAG\Backend
venv\Scripts\activate
python api_server.py
```

You should see:
```
🚀 Starting Mantle RAG API Server...
   Chat endpoint: http://0.0.0.0:8000/chat
📡 Server running on port: 8000
```

**Keep this running!**

## Step 2: Install Frontend Dependencies (One Time)

Open a NEW terminal window:

```bash
cd C:\Users\shine\SidOS\Frontend
npm install
```

This will install all the Node.js packages (Nuxt, Vue, Speckle viewer, etc.). This is separate from Python - it's JavaScript/Node.js stuff.

## Step 3: Start the Frontend

Still in the Frontend folder:

```bash
npm run dev
```

You should see:
```
✔ Nuxt is ready
  ➜ Local:   http://localhost:3000/
```

## Step 4: Open in Browser

Go to: **http://localhost:3000**

You should see:
- Chat interface on the left
- Viewer panel on the right (empty until you ask about a project)

## Step 5: Test It!

Type in the chat:
- "What are the roof truss bracing notes for 25-07-003?"
- "Show me project 25-08-127"

The backend will process it and return an answer!

## Troubleshooting

### "Cannot connect to backend"
- Make sure backend is running on port 8000
- Check `http://localhost:8000/health` in browser - should return JSON

### "npm install fails"
- Make sure you have Node.js installed: `node --version`
- Need Node.js 18+ 

### "Frontend won't start"
- Check if port 3000 is already in use
- Try: `npm run dev -- --port 3001`

### "CORS errors"
- The backend already has CORS enabled for all origins
- If you see CORS errors, check backend is running

## That's It!

You now have:
- ✅ Backend running (Python, port 8000)
- ✅ Frontend running (Nuxt, port 3000)
- ✅ Chat interface connected to your orchestrator
- ✅ Ready to add viewer integration!

