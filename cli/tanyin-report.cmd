@echo off
rem Windows 包装：tanyin-report（与 py -3 cli\tanyin-report 等价；需 py launcher，
rem 无 launcher 时用: python "%~dp0tanyin-report" %*）
setlocal
set "HERE=%~dp0"
py -3 "%HERE%tanyin-report" %*
endlocal & exit /b %ERRORLEVEL%