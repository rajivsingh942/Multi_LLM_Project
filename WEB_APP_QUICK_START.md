# 🌐 Web Frontend - Quick Start Guide

**Status:** ✅ Ready to use!

---

## 🚀 Run Locally (1 minute)

### Start the web server:
```powershell
cd C:\Multi_LLM_Project
python web_app.py
```

### Open in browser:
```
http://localhost:5000
```

That's it! You should see the chat interface. 🎉

---

## 🎨 Features

✅ Beautiful chat interface  
✅ Chat with all 3 LLMs simultaneously  
✅ Real-time Firebase integration  
✅ Works on desktop, tablet, mobile  
✅ Session management  
✅ Chat history persistence  

---

## 📱 Try It Out

1. **Run:** `python web_app.py`
2. **Open:** `http://localhost:5000`
3. **Ask:** Type any question
4. **Select:** Choose model (OpenAI, Gemini, OpenRouter, or All)
5. **Send:** Click Send or press Enter
6. **Watch:** See responses in real-time!

---

## 🌍 Deploy to Get Public Link

### Fastest Option: **Render** (2 minutes)

Create file **`Procfile`** in project root:
```
web: python web_app.py
```

Then:
1. Go to [render.com](https://render.com)
2. Connect your GitHub
3. Create new Web Service
4. Add your API keys as env variables
5. Deploy!

**Your public URL:** `https://multi-llm-app.onrender.com`

---

### Alternative: **Railway** (1 minute)

1. Go to [railway.app](https://railway.app)
2. New Project → Deploy from GitHub
3. Add env variables
4. Done!

---

### Alternative: **Replit** (30 seconds)

1. Go to [replit.com](https://replit.com)
2. Create new Repl
3. Upload files
4. Click Run

---

## 📋 Full Instructions

See **`FRONTEND_DEPLOYMENT.md`** for:
- Complete setup guide
- All deployment options
- Troubleshooting
- Performance tips
- Security best practices

---

## 🔧 What You Need

✅ Python 3.13.7  
✅ Flask (`pip install flask flask-cors`)  
✅ Your LLM APIs configured  
✅ Firebase credentials (if using)  

All already set up! Just run `python web_app.py` 🎯

---

## 📞 Need Help?

| Issue | Solution |
|-------|----------|
| Port 5000 in use | Change port in `web_app.py` line 153 |
| Flask not found | Run `pip install flask flask-cors` |
| API not working | Check `.env` has all keys |
| Firebase connection fails | Verify credentials file exists |

---

## ✨ What's Included

```
✅ web_app.py          - Flask backend
✅ templates/          - Web interface
✅ FRONTEND_DEPLOYMENT.md - Complete guide
✅ requirements.txt    - All dependencies
```

---

## 🎯 Next Steps

1. **Test locally:** `python web_app.py` → Open `http://localhost:5000`
2. **Deploy:** Follow deploy instructions above
3. **Share:** Give users the live URL
4. **Monitor:** Check Firebase console for usage

---

## 💡 Pro Tips

- Use "All Models" for best responses (parallel execution)
- Session ID is unique per conversation
- Chat history auto-saves to Firebase
- Your CLI app still works: `python Main.py`
- Both CLI and web use same database!

---

**Ready?** Run `python web_app.py` and visit `http://localhost:5000` now! 🚀

For full deployment guide, see [FRONTEND_DEPLOYMENT.md](FRONTEND_DEPLOYMENT.md)
