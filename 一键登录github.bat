@echo off
echo ============================================================
echo  GitHub Login - follow the steps below
echo ============================================================
echo.
echo  STEP 1: A one-time code like XXXX-XXXX will appear here.
echo  STEP 2: Browser opens github.com/login/device
echo          (if not, open it manually)
echo  STEP 3: Paste the code, click Continue, then Authorize.
echo  STEP 4: This window shows success by itself.
echo.
echo  Press any key to start...
pause >nul
echo.
"C:\Program Files\GitHub CLI\gh.exe" auth login --hostname github.com --git-protocol https
echo.
echo  If you see "Logged in to github.com" -> DONE.
echo  Close this window, then tell A-Pu "login done".
echo  If error, copy the red text and send to A-Pu.
pause
