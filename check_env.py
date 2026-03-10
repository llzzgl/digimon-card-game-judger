import torch
print(f"PyTorch: {torch.__version__}")
print(f"CUDA: {torch.version.cuda}")
print(f"cuDNN: {torch.backends.cudnn.version()}")
print(f"GPU: {torch.cuda.get_device_name(0)}")
props = torch.cuda.get_device_properties(0)
print(f"Compute: {props.major}.{props.minor}")
print(f"BF16: {torch.cuda.is_bf16_supported()}")
