@echo off
rem Windows 包装：tanyin-install（与 py -3 cli\tanyin-install 等价；需 py launcher，
rem 无 launcher 时用: python "%~dp0tanyin-install" %*）
setlocal
set "HERE=%~dp0"
py -3 "%HERE%tanyin-install" %*
endlocal & exit /b %ERRORLEVEL%
