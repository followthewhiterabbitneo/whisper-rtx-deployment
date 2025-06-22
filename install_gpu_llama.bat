@echo off
echo Installing llama-cpp-python with GPU support for Windows...
echo.

REM Uninstall current version
pip uninstall -y llama-cpp-python

REM Install pre-built CUDA version
echo Installing CUDA-enabled version...
pip install https://github.com/ggerganov/llama.cpp/releases/download/b4489/llama_cpp_python_cuda-0.3.2-cp311-cp311-win_amd64.whl

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo First attempt failed, trying alternative...
    pip install llama-cpp-python-cuda --extra-index-url https://jllllll.github.io/llama-cpp-python-cuBLAS-wheels/AVX2/cu121
)

echo.
echo Done! Test with: python test_gemma3_legal.py test_output/20250620_145645_LOLW.wav.txt