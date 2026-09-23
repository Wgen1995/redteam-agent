@echo off
rem Windows 包装：tanyin-egress（与 py -3 cli\tanyin-egress 等价；需 py launcher，
rem 无 launcher 时用: python "%~dp0tanyin-egress" %*）
setlocal
set "HERE=%~dp0"
py -3 "%HERE%tanyin-egress" %*
endlocal & exit /b %ERRORLEVEL%
