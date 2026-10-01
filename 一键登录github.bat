@echo off
echo ============================================
echo   双击本文件即可完成 GitHub 登录授权
echo   （只需在浏览器里点一下"授权"，无需记命令）
echo ============================================
echo.
echo 即将打开浏览器并显示一个一次性验证码。
echo 请按提示在浏览器里粘贴验证码并点击 Authorize。
echo.
pause
"C:\Program Files\GitHub CLI\gh.exe" auth login --web --git-protocol https --hostname github.com
echo.
echo ============================================
echo   登录完成后，这个窗口会自动停在下面这行。
echo   看到 "Logged in to github.com" 就成功了。
echo   直接关掉窗口，然后告诉阿朴"登录好了"即可。
echo ============================================
pause
