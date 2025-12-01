# 📱 Mobile Access Instructions

## Running the Golf Scoring Probability Calculator on Your iPhone

### Quick Start

1. **Start the server** (on your computer):
   ```bash
   ./run_mobile.sh
   ```
   
   Or manually:
   ```bash
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

2. **Get your computer's IP address**:
   - The script will show you the IP address automatically
   - Or run: `hostname -I | awk '{print $1}'`
   - For example: `10.0.3.51`

3. **Connect from your iPhone**:
   - Make sure your iPhone is on the **SAME Wi-Fi network** as your computer
   - Open **Safari** on your iPhone
   - Go to: `http://YOUR_IP_ADDRESS:8000`
   - For example: `http://10.0.3.51:8000`

### Add to Home Screen (Optional but Recommended)

To make the app easily accessible like a native app:

1. Open the app in Safari on your iPhone
2. Tap the **Share** button (box with arrow)
3. Scroll down and tap **Add to Home Screen**
4. Give it a name (e.g., "Golf Calculator")
5. Tap **Add**

Now you'll have an app icon on your home screen!

### Mobile Features

✅ **Touch-optimized interface** - All buttons and inputs sized for comfortable mobile use  
✅ **No zoom on input focus** - Prevents annoying zoom behavior on iOS  
✅ **Swipeable tabs** - Easy navigation between different calculators  
✅ **Form data persistence** - Your inputs are saved locally  
✅ **Works offline** - Once loaded, most calculations work without internet  
✅ **Responsive design** - Adapts perfectly to your iPhone screen

### Troubleshooting

**Can't connect from iPhone?**
- Verify both devices are on the same Wi-Fi network
- Check if firewall is blocking port 8000
- Try using the computer's IP address instead of `localhost`
- Make sure the server is running (`./run_mobile.sh`)

**Page loads but data doesn't save?**
- Make sure you're using Safari (other browsers may have restrictions)
- Check that Safari's "Block All Cookies" setting is disabled

**Buttons too small?**
- Try landscape mode for wider spacing
- All touch targets are minimum 44x44px per iOS guidelines

### System Requirements

- **Computer**: Python 3.12+, any OS (Mac, Windows, Linux)
- **iPhone**: iOS 12+ with Safari browser
- **Network**: Both devices must be on the same local network (Wi-Fi)

### Security Note

This setup is for **local network use only**. The app is accessible to anyone on your Wi-Fi network. Do not expose it to the internet without proper security measures.
