@echo off
rem Windows 包装：tanyin-tools（与 py -3 cli\tanyin-tools 等价；需 py launcher，
rem 无 launcher 时用: python "%~dp0tanyin-tools" %*）
setlocal
set "HERE=%~dp0"
py -3 "%HERE%tanyin-tools" %*
endlocal & exit /b %ERRORLEVEL%
