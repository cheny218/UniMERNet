import os
import sys
import argparse
import torch
from PIL import Image

# 兼容打包前后的绝对路径定位
if getattr(sys, 'frozen', False):
    base_dir = os.path.dirname(sys.executable)
    os.chdir(base_dir)  # 锁定工作目录为 exe 所在目录
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))

if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from unimernet.common.config import Config
import unimernet.tasks as tasks
from unimernet.processors import load_processor


class UniMERNetEngine:
    def __init__(self, cfg_path: str = None, model_path: str = None, device: str = None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        
        # 自动探测 demo.yaml
        possible_cfg_paths = [
            cfg_path,
            os.path.join(base_dir, "configs", "demo.yaml"),
            os.path.join(base_dir, "_internal", "configs", "demo.yaml"),
            os.path.join(base_dir, "..", "configs", "demo.yaml"),
        ]
        self.cfg_path = next((p for p in possible_cfg_paths if p and os.path.exists(p)), "configs/demo.yaml")
        
        # 自动探测本地模型权重文件
        possible_model_paths = [
            model_path,
            os.path.join(base_dir, "models", "unimernet_base", "unimernet_base.pth"),
            os.path.join(base_dir, "models", "unimernet_base", "pytorch_model.pth"),
        ]
        self.model_path = next((p for p in possible_model_paths if p and os.path.exists(p)), None)
        
        self.model = None
        self.vis_processor = None
        self._load_model()

    def _load_model(self):
        # 采用官方标准的方式加载 Config
        args = argparse.Namespace(cfg_path=self.cfg_path, options=None)
        cfg = Config(args)

        # 动态绑定已放置好的模型权重路径
        if self.model_path:
            cfg.config.model.pretrained = self.model_path
            cfg.config.model.model_config.model_name = os.path.dirname(self.model_path)
            cfg.config.model.tokenizer_config.path = os.path.dirname(self.model_path)

        task = tasks.setup_task(cfg)
        self.model = task.build_model(cfg).to(self.device).eval()
        self.vis_processor = load_processor(
            'formula_image_eval', 
            cfg.config.datasets.formula_rec_eval.vis_processor.eval
        )

    def predict(self, image: Image.Image) -> str:
        if image.mode != "RGB":
            image = image.convert("RGB")
        processed_img = self.vis_processor(image).unsqueeze(0).to(self.device)
        with torch.no_grad():
            output = self.model.generate({"image": processed_img})
        
        latex_code = output.get("pred_str", [""])[0]
        return latex_code.strip()
