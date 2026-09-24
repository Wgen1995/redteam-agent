@echo off
rem Windows 包装：tanyin-replay（与 py -3 cli\tanyin-replay 等价；需 py launcher，
rem 无 launcher 时用: python "%~dp0tanyin-replay" %*）
setlocal
set "HERE=%~dp0"
py -3 "%HERE%tanyin-replay" %*
endlocal & exit /b %ERRORLEVEL%
