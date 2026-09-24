@echo off
rem Windows 包装：tanyin-viz（与 py -3 cli\tanyin-viz 等价；需 py launcher，
rem 无 launcher 时用: python "%~dp0tanyin-viz" %*）
setlocal
set "HERE=%~dp0"
py -3 "%HERE%tanyin-viz" %*
endlocal & exit /b %ERRORLEVEL%