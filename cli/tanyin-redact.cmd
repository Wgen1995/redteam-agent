@echo off
rem Windows 包装：tanyin-redact（与 py -3 cli\tanyin-redact 等价；需 py launcher，
rem 无 launcher 时用: python "%~dp0tanyin-redact" %*）
setlocal
set "HERE=%~dp0"
py -3 "%HERE%tanyin-redact" %*
endlocal & exit /b %ERRORLEVEL%
