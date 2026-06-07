# Infinix Hot 60 Pro + Recovery Mode Guide

## 🔄 Recovery Mode Entry Methods for Infinix Hot 60 Pro +

Since standard Android methods didn't work, Infinix uses custom recovery combinations.

---

## ✅ Method 1: Volume UP + Power (RECOMMENDED)

```
1. Power OFF the phone completely
2. Wait 5 seconds
3. Press and HOLD together:
   - Volume UP button
   - Power button
4. Keep holding for 15-20 seconds (LONGER than usual)
5. You should see:
   - Infinix logo
   - Recovery menu appears
6. RELEASE the buttons
```

**What to look for:**
- Infinix boot logo appears
- Menu with options appears
- Usually shows options like:
  - Reboot System
  - Wipe data/factory reset
  - Wipe cache partition

---

## ✅ Method 2: Volume DOWN + Power (ALTERNATIVE)

If Method 1 doesn't work:

```
1. Power OFF completely
2. Hold: Volume DOWN + Power together
3. Hold for 20-25 seconds (even longer)
4. Watch for boot logo
5. When menu appears, release buttons
```

---

## ✅ Method 3: Power Button Multiple Presses

```
1. Power OFF
2. While OFF, press Power button:
   - Press and hold for 3 seconds
   - Release
   - Press again for 3 seconds
   - Release
   - Press again for 5 seconds and HOLD
3. This sometimes triggers recovery boot
```

---

## ✅ Method 4: ADB Reboot to Recovery (if ADB connected)

```powershell
# If device is connected via USB:
adb reboot recovery

# You'll immediately enter recovery mode
# No button pressing needed!
```

---

## 🎯 FACTORY RESET in Recovery Mode

Once in recovery menu:

```
1. You should see a menu with options
2. Look for:
   - "Wipe data/factory reset"
   - "Format data"
   - "Erase everything"

3. Use Volume buttons to navigate (up/down)

4. Press Power button to SELECT

5. Confirm when prompted:
   - Look for "YES" or "CONFIRM"
   - Press Power button on "YES"

6. Wait for reset to complete (2-5 minutes)

7. Device will reboot automatically

8. ✓ MALWARE IS GONE
   ✓ Phone is factory new
   ✓ No lock screen
   ✓ Start fresh setup
```

---

## ⏱️ Button Timing for Infinix

| Method | Hold Duration | Extra Notes |
|--------|--------------|------------|
| Vol UP + Power | 15-20s | Most reliable |
| Vol DOWN + Power | 20-25s | Longer hold |
| Power only | 5s then 3s | Less common |
| ADB reboot | N/A | Easiest if USB works |

**KEY: Hold longer than standard Android!** Infinix requires extended button holding.

---

## 🔴 If Recovery Mode Still Won't Enter

Try this nuclear method:

```
1. Power OFF
2. Hold Volume UP
3. While holding UP, press Power 5 times quickly
4. Keep holding Volume UP
5. Release after boot logo appears
```

Or:

```
1. Power OFF
2. Hold Volume DOWN
3. Press Power button repeatedly (10 times) while holding DOWN
4. Release when logo appears
```

---

## 💻 If You Have USB Access (EASIEST)

```powershell
# Connect via USB cable
# Select File Transfer mode on phone

# Then use ADB:
adb reboot recovery

# Immediately enters recovery without button pressing!
# Then select factory reset from menu
```

---

## 🎯 Factory Reset Steps (Visual Guide)

```
Boot Menu (Recovery)
│
├─ Reboot System
├─ Wipe Data/Factory Reset  ← SELECT THIS
├─ Wipe Cache Partition
└─ Power Off

[Press Power on "Wipe Data/Factory Reset"]
    ↓
Confirm Wipe? (Yes/No)

[Navigate to "Yes" with Volume buttons]
[Press Power on "Yes"]
    ↓
Wiping... (wait 2-5 minutes)
    ↓
Reboot System Now

[Device reboots]
    ↓
✓ CLEAN FACTORY PHONE
✓ MALWARE REMOVED
✓ START FRESH SETUP
```

---

## 📋 Recovery Mode Menu Navigation

| Button | Action |
|--------|--------|
| **Volume UP** | Move UP in menu |
| **Volume DOWN** | Move DOWN in menu |
| **Power** | SELECT menu item |
| **Power** + **Vol UP** | Quit menu (sometimes) |

---

## ⚠️ Important Safety Tips

✅ **Safe to do:**
- Factory reset removes everything, but safely
- It's done at firmware level (before OS loads)
- Cannot fail or brick device
- Malware cannot interfere

❌ **Don't:**
- Don't disconnect during wipe
- Don't press random buttons
- Don't power off during wipe
- Don't interrupt the process

✓ **Do:**
- Let it complete fully
- Wait for reboot to finish
- Let it settle for 2 minutes after boot
- Then start setup fresh

---

## 🆘 If Factory Reset Doesn't Work

This is extremely rare, but if recovery menu won't appear:

### **Contact Infinix Support**
- Phone: (Infinix support number)
- Website: www.infinixmobility.com
- Email: support@infinix.com

### **Hardware Reset as Last Resort**
```
1. Power OFF
2. Remove battery (if removable)
3. Wait 30 seconds
4. Reinsert battery
5. Power ON
6. Try recovery again
```

---

## 🎯 Quick Checklist

- [ ] Phone is completely powered OFF
- [ ] I'm holding Volume UP (or DOWN) and Power together
- [ ] Holding for 15-20+ seconds (LONGER than usual)
- [ ] I see Infinix logo and menu
- [ ] Selecting "Wipe data/factory reset"
- [ ] Confirming "YES"
- [ ] NOT interrupting during wipe
- [ ] Waiting for complete reboot
- [ ] ✓ Phone is now factory new!

---

## 📞 My Recommendations (Priority Order)

1. **FIRST: Try Method 1** (Vol UP + Power, hold 20 seconds)
2. **SECOND: Try Method 4** (ADB reboot if USB works)
3. **THIRD: Try Method 2** (Vol DOWN + Power, hold 25 seconds)
4. **FOURTH: Try Method 3** (Power button presses)
5. **FIFTH: Try Nuclear Method** (Extended button combos)
6. **SIXTH: Contact Infinix Support** (if none work)

---

## ✅ Success Signs

When you did it right:
- Boot logo appears within 20 seconds
- Recovery menu is displayed
- Factory reset starts
- Phone goes dark for several minutes
- Infinix logo and setup screen appear
- **NEW PHONE - MALWARE FREE**

---

**Your Infinix Hot 60 Pro + will be completely clean after factory reset!**
