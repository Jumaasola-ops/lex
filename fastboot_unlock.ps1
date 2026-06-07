# Fastboot Unlock Script for Infinix Hot 60 Pro+
# This script helps unlock bootloader and remove payment lock

$ADB = "C:\Users\hp\.android\platform-tools\adb.exe"
$FASTBOOT = "C:\Users\hp\.android\platform-tools\fastboot.exe"

function Check-Device {
    Write-Host "`n=== CHECKING FOR DEVICES ===" -ForegroundColor Cyan
    
    Write-Host "`nChecking ADB devices..." -ForegroundColor Yellow
    & $ADB devices
    
    Write-Host "`nChecking Fastboot devices..." -ForegroundColor Yellow
    & $FASTBOOT devices
}

function Reboot-To-Bootloader {
    Write-Host "`n=== REBOOTING TO BOOTLOADER ===" -ForegroundColor Cyan
    Write-Host "Sending reboot bootloader command..." -ForegroundColor Yellow
    & $ADB reboot bootloader
    Write-Host "Wait 5 seconds for phone to reboot..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
    Check-Device
}

function Unlock-Bootloader {
    Write-Host "`n=== UNLOCKING BOOTLOADER ===" -ForegroundColor Cyan
    Write-Host "Attempting bootloader unlock..." -ForegroundColor Yellow
    & $FASTBOOT flashing unlock
    Write-Host "If prompted on device, confirm the unlock!" -ForegroundColor Yellow
    Start-Sleep -Seconds 3
    Check-Device
}

function Erase-Userdata {
    Write-Host "`n=== ERASING USERDATA (REMOVES PAYMENT LOCK) ===" -ForegroundColor Cyan
    Write-Host "WARNING: This will erase all user data!" -ForegroundColor Red
    $confirm = Read-Host "Continue? (yes/no)"
    
    if ($confirm -eq "yes") {
        Write-Host "Erasing userdata..." -ForegroundColor Yellow
        & $FASTBOOT erase userdata
        Write-Host "Done!" -ForegroundColor Green
    }
}

function Reboot-Device {
    Write-Host "`n=== REBOOTING DEVICE ===" -ForegroundColor Cyan
    Write-Host "Rebooting phone..." -ForegroundColor Yellow
    & $FASTBOOT reboot
}

# Menu
while ($true) {
    Write-Host "`n=====================================" -ForegroundColor Green
    Write-Host "INFINIX FASTBOOT UNLOCK MENU" -ForegroundColor Green
    Write-Host "=====================================" -ForegroundColor Green
    Write-Host "1. Check Devices (ADB & Fastboot)" -ForegroundColor Cyan
    Write-Host "2. Reboot to Bootloader" -ForegroundColor Cyan
    Write-Host "3. Unlock Bootloader" -ForegroundColor Cyan
    Write-Host "4. Erase Userdata (Removes Lock)" -ForegroundColor Cyan
    Write-Host "5. Reboot Device" -ForegroundColor Cyan
    Write-Host "6. Exit" -ForegroundColor Cyan
    Write-Host "=====================================" -ForegroundColor Green
    
    $choice = Read-Host "Select option (1-6)"
    
    switch ($choice) {
        "1" { Check-Device }
        "2" { Reboot-To-Bootloader }
        "3" { Unlock-Bootloader }
        "4" { Erase-Userdata }
        "5" { Reboot-Device }
        "6" { 
            Write-Host "Exiting..." -ForegroundColor Yellow
            exit 0
        }
        default { Write-Host "Invalid option!" -ForegroundColor Red }
    }
}
