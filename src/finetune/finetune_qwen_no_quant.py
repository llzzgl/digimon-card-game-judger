# -*- coding: utf-8 -*-
"""
DTCG 规则微调脚本 - 不使用量化版本（更稳定）
适用于 bitsandbytes 有兼容性问题的环境
"""
import os
import json
import torch
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List, Dict
import logging

from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForSeq2Seq,
)
from peft import (
    LoraConfig,
    get_peft_model,
    TaskType,
    PeftModel
)
from datasets import Dataset

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class FinetuneConfig:
    """微调配置"""
    model_name: str = "Qwen/Qwen2-1.5B-Instruct"
    train_data_path: str = "training_data/dtcg_finetune_data.jsonl"
    eval_data_path: Optional[str] = None
    max_length: int = 512
    data_format: str = "instruction"
    
    # LoRA 配置
    lora_r: int = 64
    lora_alpha: int = 128
    lora_dropout: float = 0.05
    target_modules: List[str] = field(default_factory=lambda: [
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj"
    ])
    
    # 训练配置
    output_dir: str = "output/dtcg_qwen_lora"
    num_train_epochs: int = 3
    per_device_train_batch_size: int = 1
    gradient_accumulation_steps: int = 16
    learning_rate: float = 2e-4
    warmup_ratio: float = 0.1
    logging_steps: int = 10
    save_steps: int = 100
    gradient_checkpointing: bool = True
    seed: int = 42


class DTCGFineTuner:
    """DTCG 微调训练器 - 不使用量化"""
    
    CHATML_TEMPLATE = "<|im_start|>system\n{system}<|im_end|>\n<|im_start|>user\n{user}<|im_end|>\n<|im_start|>assistant\n{assistant}<|im_end|>"
    DEFAULT_SYSTEM = "你是数码宝贝卡牌游戏(DTCG)的规则专家。请准确回答关于游戏规则的问题。"
    
    def __init__(self, config: FinetuneConfig):
        self.config = config
        self.tokenizer = None
        self.model = None
        self.dataset = None
        torch.manual_seed(config.seed)
    
    def load_tokenizer(self):
        logger.info(f"📥 加载分词器: {self.config.model_name}")
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.config.model_name, trust_remote_code=True, padding_side="right"
        )
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        logger.info(f"✅ 分词器加载完成")
        return self.tokenizer

    def load_model(self):
        logger.info(f"📥 加载模型: {self.config.model_name}")
        logger.info("⚠️  不使用量化，需要更多显存")
        
        # 设置环境变量，避免 CUBLAS 问题
        os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'max_split_size_mb:128'
        
        # 不使用量化，直接加载模型
        # 使用 bfloat16 代替 float16，更稳定
        dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float32
        logger.info(f"✅ 使用数据类型: {dtype}")
        
        self.model = AutoModelForCausalLM.from_pretrained(
            self.config.model_name,
            device_map="auto",
            trust_remote_code=True,
            torch_dtype=dtype,
            use_cache=False,
            attn_implementation="eager"  # 使用标准注意力实现，避免优化导致的问题
        )
        
        # 启用 gradient checkpointing
        if self.config.gradient_checkpointing:
            self.model.gradient_checkpointing_enable()
            logger.info("✅ 启用 gradient checkpointing")
        
        # 配置 LoRA
        lora_config = LoraConfig(
            r=self.config.lora_r,
            lora_alpha=self.config.lora_alpha,
            lora_dropout=self.config.lora_dropout,
            target_modules=self.config.target_modules,
            bias="none",
            task_type=TaskType.CAUSAL_LM
        )
        
        self.model = get_peft_model(self.model, lora_config)
        
        trainable = sum(p.numel() for p in self.model.parameters() if p.requires_grad)
        total = sum(p.numel() for p in self.model.parameters())
        logger.info(f"✅ 可训练参数: {trainable:,} ({100*trainable/total:.2f}%)")
        return self.model
    
    def load_dataset(self):
        data_path = Path(self.config.train_data_path)
        if not data_path.exists():
            raise FileNotFoundError(f"训练数据不存在: {data_path}")
        
        logger.info(f"📥 加载训练数据: {data_path}")
        data_list = []
        with open(data_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    data_list.append(json.loads(line))
        
        logger.info(f"✅ 加载了 {len(data_list)} 条训练数据")
        self.dataset = Dataset.from_list(data_list)
        return self.dataset
    
    def format_example(self, example: Dict) -> str:
        system = example.get("instruction", self.DEFAULT_SYSTEM)
        user = example.get("input", "")
        assistant = example.get("output", "")
        return self.CHATML_TEMPLATE.format(system=system, user=user, assistant=assistant)
    
    def tokenize_function(self, examples):
        texts = [self.format_example({"instruction": i, "input": inp, "output": o}) 
                 for i, inp, o in zip(
                     examples.get("instruction", [self.DEFAULT_SYSTEM]*len(examples["input"])),
                     examples["input"], examples["output"])]
        
        tokenized = self.tokenizer(
            texts, truncation=True, max_length=self.config.max_length,
            padding="max_length", return_tensors=None
        )
        tokenized["labels"] = tokenized["input_ids"].copy()
        return tokenized

    def train(self):
        if self.tokenizer is None: self.load_tokenizer()
        if self.model is None: self.load_model()
        if self.dataset is None: self.load_dataset()
        
        # 清理 CUDA 缓存
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            logger.info(f"🔧 CUDA 设备: {torch.cuda.get_device_name(0)}")
            logger.info(f"🔧 CUDA 内存: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
        
        logger.info("🔄 处理训练数据...")
        tokenized_dataset = self.dataset.map(
            self.tokenize_function, batched=True,
            remove_columns=self.dataset.column_names
        )
        
        training_args = TrainingArguments(
            output_dir=self.config.output_dir,
            num_train_epochs=self.config.num_train_epochs,
            per_device_train_batch_size=self.config.per_device_train_batch_size,
            gradient_accumulation_steps=self.config.gradient_accumulation_steps,
            learning_rate=self.config.learning_rate,
            warmup_ratio=self.config.warmup_ratio,
            logging_steps=self.config.logging_steps,
            save_steps=self.config.save_steps,
            save_total_limit=3,
            fp16=True,
            optim="adamw_torch",  # 使用标准 AdamW
            lr_scheduler_type="cosine",
            report_to="tensorboard",
            gradient_checkpointing=self.config.gradient_checkpointing,
            remove_unused_columns=False,
            ddp_find_unused_parameters=False,
            dataloader_pin_memory=False
        )
        
        data_collator = DataCollatorForSeq2Seq(
            tokenizer=self.tokenizer, model=self.model, padding=True
        )
        
        trainer = Trainer(
            model=self.model, args=training_args,
            train_dataset=tokenized_dataset, data_collator=data_collator
        )
        
        logger.info("🚀 开始训练...")
        trainer.train()
        
        logger.info(f"💾 保存模型到: {self.config.output_dir}")
        trainer.save_model()
        self.tokenizer.save_pretrained(self.config.output_dir)
        
        # 保存配置
        config_path = Path(self.config.output_dir) / "finetune_config.json"
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config.__dict__, f, ensure_ascii=False, indent=2, default=list)
        
        logger.info("✅ 训练完成!")
        return trainer
    
    def merge_and_save(self, output_path: str = None):
        if output_path is None:
            output_path = f"{self.config.output_dir}_merged"
        
        logger.info("🔄 合并 LoRA 权重...")
        merged_model = self.model.merge_and_unload()
        
        logger.info(f"💾 保存合并后的模型到: {output_path}")
        merged_model.save_pretrained(output_path)
        self.tokenizer.save_pretrained(output_path)
        logger.info("✅ 模型合并完成!")
        return output_path


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="DTCG 规则微调训练（不使用量化）")
    parser.add_argument("--model", type=str, default="Qwen/Qwen2-1.5B-Instruct")
    parser.add_argument("--data", type=str, default="training_data/dtcg_finetune_data.jsonl")
    parser.add_argument("--output", type=str, default="output/dtcg_qwen_lora")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch_size", type=int, default=1)
    parser.add_argument("--max_length", type=int, default=512)
    parser.add_argument("--lora_r", type=int, default=64)
    parser.add_argument("--merge", action="store_true")
    
    args = parser.parse_args()
    
    config = FinetuneConfig(
        model_name=args.model,
        train_data_path=args.data,
        output_dir=args.output,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        max_length=args.max_length,
        lora_r=args.lora_r
    )
    
    print("=" * 60)
    print("DTCG 规则微调训练（不使用量化）")
    print("=" * 60)
    print(f"模型: {config.model_name}")
    print(f"数据: {config.train_data_path}")
    print(f"输出: {config.output_dir}")
    print(f"轮数: {config.num_train_epochs}")
    print(f"Batch size: {config.per_device_train_batch_size}")
    print(f"Max length: {config.max_length}")
    print(f"LoRA rank: {config.lora_r}")
    print(f"量化: 不使用（需要更多显存）")
    print("=" * 60)
    
    trainer = DTCGFineTuner(config)
    trainer.train()
    
    if args.merge:
        trainer.merge_and_save()


if __name__ == "__main__":
    main()
